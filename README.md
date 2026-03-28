# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

Beyond the basic daily planner, PawPal+ includes four algorithmic features:

- **Filter tasks** — narrow tasks by completion status, category, priority, or pet name (`Scheduler.filter_tasks`, `Owner.get_tasks`).
- **Sort tasks** — order tasks by priority, duration, category, title, or fixed time (`Pet.sort_tasks`, `Scheduler.sort_by_time`).
- **Recurring tasks** — daily and weekly tasks auto-reset via `CareTask.is_due()`, so the scheduler re-includes them without manual re-adding.
- **Conflict detection** — `Scheduler.detect_conflicts` uses a sort-then-sweep algorithm to find overlapping fixed-time tasks within or across pets, returning warnings instead of crashing.

The scheduler itself uses a **two-phase greedy algorithm**: fixed-time tasks are placed first (with overlap rejection), then free time slots are filled with flexible tasks ranked by a scoring formula (priority + efficiency bonus + preference boost).

## Testing PawPal+

### Running tests

```bash
source .venv/bin/activate
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

The test suite contains 22 tests across six areas:

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

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
