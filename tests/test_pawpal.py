import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Pet, PetTask


def make_task(task_id="t1"):
    return PetTask(
        task_id=task_id,
        type="walk",
        description="Test walk",
        duration_minutes=20,
        frequency="daily",
        priority=2,
    )


def test_mark_complete_changes_status():
    task = make_task()
    assert task.status == "pending"
    task.mark_complete()
    assert task.status == "complete"


def test_add_task_increases_pet_task_count():
    pet = Pet(pet_id="p1", name="Rex", species="Dog", breed="Poodle", age=2)
    assert len(pet.tasks) == 0
    pet.add_task(make_task("t1"))
    pet.add_task(make_task("t2"))
    assert len(pet.tasks) == 2
