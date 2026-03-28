"""Tests for PawPal+ core behaviors."""

from datetime import date, timedelta

from pawpal_system import (
    CareTask,
    ConstraintProfile,
    DailyPlan,
    Owner,
    Pet,
    Priority,
    Scheduler,
)


# ── Existing tests ───────────────────────────────────────────────


def test_mark_complete_changes_status():
    task = CareTask("t1", "Morning walk", "exercise", 30, Priority.HIGH)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Bella", species="Dog", age=4)
    assert len(pet.tasks) == 0

    task1 = CareTask("t1", "Morning walk", "exercise", 30, Priority.HIGH)
    pet.add_task(task1)
    assert len(pet.tasks) == 1

    task2 = CareTask("t2", "Brush fur", "grooming", 15, Priority.MEDIUM)
    pet.add_task(task2)
    assert len(pet.tasks) == 2


# ── Sorting: by time ────────────────────────────────────────────


def test_sort_by_time_chronological_order():
    """Tasks with fixed_time are returned earliest-first."""
    t1 = CareTask("t1", "Walk",  "exercise", 30, Priority.HIGH, fixed_time="09:00")
    t2 = CareTask("t2", "Feed",  "feeding",  10, Priority.HIGH, fixed_time="07:30")
    t3 = CareTask("t3", "Groom", "grooming", 15, Priority.LOW,  fixed_time="11:00")

    result = Scheduler.sort_by_time([t1, t2, t3])
    assert [t.task_id for t in result] == ["t2", "t1", "t3"]


def test_sort_by_time_none_fixed_time_goes_last():
    """Tasks without a fixed_time are pushed to the end."""
    fixed = CareTask("t1", "Walk", "exercise", 30, Priority.HIGH, fixed_time="09:00")
    flex  = CareTask("t2", "Play", "exercise", 20, Priority.LOW)

    result = Scheduler.sort_by_time([flex, fixed])
    assert result[0].task_id == "t1"
    assert result[1].task_id == "t2"


# ── Sorting: by priority ────────────────────────────────────────


def test_sort_tasks_by_priority_descending():
    """HIGH comes before MEDIUM comes before LOW."""
    low  = CareTask("t1", "Play",  "exercise", 20, Priority.LOW)
    high = CareTask("t2", "Walk",  "exercise", 30, Priority.HIGH)
    med  = CareTask("t3", "Groom", "grooming", 15, Priority.MEDIUM)

    result = Pet.sort_tasks([low, high, med], key="priority", reverse=True)
    assert [t.priority for t in result] == [Priority.HIGH, Priority.MEDIUM, Priority.LOW]


def test_sort_tasks_same_priority_no_crash():
    """All tasks at the same priority level — should not error."""
    t1 = CareTask("t1", "A", "exercise", 10, Priority.MEDIUM)
    t2 = CareTask("t2", "B", "exercise", 20, Priority.MEDIUM)

    result = Pet.sort_tasks([t1, t2], key="priority")
    assert len(result) == 2


# ── Recurrence logic ────────────────────────────────────────────


def test_daily_task_due_after_one_day():
    """A daily task completed yesterday should be due today."""
    today = date(2026, 3, 28)
    yesterday = today - timedelta(days=1)

    task = CareTask("t1", "Walk", "exercise", 30, Priority.HIGH, recurrence="daily")
    task.completed = True
    task.last_completed_date = yesterday

    assert task.is_due(today) is True


def test_daily_task_not_due_same_day():
    """A daily task completed today should NOT be due again today."""
    today = date(2026, 3, 28)

    task = CareTask("t1", "Walk", "exercise", 30, Priority.HIGH, recurrence="daily")
    task.completed = True
    task.last_completed_date = today

    assert task.is_due(today) is False


def test_weekly_task_not_due_after_three_days():
    """A weekly task completed 3 days ago is NOT due yet."""
    today = date(2026, 3, 28)
    three_days_ago = today - timedelta(days=3)

    task = CareTask("t1", "Bath", "grooming", 45, Priority.LOW, recurrence="weekly")
    task.completed = True
    task.last_completed_date = three_days_ago

    assert task.is_due(today) is False


def test_weekly_task_due_after_seven_days():
    """A weekly task completed 7+ days ago IS due."""
    today = date(2026, 3, 28)
    eight_days_ago = today - timedelta(days=8)

    task = CareTask("t1", "Bath", "grooming", 45, Priority.LOW, recurrence="weekly")
    task.completed = True
    task.last_completed_date = eight_days_ago

    assert task.is_due(today) is True


def test_recurring_task_never_completed_is_due():
    """A recurring task that has never been done is always due."""
    task = CareTask("t1", "Walk", "exercise", 30, Priority.HIGH, recurrence="daily")
    assert task.is_due(date(2026, 3, 28)) is True


def test_non_recurring_completed_task_not_due():
    """A one-time task that is completed should not be due."""
    task = CareTask("t1", "Vet visit", "health", 60, Priority.HIGH)
    task.mark_complete()
    assert task.is_due() is False


# ── Conflict detection ───────────────────────────────────────────


def test_detect_conflicts_overlapping_tasks():
    """Two fixed-time tasks that overlap produce a warning."""
    t1 = CareTask("t1", "Walk",    "exercise", 30, Priority.HIGH, fixed_time="09:00")
    t2 = CareTask("t2", "Feed",    "feeding",  15, Priority.HIGH, fixed_time="09:10")

    warnings = Scheduler.detect_conflicts([("Bella", t1), ("Bella", t2)])
    assert len(warnings) == 1
    assert "Walk" in warnings[0]
    assert "Feed" in warnings[0]


def test_detect_conflicts_cross_pet():
    """Conflicts are detected across different pets."""
    t1 = CareTask("t1", "Walk Bella", "exercise", 30, Priority.HIGH, fixed_time="09:00")
    t2 = CareTask("t2", "Feed Mochi", "feeding",  15, Priority.HIGH, fixed_time="09:00")

    warnings = Scheduler.detect_conflicts([("Bella", t1), ("Mochi", t2)])
    assert len(warnings) == 1
    assert "Bella" in warnings[0]
    assert "Mochi" in warnings[0]


def test_detect_conflicts_no_overlap():
    """Non-overlapping tasks produce no warnings."""
    t1 = CareTask("t1", "Walk", "exercise", 30, Priority.HIGH, fixed_time="09:00")
    t2 = CareTask("t2", "Feed", "feeding",  15, Priority.HIGH, fixed_time="10:00")

    warnings = Scheduler.detect_conflicts([("Bella", t1), ("Bella", t2)])
    assert len(warnings) == 0


def test_detect_conflicts_no_fixed_time_tasks():
    """All flexible tasks — nothing to conflict."""
    t1 = CareTask("t1", "Play", "exercise", 20, Priority.LOW)
    t2 = CareTask("t2", "Nap",  "rest",     30, Priority.LOW)

    warnings = Scheduler.detect_conflicts([("Bella", t1), ("Bella", t2)])
    assert len(warnings) == 0


# ── Schedule generation ──────────────────────────────────────────


def test_generate_plan_fixed_before_flexible():
    """Fixed-time tasks are placed at their anchor; flexible fills gaps."""
    owner = Owner("Jo", 120)
    pet = Pet("Rex", "Dog")
    fixed = CareTask("t1", "Vet",  "health",   30, Priority.HIGH, fixed_time="09:00")
    flex  = CareTask("t2", "Play", "exercise",  20, Priority.LOW)
    pet.add_task(fixed)
    pet.add_task(flex)

    plan = Scheduler().generate_plan(
        owner, pet, pet.tasks,
        ConstraintProfile(time_available_minutes=120),
    )
    assert len(plan.items) == 2
    assert plan.items[0].task.task_id == "t1"  # fixed placed first


def test_generate_plan_empty_tasks():
    """A pet with no tasks produces an empty plan without errors."""
    owner = Owner("Jo", 60)
    pet = Pet("Rex", "Dog")

    plan = Scheduler().generate_plan(
        owner, pet, [],
        ConstraintProfile(time_available_minutes=60),
    )
    assert len(plan.items) == 0
    assert len(plan.dropped) == 0


def test_generate_plan_drops_when_no_time():
    """Tasks that don't fit are recorded in the dropped list."""
    owner = Owner("Jo", 10)
    pet = Pet("Rex", "Dog")
    task = CareTask("t1", "Long walk", "exercise", 60, Priority.HIGH)
    pet.add_task(task)

    plan = Scheduler().generate_plan(
        owner, pet, pet.tasks,
        ConstraintProfile(time_available_minutes=10),
    )
    assert len(plan.items) == 0
    assert len(plan.dropped) == 1
    assert "Long walk" in plan.dropped[0].task.title


# ── Filtering ────────────────────────────────────────────────────


def test_filter_tasks_by_category():
    """Only tasks matching the category are returned."""
    t1 = CareTask("t1", "Walk",  "exercise", 30, Priority.HIGH)
    t2 = CareTask("t2", "Brush", "grooming", 15, Priority.MEDIUM)
    t3 = CareTask("t3", "Run",   "exercise", 20, Priority.LOW)

    result = Scheduler.filter_tasks([t1, t2, t3], category="exercise")
    assert len(result) == 2
    assert all(t.category == "exercise" for t in result)


def test_filter_tasks_by_priority():
    """Only tasks matching the priority are returned."""
    t1 = CareTask("t1", "Walk",  "exercise", 30, Priority.HIGH)
    t2 = CareTask("t2", "Brush", "grooming", 15, Priority.MEDIUM)

    result = Scheduler.filter_tasks([t1, t2], priority=Priority.HIGH)
    assert len(result) == 1
    assert result[0].task_id == "t1"


def test_owner_get_tasks_by_pet_name():
    """Owner.get_tasks filters to a single pet's tasks."""
    owner = Owner("Jo", 60)
    bella = Pet("Bella", "Dog")
    mochi = Pet("Mochi", "Cat")
    bella.add_task(CareTask("t1", "Walk", "exercise", 30, Priority.HIGH))
    mochi.add_task(CareTask("t2", "Feed", "feeding",  10, Priority.HIGH))
    owner.add_pet(bella)
    owner.add_pet(mochi)

    result = owner.get_tasks(pet_name="Mochi")
    assert len(result) == 1
    assert result[0][0] == "Mochi"
