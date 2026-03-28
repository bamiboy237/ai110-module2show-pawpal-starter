# PawPal+ Project Reflection

## 1. System Design

Response: A User should be a able to add pets and their info, add/edit tasks with constraints, get a plan/daily schedule, see the plan


**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

Response: The design includes 10 classes. **Owner** and **Pet** hold user/animal info. **CareTask** represents a care activity with duration and priority (using a **Priority** enum). **ConstraintProfile** bundles scheduling limits (available time, max tasks, preferences). **Scheduler** scores and ranks tasks, then produces a **DailyPlan** containing **PlanItems** (scheduled tasks with time slots and reasoning) and **DroppedItems** (excluded tasks with explanations). **PawPalApp** is the Streamlit UI layer that collects input and displays the plan.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Response: Added `task_id: str` to CareTask. This is the entity users edit, select, and delete, so it needs a stable identifier. PlanItem and DroppedItem reference the CareTask object directly and don't need their own ids unless we later serialize to storage with independent row identifiers.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
