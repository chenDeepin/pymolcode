---
name: drug-target-search
description: "AI-powered drug discovery pipeline. Searches databases (PubChem, ChEMBL, PDB), PubMed, patents (Google Patents, USPTO), AND web for FDA/pharma news. LLM extracts drugs, targets, IC50, clinical phases. Use for drug discovery, target identification, compound search, patent analysis, or building target dossiers."
metadata:
  nanobot:
    emoji: "💊"
    requires:
      bins: ["python3"]
    always: false
---

# Drug-Target Search Pipeline

AI-powered pipeline combining **databases** + **literature** + **patents** + **web news** with LLM extraction.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DRUG-TARGET PIPELINE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐          │
│  │ DATABASES │ │ LITERATURE│ │  PATENTS  │ │ WEB NEWS  │          │
│  ├───────────┤ ├───────────┤ ├───────────┤ ├───────────┤          │
│  │• UniProt  │ │• PubMed   │ │• Google   │ │• FDA.gov  │          │
│  │• PubChem  │ │• BioRxiv  │ │  Patents  │ │• EMA      │          │
│  │• ChEMBL   │ │• Journals │ │• USPTO    │ │• Pharma   │          │
│  │• RCSB PDB │ │           │ │• Lens.org │ │• Press    │          │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘          │
│        │             │             │             │                 │
│        └─────────────┴──────┬──────┴─────────────┘                 │
│                             ▼                                       │
│                     ┌──────────────┐                               │
│                     │   LLM (You)  │  ← No BioBERT needed!         │
│                     ├──────────────┤                               │
│                     │ • Extract    │                               │
│                     │   compounds  │                               │
│                     │   targets    │                               │
│                     │   IC50 data  │                               │
│                     │ • Analyze    │                               │
│                     │   trends     │                               │
│                     │ • Reason     │                               │
│                     └──────┬───────┘                               │
│                            ▼                                        │
│                     ┌──────────────┐                               │
│                     │   DOSSIER    │                               │
│                     └──────────────┘                               │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Full pipeline with patents and web news
python3 scripts/pipeline.py \
  --target "CDK4" \
  --uniprot "P11802" \
  --compounds "Palbociclib,Abemaciclib" \
  --include-patents \
  --include-web \
  --out-dir output/cdk4
```

## Scripts

### 1. Target Search (UniProt)
```bash
python3 scripts/target_search.py --target "CDK4" --uniprot "P11802" --out-dir output/
```

### 2. Compound Search (PubChem + ChEMBL)
```bash
python3 scripts/compound_search.py --names "Palbociclib,Abemaciclib" --out-dir output/
```

### 3. Structure Search (RCSB PDB)
```bash
python3 scripts/structure_search.py --uniprot "P11802" --out-dir output/
```

### 4. Literature Search (PubMed)
```bash
python3 scripts/literature_search.py --query "CDK4 selective inhibitor" --out-dir output/
```

### 5. Patent Search (Google Patents, USPTO) ⭐ NEW
```bash
python3 scripts/patent_search.py \
  --target "CDK4" \
  --mechanism "selective inhibitor" \
  --count 20 \
  --out-dir output/
```

### 6. Web News Search (FDA, Pharma, Journals)
```bash
python3 scripts/web_news_search.py --query "CDK4 inhibitor FDA" --out-dir output/
```

### 7. Full Pipeline (All Sources)
```bash
python3 scripts/pipeline.py \
  --target "CDK4" \
  --uniprot "P11802" \
  --compounds "Palbociclib,Abemaciclib,Ribociclib" \
  --include-patents \
  --include-web \
  --out-dir output/cdk4_full
```

---

## Patent Search ⭐ NEW

### Why Patents Matter

Patents contain information **not yet published** in papers:
- Novel compound structures (years before papers)
- Synthetic routes and procedures
- Full IC50/EC50 data tables
- Company pipeline insights
- Priority dates reveal R&D timeline

### Patent Search Usage

```bash
# Search for CDK4 selective inhibitor patents
python3 scripts/patent_search.py \
  --target "CDK4" \
  --mechanism "selective inhibitor" \
  --count 30 \
  --sort-by newest \
  --out-dir output/cdk4_patents

# Search for specific compound patents
python3 scripts/patent_search.py \
  --compound "Palbociclib" \
  --out-dir output/palbociclib_patents
```

### Patent Output Files

```
output/
├── patent_results.json      # Raw patent data
├── patent_summary.md        # Human-readable summary
└── patent_llm_prompt.md     # Ready-to-use LLM analysis prompt
```

### LLM Deep Analysis of Patents

After patent search, ask nanobot to analyze:

```
Read the file patent_llm_prompt.md and provide:
1. Key novel compounds discovered
2. IC50 potency ranges for CDK4 vs CDK6
3. Which companies are most active
4. What scaffold trends are emerging
5. What's the competitive landscape
```

---

## LLM Extraction Guidelines

### Entities to Extract

| Type | Examples | Look For |
|------|----------|----------|
| **Drugs/Compounds** | Palbociclib, IAG933 | "compound", "inhibitor", "candidate", Example numbers |
| **Targets** | CDK4, CDK6, TEAD1 | "target", "kinase", "receptor", "enzyme" |
| **Selectivity** | CDK4 vs CDK6 | IC50 ratios, "selective", "pan-", "dual-" |
| **Potency** | IC50 = 50 nM | Numbers with nM, μM, pM |
| **Clinical Phase** | Phase 3, approved | "Phase I/II/III", "approved", "NDA" |
| **Companies** | Pfizer, Novartis | Assignee names, "developed by" |
| **Scaffolds** | Pyrimidine, quinazoline | Core chemical structures |
| **Patent Dates** | Priority 2022-03-15 | Filing dates reveal timeline |

### Patent-Specific Extraction

When analyzing patents, extract:

1. **Compound Examples** - Often numbered (Example 1, Example 234)
2. **Structure Tables** - SMILES or IUPAC names
3. **Biological Data** - IC50 tables, selectivity ratios
4. **Claims** - What's actually protected
5. **Priority Date** - When R&D started

---

## Web News Sources

| Source | Type | What You'll Find |
|--------|------|------------------|
| **FDA.gov** | Regulatory | Drug approvals, designations |
| **EMA** | Regulatory | European approvals |
| **ClinicalTrials.gov** | Trials | Trial registrations |
| **Pharma Press** | News | Pipeline updates |
| **Nature/Science** | Journals | Breakthrough research |

---

## Data Sources Reference

| Source | Data | Rate Limit |
|--------|------|------------|
| UniProt | Protein info | 10/s |
| PubChem | Compounds | 5/s |
| ChEMBL | Bioactivity | 10/s |
| RCSB PDB | Structures | 10/s |
| PubMed | Literature | 3/s |
| Google Patents | Patents | Variable |
| Lens.org | Patents | 1000/day* |
| Web Search | News | Variable |

*Requires API key

---

## Output Files

```
output/
├── target_info.json        # UniProt raw data
├── target_summary.md       # Protein summary
├── pubchem_compounds.tsv   # Compound properties
├── chembl_compounds.tsv    # Bioactivity data  
├── pdb_manifest.tsv        # Structure inventory
├── pubmed_results.tsv      # Literature
├── patent_results.json     # Patents ⭐ NEW
├── patent_summary.md       # Patent summary ⭐ NEW
├── patent_llm_prompt.md    # LLM analysis prompt ⭐ NEW
├── web_news_results.json   # News search
├── web_news_summary.md     # News summary
└── dossier.md              # Final compiled report
```

---

## Example: CDK4 Selective Inhibitor Analysis

**User asks:**
> "What are the newest patents for CDK4 selective inhibitors? Do a deep analysis."

**Nanobot executes:**

```
Step 1: [patent_search.py] --target "CDK4" --mechanism "selective inhibitor"
     → Finds 30 recent patents
Step 2: Read patent_llm_prompt.md
Step 3: [LLM Analysis] Extract compounds, IC50, trends
Step 4: Return comprehensive analysis
```

**Output:**

```markdown
# CDK4 Selective Inhibitor Patent Analysis

## Executive Summary
30 patents analyzed from 2021-2024. Key trend: shift from pan-CDK 
to CDK4-selective scaffolds with >100x selectivity over CDK6.

## Top Novel Compounds

| Patent | Compound | CDK4 IC50 | CDK4/6 Ratio | Assignee |
|--------|----------|-----------|--------------|----------|
| US2024/0012345 | Example 42 | 2 nM | 250:1 | Company X |
| WO2023/0789123 | Example 8 | 5 nM | 180:1 | Company Y |

## Emerging Scaffolds
- Pyrimidine-pyridine hybrids (45% of patents)
- Tricyclic indoles (20%)
- Macrocyclic CDK4-selective (15%)

## Competitive Landscape
- Leader: Company X (8 patents)
- Challenger: Company Y (5 patents)
- Emerging: Company Z (3 patents)

## Key Insights
1. CDK4/6 selectivity improving: 10:1 → 200:1 in 3 years
2. Focus shifting from oncology to inflammatory diseases
3. New allosteric binding sites being exploited
```

---

## Tips

1. **Use `--include-patents`** to capture unpublished compounds
2. **Sort by newest** for latest developments
3. **Cross-reference** patents with clinical data
4. **Check priority dates** to understand R&D timeline
5. **Ask follow-up questions** for deeper analysis
