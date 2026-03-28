"""PawPal+ — demo script: build objects, schedule, sort, and filter."""

from pawpal_system import (
    CareTask,
    ConstraintProfile,
    Owner,
    Pet,
    Priority,
    Scheduler,
)

# ── Owner & Pets ─────────────────────────────────────────────────
owner = Owner(
    name="Jordan",
    available_minutes_per_day=90,
    preferences={"grooming": "preferred"},
)

bella = Pet(name="Bella", species="Dog", age=4)
mochi = Pet(name="Mochi", species="Cat", age=2)
owner.add_pet(bella)
owner.add_pet(mochi)

# ── Tasks added OUT OF ORDER (mixed pets, mixed times) ───────────
bella.add_task(CareTask("t1", "Morning walk",  "exercise", 30, Priority.HIGH,   fixed_time="09:00"))
bella.add_task(CareTask("t4", "Play fetch",    "exercise", 20, Priority.LOW,    fixed_time="14:00"))
bella.add_task(CareTask("t2", "Brush fur",     "grooming", 15, Priority.MEDIUM, fixed_time="11:30"))
mochi.add_task(CareTask("t3", "Vet check-up",  "health",   45, Priority.HIGH,   notes="Annual vaccines"))
mochi.add_task(CareTask("t5", "Nail trim",     "grooming", 10, Priority.MEDIUM, fixed_time="08:15"))

# Intentional conflicts for testing:
# Cross-pet: Mochi's feeding overlaps Bella's walk (both at 09:00)
mochi.add_task(CareTask("t6", "Feed Mochi",    "feeding",  15, Priority.HIGH,   fixed_time="09:00"))
# Same-pet: Bella already has "Morning walk" at 09:00
bella.add_task(CareTask("t7", "Bella vitamins", "health",  10, Priority.MEDIUM, fixed_time="09:10"))

# Mark one task complete to test filtering
bella.tasks[1].mark_complete()  # Play fetch is done

scheduler = Scheduler()

# ── 1. Sort by time ──────────────────────────────────────────────
print(f"\n{'=' * 55}")
print("  SORT BY TIME — Bella's tasks (earliest first)")
print(f"{'=' * 55}")
sorted_by_time = scheduler.sort_by_time(bella.tasks)
for t in sorted_by_time:
    status = "DONE" if t.completed else "todo"
    print(f"  {t.fixed_time or 'flex':>5}  {t.title:<18} {t.priority.name:<8} [{status}]")

# ── 2. Sort by priority ─────────────────────────────────────────
print(f"\n{'=' * 55}")
print("  SORT BY PRIORITY — all Bella tasks (highest first)")
print(f"{'=' * 55}")
sorted_by_pri = Pet.sort_tasks(bella.tasks, key="priority", reverse=True)
for t in sorted_by_pri:
    print(f"  {t.priority.name:<8} {t.title:<18} {t.duration_minutes:>3} min")

# ── 3. Filter by pet name ───────────────────────────────────────
print(f"\n{'=' * 55}")
print("  FILTER — only Mochi's tasks")
print(f"{'=' * 55}")
mochi_tasks = owner.get_tasks(pet_name="Mochi")
for pet_name, t in mochi_tasks:
    print(f"  [{pet_name}]  {t.title:<18} {t.category}")

# ── 4. Filter by completion status ──────────────────────────────
print(f"\n{'=' * 55}")
print("  FILTER — incomplete tasks across ALL pets")
print(f"{'=' * 55}")
incomplete = owner.get_tasks(completed=False)
for pet_name, t in incomplete:
    print(f"  [{pet_name}]  {t.title:<18} {t.priority.name}")

# ── 5. Combined: filter + sort ──────────────────────────────────
print(f"\n{'=' * 55}")
print("  FILTER + SORT — incomplete tasks, sorted by time")
print(f"{'=' * 55}")
incomplete_tasks = [t for _, t in owner.get_tasks(completed=False)]
sorted_incomplete = scheduler.sort_by_time(incomplete_tasks)
for t in sorted_incomplete:
    print(f"  {t.fixed_time or 'flex':>5}  {t.title:<18} {t.priority.name}")

# ── 6. Conflict detection (cross-pet) ───────────────────────────
print(f"\n{'=' * 55}")
print("  CONFLICT DETECTION — all pets, all fixed-time tasks")
print(f"{'=' * 55}")
all_labeled = owner.get_tasks()  # (pet_name, task) tuples for every pet
warnings = Scheduler.detect_conflicts(all_labeled)
if warnings:
    for w in warnings:
        print(f"  {w}")
else:
    print("  No conflicts found.")

# ── 7. Schedule (uses the two-phase algorithm) ──────────────────
constraints = ConstraintProfile(
    time_available_minutes=owner.available_minutes_per_day,
    owner_preferences=owner.preferences,
    max_tasks_per_day=10,
)

plan = scheduler.generate_plan(owner, bella, bella.tasks, constraints)

print(f"\n{'=' * 55}")
print(f"  TODAY'S SCHEDULE for {bella.summary()}")
print(f"  Owner: {owner.name} | Budget: {plan.total_minutes_available} min")
print(f"{'=' * 55}")
print(f"  {'Time':<14} {'Task':<20} {'Pri':<8} {'Min':>4}")
print(f"  {'-'*14} {'-'*20} {'-'*8} {'-'*4}")
for item in plan.items:
    t = item.task
    print(f"  {item.start_time}-{item.end_time:<8} {t.title:<20} {t.priority.name:<8} {t.duration_minutes:>4}")

if plan.dropped:
    print(f"\n  Dropped tasks:")
    for d in plan.dropped:
        print(f"    ✗ {d.task.title} — {d.reason}")

print(f"\n  Used {plan.total_minutes_used}/{plan.total_minutes_available} min "
      f"({plan.utilization():.0%} utilization)")
print(f"{'=' * 55}\n")
