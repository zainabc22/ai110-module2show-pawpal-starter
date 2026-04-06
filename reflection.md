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

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The clearest tradeoff is in the adjust_for_constraints simplification.

Original: O(k · n) — it drops entries one at a time and stops as soon as the budget fits. If only 1 task needs to be removed from a list of 100, it does 1 removal.

New: Always O(n log n) — it sorts all entries upfront and does a second sort at the end to restore time order, even when only 1 entry needs to be dropped.

So the simplified version is faster in the worst case (many removals needed), but slower in the best case (almost nothing needs to be removed). For a pet scheduling app with a small number of tasks the difference is negligible, but it's a real algorithmic tradeoff: you traded adaptive early-exit behavior for predictable fixed-cost sorting.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
