#!/usr/bin/env python3
"""
Literature search script - fetches PubMed articles.
"""

import argparse
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List
from urllib.parse import quote

import requests


NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


@dataclass
class PubMedArticle:
    """PubMed article record."""
    pmid: str
    title: Optional[str]
    authors: str
    journal: Optional[str]
    year: Optional[str]
    doi: Optional[str]
    pmcid: Optional[str]
    abstract: Optional[str]
    pubmed_url: str


def _get_xml(url: str, params: dict, timeout_s: int = 30, retries: int = 3) -> str:
    """GET XML from NCBI with retries."""
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout_s)
            r.raise_for_status()
            return r.text
        except Exception as e:
            last_exc = e
            time.sleep(0.5 * (2 ** attempt))
    raise RuntimeError(f"Failed after {retries} attempts") from last_exc


def _get_json(url: str, params: dict, timeout_s: int = 30, retries: int = 3) -> dict:
    """GET JSON with retries."""
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout_s)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_exc = e
            time.sleep(0.5 * (2 ** attempt))
    raise RuntimeError(f"Failed after {retries} attempts") from last_exc


def search_pubmed(query: str, max_results: int = 20) -> List[str]:
    """Search PubMed and return PMIDs."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance"
    }
    
    data = _get_json(f"{NCBI_EUTILS}/esearch.fcgi", params)
    id_list = data.get("esearchresult", {}).get("idlist", [])
    return id_list


def fetch_articles(pmids: List[str]) -> List[PubMedArticle]:
    """Fetch article details for PMIDs."""
    if not pmids:
        return []
    
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }
    
    xml = _get_xml(f"{NCBI_EUTILS}/efetch.fcgi", params)
    
    # Parse XML
    articles = []
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml)
        
        for article in root.findall(".//PubmedArticle"):
            pmid = article.findtext(".//PMID") or ""
            
            # Title
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else None
            
            # Authors
            authors = []
            for author in article.findall(".//Author"):
                last = author.findtext("LastName") or ""
                fore = author.findtext("ForeName") or ""
                if last:
                    authors.append(f"{last} {fore}".strip())
            authors_str = "; ".join(authors[:5])
            if len(authors) > 5:
                authors_str += f" et al."
            
            # Journal
            journal = article.findtext(".//Journal/Title")
            
            # Year
            year = article.findtext(".//PubDate/Year")
            if not year:
                year = article.findtext(".//ArticleDate/Year")
            
            # DOI
            doi = None
            for eloc in article.findall(".//ArticleId"):
                if eloc.get("IdType") == "doi":
                    doi = eloc.text
                    break
            
            # PMCID
            pmcid = None
            for eloc in article.findall(".//ArticleId"):
                if eloc.get("IdType") == "pmc":
                    pmcid = eloc.text
                    break
            
            # Abstract
            abstract_parts = []
            for abstract_text in article.findall(".//Abstract/AbstractText"):
                label = abstract_text.get("Label", "")
                text = abstract_text.text or ""
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts)[:500] if abstract_parts else None
            
            articles.append(PubMedArticle(
                pmid=pmid,
                title=title,
                authors=authors_str,
                journal=journal,
                year=year,
                doi=doi,
                pmcid=pmcid,
                abstract=abstract,
                pubmed_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            ))
    except Exception as e:
        print(f"Warning: XML parsing error: {e}")
    
    return articles


def format_summary(articles: List[PubMedArticle]) -> str:
    """Format articles as markdown summary."""
    lines = [f"# Literature Search Results\n"]
    lines.append(f"Found {len(articles)} articles\n")
    
    for i, art in enumerate(articles, 1):
        lines.append(f"## {i}. {art.title or 'No title'}\n")
        lines.append(f"- **PMID**: [{art.pmid}]({art.pubmed_url})")
        if art.authors:
            lines.append(f"- **Authors**: {art.authors}")
        if art.journal:
            lines.append(f"- **Journal**: {art.journal}")
        if art.year:
            lines.append(f"- **Year**: {art.year}")
        if art.doi:
            lines.append(f"- **DOI**: [{art.doi}](https://doi.org/{art.doi})")
        if art.pmcid:
            lines.append(f"- **PMCID**: {art.pmcid}")
        if art.abstract:
            lines.append(f"\n**Abstract**: {art.abstract[:300]}...")
        lines.append("")
    
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Search PubMed for literature")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--max-results", type=int, default=20, help="Max results")
    parser.add_argument("--sleep-s", type=float, default=0.4, help="Sleep between requests")
    args = parser.parse_args()
    
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Searching PubMed: {args.query}")
    pmids = search_pubmed(args.query, args.max_results)
    print(f"Found {len(pmids)} PMIDs")
    
    time.sleep(args.sleep_s)
    
    articles = fetch_articles(pmids)
    
    # Save TSV
    import pandas as pd
    df = pd.DataFrame([asdict(a) for a in articles])
    df.to_csv(out_dir / "pubmed_results.tsv", sep="\t", index=False)
    
    # Save summary
    summary = format_summary(articles)
    (out_dir / "literature_summary.md").write_text(summary)
    
    print(f"Processed {len(articles)} articles")
    print(f"Output: {out_dir}")


if __name__ == "__main__":
    main()
