# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

The classes I chose are categorized by the following:

Three core actions of the assistant:
1. Track pet tasks 
- needs to include: tasks
- actions: tracks

2. See owner prefrences
- includes: owners prefrences 
- actions: organizes by priority 

3. Make  daily plan 
- includes: time, tasks, priority
- actions: organized plan 

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.


Yes,

New additions
_time_to_minutes / _minutes_to_time helpers — shared by generate_plan for real time arithmetic
Pet.pet_id — unique identifier so lookups are unambiguous
PetTask.scheduled_time — lets reschedule actually store the new time

OwnerPreferences.priority_overrides dict — backing store for set_priority
Fixed relationships

PlanEntry.pet — every entry now knows which pet it belongs to; get_details includes the pet name

DailyPlan.owner — the plan holds a reference to the owner so adjust_for_constraints is always in sync with available_time_minutes
PawPalAssistant.pets is now a @property that returns owner.pets directly — no stale list copy

Implemented logic

OwnerPreferences.set_priority — stores overrides in priority_overrides
OwnerPreferences.

organize_by_priority — respects overrides first, then preferred_task_order, then the task's own priority field

DailyPlan.generate_plan — sorts (pet, task) pairs, walks forward from wake_up_time, skips tasks that exceed bedtime or the daily minute cap, records reasoning
DailyPlan.

adjust_for_constraints — drops lowest-priority entries until total_duration fits within available_time_minutes
PawPalAssistant.track_task — looks up pet by pet_id, raises ValueError on a miss
PawPalAssistant.

make_daily_plan — collects all tasks from all pets, calls generate_plan then adjust_for_constraints
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers four layered constraints:

1. **Bedtime** — a task is skipped entirely if placing it would run past `bed_time`. This is the hardest constraint because a task that spills into sleeping hours is genuinely impossible.
2. **Daily minute cap** — `max_daily_task_minutes` limits cumulative care time per day. A pet owner only has so many hours; exceeding this cap leads to burnout.
3. **Owner priority overrides** — specific task types (e.g. "meds") can be pinned to the top of the queue regardless of other ordering. Medical tasks were made the highest-priority constraint because missing medication has real health consequences.
4. **Available time trimming** — after the plan is built, `adjust_for_constraints` drops the lowest-priority entries to fit within `owner.available_time_minutes`. This acts as a soft budget that defers non-essential tasks rather than failing.

Bedtime and meds priority were treated as non-negotiable first because they map most directly to pet welfare.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The clearest tradeoff is in the `adjust_for_constraints` simplification.

**Original:** O(k · n) — it drops entries one at a time and stops as soon as the budget fits. If only 1 task needs to be removed from a list of 100, it does 1 removal.

**New:** Always O(n log n) — it sorts all entries upfront and does a second sort at the end to restore chronological order, even when only 1 entry needs to be dropped.

So the simplified version is faster in the worst case (many removals needed), but slower in the best case (almost nothing needs to be removed). For a pet scheduling app with a small number of tasks the difference is negligible, but it is a real algorithmic tradeoff: adaptive early-exit behavior was traded for predictable fixed-cost sorting. For this domain the predictability is worth it — the code is easier to read, reason about, and explain to a classmate.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

AI tools were used at every phase, but with different roles at each stage:

- **Design brainstorming (Copilot Chat):** Early on I used a separate chat session to ask "what algorithms would make a pet care scheduler smarter?" without touching the actual codebase. This produced a list of candidates — sorting by time, filtering by status, recurring task expansion, conflict detection — which I then evaluated and chose from. Keeping this in its own session meant the brainstorm stayed conceptual and did not accidentally generate code that would need cleaning up later.
- **Inline code generation (Copilot Inline Chat / Agent Mode):** Once I knew *what* to build, I used inline suggestions for specific method bodies — particularly the `timedelta` math in `next_occurrence()` and the single-pass comprehension in `filter_tasks()`. The most effective prompts were narrow and described the contract ("given a frequency string, return a copy of the task due N days later") rather than broad ("make recurring tasks work").
- **Refactoring and documentation (Agent Mode + smart actions):** The "Generate documentation" smart action was used to scaffold docstring structure for the new algorithmic methods, which I then filled in with project-specific detail. Agent Mode handled the multi-file `mark_task_complete` → `next_occurrence` → `generate_plan` change because it could reason across files simultaneously.

The most helpful prompt pattern was: **state the input, the output, and one constraint**, then let the AI suggest the implementation. Vague prompts like "add recurring tasks" produced suggestions that needed complete rewrites.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

When asking Copilot how to handle `"twice daily"` tasks, the initial suggestion was to add a second `PetTask` directly in `main.py` for the evening occurrence — hardcoded at a fixed time like `"18:00"`. I rejected this because it pushed scheduling logic into the demo script and would break for any owner with a different `bed_time`.

Instead, I moved the expansion into the helper `_expand_recurring_tasks()` inside `pawpal_system.py`, anchoring the evening copy to `(wake_up_time + bed_time) // 2`. To verify the fix I ran `main.py` and confirmed the evening slot shifted correctly when I changed the owner's `wake_up_time` — something the hardcoded version would have failed silently.

The evaluation process was: *does the output change when the input changes?* If not, the logic is in the wrong place.

**c. Copilot features: most effective**

- **Inline Chat on a selected method** — highlighting `sort_by_time` and asking "suggest a key function to sort HH:MM strings without lexicographic bugs" gave a focused, correct answer immediately. The narrow scope prevented Copilot from rewriting unrelated code.
- **Agent Mode for cross-file changes** — implementing auto-reschedule required touching `PetTask`, `PawPalAssistant.mark_task_complete`, `DailyPlan.generate_plan`, and `main.py` in a coordinated way. Agent Mode tracked all four files simultaneously and kept the changes consistent.
- **Separate chat sessions per phase** — the brainstorm session (algorithm ideas), the implementation session (actual code), and the documentation session (docstrings + README) were kept separate. This prevented the context window from mixing design discussion with code details, and made it easy to revisit a decision without scrolling through unrelated output.

**d. Being the lead architect**

Working with a powerful AI as a collaborator clarified one thing quickly: the AI is very good at *executing a well-defined task* and very bad at *deciding which task to execute*. Every time I gave a vague goal, the result needed significant rework. Every time I gave a precise contract — input type, output type, one key constraint — the suggestion was close to correct on the first try.

The lead architect role meant making three kinds of decisions the AI could not make for me:

1. **Where logic belongs** — The AI repeatedly suggested putting scheduling decisions in `main.py`. I had to insist those decisions belonged in `pawpal_system.py` so the Streamlit UI could reuse them without duplicating code.
2. **What to leave out** — Several suggestions added clever features (e.g. auto-detecting conflicts and rescheduling them) that were outside the current scope. Saying "no, that's a later problem" was a recurring judgment call.
3. **When to stop** — AI tools naturally tend to add more. Knowing that a method was done — that it did exactly one thing and did it clearly — required stepping back from the suggestions and reading the code as a whole.

The key takeaway: AI accelerates the distance between a decision and its implementation, which means the cost of a *bad decision* is much higher than it used to be. The architect's job is not to write less code — it is to think more carefully before asking the AI to write any.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

The existing test suite covers two fundamental data-model behaviors:

| Test | Why it matters |
|---|---|
| `test_mark_complete_changes_status` | Confirms the state machine on `PetTask` works — everything downstream (filtering, plan generation, auto-reschedule) depends on `status` being accurate. |
| `test_add_task_increases_pet_task_count` | Confirms `Pet.add_task` actually stores tasks — a silent failure here would mean every scheduler method operates on an empty list. |

These were prioritized first because they are the foundation every other feature sits on. If a `PetTask` cannot change state or a `Pet` cannot hold tasks, nothing above that layer can be trusted.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

**Confidence: 3 / 5** — The demo output in `main.py` is manually verified against expected output for the happy path. The two unit tests cover the data model. But the scheduler's critical paths have no automated tests yet.

Edge cases to add next:

- **All tasks exceed bedtime** — `generate_plan` should return an empty plan, not crash.
- **Completing a task twice** — calling `mark_task_complete` on an already-complete task should not create a duplicate recurrence.
- **`"twice daily"` task close to bedtime** — the evening expansion should be skipped if the midpoint falls past `bed_time`.
- **`adjust_for_constraints` with available_minutes = 0** — all entries should be deferred cleanly.
- **Conflict detection with back-to-back tasks** — tasks that end exactly when the next starts should *not* be flagged as a conflict (`a_end == b_start` is not an overlap).

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The recurring task system (`next_occurrence` + `due_date` gate in `generate_plan`) is the part I am most satisfied with. It solves a real problem — a daily medication task should not need to be manually re-entered every morning — and the design is clean: marking complete triggers one method, which creates one object, which the scheduler discovers automatically on the right day. Each piece has a single responsibility and they compose without knowing about each other.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

Two things:

1. **`PetTask` mutation during planning** — `generate_plan` calls `task.reschedule(time_str)` which mutates the original task object. This means running `make_daily_plan` twice on the same data produces different results. I would change this to store the scheduled time on `PlanEntry` only, leaving `PetTask` immutable during planning.
2. **Test coverage** — The scheduler's most complex methods (`generate_plan`, `adjust_for_constraints`, `detect_conflicts`, `next_occurrence`) have no unit tests. A second iteration would add parametrized tests for each constraint type before adding any new features.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The most important lesson was that **scope discipline is an architectural skill, not a personality trait**. AI tools will fill any open-ended prompt with features. Without a clear decision about what the system does *not* do, the codebase grows in every direction at once and becomes hard to reason about.

Making explicit decisions — "conflict detection warns but does not auto-fix," "filtering is read-only and does not mutate state," "recurring logic lives in `PetTask`, not in the scheduler" — kept each class focused and made every AI suggestion easy to evaluate: does this fit the responsibility of this class, or does it belong somewhere else? That question, asked consistently, was the most useful tool in the project.
