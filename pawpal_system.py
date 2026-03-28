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
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_pet(self, name: str) -> Pet | None:
        """Look up a pet by name."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        return None

    def get_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[tuple[str, CareTask]]:
        """Collect tasks across all pets with optional filters.

        Args:
            pet_name: If provided, only include tasks belonging to this pet.
            completed: If provided, only include tasks matching this status.

        Returns:
            List of (pet_name, task) tuples so callers know which pet owns
            each task.
        """
        results: list[tuple[str, CareTask]] = []
        for pet in self.pets:
            if pet_name is not None and pet.name != pet_name:
                continue
            for task in pet.tasks:
                if completed is not None and task.completed != completed:
                    continue
                results.append((pet.name, task))
        return results


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

    @staticmethod
    def sort_tasks(
        tasks: list[CareTask], key: str = "priority", reverse: bool = True,
    ) -> list[CareTask]:
        """Sort tasks by the given key.

        Args:
            tasks: The list of CareTask objects to sort.
            key: Sort criterion — one of "priority", "duration", "category",
                 or "title". Defaults to "priority".
            reverse: If True, sort descending (highest first). Defaults to True.

        Returns:
            A new sorted list (the original is not modified).
        """
        sort_keys = {
            "priority": lambda t: t.priority.value,
            "duration": lambda t: t.duration_minutes,
            "category": lambda t: t.category,
            "title": lambda t: t.title,
        }
        return sorted(tasks, key=sort_keys.get(key, sort_keys["priority"]), reverse=reverse)


@dataclass
class CareTask:
    task_id: str
    title: str
    category: str
    duration_minutes: int
    priority: Priority
    notes: str = ""
    completed: bool = False
    recurrence: str | None = None
    last_completed_date: date | None = None
    fixed_time: str | None = None

    def mark_complete(self) -> None:
        """Mark this task as completed and record the date."""
        self.completed = True
        self.last_completed_date = date.today()

    def is_due(self, today: date | None = None) -> bool:
        """Check whether this task needs to be done today.

        For non-recurring tasks, returns True if not yet completed.
        For recurring tasks, compares last_completed_date against today
        using the recurrence interval (daily or weekly).

        Args:
            today: Override for the current date (useful for testing).
        """
        if today is None:
            today = date.today()
        if self.recurrence is None:
            return not self.completed
        if self.last_completed_date is None:
            return True
        if self.recurrence == "daily":
            return self.last_completed_date < today
        if self.recurrence == "weekly":
            return (today - self.last_completed_date).days >= 7
        return True


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
    conflicts: list[str] = field(default_factory=list)

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
        
        """Build a daily schedule using a two-phase algorithm.

        Phase 1 places fixed-time (anchored) tasks, detecting overlaps.
        Phase 2 builds free time slots from the gaps and fills them with
        flexible tasks in descending score order (greedy first-fit).

        Args:
            owner: The pet owner (used for future multi-pet plans).
            pet: The pet whose tasks are being scheduled.
            tasks: Candidate tasks — only those passing is_due() are considered.
            constraints: Time budget, preferences, and max-tasks-per-day limit.

        Returns:
            A DailyPlan with scheduled items, dropped items, and any conflict
            warnings.
        """
        today = date.today()
        tasks = [t for t in tasks if t.is_due(today)]

        plan = DailyPlan(
            date=today.isoformat(),
            total_minutes_available=constraints.time_available_minutes,
        )

        day_start = self.START_HOUR * 60
        day_end = day_start + constraints.time_available_minutes

        # Split into fixed-time (anchored) and flexible tasks
        fixed = sorted(
            [t for t in tasks if t.fixed_time],
            key=lambda t: self._time_to_minutes(t.fixed_time),
        )
        flexible = sorted(
            [t for t in tasks if not t.fixed_time],
            key=lambda t: self.score_task(t, constraints),
            reverse=True,
        )

        # Phase 1: place fixed-time tasks, detect conflicts
        occupied: list[tuple[int, int, CareTask]] = []

        for task in fixed:
            start_min = self._time_to_minutes(task.fixed_time)
            end_min = start_min + task.duration_minutes

            if start_min < day_start or end_min > day_end:
                plan.drop_item(DroppedItem(task, "Outside available time window"))
                continue

            if len(plan.items) >= constraints.max_tasks_per_day:
                plan.drop_item(DroppedItem(task, "Reached max tasks per day"))
                continue

            conflict_found = False
            for occ_start, occ_end, occ_task in occupied:
                if start_min < occ_end and end_min > occ_start:
                    plan.conflicts.append(
                        f"'{task.title}' ({task.fixed_time}) overlaps with "
                        f"'{occ_task.title}' ({occ_task.fixed_time})"
                    )
                    plan.drop_item(DroppedItem(task, "Time conflict with fixed task"))
                    conflict_found = True
                    break

            if conflict_found:
                continue

            plan.add_item(PlanItem(
                task=task,
                start_time=task.fixed_time,
                end_time=self._minutes_to_time(end_min - day_start),
                reason=self.explain_choice(task),
            ))
            occupied.append((start_min, end_min, task))

        # Phase 2: build free slots, fill with flexible tasks
        occupied.sort(key=lambda x: x[0])
        free_slots: list[list[int]] = []

        cursor = day_start
        for occ_start, occ_end, _ in occupied:
            if cursor < occ_start:
                free_slots.append([cursor, occ_start])
            cursor = max(cursor, occ_end)
        if cursor < day_end:
            free_slots.append([cursor, day_end])

        for task in flexible:
            if len(plan.items) >= constraints.max_tasks_per_day:
                plan.drop_item(DroppedItem(task, "Reached max tasks per day"))
                continue

            placed = False
            for slot in free_slots:
                if task.duration_minutes <= (slot[1] - slot[0]):
                    start_elapsed = slot[0] - day_start
                    plan.add_item(PlanItem(
                        task=task,
                        start_time=self._minutes_to_time(start_elapsed),
                        end_time=self._minutes_to_time(start_elapsed + task.duration_minutes),
                        reason=self.explain_choice(task),
                    ))
                    slot[0] += task.duration_minutes
                    placed = True
                    break

            if not placed:
                plan.drop_item(DroppedItem(
                    task,
                    f"No contiguous slot (needs {task.duration_minutes} min)",
                ))

        # Summary
        dropped_names = [d.task.title for d in plan.dropped]
        conflict_note = f" Conflicts: {len(plan.conflicts)}." if plan.conflicts else ""
        plan.summary_reasoning = (
            f"Scheduled {len(plan.items)} task(s) for {pet.name} "
            f"using {plan.total_minutes_used}/{constraints.time_available_minutes} min. "
            + (f"Dropped: {', '.join(dropped_names)}. " if dropped_names else "All tasks fit. ")
            + conflict_note
        )

        return plan

    def score_task(
        self,
        task: CareTask,
        constraints: ConstraintProfile,
    ) -> float:
        """Score a task for scheduling priority.

        Formula: priority.value * 100 + efficiency_bonus + preference_boost.
        Higher scores are scheduled first. Shorter tasks get a small bonus
        so the scheduler can fit more into the day.

        Args:
            task: The task to score.
            constraints: Provides owner_preferences for the category boost.

        Returns:
            A numeric score (higher = scheduled sooner).
        """
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

    @staticmethod
    def _time_to_minutes(time_str: str) -> int:
        """Convert 'HH:MM' to total minutes since midnight."""
        h, m = map(int, time_str.split(":"))
        return h * 60 + m

    @staticmethod
    def sort_by_time(tasks: list[CareTask], reverse: bool = False) -> list[CareTask]:
        """Sort tasks chronologically by their fixed_time ('HH:MM').

        Leverages lexicographic string comparison on zero-padded times.
        Tasks without a fixed_time are pushed to the end via a '99:99'
        sentinel value.

        Args:
            tasks: The list of CareTask objects to sort.
            reverse: If True, sort latest-first. Defaults to False.

        Returns:
            A new sorted list (the original is not modified).
        """
        return sorted(
            tasks,
            key=lambda t: t.fixed_time if t.fixed_time else "99:99",
            reverse=reverse,
        )

    @staticmethod
    def detect_conflicts(
        labeled_tasks: list[tuple[str, CareTask]],
    ) -> list[str]:
        """Detect time overlaps among fixed-time tasks (within or across pets).

        Uses a sort-then-sweep algorithm: tasks are sorted by start time,
        then each task is compared only to its neighbors until a non-
        overlapping task is found (early exit via break).

        Args:
            labeled_tasks: List of (label, task) pairs where label is
                typically the pet name. Only tasks with a fixed_time are
                checked.

        Returns:
            A list of human-readable warning strings. An empty list means
            no conflicts were found.
        """
        fixed = [
            (label, t) for label, t in labeled_tasks if t.fixed_time
        ]
        fixed.sort(key=lambda pair: Scheduler._time_to_minutes(pair[1].fixed_time))

        warnings: list[str] = []
        for i in range(len(fixed)):
            label_a, task_a = fixed[i]
            start_a = Scheduler._time_to_minutes(task_a.fixed_time)
            end_a = start_a + task_a.duration_minutes

            for j in range(i + 1, len(fixed)):
                label_b, task_b = fixed[j]
                start_b = Scheduler._time_to_minutes(task_b.fixed_time)

                if start_b >= end_a:
                    break  # sorted, so no further overlaps with task_a

                warnings.append(
                    f"⚠ CONFLICT: '{task_a.title}' [{label_a}] "
                    f"({task_a.fixed_time}-{Scheduler._minutes_to_time_static(end_a)}) "
                    f"overlaps '{task_b.title}' [{label_b}] "
                    f"({task_b.fixed_time})"
                )
        return warnings

    @staticmethod
    def _minutes_to_time_static(total_minutes: int) -> str:
        """Convert total minutes since midnight to 'HH:MM'."""
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"

    @staticmethod
    def filter_tasks(
        tasks: list[CareTask],
        completed: bool | None = None,
        category: str | None = None,
        priority: Priority | None = None,
    ) -> list[CareTask]:
        """Filter tasks by completion status, category, and/or priority.

        All provided criteria must match (AND logic). Passing None for a
        parameter means "don't filter on this dimension."

        Args:
            tasks: The list of CareTask objects to filter.
            completed: Filter by completion status (True/False), or None for all.
            category: Filter by exact category string, or None for all.
            priority: Filter by Priority enum value, or None for all.

        Returns:
            A new list containing only the tasks that match all criteria.
        """
        result = tasks
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        if category is not None:
            result = [t for t in result if t.category == category]
        if priority is not None:
            result = [t for t in result if t.priority == priority]
        return result
