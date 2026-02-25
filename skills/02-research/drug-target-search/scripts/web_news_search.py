#!/usr/bin/env python3
"""
Web news search script - fetches latest news from FDA, pharma, journals.
Uses web search API to find recent developments.
"""

import argparse
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from urllib.parse import quote

import requests


# Search query templates for different news types
QUERY_TEMPLATES = {
    "fda_approval": "{drug} FDA approval",
    "clinical_trial": "{drug} OR {target} clinical trial results",
    "press_release": "{drug} {company} press release",
    "breakthrough": "{target} OR {disease} treatment breakthrough 2024",
    "regulatory": "{drug} FDA EMA designation orphan breakthrough",
}


@dataclass
class NewsResult:
    """Web news search result."""
    query: str
    title: str
    url: str
    snippet: str
    source: Optional[str]
    date: Optional[str]
    relevance: str  # high/medium/low


def extract_source(url: str) -> str:
    """Extract source name from URL."""
    domain_map = {
        "fda.gov": "FDA",
        "ema.europa.eu": "EMA",
        "clinicaltrials.gov": "ClinicalTrials.gov",
        "nature.com": "Nature",
        "science.org": "Science",
        "cell.com": "Cell",
        "nejm.org": "NEJM",
        "biorxiv.org": "BioRxiv",
        "medrxiv.org": "MedRxiv",
        "pubmed.ncbi.nlm.nih.gov": "PubMed",
        "reuters.com": "Reuters",
        "bloomberg.com": "Bloomberg",
        "statnews.com": "STAT News",
        "fiercebiotech.com": "FierceBiotech",
        "biopharmadive.com": "BioPharma Dive",
        "genengnews.com": "GEN",
        "novartis.com": "Novartis",
        "roche.com": "Roche",
        "pfizer.com": "Pfizer",
        "merck.com": "Merck",
        "astrazeneca.com": "AstraZeneca",
    }
    
    for domain, source in domain_map.items():
        if domain in url.lower():
            return source
    
    # Extract domain name as fallback
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        return domain.replace("www.", "").split(".")[0].title()
    except:
        return "Unknown"


def search_brave(query: str, api_key: str, count: int = 10) -> List[NewsResult]:
    """Search using Brave Search API."""
    if not api_key:
        return [NewsResult(
            query=query,
            title="Error: BRAVE_API_KEY not configured",
            url="",
            snippet="Set BRAVE_API_KEY environment variable or use --api-key",
            source=None,
            date=None,
            relevance="error"
        )]
    
    try:
        r = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": count, "freshness": "pw"},  # Past week
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": api_key
            },
            timeout=15
        )
        r.raise_for_status()
        
        results = []
        data = r.json()
        
        for item in data.get("web", {}).get("results", []):
            url = item.get("url", "")
            results.append(NewsResult(
                query=query,
                title=item.get("title", ""),
                url=url,
                snippet=item.get("description", ""),
                source=extract_source(url),
                date=None,  # Brave doesn't always provide dates
                relevance="medium"
            ))
        
        return results
    
    except Exception as e:
        return [NewsResult(
            query=query,
            title=f"Search error: {str(e)}",
            url="",
            snippet="",
            source=None,
            date=None,
            relevance="error"
        )]


def format_summary(results: List[NewsResult]) -> str:
    """Format news results as markdown summary."""
    lines = ["# Web News Search Results\n"]
    
    # Group by query
    by_query = {}
    for r in results:
        if r.query not in by_query:
            by_query[r.query] = []
        by_query[r.query].append(r)
    
    for query, items in by_query.items():
        lines.append(f"## Query: {query}\n")
        
        for item in items:
            if item.relevance == "error":
                lines.append(f"**Error**: {item.title}\n")
                continue
            
            lines.append(f"### [{item.title}]({item.url})\n")
            if item.source:
                lines.append(f"- **Source**: {item.source}")
            if item.date:
                lines.append(f"- **Date**: {item.date}")
            if item.snippet:
                lines.append(f"- **Summary**: {item.snippet[:200]}...")
            lines.append("")
    
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Search web for drug/target news")
    parser.add_argument("--query", required=True, help="Search query (or use --drug, --target)")
    parser.add_argument("--drug", help="Drug name for templated searches")
    parser.add_argument("--target", help="Target name for templated searches")
    parser.add_argument("--disease", help="Disease name for templated searches")
    parser.add_argument("--company", help="Company name for press releases")
    parser.add_argument("--search-type", choices=["fda_approval", "clinical_trial", "press_release", "breakthrough", "regulatory"],
                        help="Use predefined query template")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--api-key", help="Brave Search API key (or set BRAVE_API_KEY)")
    parser.add_argument("--count", type=int, default=10, help="Results per query")
    args = parser.parse_args()
    
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Get API key
    import os
    api_key = args.api_key or os.environ.get("BRAVE_API_KEY", "")
    
    # Build queries
    queries = []
    
    if args.search_type and args.drug:
        template = QUERY_TEMPLATES.get(args.search_type, "{drug}")
        query = template.format(
            drug=args.drug or "",
            target=args.target or "",
            disease=args.disease or "",
            company=args.company or ""
        )
        queries.append(query)
    else:
        queries.append(args.query)
    
    # Add recent news query
    if args.drug or args.target:
        recent_query = f"{args.drug or args.target} latest news 2024"
        queries.append(recent_query)
    
    # Search
    all_results: List[NewsResult] = []
    
    for query in queries:
        print(f"Searching: {query}")
        results = search_brave(query, api_key, args.count)
        all_results.extend(results)
        time.sleep(0.5)  # Rate limiting
    
    # Save JSON
    json_data = [asdict(r) for r in all_results]
    (out_dir / "web_news_results.json").write_text(
        json.dumps(json_data, indent=2) + "\n"
    )
    
    # Save summary
    summary = format_summary(all_results)
    (out_dir / "web_news_summary.md").write_text(summary)
    
    # Stats
    errors = sum(1 for r in all_results if r.relevance == "error")
    print(f"Found {len(all_results) - errors} results ({errors} errors)")
    print(f"Output: {out_dir}")


if __name__ == "__main__":
    main()
