from dataclasses import dataclass, field
from typing import List, Optional


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

    def mark_complete(self):
        self.status = "complete"

    def reschedule(self, _new_time: str):
        # TODO: update scheduled time
        pass


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    tasks: List[PetTask] = field(default_factory=list)

    def add_task(self, task: PetTask):
        self.tasks.append(task)

    def remove_task(self, task_id: str):
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def get_tasks(self) -> List[PetTask]:
        return self.tasks


@dataclass
class PlanEntry:
    scheduled_time: str
    task: PetTask
    priority_score: int
    notes: str = ""

    def get_details(self) -> str:
        return (
            f"[{self.scheduled_time}] {self.task.type} — "
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

    def set_priority(self, task_type: str, level: int):
        # TODO: store per-type priority overrides
        pass

    def get_top_priorities(self) -> List[str]:
        # TODO: return task types sorted by priority
        return self.preferred_task_order

    def organize_by_priority(self, tasks: List[PetTask]) -> List[PetTask]:
        # TODO: sort tasks using preferred_task_order and priority field
        return sorted(tasks, key=lambda t: t.priority)


class Owner:
    def __init__(self, name: str, available_time_minutes: int):
        self.name = name
        self.available_time_minutes = available_time_minutes
        self.preferences: Optional[OwnerPreferences] = None
        self.pets: List[Pet] = []

    def update_preferences(self, prefs: OwnerPreferences):
        self.preferences = prefs

    def add_pet(self, pet: Pet):
        self.pets.append(pet)


class DailyPlan:
    def __init__(self, date: str):
        self.date = date
        self.entries: List[PlanEntry] = []
        self.reasoning: str = ""
        self.total_duration: int = 0

    def generate_plan(self, tasks: List[PetTask], preferences: OwnerPreferences):
        # TODO: schedule tasks within available time, respecting priority
        pass

    def adjust_for_constraints(self, available_minutes: int):
        # TODO: trim or defer low-priority tasks if over time budget
        pass

    def explain_plan(self) -> str:
        # TODO: return human-readable reasoning for the chosen plan
        return self.reasoning


class PawPalAssistant:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.pets: List[Pet] = owner.pets
        self.current_plan: Optional[DailyPlan] = None

    def track_task(self, pet_name: str, task: PetTask):
        # TODO: find pet by name and add the task
        pass

    def view_preferences(self) -> Optional[OwnerPreferences]:
        return self.owner.preferences

    def make_daily_plan(self, date: str) -> DailyPlan:
        # TODO: collect all tasks, apply preferences, generate and return plan
        plan = DailyPlan(date)
        self.current_plan = plan
        return plan

    def explain_plan_reasoning(self) -> str:
        if self.current_plan is None:
            return "No plan generated yet."
        return self.current_plan.explain_plan()
