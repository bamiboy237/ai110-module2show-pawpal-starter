# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit-powered pet care planner that helps busy owners schedule daily tasks for their pets. It supports multiple pets, fixed-time and flexible tasks, recurring schedules, and automatic conflict detection.

## Features

### Owner and Pet Management
- Register an owner with a daily time budget and category preferences
- Add multiple pets (dog, cat, or other) each with their own task list
- Look up any pet by name; view all pets in a summary table

### Task Scheduling (Two-Phase Greedy Algorithm)
- **Phase 1 — Fixed-time placement:** Tasks with an anchored start time (e.g., "09:00") are placed first, sorted chronologically. Overlapping tasks are rejected and recorded as dropped.
- **Phase 2 — Flexible gap-filling:** Remaining tasks are scored by `priority * 100 + efficiency_bonus + preference_boost` and greedily placed into the largest available time slot.
- Each scheduled task includes a plain-English reason explaining why it was selected.

### Sorting
- **By time** — Lexicographic sort on zero-padded "HH:MM" strings; tasks without a fixed time are pushed to the end via a `"99:99"` sentinel value (`Scheduler.sort_by_time`).
- **By priority, duration, category, or title** — Configurable key with ascending/descending toggle (`Pet.sort_tasks`).

### Filtering
- **By completion status** — Show all, incomplete only, or completed only.
- **By category** — Exercise, grooming, health, feeding, or general.
- **By priority** — LOW, MEDIUM, or HIGH.
- **By pet name** — Aggregate tasks across all pets with `Owner.get_tasks`, then narrow to one pet.
- All filters use AND logic and can be combined freely (`Scheduler.filter_tasks`).

### Recurring Tasks
- Set any task to repeat **daily** or **weekly**.
- `CareTask.is_due()` checks the recurrence interval against `last_completed_date` to decide if the task belongs in today's plan.
- Marking a recurring task complete records the date; the scheduler automatically re-includes it once the interval elapses.

### Conflict Detection
- **Sort-then-sweep algorithm** (`Scheduler.detect_conflicts`) — O(n log n) overlap detection across all pets.
- Finds overlapping fixed-time tasks both within a single pet and across different pets.
- Returns human-readable warnings (not crashes), displayed prominently in the UI with actionable tips.

## Demo

![Owner Setup and Add Pet](Screenshot%20from%202026-03-28%2017-27-53.png)

![Add Tasks with Filters and Sorting](Screenshot%20from%202026-03-28%2017-28-07.png)

![Generated Schedule with Metrics](Screenshot%20from%202026-03-28%2017-29-09.png)

To run the app locally:

```bash
source .venv/bin/activate
streamlit run app.py
```

## Architecture

The system is built from 10 classes defined in `pawpal_system.py`:

| Class | Role |
|-------|------|
| `Owner` | Stores owner info, preferences, and a list of pets |
| `Pet` | Holds pet details and its task list |
| `CareTask` | A single care activity with duration, priority, recurrence, and optional fixed time |
| `Priority` | Enum: LOW (1), MEDIUM (2), HIGH (3) |
| `ConstraintProfile` | Bundles scheduling limits (time budget, max tasks, preferences) |
| `Scheduler` | Scores, sorts, filters, detects conflicts, and generates the daily plan |
| `DailyPlan` | The output: scheduled items, dropped items, conflicts, and utilization stats |
| `PlanItem` | A scheduled task with start/end time and reasoning |
| `DroppedItem` | A task that could not be scheduled, with the reason why |
| `PawPalApp` | The Streamlit UI layer (`app.py`) |

See [uml_final.png](uml_final.png) for the full class diagram, or edit [pawpal_uml.mmd](pawpal_uml.mmd) in Mermaid.

## Testing PawPal+

### Running tests

```bash
source .venv/bin/activate
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

The test suite contains 22 tests across seven areas:

| Area | Tests | What is verified |
|------|-------|------------------|
| Task basics | 2 | Marking complete, adding tasks to a pet |
| Sort by time | 2 | Chronological ordering, `None` times sort last |
| Sort by priority | 2 | HIGH > MEDIUM > LOW, same-priority stability |
| Recurrence logic | 5 | Daily/weekly due dates, never-completed, one-time tasks |
| Conflict detection | 4 | Same-pet overlaps, cross-pet overlaps, no-conflict and no-fixed-time edge cases |
| Scheduling | 3 | Fixed-before-flexible placement, empty input, dropped tasks when time runs out |
| Filtering | 3 | By category, by priority, by pet name across multiple pets |

### Confidence level

**4 / 5 stars** — The core scheduling logic, recurrence rules, and conflict detection are well covered with both happy-path and edge-case tests. One star is withheld because the Streamlit UI layer (`app.py`) is not yet tested, and more complex multi-pet scheduling scenarios (e.g., interleaving fixed tasks from two pets into a single owner time budget) have not been exercised.

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
