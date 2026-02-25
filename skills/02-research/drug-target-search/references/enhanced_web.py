"""Enhanced Web tools: web_search with multiple providers and web_fetch."""

import html
import json
import os
import re
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

from nanobot.agent.tools.base import Tool

# Shared constants
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2) AppleWebKit/537.36"
MAX_REDIRECTS = 5


def _strip_tags(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<script[\s\S]*?</script>', '', text, flags=re.I)
    text = re.sub(r'<style[\s\S]*?</style>', '', text, flags=re.I)
    text = re.sub(r'<[^>]+>', '', text)
    return html.unescape(text).strip()


def _normalize(text: str) -> str:
    """Normalize whitespace."""
    text = re.sub(r'[ \t]+', ' ', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def _validate_url(url: str) -> tuple[bool, str]:
    """Validate URL: must be http(s) with valid domain."""
    try:
        p = urlparse(url)
        if p.scheme not in ('http', 'https'):
            return False, f"Only http/https allowed, got '{p.scheme or 'none'}'"
        if not p.netloc:
            return False, "Missing domain"
        return True, ""
    except Exception as e:
        return False, str(e)


class WebSearchTool(Tool):
    """Search the web using multiple providers (Brave, Exa, or DuckDuckGo fallback)."""
    
    name = "web_search"
    description = "Search the web. Returns titles, URLs, and snippets. Supports multiple search providers."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "count": {"type": "integer", "description": "Results (1-20)", "minimum": 1, "maximum": 20},
            "provider": {"type": "string", "description": "Search provider: brave, exa, duckduckgo", "enum": ["brave", "exa", "duckduckgo"]}
        },
        "required": ["query"]
    }
    
    def __init__(self, brave_api_key: str | None = None, exa_api_key: str | None = None, max_results: int = 10):
        self.brave_api_key = brave_api_key or os.environ.get("BRAVE_API_KEY", "")
        self.exa_api_key = exa_api_key or os.environ.get("EXA_API_KEY", "")
        self.max_results = max_results
    
    async def execute(self, query: str, count: int | None = None, provider: str = "auto", **kwargs: Any) -> str:
        n = min(max(count or self.max_results, 1), 20)
        
        # Try providers in order
        if provider == "exa" or (provider == "auto" and self.exa_api_key):
            result = await self._search_exa(query, n)
            if not result.startswith("Error"):
                return result
        
        if provider == "brave" or (provider == "auto" and self.brave_api_key):
            result = await self._search_brave(query, n)
            if not result.startswith("Error"):
                return result
        
        # Fallback to DuckDuckGo (no API key needed)
        if provider in ("duckduckgo", "auto"):
            result = await self._search_duckduckgo(query, n)
            if not result.startswith("Error"):
                return result
        
        return f"Error: No search provider available. Set BRAVE_API_KEY or EXA_API_KEY environment variable."
    
    async def _search_brave(self, query: str, count: int) -> str:
        """Search using Brave Search API."""
        if not self.brave_api_key:
            return "Error: BRAVE_API_KEY not configured"
        
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params={"q": query, "count": count},
                    headers={"Accept": "application/json", "X-Subscription-Token": self.brave_api_key},
                    timeout=15.0
                )
                r.raise_for_status()
            
            results = r.json().get("web", {}).get("results", [])
            if not results:
                return f"No results for: {query}"
            
            lines = [f"## Brave Search Results: {query}\n"]
            for i, item in enumerate(results[:count], 1):
                lines.append(f"### {i}. {item.get('title', 'No title')}\n")
                lines.append(f"**URL**: {item.get('url', '')}")
                if desc := item.get("description"):
                    lines.append(f"**Summary**: {desc[:300]}...")
                lines.append("")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"
    
    async def _search_exa(self, query: str, count: int) -> str:
        """Search using Exa AI API (high-quality results)."""
        if not self.exa_api_key:
            return "Error: EXA_API_KEY not configured"
        
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://api.exa.ai/search",
                    json={
                        "query": query,
                        "numResults": count,
                        "useAutoprompt": True,
                        "type": "auto"
                    },
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": self.exa_api_key
                    },
                    timeout=30.0
                )
                r.raise_for_status()
            
            data = r.json()
            results = data.get("results", [])
            if not results:
                return f"No results for: {query}"
            
            lines = [f"## Exa Search Results: {query}\n"]
            for i, item in enumerate(results[:count], 1):
                lines.append(f"### {i}. {item.get('title', 'No title')}\n")
                lines.append(f"**URL**: {item.get('url', '')}")
                if text := item.get("text"):
                    lines.append(f"**Content**: {text[:400]}...")
                if author := item.get("author"):
                    lines.append(f"**Author**: {author}")
                if date := item.get("publishedDate"):
                    lines.append(f"**Date**: {date}")
                lines.append("")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"
    
    async def _search_duckduckgo(self, query: str, count: int) -> str:
        """Search using DuckDuckGo Instant Answer API (free, no API key)."""
        try:
            async with httpx.AsyncClient() as client:
                # DuckDuckGo HTML search (no official API, but works)
                r = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": USER_AGENT},
                    timeout=15.0
                )
                r.raise_for_status()
            
            # Parse results from HTML
            results = []
            pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, r.text)
            
            for url, title in matches[:count]:
                # DuckDuckGo uses redirect URLs, extract actual URL
                if "uddg=" in url:
                    from urllib.parse import unquote
                    actual_url = unquote(url.split("uddg=")[-1].split("&")[0])
                else:
                    actual_url = url
                results.append({"title": _strip_tags(title), "url": actual_url})
            
            if not results:
                return f"No results for: {query}"
            
            lines = [f"## DuckDuckGo Search Results: {query}\n"]
            lines.append("*Note: Using DuckDuckGo (free tier). For better results, set BRAVE_API_KEY or EXA_API_KEY*\n")
            for i, item in enumerate(results, 1):
                lines.append(f"### {i}. {item['title']}\n")
                lines.append(f"**URL**: {item['url']}")
                lines.append("")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"


class WebFetchTool(Tool):
    """Fetch and extract content from a URL using Readability."""
    
    name = "web_fetch"
    description = "Fetch URL and extract readable content (HTML → markdown/text)."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to fetch"},
            "extractMode": {"type": "string", "enum": ["markdown", "text"], "default": "markdown"},
            "maxChars": {"type": "integer", "minimum": 100}
        },
        "required": ["url"]
    }
    
    def __init__(self, max_chars: int = 50000):
        self.max_chars = max_chars
    
    async def execute(self, url: str, extractMode: str = "markdown", maxChars: int | None = None, **kwargs: Any) -> str:
        from readability import Document

        max_chars = maxChars or self.max_chars

        # Validate URL before fetching
        is_valid, error_msg = _validate_url(url)
        if not is_valid:
            return json.dumps({"error": f"URL validation failed: {error_msg}", "url": url})

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                max_redirects=MAX_REDIRECTS,
                timeout=30.0
            ) as client:
                r = await client.get(url, headers={"User-Agent": USER_AGENT})
                r.raise_for_status()
            
            ctype = r.headers.get("content-type", "")
            
            # JSON
            if "application/json" in ctype:
                text, extractor = json.dumps(r.json(), indent=2), "json"
            # HTML
            elif "text/html" in ctype or r.text[:256].lower().startswith(("<!doctype", "<html")):
                doc = Document(r.text)
                content = self._to_markdown(doc.summary()) if extractMode == "markdown" else _strip_tags(doc.summary())
                text = f"# {doc.title()}\n\n{content}" if doc.title() else content
                extractor = "readability"
            else:
                text, extractor = r.text, "raw"
            
            truncated = len(text) > max_chars
            if truncated:
                text = text[:max_chars]
            
            return json.dumps({"url": url, "finalUrl": str(r.url), "status": r.status_code,
                              "extractor": extractor, "truncated": truncated, "length": len(text), "text": text})
        except Exception as e:
            return json.dumps({"error": str(e), "url": url})
    
    def _to_markdown(self, html: str) -> str:
        """Convert HTML to markdown."""
        text = re.sub(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>',
                      lambda m: f'[{_strip_tags(m[2])}]({m[1]})', html, flags=re.I)
        text = re.sub(r'<h([1-6])[^>]*>([\s\S]*?)</h\1>',
                      lambda m: f'\n{"#" * int(m[1])} {_strip_tags(m[2])}\n', text, flags=re.I)
        text = re.sub(r'<li[^>]*>([\s\S]*?)</li>', lambda m: f'\n- {_strip_tags(m[1])}', text, flags=re.I)
        text = re.sub(r'</(p|div|section|article)>', '\n\n', text, flags=re.I)
        text = re.sub(r'<(br|hr)\s*/?>', '\n', text, flags=re.I)
        return _normalize(_strip_tags(text))


# Export tool classes for registration
TOOLS = [WebSearchTool, WebFetchTool]
