# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

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
