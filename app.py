import streamlit as st
from pawpal_system import Owner, OwnerPreferences, Pet, PetTask, PawPalAssistant, DailyPlan

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# ── Session-state initialisation (runs only on first load) ───────────────────

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_time_minutes=120)
    st.session_state.owner.update_preferences(OwnerPreferences(
        wake_up_time="07:00",
        bed_time="22:00",
        max_daily_task_minutes=120,
        preferred_task_order=["meds", "feeding", "walk", "grooming"],
    ))

if "assistant" not in st.session_state:
    st.session_state.assistant = PawPalAssistant(st.session_state.owner)

if "pet_counter" not in st.session_state:
    st.session_state.pet_counter = 0

if "task_counter" not in st.session_state:
    st.session_state.task_counter = 0

owner     = st.session_state.owner
assistant = st.session_state.assistant

# ── Add a Pet ────────────────────────────────────────────────────────────────

st.subheader("Add a Pet")

with st.form("add_pet_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        pet_name    = st.text_input("Pet name",  value="Mochi")
        pet_species = st.selectbox("Species", ["dog", "cat", "other"])
    with col2:
        pet_breed = st.text_input("Breed", value="Mixed")
        pet_age   = st.number_input("Age (years)", min_value=0, max_value=30, value=2)

    submitted_pet = st.form_submit_button("Add Pet")

if submitted_pet:
    st.session_state.pet_counter += 1
    new_pet = Pet(
        pet_id  = f"pet_{st.session_state.pet_counter:03d}",
        name    = pet_name,
        species = pet_species,
        breed   = pet_breed,
        age     = int(pet_age),
    )
    # owner.add_pet() stores the Pet and makes it visible everywhere
    owner.add_pet(new_pet)
    st.success(f"Added {pet_name} to the roster!")

# Show current pets
if owner.pets:
    st.write("**Current pets:**")
    st.table([
        {"Name": p.name, "Species": p.species, "Breed": p.breed, "Age": p.age}
        for p in owner.pets
    ])
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ── Schedule a Task ──────────────────────────────────────────────────────────

st.subheader("Schedule a Task")

if not owner.pets:
    st.warning("Add at least one pet before scheduling tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_options = {p.name: p.pet_id for p in owner.pets}
        selected_pet_name = st.selectbox("Assign to pet", list(pet_options.keys()))

        col1, col2, col3 = st.columns(3)
        with col1:
            task_type = st.selectbox("Task type", ["walk", "feeding", "meds", "grooming"])
        with col2:
            task_desc = st.text_input("Description", value="Morning walk")
        with col3:
            duration  = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)

        col4, col5 = st.columns(2)
        with col4:
            priority  = st.selectbox("Priority (1 = highest)", [1, 2, 3, 4, 5])
        with col5:
            frequency = st.selectbox("Frequency", ["daily", "twice daily", "weekly"])

        submitted_task = st.form_submit_button("Add Task")

    if submitted_task:
        st.session_state.task_counter += 1
        new_task = PetTask(
            task_id          = f"task_{st.session_state.task_counter:03d}",
            type             = task_type,
            description      = task_desc,
            duration_minutes = int(duration),
            frequency        = frequency,
            priority         = priority,
        )
        # assistant.track_task() looks up the pet by ID and calls pet.add_task()
        pet_id = pet_options[selected_pet_name]
        assistant.track_task(pet_id, new_task)
        st.success(f"Scheduled '{task_desc}' for {selected_pet_name}!")

    # Show all tasks grouped by pet
    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.write("**All scheduled tasks:**")
        st.table([
            {
                "Pet":         pet.name,
                "Type":        task.type,
                "Description": task.description,
                "Duration":    f"{task.duration_minutes} min",
                "Priority":    task.priority,
                "Status":      task.status,
            }
            for pet, task in all_tasks
        ])

st.divider()

# ── Generate Schedule ────────────────────────────────────────────────────────

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    pending = owner.get_all_pending_tasks()
    if not pending:
        st.warning("No pending tasks to schedule. Add tasks above.")
    else:
        plan = assistant.make_daily_plan("2026-04-05")
        if plan.entries:
            st.success("Today's schedule is ready!")
            st.table([
                {
                    "Time":        entry.scheduled_time,
                    "Pet":         entry.pet.name,
                    "Task":        entry.task.type,
                    "Description": entry.task.description,
                    "Duration":    f"{entry.task.duration_minutes} min",
                }
                for entry in plan.entries
            ])
            st.caption(f"Total time: {plan.total_duration} min")
            with st.expander("Scheduling reasoning"):
                st.text(assistant.explain_plan_reasoning())
        else:
            st.error("No tasks could be fit into today's schedule (check bedtime / time budget).")
