# PawPal+ Project Reflection

## 1. System Design

Response: A User should be a able to add pets and their info, add/edit tasks with constraints, get a plan/daily schedule, see the plan


**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

Response: My design includes 10 classes. **Owner** and **Pet** hold user/animal info. **CareTask** represents a care activity with duration and priority (using a **Priority** enum). **ConstraintProfile** bundles scheduling limits (available time, max tasks, preferences). **Scheduler** scores and ranks tasks, then produces a **DailyPlan** containing **PlanItems** (scheduled tasks with time slots and reasoning) and **DroppedItems** (excluded tasks with explanations). 

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Response: Added `task_id: str` to CareTask. This is the entity users edit, select, and delete, so it needs a stable identifier. PlanItem and DroppedItem reference the CareTask object directly and don't need their own ids unless we later serialize to storage with independent row identifiers.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

Response: The scheduler considers three constraints: **time budget** (total available minutes per day), **task priority** (HIGH/MEDIUM/LOW via an enum scored at 300/200/100), and **owner preferences** (a category boost of +50 for preferred categories like grooming). It also factors in **task efficiency** — shorter tasks get a small bonus so the algorithm can pack more into the day. I decided time was the hard constraint (you can't schedule 120 minutes of tasks into a 60-minute window), while priority and preferences are soft constraints that influence ordering. This mirrors how a real pet owner thinks: "I only have an hour — what's most important?"

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

Response: The scheduler uses a **greedy, first-fit** algorithm for flexible tasks: it sorts them by score (priority + efficiency + preference boost) and drops each one into the first free slot that is large enough. This means a high-priority 25-minute task might consume a 60-minute gap, leaving only 35 minutes — even though swapping it with a lower-priority 20-minute task first could have fit both. A true optimal solution would try every possible ordering (a bin-packing problem, which is NP-hard), so the greedy approach trades **schedule optimality for speed and simplicity**. For a pet-care app where the owner has 5-10 daily tasks this tradeoff is reasonable — the greedy result is "good enough" and the code stays readable. If we needed to squeeze every minute, we could add backtracking or use a constraint solver, but that complexity isn't justified at this scale.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

Response: I used Claude Code (via the VS Code extension) across every phase of the project. The most effective features were:

- **Inline code generation** — asking for specific methods like `sort_by_time()` with a lambda key, or `detect_conflicts()` with a sort-then-sweep algorithm. Describing the *algorithm name* in the prompt ("use a sort-then-sweep approach") produced much better results than vague requests like "find conflicts."
- **Explain and refactor sessions** — asking the AI to evaluate whether a "more Pythonic" version (using `any()` or `for/else`) was actually better than an explicit loop. This led to keeping the explicit flag pattern in `generate_plan` because the loop needed side effects (appending conflict messages) that `any()` can't express cleanly.
- **Test generation** — describing the 5 core behaviors to test and letting the AI draft all 20 new test functions, which I reviewed and ran. The AI correctly injected dates into `is_due()` tests instead of relying on `date.today()`.
- **Documentation** — using the AI to draft Google-style docstrings with Args/Returns blocks for algorithmic methods, and to restructure the README as a professional manual.

The most helpful prompts were specific and technical: "implement conflict detection using a sort-then-sweep algorithm that returns warnings instead of crashing" worked far better than "add conflict detection."

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

Response: When the AI first proposed the `Owner.get_tasks()` method, I didn't immediately understand why it returned `list[tuple[str, CareTask]]` instead of a plain `list[CareTask]`. I asked for an explanation before accepting the edit. The AI explained that when aggregating tasks across multiple pets, each task needs to carry its pet's name — otherwise you lose track of which pet owns which task. This matters for conflict detection (the warning message says "Bella's walk overlaps Mochi's feeding"). After understanding the reasoning, I accepted the same code. The lesson: don't accept code you can't explain, even if it looks correct.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

Response: The test suite covers 22 tests across seven areas: task basics (mark complete, add task), sorting by time (chronological order, None-goes-last), sorting by priority (descending order, same-priority stability), recurrence logic (daily due/not-due, weekly due/not-due, never-completed, one-time completed), conflict detection (same-pet overlap, cross-pet overlap, no overlap, no fixed-time tasks), schedule generation (fixed-before-flexible placement, empty input, dropped tasks), and filtering (by category, by priority, by pet name). These tests matter because the scheduler has multiple interacting subsystems — a bug in `is_due()` would silently exclude tasks from the plan, and a bug in conflict detection could let overlapping tasks through without warning. Testing both happy paths and edge cases (empty lists, None values, boundary dates) catches the bugs that only surface with unusual inputs.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

Response: **4 out of 5 stars.** The core algorithms (two-phase scheduling, sort-then-sweep conflict detection, recurrence checks) are well covered. If I had more time, I would test: (1) multi-pet scheduling where two pets compete for the same owner time budget, (2) a task with `fixed_time` set outside the available window (e.g., "14:00" when the owner only has 08:00–09:30), (3) the `max_tasks_per_day` cap when there are more eligible tasks than the limit, and (4) the Streamlit UI layer with integration tests to verify that session state, filters, and schedule generation work end-to-end in the browser.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

Response: The conflict detection system. It started as a simple "check if two tasks have the same time" idea, but evolved into a proper sort-then-sweep algorithm that detects *overlapping durations* across multiple pets. The fact that it works as a standalone static method (`Scheduler.detect_conflicts`) that accepts labeled tuples from any source — not just from `generate_plan` — makes it reusable. I'm also satisfied that the UI presents conflicts with actionable tips ("change the fixed time") instead of just showing a raw warning.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

Response: Two things. First, the scheduler currently plans for one pet at a time. I would redesign `generate_plan` to accept tasks from multiple pets and produce a unified daily plan for the owner, since the owner's time budget is shared. Second, the greedy gap-filling in Phase 2 doesn't backtrack — if a large high-priority task claims a slot that could have fit two smaller tasks, it can't undo that choice. Adding a simple backtracking step or a best-fit (instead of first-fit) slot selection would improve utilization without much added complexity.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

Response: The most important lesson is that **AI is a powerful collaborator, but you must remain the lead architect.** The AI can generate correct code fast, but it doesn't know your design intent. When the AI suggested replacing an explicit loop with `any()` for "Pythonic" style, I had to evaluate whether that actually served the code — it didn't, because the loop needed side effects. When it proposed the tuple return type for `get_tasks()`, I didn't accept it until I understood *why*. Using separate chat sessions for different phases (design, implementation, testing, documentation) helped keep each conversation focused and prevented context drift. The pattern that worked best: describe the algorithm or behavior you want by name, let the AI draft the implementation, then review it critically before accepting. You set the direction; the AI handles the velocity.
