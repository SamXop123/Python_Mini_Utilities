import os
import tempfile
import re

TODO_FILE = "todos.txt"
MAX_TASK_LEN = 36
PRIORITY_LABELS = {1: "🔴 HIGH", 2: "🟡 MEDIUM", 3: "🟢 LOW"}
PRIORITY_EMOJIS = {1: "🔴", 2: "🟡", 3: "🟢"}


def _todo_path():
    return os.path.join(os.path.dirname(__file__), TODO_FILE)


def parse_task(line):
    """Parse task line into dict with text, priority, completed status.
    Supports legacy formats and new [P1][x] format."""
    line = line.strip()
    if not line:
        return None
    
    # Remove completion marker if present
    completed = False
    if line.startswith("[x] "):
        line = line[4:]
        completed = True
    elif line.startswith("[x]"):
        line = line[3:]
        completed = True
    
    # Parse priority [P1], [P2], [P3] - case insensitive
    priority_match = re.match(r'\[P([1-3])\]\s*(.*)', line, re.IGNORECASE)
    if priority_match:
        priority = int(priority_match.group(1))
        text = priority_match.group(2).strip()
    else:
        # Legacy task - default priority 2
        priority = 2
        text = line
    
    return {
        "text": text,
        "priority": priority,
        "completed": completed
    }


def format_task(task_dict):
    """Format task dict back to file format: [P1][x] text or [P2] text"""
    markers = []
    if task_dict["priority"] in [1, 2, 3]:
        markers.append(f"[P{task_dict['priority']}]")
    if task_dict["completed"]:
        markers.append("[x]")
    
    marker_str = "".join(markers) + " " if markers else ""
    return f"{marker_str}{task_dict['text']}"


def load_todos():
    """Load todos, parsing priority and completion status."""
    path = _todo_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_lines = [line.strip() for line in f if line.strip()]
        return [parse_task(line) for line in raw_lines if parse_task(line)]
    except FileNotFoundError:
        return []


def save_todos(todos):
    """Atomically save parsed todos back to file."""
    path = _todo_path()
    dirpath = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=TODO_FILE, dir=dirpath)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for todo in todos:
                f.write(format_task(todo) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass


def add_task(task_text: str) -> bool:
    """Add task with priority, avoiding duplicates."""
    task_text = task_text.strip()
    if not task_text or len(task_text) > MAX_TASK_LEN:
        if len(task_text) > MAX_TASK_LEN:
            task_text = task_text[:MAX_TASK_LEN]
        return False
    
    todos = load_todos()
    normalized = {t["text"].lower() for t in todos}
    
    if task_text.lower() in normalized:
        return False
    
    # Get priority from user
    while True:
        priority_input = input("Priority (1=High, 2=Medium, 3=Low) [default:2]: ").strip()
        if not priority_input:
            priority = 2
            break
        try:
            priority = int(priority_input)
            if priority in [1, 2, 3]:
                break
            print("Please enter 1, 2, or 3")
        except ValueError:
            print("Please enter a number (1-3)")
    
    new_task = {
        "text": task_text,
        "priority": priority,
        "completed": False
    }
    
    todos.append(new_task)
    save_todos(todos)
    return True


def toggle_completion(task_dict):
    """Toggle completion status."""
    task_dict["completed"] = not task_dict["completed"]
    return task_dict


def delete_task(todos, index):
    """Delete task by index."""
    if 0 <= index < len(todos):
        return todos.pop(index)
    return None


def show_todos(todos, sort_priority=False):
    """Display todos with priority and completion status."""
    if not todos:
        print("No tasks yet ✨")
        return

    # Sort by priority if requested (High=1 first)
    display_todos = sorted(todos, key=lambda x: x['priority']) if sort_priority else todos

    print("\n📋 Your To-Do List:")
    if sort_priority:
        print("   (Sorted by priority: 🔴HIGH → 🟡MEDIUM → 🟢LOW)")
    
    completed_count = sum(1 for t in display_todos if t["completed"])
    pending_count = len(display_todos) - completed_count
    
    for i, task in enumerate(display_todos, start=1):
        status = "✅" if task["completed"] else "⏳"
        if sort_priority:
            # PRIORITY VIEW: Show emoji + label
            prio_emoji = PRIORITY_EMOJIS.get(task["priority"], "❓")
            prio_label = PRIORITY_LABELS.get(task["priority"], f"P{task['priority']}")
            print(f"{i:2d}. [{status}] {prio_emoji}  {task['text']}")
        else:
            # REGULAR VIEW: Clean, no priority symbols
            print(f"{i:2d}. [{status}] {task['text']}")
    
    print(f"\n({pending_count} pending, {completed_count} done)")


def main():
    todos = load_todos()

    while True:
        print("\n" + "="*30)
        print("🎯 TO-DO MENU (with PRIORITY SUPPORT!)")
        print("1. View tasks")
        print("2. View tasks (SORTED by priority)")
        print("3. Add task") 
        print("4. Delete task")
        print("5. Mark Done")  
        print("6. Exit")
        print("="*30)

        choice = input("Choose (1-6): ").strip()

        if choice == "1":
            show_todos(todos, sort_priority=False)

        elif choice == "2":
            show_todos(todos, sort_priority=True)

        elif choice == "3":
            task = input("➕ New task: ").strip()
            if add_task(task):
                todos = load_todos()
                print("Task added ✅")
            else:
                print("Task is a duplicate, too long, or empty ❌")

        elif choice == "4":
            show_todos(todos, sort_priority=False)
            if todos:
                try:
                    index = int(input("🗑️  Task number to delete: ")) - 1
                    removed = delete_task(todos, index)
                    if removed:
                        save_todos(todos)
                        prio_label = PRIORITY_LABELS.get(removed['priority'], f"P{removed['priority']}")
                        print(f"🗑️  Removed: {prio_label} {removed['text']}")
                    else:
                        print("❌ Invalid number")
                except ValueError:
                    print("❌ Enter a valid number")

        elif choice == "5":
            show_todos(todos, sort_priority=False)
            if todos:
                try:
                    index = int(input("✅ Task number to toggle: ")) - 1
                    if 0 <= index < len(todos):
                        old_task = todos[index]
                        todos[index] = toggle_completion(old_task)
                        save_todos(todos)
                        new_status = "marked DONE ✅" if todos[index]["completed"] else "marked PENDING ⏳"
                        prio_label = PRIORITY_LABELS.get(todos[index]['priority'], f"P{todos[index]['priority']}")
                        print(f"Toggle: {prio_label} {old_task['text']} → {new_status}")
                    else:
                        print("❌ Invalid number")
                except ValueError:
                    print("❌ Enter a valid number")

        elif choice == "6":
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid option (1-6)")


if __name__ == "__main__":
    main()
