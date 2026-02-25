---
name: question-analyst
description: "Meta-skill for decomposing complex questions into actionable components. Analyzes question dimensions, identifies required expertise, and orchestrates multi-perspective responses. Use BEFORE executing tasks."
---

# Question Analyst - Think First, Then Execute

## Core Principle
**Never jump to search immediately.** First understand:
1. What dimensions does this question cover?
2. What perspectives are needed?
3. What skills/tools should be used for each component?
4. How should findings be synthesized?

## Question Decomposition Framework

### Step 1: Identify Question Type (5 seconds)

| Question Type | Indicators | Required Perspectives |
|--------------|------------|----------------------|
| **Trend Analysis** | "newest", "trends", "emerging", "hot" | Technology + Market + Clinical + Investment |
| **Competitive Intel** | "vs", "compare", "landscape" | Pipeline + Market + IP |
| **Target Deep Dive** | "tell me about X", "X target" | Biology + Drugs + Clinical + Pipeline |
| **Drug Analysis** | "how does X work", "X drug" | Mechanism + Clinical + Safety + Market |
| **Investment Thesis** | "invest", "opportunity", "pipeline value" | Science + Market + Competition + Risk |

### Step 2: Map Dimensions (10 seconds)

For drug discovery questions, ALWAYS consider these 5 dimensions:

```
┌─────────────────────────────────────────────────────────────┐
│                    QUESTION DIMENSIONS                       │
├─────────────────────────────────────────────────────────────┤
│ 1. 🔬 SCIENCE & TECHNOLOGY                                   │
│    - Mechanism of action                                      │
│    - Target biology                                           │
│    - Modality (small molecule, biologic, etc.)               │
│    - Scientific innovation                                   │
├─────────────────────────────────────────────────────────────┤
│ 2. 👥 PATIENTS & CLINICAL                                    │
│    - Disease burden (prevalence, mortality)                  │
│    - Current standard of care                                │
│    - Unmet clinical needs                                    │
│    - Patient subpopulations                                  │
├─────────────────────────────────────────────────────────────┤
│ 3. 💊 PIPELINE & COMPETITION                                  │
│    - Drugs in development                                    │
│    - Companies involved                                      │
│    - Clinical trial stages                                   │
│    - Approval status                                         │
├─────────────────────────────────────────────────────────────┤
│ 4. 📊 MARKET & COMMERCIAL                                     │
│    - Market size                                             │
│    - Revenue potential                                       │
│    - Pricing considerations                                  │
│    - Launch timeline                                         │
├─────────────────────────────────────────────────────────────┤
│ 5. 💰 INVESTMENT & BUSINESS                                   │
│    - Funding rounds                                          │
│    - M&A activity                                            │
│    - Partnership deals                                       │
│    - Risk/reward assessment                                  │
└─────────────────────────────────────────────────────────────┘
```

### Step 3: Plan Execution (15 seconds)

Based on question type, select tools:

```markdown
## Execution Plan for: "[User Question]"

### Question Type: [Trend Analysis / Target Deep Dive / etc.]

### Dimensions to Cover:
- [ ] Science & Technology
- [ ] Patients & Clinical  
- [ ] Pipeline & Competition
- [ ] Market & Commercial
- [ ] Investment & Business

### Tools to Use (in order):
1. **[Tool Name]**: Purpose
2. **[Tool Name]**: Purpose
3. **[Tool Name]**: Purpose

### Expected Output:
- [What should the answer contain]
```

### Step 4: Execute Systematically

For each dimension:
1. Search relevant sources
2. Extract key facts
3. Note data quality (confirmed vs estimated)
4. Save sources for citation

### Step 5: Synthesize & Structure

```markdown
## [Question Topic]: Multi-Dimensional Analysis

### 🎯 Executive Summary
[2-3 sentences answering the core question]

### 🔬 Science & Technology
[Key scientific insights]

### 👥 Patients & Clinical Need
[Patient impact and unmet needs]

### 💊 Pipeline & Competition
[Who's doing what]

### 📊 Market Outlook
[Commercial potential]

### 💰 Investment Perspective
[Opportunities and risks]

### 📚 Sources
- Source 1
- Source 2
```

## Example: Trend Question Analysis

**User asks**: "What are the newest trends in small molecule drug discovery?"

### Decomposition:
```
Type: TREND ANALYSIS

Dimensions:
✅ Science - What new modalities/technologies?
✅ Patients - What diseases being targeted?
✅ Pipeline - What's in clinical trials?
✅ Market - Where is pharma investing?
✅ Investment - What VCs funding?

Tools:
1. zhipu_web_search: "small molecule drug discovery trends 2025"
2. zhipu_web_search: "FDA drug approvals 2024 2025 small molecule"
3. zhipu_web_search: "biotech funding 2024 2025 drug discovery"
4. patent_search: "small molecule 2025" (if EPO creds available)

Output Structure:
- Top 3 modalities (PROTAC, covalent, molecular glue, etc.)
- Hot targets with diseases
- Key companies and deals
- Investment signals
```

## Anti-Patterns

❌ **Don't do this**:
```
User: "What's new in KRAS inhibitors?"
Bot: *immediately searches "KRAS inhibitors"*
Bot: "Here's what I found: [random facts]"
```

✅ **Do this instead**:
```
User: "What's new in KRAS inhibitors?"

Bot Internal Analysis:
- Type: Trend Analysis + Target Deep Dive
- Dimensions: Science (KRAS biology), Pipeline (drugs), Clinical (trials), Market (sales), Investment (deals)
- Plan: Search → FDA → Clinical trials → Deals
- Structure: Modalities → Drugs → Companies → Outlook

Bot Response:
## KRAS Inhibitors: 2025 Landscape

### Executive Summary
[KRAS went from "undruggable" to hot target. 2024-2025 sees expansion beyond G12C...]

### 🔬 Science: Beyond G12C
[Pan-KRAS, G12D, G12V approaches...]

### 💊 Pipeline Update
[Approved: sotorasib, adagrasib | In trials: RMC-6236, etc.]

### 📊 Market
[KRAS G12C market ~$X billion by 202Y...]

### 💰 Investment Signals
[Revolution Medicines raised $X, Roivant deal $X...]

### 👥 Patient Impact
[X million KRAS-mutant cancers annually...]
```

## Integration with Other Skills

This meta-skill should be **automatically invoked** before:
- drug-discovery-trends
- drug-target-search
- Any complex multi-faceted query

The LLM should **internally apply this framework** without explicit user instruction.
