"""PawPal+ — Pet care planning system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


# ── Priority Enum ──────────────────────────────────────────────────

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


# ── Core Data Classes ──────────────────────────────────────────────

@dataclass
class Owner:
    name: str
    available_minutes_per_day: int
    preferences: dict[str, str] = field(default_factory=dict)


@dataclass
class Pet:
    name: str
    species: str
    age: int = 0
    tasks: list[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def summary(self) -> str:
        """Return a short label for display."""
        return f"{self.name} ({self.species}, {self.age} yrs)"


@dataclass
class CareTask:
    task_id: str
    title: str
    category: str
    duration_minutes: int
    priority: Priority
    notes: str = ""
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True


# ── Constraint Profile ────────────────────────────────────────────

@dataclass
class ConstraintProfile:
    time_available_minutes: int
    owner_preferences: dict[str, str] = field(default_factory=dict)
    max_tasks_per_day: int = 10


# ── Plan Output Classes ───────────────────────────────────────────

@dataclass
class PlanItem:
    task: CareTask
    start_time: str
    end_time: str
    reason: str


@dataclass
class DroppedItem:
    task: CareTask
    reason: str


@dataclass
class DailyPlan:
    date: str
    items: list[PlanItem] = field(default_factory=list)
    dropped: list[DroppedItem] = field(default_factory=list)
    total_minutes_used: int = 0
    total_minutes_available: int = 0
    summary_reasoning: str = ""

    def add_item(self, item: PlanItem) -> None:
        """Add a scheduled item and update used time."""
        self.items.append(item)
        self.total_minutes_used += item.task.duration_minutes

    def drop_item(self, item: DroppedItem) -> None:
        """Record a task that could not be scheduled."""
        self.dropped.append(item)

    def utilization(self) -> float:
        """Return the fraction of available time that was used."""
        if self.total_minutes_available == 0:
            return 0.0
        return self.total_minutes_used / self.total_minutes_available


# ── Scheduler ─────────────────────────────────────────────────────

class Scheduler:
    """Generates a DailyPlan from tasks and constraints."""

    START_HOUR = 8  # plans start at 8:00 AM

    def generate_plan(
        self,
        owner: Owner,
        pet: Pet,
        tasks: list[CareTask],
        constraints: ConstraintProfile,
    ) -> DailyPlan:
        """Build a day plan by ranking tasks and fitting them into time."""
        ranked = sorted(tasks, key=lambda t: self.score_task(t, constraints), reverse=True)

        plan = DailyPlan(
            date=date.today().isoformat(),
            total_minutes_available=constraints.time_available_minutes,
        )

        elapsed = 0

        for task in ranked:
            if len(plan.items) >= constraints.max_tasks_per_day:
                plan.drop_item(DroppedItem(task, "Reached max tasks per day"))
                continue

            if elapsed + task.duration_minutes > constraints.time_available_minutes:
                plan.drop_item(DroppedItem(
                    task,
                    f"Not enough time ({constraints.time_available_minutes - elapsed} min left, "
                    f"needs {task.duration_minutes} min)",
                ))
                continue

            start = self._minutes_to_time(elapsed)
            end = self._minutes_to_time(elapsed + task.duration_minutes)
            reason = self.explain_choice(task)

            plan.add_item(PlanItem(task=task, start_time=start, end_time=end, reason=reason))
            elapsed += task.duration_minutes

        scheduled = [i.task.title for i in plan.items]
        dropped = [d.task.title for d in plan.dropped]
        plan.summary_reasoning = (
            f"Scheduled {len(plan.items)} task(s) for {pet.name} "
            f"using {plan.total_minutes_used}/{constraints.time_available_minutes} min. "
            + (f"Dropped: {', '.join(dropped)}." if dropped else "All tasks fit.")
        )

        return plan

    def score_task(
        self,
        task: CareTask,
        constraints: ConstraintProfile,
    ) -> float:
        """Score a task using priority, duration, and preferences."""
        # Primary: priority value (HIGH=3, MED=2, LOW=1)
        # Tiebreaker: shorter tasks score slightly higher (fit more into the day)
        priority_score = task.priority.value * 100
        efficiency_bonus = max(0, 60 - task.duration_minutes)

        # Preference boost: if owner flagged a category as preferred
        pref_boost = 50 if constraints.owner_preferences.get(task.category) == "preferred" else 0

        return priority_score + efficiency_bonus + pref_boost

    def explain_choice(self, task: CareTask) -> str:
        """Summarize why a task was selected."""
        return f"{task.priority.name} priority {task.category} task ({task.duration_minutes} min)"

    def _minutes_to_time(self, minutes: int) -> str:
        """Convert elapsed minutes to a time string starting from START_HOUR."""
        h = self.START_HOUR + minutes // 60
        m = minutes % 60
        return f"{h:02d}:{m:02d}"
