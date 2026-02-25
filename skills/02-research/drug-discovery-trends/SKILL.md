---
name: drug-discovery-trends
description: "Analyze latest trends in small molecule drug discovery. Combines web search, PubMed, and industry news to identify emerging therapeutic targets, modalities, and technologies. Provides data-driven trend analysis."
---

# Drug Discovery Trends Analysis

## Purpose
Help users understand the **latest trends** in small molecule drug discovery by:
- Searching recent scientific publications
- Analyzing industry news and FDA approvals
- Identifying emerging targets and modalities
- Providing data-backed insights

## When to Use
- "What are the newest trends in [area] drug discovery?"
- "What's hot in small molecule [target]?"
- "Latest advances in [modality]?"
- "What targets are companies focusing on?"

## Trend Analysis Workflow

### Step 1: Define Search Scope (30 seconds)
Before searching, identify:
- **Time window**: Focus on last 6-12 months (current year priority)
- **Topic keywords**: Extract key terms from user question
- **Target area**: Oncology, neurology, immunology, etc.

### Step 2: Multi-Source Search (2-3 minutes)
Search in parallel:

1. **Industry News (Priority 1)**
   - FDA approvals 2024-2025
   - Big pharma pipeline updates
   - Biotech funding rounds
   - Key: Focus on what's getting APPROVED and FUNDED

2. **Scientific Literature**
   - High-impact papers (Nature, Science, Cell, JACS)
   - Review articles
   - Key: What are TOP researchers working on?

3. **Clinical Trials**
   - Phase 2/3 trials started recently
   - Key: What's reaching LATE STAGE?

### Step 3: Synthesize Trends
Group findings into categories:
- **🎯 Hot Targets**: Most mentioned targets
- **🔬 Emerging Modalities**: PROTACs, molecular glues, covalent, etc.
- **🧪 Technology Trends**: AI/ML, DEL, fragment-based, etc.
- **📊 Market Indicators**: Funding, deals, approvals

### Step 4: Provide Actionable Insights
For each trend:
1. **What**: Brief description
2. **Why it matters**: Clinical/commercial relevance
3. **Key players**: Companies or research groups
4. **Evidence**: 2-3 specific examples with sources

## Response Format

```markdown
## 🔬 Latest Trends in [Topic] (2025)

### 📈 Top 3 Emerging Trends

#### 1. [Trend Name]
**What**: One-line description
**Why it matters**: Impact statement
**Key examples**:
- Example 1 (Source: X)
- Example 2 (Source: Y)
**Companies/Groups**: A, B, C

#### 2. [Trend Name]
...

### 🎯 Hot Targets
| Target | Indication | Why Hot | Key Companies |
|--------|------------|---------|---------------|
| ... | ... | ... | ... |

### 💊 Modality Trends
- **PROTACs**: [status and examples]
- **Molecular glues**: [status and examples]
- **Covalent inhibitors**: [status and examples]

### 📚 Key Recent Papers
1. Title (Journal, Date) - One-line significance
2. ...

### 💡 Bottom Line
2-3 sentences summarizing the most important insight
```

## Search Query Templates

### For Web Search (Zhipu)
```
"[topic] drug discovery 2025 trends"
"[topic] FDA approval 2024 2025"
"[topic] clinical trial results 2025"
"[modality] breakthrough 2025"
```

### For PubMed
```
"[topic] AND (2024[dp] OR 2025[dp]) AND review[pt]"
"[topic] AND clinical trial[pt] AND 2024[dp]"
```

## Common Topics & Keywords

| Topic | Key Search Terms |
|-------|------------------|
| **Oncology** | KRAS, EGFR, ADC, bispecific, IO combinations |
| **Neurology** | Alzheimer, Parkinson, ALS, neuroinflammation |
| **Autoimmune** | JAK, TYK2, IL-17, TNF, BTK |
| **Metabolic** | GLP-1, GIP, amylin, NASH, obesity |
| **Modalities** | PROTAC, molecular glue, covalent, macrocycle, peptide |

## Quality Checks

Before finalizing response, verify:
- [ ] All data is from 2024-2025 (not outdated)
- [ ] At least 3 specific examples cited
- [ ] Trends are backed by evidence (not speculation)
- [ ] No random symbols or formatting issues
- [ ] Actionable insights provided

## Anti-Patterns to Avoid

❌ Don't:
- List outdated information (pre-2024)
- Use vague statements without examples
- Include random symbols or broken formatting
- Speculate without evidence
- Give generic "AI is transforming" answers

✅ Do:
- Cite specific drugs, companies, papers
- Provide concrete numbers and dates
- Focus on what's clinically/commercially relevant
- Prioritize FDA-approved or late-stage pipeline

## Example Queries

| User Question | Key Focus |
|---------------|-----------|
| "newest trends in small molecule drug discovery" | Broad: AI, PROTACs, covalent, targets |
| "what's hot in oncology small molecules?" | KRAS inhibitors, ADCs, KRAS G12C, etc. |
| "latest in PROTAC technology" | PROTAC-specific: E3 ligases, clinical trials |
| "emerging targets for Alzheimer's" | Neuro-specific: amyloid, tau, inflammation |
