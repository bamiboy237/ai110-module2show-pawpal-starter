from datetime import time as dt_time

import streamlit as st

from pawpal_system import Owner, Pet, CareTask, Priority, Scheduler, ConstraintProfile

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# ── Owner ─────────────────────────────────────────────────────────
st.subheader("Owner Setup")

owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input("Available minutes per day", min_value=10, max_value=480, value=90)

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, available_minutes_per_day=available_minutes)

if st.button("Update Owner"):
    st.session_state.owner.name = owner_name
    st.session_state.owner.available_minutes_per_day = available_minutes
    st.success(f"Owner updated: {owner_name}, {available_minutes} min/day")

# ── Add Pet ───────────────────────────────────────────────────────
st.subheader("Add a Pet")

pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["Dog", "Cat", "Other"])
pet_age = st.number_input("Pet age (years)", min_value=0, max_value=30, value=2)

if st.button("Add pet"):
    owner = st.session_state.owner
    if owner.get_pet(pet_name):
        st.warning(f"{pet_name} already exists.")
    else:
        new_pet = Pet(name=pet_name, species=species, age=pet_age)
        owner.add_pet(new_pet)
        st.success(f"Added {new_pet.summary()} to {owner.name}'s pets")

if st.session_state.owner.pets:
    st.write("Registered pets:")
    st.table([
        {"Name": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.tasks)}
        for p in st.session_state.owner.pets
    ])
else:
    st.info("No pets yet. Add one above.")

# ── Add Task to a Pet ─────────────────────────────────────────────
st.subheader("Add a Task")

pet_names = [p.name for p in st.session_state.owner.pets]

if pet_names:
    selected_pet_name = st.selectbox("Assign to pet", pet_names)

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["LOW", "MEDIUM", "HIGH"], index=2)

    category = st.selectbox("Category", ["exercise", "grooming", "health", "feeding", "general"])
    recurrence = st.selectbox("Recurrence", ["None", "daily", "weekly"])

    use_fixed_time = st.checkbox("Set fixed time")
    fixed_time = None
    if use_fixed_time:
        time_val = st.time_input("Fixed time", value=dt_time(10, 0))
        fixed_time = time_val.strftime("%H:%M")

    if st.button("Add task"):
        pet = st.session_state.owner.get_pet(selected_pet_name)
        task_id = f"t{len(pet.tasks) + 1}"
        new_task = CareTask(
            task_id=task_id,
            title=task_title,
            category=category,
            duration_minutes=int(duration),
            priority=Priority[priority],
            recurrence=None if recurrence == "None" else recurrence,
            fixed_time=fixed_time,
        )
        pet.add_task(new_task)
        st.success(f"Added '{task_title}' to {pet.name}")

    # ── Filter & Sort ─────────────────────────────────────────────
    selected_pet = st.session_state.owner.get_pet(selected_pet_name)
    if selected_pet and selected_pet.tasks:
        st.write(f"Tasks for {selected_pet.name}:")

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            filter_status = st.selectbox("Filter by status", ["All", "Incomplete", "Completed"], key="fstatus")
        with fc2:
            filter_cat = st.selectbox("Filter by category", ["All", "exercise", "grooming", "health", "feeding", "general"], key="fcat")
        with fc3:
            filter_pri = st.selectbox("Filter by priority", ["All", "LOW", "MEDIUM", "HIGH"], key="fpri")

        sc1, sc2 = st.columns(2)
        with sc1:
            sort_key = st.selectbox("Sort by", ["priority", "duration", "category", "title"], key="sortkey")
        with sc2:
            sort_desc = st.checkbox("Descending", value=True, key="sortdesc")

        display_tasks = list(selected_pet.tasks)
        if filter_status == "Incomplete":
            display_tasks = Scheduler.filter_tasks(display_tasks, completed=False)
        elif filter_status == "Completed":
            display_tasks = Scheduler.filter_tasks(display_tasks, completed=True)
        if filter_cat != "All":
            display_tasks = Scheduler.filter_tasks(display_tasks, category=filter_cat)
        if filter_pri != "All":
            display_tasks = Scheduler.filter_tasks(display_tasks, priority=Priority[filter_pri])

        display_tasks = Pet.sort_tasks(display_tasks, key=sort_key, reverse=sort_desc)

        if display_tasks:
            st.table([
                {
                    "Title": t.title,
                    "Category": t.category,
                    "Duration": f"{t.duration_minutes} min",
                    "Priority": t.priority.name,
                    "Recurrence": t.recurrence or "—",
                    "Fixed Time": t.fixed_time or "Flexible",
                    "Done": "Yes" if t.completed else "No",
                }
                for t in display_tasks
            ])
        else:
            st.info("No tasks match the current filters.")
else:
    st.info("Add a pet first before creating tasks.")

# ── Schedule ──────────────────────────────────────────────────────
st.divider()
st.subheader("Build Schedule")

if pet_names:
    schedule_pet_name = st.selectbox("Schedule for pet", pet_names, key="schedule_pet")

    if st.button("Generate schedule"):
        owner = st.session_state.owner
        pet = owner.get_pet(schedule_pet_name)

        if not pet.tasks:
            st.warning(f"{pet.name} has no tasks. Add some first.")
        else:
            constraints = ConstraintProfile(
                time_available_minutes=owner.available_minutes_per_day,
                owner_preferences=owner.preferences,
            )
            scheduler = Scheduler()
            plan = scheduler.generate_plan(owner, pet, pet.tasks, constraints)

            st.markdown(f"**Schedule for {pet.summary()}** — Owner: {owner.name}")
            for item in plan.items:
                t = item.task
                st.markdown(
                    f"- `{item.start_time}–{item.end_time}` **{t.title}** "
                    f"({t.priority.name}, {t.duration_minutes} min) — {item.reason}"
                )

            if plan.conflicts:
                st.warning("**Schedule Conflicts Detected:**")
                for c in plan.conflicts:
                    st.markdown(f"- {c}")

            if plan.dropped:
                st.markdown("**Dropped tasks:**")
                for d in plan.dropped:
                    st.markdown(f"- ✗ {d.task.title} — {d.reason}")

            st.info(
                f"Used {plan.total_minutes_used}/{plan.total_minutes_available} min "
                f"({plan.utilization():.0%} utilization)"
            )
            st.markdown(f"*{plan.summary_reasoning}*")
else:
    st.info("Add a pet to start scheduling.")
