from pawpal_system import Owner, OwnerPreferences, Pet, PetTask, PawPalAssistant

# ── Owner & preferences ───────────────────────────────────────────────────────
owner = Owner(name="Alex", available_time_minutes=180)
owner.update_preferences(OwnerPreferences(
    wake_up_time="07:00",
    bed_time="22:00",
    max_daily_task_minutes=180,
    preferred_task_order=["meds", "feeding", "walk", "grooming"],
))

# ── Pets ──────────────────────────────────────────────────────────────────────
buddy = Pet(pet_id="pet_001", name="Buddy", species="Dog", breed="Labrador", age=3)
luna  = Pet(pet_id="pet_002", name="Luna",  species="Cat", breed="Siamese",  age=5)

owner.add_pet(buddy)
owner.add_pet(luna)

# ── Tasks added INTENTIONALLY OUT OF CHRONOLOGICAL ORDER ─────────────────────
# The scheduled_times below are scrambled to show why sort_by_time() matters.
# As-added order:  19:00 → 17:00 → 07:00 → 09:00 → 08:30 → 07:30 → 07:45 → 08:00
# After sorting:   07:00 → 07:30 → 07:45 → 08:00 → 08:30 → 17:00 → 19:00

buddy.add_task(PetTask(                         # added first — latest time
    task_id="t6", type="grooming",
    description="Evening brush",
    duration_minutes=10, frequency="daily", priority=3,
    scheduled_time="19:00",
))
buddy.add_task(PetTask(                         # added second — early evening
    task_id="t8", type="walk",
    description="Evening stroll",
    duration_minutes=25, frequency="daily", priority=2,
    scheduled_time="17:00",
))
buddy.add_task(PetTask(                         # added third — morning
    task_id="t1", type="meds",
    description="Heartworm pill",
    duration_minutes=5, frequency="daily", priority=1,
    scheduled_time="07:00",
))
luna.add_task(PetTask(                          # added fourth — mid-morning
    task_id="t5", type="grooming",
    description="Brush coat",
    duration_minutes=15, frequency="daily", priority=4,
    scheduled_time="09:00",
))
luna.add_task(PetTask(                          # added fifth — mid-morning meds
    task_id="t7", type="meds",
    description="Allergy tablet",
    duration_minutes=5, frequency="daily", priority=1,
    scheduled_time="08:30",
))
buddy.add_task(PetTask(                         # added sixth — twice daily feeding
    task_id="t2", type="feeding",
    description="Morning kibble",
    duration_minutes=10, frequency="twice daily", priority=2,
    scheduled_time="07:30",
))
luna.add_task(PetTask(                          # added seventh — morning feeding
    task_id="t4", type="feeding",
    description="Wet food breakfast",
    duration_minutes=10, frequency="daily", priority=2,
    scheduled_time="07:45",
))
buddy.add_task(PetTask(                         # added last — morning walk
    task_id="t3", type="walk",
    description="Morning walk around the block",
    duration_minutes=30, frequency="daily", priority=3,
    scheduled_time="08:00",
))

# ── Build assistant ───────────────────────────────────────────────────────────
assistant = PawPalAssistant(owner)

# ── 1. SORT DEMO: show tasks before and after sort_by_time() ─────────────────
all_tasks = assistant.get_all_tasks()

print("=" * 45)
print("  AS-ADDED ORDER (unsorted)")
print("=" * 45)
for pet, task in all_tasks:
    print(f"  [{task.scheduled_time}] {pet.name} — {task.type}: {task.description}")

print()
print("=" * 45)
print("  SORTED BY TIME  (sort_by_time)")
print("  key=lambda pair: _time_to_minutes(pair[1].scheduled_time)")
print("=" * 45)
for pet, task in assistant.sort_by_time(all_tasks):
    print(f"  [{task.scheduled_time}] {pet.name} — {task.type}: {task.description}")

# ── 2. GENERATE DAILY PLAN ────────────────────────────────────────────────────
plan = assistant.make_daily_plan("2026-04-05")

print()
print("=" * 45)
print("       PAWPAL+ — TODAY'S SCHEDULE")
print("       Date: 2026-04-05")
print("=" * 45)
for entry in plan.entries:
    print(entry.get_details())
print("-" * 45)
print(f"Total time scheduled: {plan.total_duration} min")
print("=" * 45)

# ── 3. FILTER BY PET NAME ─────────────────────────────────────────────────────
print()
print("=" * 45)
print("  FILTER: filter_by_pet_name('Luna')")
print("=" * 45)
for pet, task in assistant.filter_by_pet_name("Luna"):
    status_tag = "[done]" if task.is_complete() else "[pending]"
    print(f"  {status_tag} {task.type}: {task.description} @ {task.scheduled_time}")

# ── 4. FILTER BY STATUS ───────────────────────────────────────────────────────
print()
print("=" * 45)
print("  FILTER: filter_by_status('pending')")
print("=" * 45)
for pet, task in assistant.filter_by_status("pending"):
    print(f"  {pet.name} — {task.type}: {task.description}")

# ── 5. CONFLICT CHECK ─────────────────────────────────────────────────────────
print()
print("=" * 45)
print("  CONFLICT CHECK")
print("=" * 45)
conflicts = plan.detect_conflicts()
if conflicts:
    for a, b in conflicts:
        print(f"  CONFLICT: {a.pet.name} '{a.task.type}' ({a.scheduled_time}) "
              f"overlaps {b.pet.name} '{b.task.type}' ({b.scheduled_time})")
else:
    print("  No scheduling conflicts detected.")

# ── 6. AUTO-RESCHEDULE DEMO ───────────────────────────────────────────────────
# Mark two tasks complete for today (2026-04-06).
# Because both are "daily", mark_task_complete will automatically create a new
# pending copy due tomorrow (2026-04-07) using timedelta(days=1).
print()
print("=" * 45)
print("  AUTO-RESCHEDULE: completing today's tasks")
print("=" * 45)
assistant.mark_task_complete("pet_002", "t7", completed_on="2026-04-06")  # Luna allergy tablet
assistant.mark_task_complete("pet_001", "t1", completed_on="2026-04-06")  # Buddy heartworm pill
print("  Marked complete: Luna 't7' (allergy tablet) — daily")
print("  Marked complete: Buddy 't1' (heartworm pill) — daily")
print("  -> next_occurrence() used timedelta(days=1) to set due_date=2026-04-07")

print()
print("  Luna's full task list after completion:")
for pet, task in assistant.filter_by_pet_name("Luna"):
    due = f"  due: {task.due_date}" if task.due_date else ""
    print(f"    [{task.status:8}] {task.task_id:30} {task.type}{due}")

# ── 7. TOMORROW'S PLAN (proves recurrences appear on the right day) ───────────
print()
print("=" * 45)
print("  TOMORROW'S PLAN  (2026-04-07)")
print("  Recurred tasks should appear; today's completed ones should not.")
print("=" * 45)
plan_tomorrow = assistant.make_daily_plan("2026-04-07")
for entry in plan_tomorrow.entries:
    print(f"  {entry.get_details()}")
print(f"  Total: {plan_tomorrow.total_duration} min")
