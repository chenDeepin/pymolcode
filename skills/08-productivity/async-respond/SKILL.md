---
name: async-respond
description: "Enable asynchronous responses for long-running investigations. Persists conversation context for hours/days and notifies user when investigation completes. Critical for multi-step research tasks."
---

# Async Response System for Long-Running Tasks

## Problem
User asks complex question → Investigation takes 30min+ → User gets no response → Context lost

## Solution
1. **Acknowledge immediately** - Tell user task is started
2. **Persist context** - Save chat_id, user, question for later
3. **Track progress** - Log investigation steps
4. **Notify on completion** - Push response when ready, even hours later

## Workflow

### Phase 1: Acknowledge (Immediate)
```markdown
🔍 Got it! This is a complex question that requires deep investigation.

I'm analyzing:
- [Dimension 1]
- [Dimension 2]
- [Dimension 3]

⏱️ Estimated time: ~[X] minutes
📱 I'll send you the full report when ready!

Task ID: [task_xxx]
```

### Phase 2: Investigate (Background)
```
~/.nanobot/tasks/
├── task_xxx.json          # Task metadata
├── task_xxx_progress.md   # Progress log
└── task_xxx_result.md     # Final result
```

### Phase 3: Notify (When Complete)
When investigation finishes:
1. Load task_xxx.json → Get chat_id
2. Compile final report
3. Send to Telegram: "✅ Your report on [topic] is ready!"
4. Include full analysis

## Task File Structure

### task_xxx.json
```json
{
  "task_id": "task_20260213_001",
  "created": "2026-02-13T00:30:00Z",
  "status": "in_progress",
  "question": "What are the newest trends in small molecule drug discovery?",
  "chat_id": "7299981663",
  "platform": "telegram",
  "username": "Chen_nbc",
  "estimated_time": "30 minutes",
  "dimensions": [
    "science",
    "clinical", 
    "pipeline",
    "market",
    "investment"
  ],
  "progress": {
    "science": "completed",
    "clinical": "in_progress",
    "pipeline": "pending",
    "market": "pending",
    "investment": "pending"
  },
  "completed": false
}
```

### task_xxx_progress.md
```markdown
# Task: Small Molecule Drug Discovery Trends

## Started: 2026-02-13 00:30

### Progress Log

#### 00:35 - Science dimension
- Searched: "small molecule drug discovery 2025 trends"
- Found: PROTACs, molecular glues, covalent inhibitors
- Status: ✅ Complete

#### 00:40 - Clinical dimension  
- Searched: "FDA approvals 2025 small molecule"
- Found: [drugs listed]
- Status: ✅ Complete

#### 00:45 - Pipeline dimension
- Searching clinical trials...
- Status: 🔄 In Progress

#### [Continue logging...]
```

## Implementation Guide

### For the LLM

When receiving a complex question:

**Step 1: Assess Complexity**
```
If investigation_time > 5 minutes:
    → Use async response pattern
Else:
    → Respond normally
```

**Step 2: Create Task**
```python
task = {
    "task_id": f"task_{timestamp}",
    "question": user_question,
    "chat_id": current_chat_id,
    "platform": "telegram",
    "status": "in_progress"
}

# Save task file
save_task(task)
```

**Step 3: Acknowledge**
```
Send immediate response:
"🔍 Starting investigation on [topic]...
This will take ~X minutes. I'll notify you when ready!"
```

**Step 4: Investigate**
```
For each dimension:
    - Search
    - Analyze
    - Update progress file
    - If interrupted, progress is saved
```

**Step 5: Complete & Notify**
```
When done:
1. Mark task completed
2. Compile report
3. Use telegram_send_message with saved chat_id
4. Send: "✅ Your analysis is ready! [full report]"
```

## Recovery System

If nanobot restarts during investigation:
1. On startup, check `~/.nanobot/tasks/` for incomplete tasks
2. Resume from last checkpoint
3. Continue investigation
4. Send result when done

## Example Scenarios

### Scenario 1: Trend Analysis (30 min)
```
User: "Analyze KRAS inhibitor landscape"

Bot: 🔍 Starting comprehensive KRAS analysis...
    - Target biology: ~5 min
    - Pipeline scan: ~10 min
    - Clinical trials: ~10 min
    - Market analysis: ~5 min
    
    📱 I'll send the full report in ~30 min!
    Task ID: task_20260213_kras
    
[30 minutes later]

Bot: ✅ Your KRAS inhibitor analysis is ready!
    
    ## KRAS Inhibitors: 2025 Landscape
    [Full comprehensive report...]
```

### Scenario 2: Multi-Day Investigation
```
User: "Deep dive into Alzheimer's drug pipeline"

Bot: 🔍 This is a major research task!
    I'll investigate over the next day and send you:
    - Daily progress updates
    - Final comprehensive report
    
    Task ID: task_20260213_ad
    
[Next day]

Bot: ✅ Alzheimer's Drug Pipeline Analysis Complete!
    [50+ page comprehensive report]
```

## Best Practices

### DO:
✅ Always acknowledge immediately
✅ Give time estimates
✅ Provide task IDs for tracking
✅ Send progress updates for long tasks (>1 hour)
✅ Persist all context to disk
✅ Enable recovery after restart

### DON'T:
❌ Leave user waiting without acknowledgment
❌ Lose context if task takes hours
❌ Require user to ask again
❌ Discard partial progress

## Telegram Integration

When investigation completes, use:
```
telegram_send_message(
    chat_id="[saved_chat_id]",
    text="[Full investigation report]"
)
```

This works even if:
- Hours have passed
- Nanobot was restarted
- User sent other messages in between

## Command Reference

### User Commands
- `status [task_id]` - Check investigation progress
- `cancel [task_id]` - Cancel running task
- `tasks` - List all pending tasks

### Example
```
User: status task_20260213_kras

Bot: 📊 Task: KRAS Analysis
     Status: In Progress (75%)
     Completed: Science, Clinical, Pipeline
     Remaining: Market
     ETA: ~5 minutes
```
