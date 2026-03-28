"""PawPal+ — demo script: build objects, schedule, and print."""

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

# ── Tasks (mixed across both pets) ───────────────────────────────
tasks = [
    CareTask("t1", "Morning walk",    "exercise",  30, Priority.HIGH),
    CareTask("t2", "Brush fur",       "grooming",  15, Priority.MEDIUM),
    CareTask("t3", "Vet check-up",    "health",    45, Priority.HIGH, notes="Annual vaccines"),
    CareTask("t4", "Play fetch",      "exercise",  20, Priority.LOW),
    CareTask("t5", "Nail trim",       "grooming",  10, Priority.MEDIUM),
]

# ── Schedule ─────────────────────────────────────────────────────
constraints = ConstraintProfile(
    time_available_minutes=owner.available_minutes_per_day,
    owner_preferences=owner.preferences,
    max_tasks_per_day=10,
)

scheduler = Scheduler()
plan = scheduler.generate_plan(owner, bella, tasks, constraints)

# ── Print ────────────────────────────────────────────────────────
print(f"\n{'=' * 50}")
print(f"  Today's Schedule for {bella.summary()}")
print(f"  Owner: {owner.name} | Budget: {plan.total_minutes_available} min")
print(f"{'=' * 50}\n")

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
print(f"{'=' * 50}\n")
