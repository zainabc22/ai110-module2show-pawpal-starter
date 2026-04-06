from pawpal_system import Owner, OwnerPreferences, Pet, PetTask, PawPalAssistant

# Create owner
owner = Owner(name="Alex", available_time_minutes=120)
owner.update_preferences(OwnerPreferences(
    wake_up_time="07:00",
    bed_time="22:00",
    max_daily_task_minutes=120,
    preferred_task_order=["meds", "feeding", "walk", "grooming"],
))

# Create pets
buddy = Pet(pet_id="pet_001", name="Buddy", species="Dog", breed="Labrador", age=3)
luna  = Pet(pet_id="pet_002", name="Luna",  species="Cat", breed="Siamese",  age=5)

owner.add_pet(buddy)
owner.add_pet(luna)

# Add tasks to Buddy
buddy.add_task(PetTask(
    task_id="t1", type="meds",
    description="Heartworm pill",
    duration_minutes=5, frequency="daily", priority=1,
    scheduled_time="07:00",
))
buddy.add_task(PetTask(
    task_id="t2", type="feeding",
    description="Morning kibble",
    duration_minutes=10, frequency="daily", priority=2,
    scheduled_time="07:30",
))
buddy.add_task(PetTask(
    task_id="t3", type="walk",
    description="Morning walk around the block",
    duration_minutes=30, frequency="daily", priority=3,
    scheduled_time="08:00",
))

# Add tasks to Luna
luna.add_task(PetTask(
    task_id="t4", type="feeding",
    description="Wet food breakfast",
    duration_minutes=10, frequency="daily", priority=2,
    scheduled_time="07:45",
))
luna.add_task(PetTask(
    task_id="t5", type="grooming",
    description="Brush coat",
    duration_minutes=15, frequency="daily", priority=4,
    scheduled_time="09:00",
))

# Set up assistant and generate plan
assistant = PawPalAssistant(owner)
plan = assistant.make_daily_plan("2026-04-05")

# Print Today's Schedule
print("=" * 45)
print("       PAWPAL+ — TODAY'S SCHEDULE")
print("       Date: 2026-04-05")
print("=" * 45)

for entry in plan.entries:
    print(entry.get_details())

print("-" * 45)
print(f"Total time scheduled: {plan.total_duration} min")
print("=" * 45)
