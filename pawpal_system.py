from copy import copy
from dataclasses import dataclass, field
from datetime import date as _date, timedelta
from typing import Dict, List, Optional, Tuple


# ── Helpers ───────────────────────────────────────────────────────────────────

def _time_to_minutes(time_str: str) -> int:
    """Convert 'HH:MM' string to minutes since midnight."""
    h, m = map(int, time_str.split(":"))
    return h * 60 + m


def _minutes_to_time(minutes: int) -> str:
    """Convert minutes since midnight to 'HH:MM' string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _expand_recurring_tasks(
    pet_tasks: List[Tuple["Pet", "PetTask"]],
    preferences: "OwnerPreferences",
) -> List[Tuple["Pet", "PetTask"]]:
    """Expand 'twice daily' tasks into a morning original and an auto-generated evening copy.

    For every task whose frequency is 'twice daily', a shallow copy is appended
    immediately after the original in the returned list.  The copy's
    scheduled_time is set to the midpoint between wake_up_time and bed_time so
    it naturally slots into the second half of the owner's active day.

    Args:
        pet_tasks:   All (Pet, PetTask) pairs to inspect.
        preferences: Owner preferences supplying wake_up_time and bed_time.

    Returns:
        A new list with at most 2x the input length; single-occurrence tasks
        pass through unchanged.
    """
    wake_min = _time_to_minutes(preferences.wake_up_time)
    bed_min = _time_to_minutes(preferences.bed_time)
    evening_anchor = _minutes_to_time((wake_min + bed_min) // 2)

    result = []
    for pet, task in pet_tasks:
        result.append((pet, task))
        if task.frequency == "twice daily":
            evening = copy(task)
            evening.task_id = task.task_id + "_evening"
            evening.scheduled_time = evening_anchor
            result.append((pet, evening))
    return result


# ── Dataclasses for lightweight data objects ──────────────────────────────────

@dataclass
class PetTask:
    task_id: str
    type: str                      # e.g. "walk", "feeding", "meds", "grooming"
    description: str
    duration_minutes: int
    frequency: str                 # e.g. "daily", "twice daily"
    priority: int                  # 1 = highest
    status: str = "pending"        # "pending" | "complete"
    scheduled_time: Optional[str] = None  # set when the task is placed in a plan
    due_date: Optional[str] = None        # ISO "YYYY-MM-DD"; None means always eligible

    def mark_complete(self):
        """Mark this task as complete."""
        self.status = "complete"

    def reschedule(self, new_time: str):
        """Update the scheduled time for this task."""
        self.scheduled_time = new_time

    def is_complete(self) -> bool:
        """Return True if the task has been completed."""
        return self.status == "complete"

    def reset(self):
        """Revert to pending with no scheduled time (e.g. for a new day)."""
        self.status = "pending"
        self.scheduled_time = None

    def next_occurrence(self, from_date: str) -> "PetTask":
        """Return a fresh pending copy of this task scheduled for its next due date.

        Uses Python's ``datetime.timedelta`` to compute the next date from
        the task's frequency:

        - ``"daily"``  -> ``timedelta(days=1)``  -> one day after *from_date*
        - ``"weekly"`` -> ``timedelta(days=7)``  -> same weekday the following week

        The copy inherits ``scheduled_time`` (HH:MM) from the original so it
        lands in the same time slot on the new day.  Its ``task_id`` is
        suffixed with ``_recur_YYYY-MM-DD`` so every recurrence is unique and
        repeated calls never overwrite each other.  ``due_date`` is set to the
        computed ISO date string so ``generate_plan`` withholds the task from
        any plan generated before that date.

        Args:
            from_date: ISO date string (``"YYYY-MM-DD"``) representing the day
                       the task was completed.  The next occurrence is offset
                       from this date, not from today's system clock.

        Returns:
            A new ``PetTask`` with ``status="pending"`` and an updated
            ``task_id`` and ``due_date``.

        Raises:
            ValueError: If ``self.frequency`` is not ``"daily"`` or
                        ``"weekly"``.
        """
        _intervals = {"daily": 1, "weekly": 7}
        days = _intervals.get(self.frequency)
        if days is None:
            raise ValueError(
                f"Cannot auto-reschedule frequency '{self.frequency}' — "
                "only 'daily' and 'weekly' are supported."
            )
        next_date = _date.fromisoformat(from_date) + timedelta(days=days)
        base_id = self.task_id.split("_recur_")[0]   # strip any prior recur suffix
        recurred = copy(self)
        recurred.task_id = f"{base_id}_recur_{next_date.isoformat()}"
        recurred.status = "pending"
        recurred.due_date = next_date.isoformat()
        return recurred


@dataclass
class Pet:
    pet_id: str                    # unique identifier used for safe lookups
    name: str
    species: str
    breed: str
    age: int
    tasks: List[PetTask] = field(default_factory=list)

    def add_task(self, task: PetTask):
        """Append a new task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_id: str):
        """Remove a task from this pet's list by its ID."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def get_tasks(self) -> List[PetTask]:
        """Return all tasks assigned to this pet."""
        return self.tasks

    def get_pending_tasks(self) -> List[PetTask]:
        """Return only the tasks that have not yet been completed."""
        return [t for t in self.tasks if not t.is_complete()]

    def get_task_by_id(self, task_id: str) -> Optional[PetTask]:
        """Look up and return a single task by its ID, or None if not found."""
        return next((t for t in self.tasks if t.task_id == task_id), None)


@dataclass
class PlanEntry:
    scheduled_time: str
    task: PetTask
    pet: Pet                       # links entry back to its pet
    priority_score: int
    notes: str = ""

    def get_details(self) -> str:
        return (
            f"[{self.scheduled_time}] {self.pet.name} — {self.task.type}: "
            f"{self.task.description} ({self.task.duration_minutes} min)"
        )


# ── Regular classes for objects with behaviour ────────────────────────────────

class OwnerPreferences:
    def __init__(
        self,
        wake_up_time: str,
        bed_time: str,
        max_daily_task_minutes: int,
        preferred_task_order: Optional[List[str]] = None,
        disliked_tasks: Optional[List[str]] = None,
    ):
        self.wake_up_time = wake_up_time
        self.bed_time = bed_time
        self.max_daily_task_minutes = max_daily_task_minutes
        self.preferred_task_order: List[str] = preferred_task_order or []
        self.disliked_tasks: List[str] = disliked_tasks or []
        self.priority_overrides: Dict[str, int] = {}  # task_type -> priority level

    def set_priority(self, task_type: str, level: int):
        """Override the priority level for a specific task type."""
        self.priority_overrides[task_type] = level

    def get_top_priorities(self) -> List[str]:
        """Return task types ordered by preference and priority overrides."""
        # preferred_task_order first, then any override-sorted types not already listed
        overrides_sorted = sorted(
            self.priority_overrides, key=lambda t: self.priority_overrides[t]
        )
        seen = set(self.preferred_task_order)
        return self.preferred_task_order + [t for t in overrides_sorted if t not in seen]

    def organize_by_priority(self, tasks: List[PetTask]) -> List[PetTask]:
        """Sort a list of tasks according to the owner's priority preferences."""
        order_map = {t: i for i, t in enumerate(self.preferred_task_order)}

        def sort_key(task: PetTask):
            override = self.priority_overrides.get(task.type)
            if override is not None:
                return (0, override, 0)
            if task.type in order_map:
                return (1, order_map[task.type], task.priority)
            return (2, 0, task.priority)

        return sorted(tasks, key=sort_key)


class Owner:
    def __init__(self, name: str, available_time_minutes: int):
        self.name = name
        self.available_time_minutes = available_time_minutes
        self.preferences: Optional[OwnerPreferences] = None
        self.pets: List[Pet] = []

    def update_preferences(self, prefs: OwnerPreferences):
        """Set or replace the owner's scheduling preferences."""
        self.preferences = prefs

    def add_pet(self, pet: Pet):
        """Register a new pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_id: str):
        """Remove a pet from this owner's list by pet ID."""
        self.pets = [p for p in self.pets if p.pet_id != pet_id]

    def get_pet_by_id(self, pet_id: str) -> Optional[Pet]:
        """Find and return a pet by its unique ID, or None if not found."""
        return next((p for p in self.pets if p.pet_id == pet_id), None)

    def get_all_tasks(self) -> List[Tuple[Pet, PetTask]]:
        """Return every (pet, task) pair across all pets — used by the Scheduler."""
        return [(pet, task) for pet in self.pets for task in pet.get_tasks()]

    def get_all_pending_tasks(self) -> List[Tuple[Pet, PetTask]]:
        """Return all incomplete (pet, task) pairs across every pet."""
        return [(pet, task) for pet in self.pets for task in pet.get_pending_tasks()]


class DailyPlan:
    def __init__(self, date: str, owner: Owner):
        self.date = date
        self.owner = owner          # stored so constraints are always in sync
        self.entries: List[PlanEntry] = []
        self.reasoning: str = ""
        self.total_duration: int = 0

    def generate_plan(
        self,
        pet_tasks: List[Tuple[Pet, PetTask]],
        preferences: OwnerPreferences,
    ):
        """Build and store a time-ordered schedule from pending tasks and owner preferences.

        Algorithm:
        1. Expand recurring ('twice daily') tasks into morning + evening copies.
        2. Sort: time-anchored tasks (have a requested scheduled_time) come first,
           ordered by that time; floating tasks follow, ordered by owner preference.
        3. For each task, start at max(current_clock, requested_time) so anchored
           tasks land at their requested slot and floating tasks fill the gaps.
        """
        # Include only pending tasks that are due on or before the plan date.
        # due_date=None means "always eligible" (no date restriction).
        pending = [
            (pet, t) for pet, t in pet_tasks
            if t.status == "pending"
            and (t.due_date is None or t.due_date <= self.date)
        ]

        # ── 1. Expand recurring tasks ────────────────────────────────────────
        expanded = _expand_recurring_tasks(pending, preferences)

        # ── 2. Sort by scheduled_time first, then by owner priority preference ─
        order_map = {t: i for i, t in enumerate(preferences.preferred_task_order)}

        def sort_key(pair: Tuple[Pet, PetTask]):
            _, task = pair
            if task.scheduled_time is not None:
                # Time-anchored: group first, ordered by requested minute
                return (0, _time_to_minutes(task.scheduled_time), 0)
            override = preferences.priority_overrides.get(task.type)
            if override is not None:
                return (1, 0, override)
            if task.type in order_map:
                return (1, order_map[task.type] + 1, task.priority)
            return (2, 0, task.priority)

        sorted_tasks = sorted(expanded, key=sort_key)

        current_minutes = _time_to_minutes(preferences.wake_up_time)
        bed_minutes = _time_to_minutes(preferences.bed_time)

        self.entries = []
        self.total_duration = 0
        reasons: List[str] = []

        # ── 3. Place each task, honoring any requested time ──────────────────
        for pet, task in sorted_tasks:
            if task.scheduled_time is not None:
                requested = _time_to_minutes(task.scheduled_time)
                start = max(current_minutes, requested)
            else:
                start = current_minutes

            if start + task.duration_minutes > bed_minutes:
                reasons.append(
                    f"Skipped '{task.type}' for {pet.name}: would exceed bedtime."
                )
                continue
            if self.total_duration + task.duration_minutes > preferences.max_daily_task_minutes:
                reasons.append(
                    f"Skipped '{task.type}' for {pet.name}: would exceed max daily minutes."
                )
                continue

            time_str = _minutes_to_time(start)
            task.reschedule(time_str)
            entry = PlanEntry(
                scheduled_time=time_str,
                task=task,
                pet=pet,
                priority_score=task.priority,
            )
            self.entries.append(entry)
            self.total_duration += task.duration_minutes
            current_minutes = start + task.duration_minutes
            reasons.append(
                f"{time_str}: {task.type} for {pet.name} "
                f"({task.duration_minutes} min, priority {task.priority})"
            )

        self.reasoning = "\n".join(reasons)

    def adjust_for_constraints(self, available_minutes: int):
        """Trim the plan to fit within *available_minutes* by dropping low-priority entries.

        Uses a greedy single-pass algorithm:

        1. Sort all entries by ``priority_score`` ascending (lower number =
           higher priority) so the most important tasks are considered first.
        2. Walk the sorted list once, accumulating duration.  Keep an entry if
           it fits in the remaining budget; otherwise mark it as deferred in
           the reasoning log.
        3. Re-sort the kept entries by ``scheduled_time`` so the final
           schedule is displayed in chronological order.

        Complexity: O(n log n) from the two ``sorted()`` calls.  This is an
        improvement over a naive while-loop that calls ``list.remove()``
        inside each iteration, which is O(n) per removal and O(n²) overall.

        Args:
            available_minutes: The hard upper bound on total plan duration
                               (typically ``owner.available_time_minutes``).
        """
        if self.total_duration <= available_minutes:
            return

        kept, total = [], 0
        for entry in sorted(self.entries, key=lambda e: e.priority_score):
            if total + entry.task.duration_minutes <= available_minutes:
                kept.append(entry)
                total += entry.task.duration_minutes
            else:
                self.reasoning += (
                    f"\nDeferred '{entry.task.type}' for {entry.pet.name} to fit time budget."
                )

        self.entries = sorted(kept, key=lambda e: _time_to_minutes(e.scheduled_time))
        self.total_duration = total

    def detect_conflicts(self) -> List[Tuple[PlanEntry, PlanEntry]]:
        """Return pairs of entries whose time windows overlap.

        Two entries conflict when entry A starts before entry B ends
        AND entry B starts before entry A ends.
        """
        conflicts = []
        for i, a in enumerate(self.entries):
            a_start = _time_to_minutes(a.scheduled_time)
            a_end = a_start + a.task.duration_minutes
            for b in self.entries[i + 1:]:
                b_start = _time_to_minutes(b.scheduled_time)
                b_end = b_start + b.task.duration_minutes
                if a_start < b_end and b_start < a_end:
                    conflicts.append((a, b))
        return conflicts

    def explain_plan(self) -> str:
        """Return the human-readable reasoning log for the current plan."""
        return self.reasoning if self.reasoning else "No plan generated yet."


class PawPalAssistant:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.current_plan: Optional[DailyPlan] = None

    @property
    def pets(self) -> List[Pet]:
        """Always reflects the live owner pet list; no stale copy."""
        return self.owner.pets

    def track_task(self, pet_id: str, task: PetTask):
        """Look up pet by unique pet_id to avoid name-collision bugs."""
        pet = next((p for p in self.owner.pets if p.pet_id == pet_id), None)
        if pet is None:
            raise ValueError(f"No pet found with id '{pet_id}'")
        pet.add_task(task)

    def view_preferences(self) -> Optional[OwnerPreferences]:
        """Return the owner's current scheduling preferences, or None if unset."""
        return self.owner.preferences

    def get_all_tasks(self) -> List[Tuple[Pet, PetTask]]:
        """Retrieve all (pet, task) pairs by delegating to Owner."""
        return self.owner.get_all_tasks()

    def get_tasks_by_type(self, task_type: str) -> List[Tuple[Pet, PetTask]]:
        """Return all tasks of a given type (e.g. 'walk', 'meds') across all pets."""
        return [(pet, t) for pet, t in self.owner.get_all_tasks() if t.type == task_type]

    def get_pending_tasks(self) -> List[Tuple[Pet, PetTask]]:
        """Return all incomplete (pet, task) pairs across the owner's pets."""
        return self.owner.get_all_pending_tasks()

    def sort_by_time(
        self, tasks: List[Tuple[Pet, PetTask]]
    ) -> List[Tuple[Pet, PetTask]]:
        """Return *tasks* sorted by each task's ``scheduled_time`` in ascending order.

        The sort key is a lambda that converts the ``"HH:MM"`` string to an
        integer (minutes since midnight) before comparing.  This avoids
        lexicographic pitfalls — e.g. the string ``"9:00"`` would sort *after*
        ``"10:00"`` alphabetically but the integer ``540`` correctly sorts
        *before* ``600``.

        Tasks whose ``scheduled_time`` is ``None`` (not yet placed in a plan)
        are given a key of ``float("inf")`` so they appear at the end of the
        sorted list rather than raising a ``TypeError``.

        Args:
            tasks: Any list of ``(Pet, PetTask)`` pairs — typically the result
                   of ``get_all_tasks()`` or one of the filter methods.

        Returns:
            A new sorted list; the original list is not modified.
        """
        return sorted(
            tasks,
            key=lambda pair: (
                _time_to_minutes(pair[1].scheduled_time)
                if pair[1].scheduled_time is not None
                else float("inf")
            ),
        )

    def filter_by_pet_name(self, name: str) -> List[Tuple[Pet, PetTask]]:
        """Return all tasks belonging to the pet whose name matches *name*.

        The comparison is case-insensitive so ``"luna"``, ``"Luna"``, and
        ``"LUNA"`` all return the same results.  If no pet has that name an
        empty list is returned.

        Args:
            name: The pet's display name to match against.

        Returns:
            A list of ``(Pet, PetTask)`` pairs for every task owned by the
            matched pet, in insertion order.
        """
        return [
            (p, t)
            for p, t in self.owner.get_all_tasks()
            if p.name.lower() == name.lower()
        ]

    def filter_by_status(self, status: str) -> List[Tuple[Pet, PetTask]]:
        """Return all (pet, task) pairs whose status equals *status*.

        Intended values are ``"pending"`` and ``"complete"``, matching the two
        states defined on ``PetTask``.  An unrecognised status string simply
        returns an empty list rather than raising an error.

        Args:
            status: The exact status string to match (``"pending"`` or
                    ``"complete"``).

        Returns:
            A list of ``(Pet, PetTask)`` pairs across all pets whose task
            status equals *status*, in owner → pet → task insertion order.
        """
        return [
            (p, t)
            for p, t in self.owner.get_all_tasks()
            if t.status == status
        ]

    def filter_tasks(
        self,
        pet_id: Optional[str] = None,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> List[Tuple[Pet, PetTask]]:
        """Filter tasks by any combination of pet ID, status, and task type.

        All three parameters are optional.  Omitting a parameter (or passing
        ``None``) means "no restriction on that dimension".  All active
        conditions must match simultaneously (logical AND).

        Implemented as a single-pass list comprehension: each ``None`` check
        short-circuits via ``or`` so the task list is traversed exactly once
        regardless of how many filters are active, compared to three separate
        passes in a naive implementation.

        Args:
            pet_id:    Match only tasks belonging to this pet's unique ID.
            status:    Match only tasks with this status (``"pending"`` /
                       ``"complete"``).
            task_type: Match only tasks of this type (e.g. ``"walk"``,
                       ``"meds"``).

        Returns:
            A list of ``(Pet, PetTask)`` pairs satisfying all supplied filters,
            in owner → pet → task insertion order.

        Example::

            # All pending walk tasks for Buddy
            assistant.filter_tasks(pet_id="pet_001", status="pending",
                                   task_type="walk")
        """
        return [
            (p, t) for p, t in self.owner.get_all_tasks()
            if (pet_id    is None or p.pet_id == pet_id)
            and (status   is None or t.status == status)
            and (task_type is None or t.type  == task_type)
        ]

    def mark_task_complete(
        self, pet_id: str, task_id: str, completed_on: Optional[str] = None
    ):
        """Mark a task complete and auto-schedule its next occurrence.

        For 'daily' and 'weekly' tasks a new pending copy is added to the pet
        with a due_date calculated via timedelta (1 day or 7 days after
        completed_on).  The new task will not appear in any plan generated
        before that due_date.

        completed_on: ISO date string "YYYY-MM-DD". Defaults to today.
        """
        pet = self.owner.get_pet_by_id(pet_id)
        if pet is None:
            raise ValueError(f"No pet found with id '{pet_id}'")
        task = pet.get_task_by_id(task_id)
        if task is None:
            raise ValueError(f"No task '{task_id}' found for pet '{pet_id}'")
        task.mark_complete()
        if task.frequency in ("daily", "weekly"):
            on = completed_on or _date.today().isoformat()
            pet.add_task(task.next_occurrence(on))

    def make_daily_plan(self, date: str) -> DailyPlan:
        """Generate, adjust, and store the daily care plan for the given date."""
        prefs = self.owner.preferences
        if prefs is None:
            raise ValueError("Owner preferences must be set before generating a plan.")

        plan = DailyPlan(date, self.owner)
        plan.generate_plan(self.owner.get_all_tasks(), prefs)
        plan.adjust_for_constraints(self.owner.available_time_minutes)
        self.current_plan = plan
        return plan

    def explain_plan_reasoning(self) -> str:
        """Return the reasoning log from the most recently generated plan."""
        if self.current_plan is None:
            return "No plan generated yet."
        return self.current_plan.explain_plan()
