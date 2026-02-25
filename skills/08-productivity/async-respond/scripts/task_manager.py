#!/usr/bin/env python3
"""Task persistence and async response management for nanobot."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

TASKS_DIR = Path.home() / ".nanobot" / "tasks"

def create_task(question: str, chat_id: str, platform: str = "telegram",
                username: str = "", estimated_time: str = "30 minutes") -> Dict[str, Any]:
    """Create a new investigation task."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_id = f"task_{timestamp}"
    
    task = {
        "task_id": task_id,
        "created": datetime.now().isoformat(),
        "status": "in_progress",
        "question": question,
        "chat_id": chat_id,
        "platform": platform,
        "username": username,
        "estimated_time": estimated_time,
        "dimensions": {},
        "progress": {},
        "completed": False,
        "result_file": None
    }
    
    # Save task
    task_file = TASKS_DIR / f"{task_id}.json"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    with open(task_file, "w") as f:
        json.dump(task, f, indent=2)
    
    # Create progress file
    progress_file = TASKS_DIR / f"{task_id}_progress.md"
    with open(progress_file, "w") as f:
        f.write(f"# Task: {question}\n\n")
        f.write(f"## Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("### Progress Log\n\n")
    
    return task


def update_progress(task_id: str, dimension: str, status: str, 
                    findings: str = "") -> None:
    """Update task progress."""
    task_file = TASKS_DIR / f"{task_id}.json"
    progress_file = TASKS_DIR / f"{task_id}_progress.md"
    
    if task_file.exists():
        with open(task_file) as f:
            task = json.load(f)
        
        task["progress"][dimension] = status
        task["dimensions"][dimension] = findings
        
        with open(task_file, "w") as f:
            json.dump(task, f, indent=2)
    
    # Append to progress log
    timestamp = datetime.now().strftime("%H:%M")
    with open(progress_file, "a") as f:
        status_emoji = "✅" if status == "completed" else "🔄" if status == "in_progress" else "⏳"
        f.write(f"#### {timestamp} - {dimension}\n")
        f.write(f"Status: {status_emoji} {status}\n")
        if findings:
            f.write(f"Findings: {findings[:200]}...\n")
        f.write("\n")


def complete_task(task_id: str, result: str) -> Dict[str, Any]:
    """Mark task as completed and save result."""
    task_file = TASKS_DIR / f"{task_id}.json"
    result_file = TASKS_DIR / f"{task_id}_result.md"
    
    if task_file.exists():
        with open(task_file) as f:
            task = json.load(f)
        
        task["status"] = "completed"
        task["completed"] = True
        task["completed_at"] = datetime.now().isoformat()
        task["result_file"] = str(result_file)
        
        with open(task_file, "w") as f:
            json.dump(task, f, indent=2)
        
        # Save full result
        with open(result_file, "w") as f:
            f.write(result)
        
        return task
    return {}


def get_pending_tasks() -> list:
    """Get all pending (incomplete) tasks."""
    tasks = []
    if TASKS_DIR.exists():
        for task_file in TASKS_DIR.glob("task_*.json"):
            with open(task_file) as f:
                task = json.load(f)
            if not task.get("completed"):
                tasks.append(task)
    return tasks


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Get task by ID."""
    task_file = TASKS_DIR / f"{task_id}.json"
    if task_file.exists():
        with open(task_file) as f:
            return json.load(f)
    return None


if __name__ == "__main__":
    # Test
    task = create_task(
        question="What are KRAS inhibitor trends?",
        chat_id="7299981663",
        platform="telegram"
    )
    print(f"Created task: {task['task_id']}")
    
    update_progress(task['task_id'], "science", "completed", "Found PROTAC data")
    print("Updated progress")
    
    pending = get_pending_tasks()
    print(f"Pending tasks: {len(pending)}")
