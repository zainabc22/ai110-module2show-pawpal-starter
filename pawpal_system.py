from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ── Helpers ───────────────────────────────────────────────────────────────────

def _time_to_minutes(time_str: str) -> int:
    """Convert 'HH:MM' string to minutes since midnight."""
    h, m = map(int, time_str.split(":"))
    return h * 60 + m


def _minutes_to_time(minutes: int) -> str:
    """Convert minutes since midnight to 'HH:MM' string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


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
        """Build and store a time-ordered schedule from pending tasks and owner preferences."""
        pending = [(pet, t) for pet, t in pet_tasks if t.status == "pending"]

        order_map = {t: i for i, t in enumerate(preferences.preferred_task_order)}

        def sort_key(pair: Tuple[Pet, PetTask]):
            _, task = pair
            override = preferences.priority_overrides.get(task.type)
            if override is not None:
                return (0, override, 0)
            if task.type in order_map:
                return (1, order_map[task.type], task.priority)
            return (2, 0, task.priority)

        sorted_tasks = sorted(pending, key=sort_key)

        current_minutes = _time_to_minutes(preferences.wake_up_time)
        bed_minutes = _time_to_minutes(preferences.bed_time)

        self.entries = []
        self.total_duration = 0
        reasons: List[str] = []

        for pet, task in sorted_tasks:
            if current_minutes + task.duration_minutes > bed_minutes:
                reasons.append(
                    f"Skipped '{task.type}' for {pet.name}: would exceed bedtime."
                )
                continue
            if self.total_duration + task.duration_minutes > preferences.max_daily_task_minutes:
                reasons.append(
                    f"Skipped '{task.type}' for {pet.name}: would exceed max daily minutes."
                )
                continue

            time_str = _minutes_to_time(current_minutes)
            task.reschedule(time_str)
            entry = PlanEntry(
                scheduled_time=time_str,
                task=task,
                pet=pet,
                priority_score=task.priority,
            )
            self.entries.append(entry)
            self.total_duration += task.duration_minutes
            current_minutes += task.duration_minutes
            reasons.append(
                f"{time_str}: {task.type} for {pet.name} "
                f"({task.duration_minutes} min, priority {task.priority})"
            )

        self.reasoning = "\n".join(reasons)

    def adjust_for_constraints(self, available_minutes: int):
        """Drop lowest-priority entries until the plan fits within available_minutes."""
        if self.total_duration <= available_minutes:
            return

        # Remove lowest-priority (highest priority number) entries first
        removable = sorted(self.entries, key=lambda e: -e.priority_score)
        while self.total_duration > available_minutes and removable:
            entry = removable.pop(0)
            self.entries.remove(entry)
            self.total_duration -= entry.task.duration_minutes
            self.reasoning += (
                f"\nDeferred '{entry.task.type}' for {entry.pet.name} to fit time budget."
            )

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

    def mark_task_complete(self, pet_id: str, task_id: str):
        """Mark a specific task as complete for the given pet."""
        pet = self.owner.get_pet_by_id(pet_id)
        if pet is None:
            raise ValueError(f"No pet found with id '{pet_id}'")
        task = pet.get_task_by_id(task_id)
        if task is None:
            raise ValueError(f"No task '{task_id}' found for pet '{pet_id}'")
        task.mark_complete()

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
