# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a busy pet owner plan and track daily care tasks across multiple pets. It generates a prioritized, time-ordered schedule based on the owner's availability and preferences, explains its decisions, and warns about scheduling conflicts.

---

## Features

### Pet & Task Management
- **Multi-pet support** — Register any number of pets (dog, cat, other), each with a unique ID used for safe lookups. Tasks are always associated with the correct pet even when two pets share the same name.
- **Task tracking** — Add tasks with type (walk, feeding, meds, grooming), description, duration, priority (1 = highest), and frequency. Tasks carry a `status` of `pending` or `complete`.
- **Mark complete** — Marking a task done via `PawPalAssistant.mark_task_complete()` updates its status and automatically creates the next occurrence for recurring tasks.

### Smart Scheduling
- **Priority-aware plan generation** — `DailyPlan.generate_plan()` sorts tasks using a three-tier key: owner priority overrides first, then `preferred_task_order`, then the task's own priority number. Tasks are placed sequentially from `wake_up_time` forward.
- **Bedtime & budget enforcement** — Any task that would push the schedule past `bed_time` or exceed `max_daily_task_minutes` is skipped and logged in the reasoning output.
- **Constraint trimming** — After generation, `adjust_for_constraints()` applies a greedy O(n log n) pass that drops the lowest-priority entries until the plan fits within `owner.available_time_minutes`, then re-sorts the kept entries chronologically.
- **Time-anchored tasks** — Tasks with a pre-set `scheduled_time` are placed at their requested slot (or the next available minute after it), while unanchored tasks fill the remaining gaps.

### Recurring Tasks
- **Daily & weekly recurrence** — When a `"daily"` or `"weekly"` task is completed, `PetTask.next_occurrence()` uses Python's `timedelta` (+1 or +7 days) to create a new pending copy with a `due_date`. The copy is invisible to the scheduler until that date arrives, so tomorrow's tasks never pollute today's plan.
- **Twice-daily expansion** — Tasks with frequency `"twice daily"` are automatically duplicated by `_expand_recurring_tasks()`, placing a morning original and an evening copy (anchored to the midpoint between wake and bed time) into each plan.

### Filtering & Sorting
- **Sort by time** — `PawPalAssistant.sort_by_time()` converts `"HH:MM"` strings to integer minutes before comparing, avoiding lexicographic pitfalls (e.g. `"9:00"` would sort after `"10:00"` alphabetically). Tasks without a scheduled time appear at the end.
- **Flexible filtering** — `filter_tasks()` accepts any combination of `pet_id`, `status`, and `task_type` and evaluates all active conditions in a single pass. `filter_by_pet_name()` is case-insensitive; `filter_by_status()` targets `"pending"` or `"complete"`.

### Conflict Detection & Warnings
- **Overlap detection** — `DailyPlan.detect_conflicts()` checks every pair of scheduled entries using the standard interval-overlap formula (`a_start < b_end and b_start < a_end`) and returns all conflicting pairs.
- **Streamlit conflict warnings** — Each conflict is surfaced as a `st.warning` card showing both pets, task types, and exact start–end windows so the owner can immediately see what clashes and by how much.

### Transparency
- **Reasoning log** — Every scheduling decision (task placed, skipped for bedtime, skipped for budget, deferred by constraint trimming) is recorded in plain English and accessible via `explain_plan_reasoning()` or the "Scheduling reasoning" expander in the UI.

---

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

Phase 3 added four algorithmic improvements to make the scheduler more useful for a real pet owner:

**Sort by time** — `PawPalAssistant.sort_by_time()` orders any list of tasks by their `scheduled_time` using a lambda key that converts `"HH:MM"` strings to integer minutes. This avoids lexicographic comparison bugs (e.g. `"9:00"` sorting after `"10:00"`) and keeps the displayed schedule in the correct order regardless of the order tasks were added.

**Flexible filtering** — `filter_tasks()`, `filter_by_pet_name()`, and `filter_by_status()` let the owner query tasks by any combination of pet, completion status, and task type. `filter_tasks()` evaluates all active conditions in a single pass through the data instead of three separate loops, so it stays efficient as the task list grows.

**Recurring task auto-scheduling** — When `mark_task_complete()` is called on a `"daily"` or `"weekly"` task, a new pending copy is automatically created using Python's `timedelta` (`+1 day` for daily, `+7 days` for weekly). The copy carries a `due_date` field so it is invisible to `generate_plan` until the correct day arrives — preventing tomorrow's tasks from cluttering today's schedule.

**Conflict detection** — `DailyPlan.detect_conflicts()` scans every pair of scheduled entries and reports any whose time windows overlap, using the standard interval-overlap formula (`a_start < b_end and b_start < a_end`). This gives the owner an immediate warning if two pets need attention at the same moment.

## Testing PawPal+

### Running the tests

```bash
python -m pytest
```

### What the tests cover

| Test | What it verifies |
|------|-----------------|
| `test_mark_complete_changes_status` | A task's `status` transitions from `"pending"` to `"complete"` when `mark_complete()` is called |
| `test_add_task_increases_pet_task_count` | Adding tasks to a `Pet` correctly grows the task list |

The current suite covers basic `PetTask` state changes and `Pet` task registration. Core scheduling behaviors — bedtime enforcement, constraint trimming, priority ordering, recurring task auto-scheduling, and conflict detection — are not yet tested.

### Confidence Level

**★★☆☆☆ (2 / 5)**

The two existing tests confirm that the most fundamental data-model operations work. However, four bugs were identified in the scheduling logic (evening task trackability, task mutation across plan runs, stale `scheduled_time` on deferred tasks, and missing `"twice daily"` recurrence), and the scheduler's critical paths have no test coverage yet. Reliability of the end-to-end plan generation cannot be confirmed until those bugs are fixed and tests are added.

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
