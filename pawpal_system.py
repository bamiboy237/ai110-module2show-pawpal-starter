"""PawPal+ — Pet care planning system."""

from __future__ import annotations

from dataclasses import dataclass, field
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

    def summary(self) -> str:
        """Return a readable description like 'Mochi (dog, 3 yrs)'."""
        ...


@dataclass
class CareTask:
    task_id: str
    title: str
    category: str
    duration_minutes: int
    priority: Priority
    notes: str = ""


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
        """Add a scheduled task to the plan."""
        ...

    def drop_item(self, item: DroppedItem) -> None:
        """Record a task that was excluded from the plan."""
        ...

    def utilization(self) -> float:
        """Return the percentage of available time used (0.0 – 1.0)."""
        ...


# ── Scheduler ─────────────────────────────────────────────────────

class Scheduler:
    """Generates a DailyPlan from tasks and constraints."""

    def generate_plan(
        self,
        owner: Owner,
        pet: Pet,
        tasks: list[CareTask],
        constraints: ConstraintProfile,
    ) -> DailyPlan:
        """Build an optimized daily plan based on priorities and constraints."""
        ...

    def score_task(
        self,
        task: CareTask,
        constraints: ConstraintProfile,
    ) -> float:
        """Score a task for ranking (higher = scheduled first)."""
        ...

    def explain_choice(self, task: CareTask) -> str:
        """Return a human-readable reason why a task was included or excluded."""
        ...
