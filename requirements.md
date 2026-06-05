# Requirements — Food Product Recommendation Web Platform

> Extracted from: *11755 – Human-Computer Interaction, Summer Semester 2026 — Final Assignment*
> Scope: implementation-focused requirements with contextual notes from documentation and presentation deliverables.

---

## Project Context

Build a **web platform that recommends food products** with explainable AI (XAI). The platform must make the underlying AI model's recommendations transparent and understandable to end users. It has been designed through a User-Centered Design process, meaning usability and accessibility are first-class concerns, not afterthoughts.

---

## 1. Functional Requirements

### 1.1 Food Product Recommendation Engine
- Integrate or interface with an AI/ML model that produces food product recommendations.
- The model must expose enough internals (feature importances, confidence scores, reasoning paths, etc.) to support XAI visualizations.
- Use a real or representative food product **dataset** as input (document its source and structure clearly in code comments).

### 1.2 Explainable AI (XAI) Features
These are the highest-weight documentation items (10 % of grade) and must be clearly surfaced in the UI:

- Display **why** a product was recommended (e.g., SHAP values, LIME explanations, feature-importance bars, counterfactual "if you liked X because of Y…" text).
- Show the **confidence level** of each recommendation in a user-readable way.
- Provide a **model overview** section or tooltip that explains in plain language what the AI considers when making recommendations.
- All XAI elements must be understandable to a non-technical user — avoid raw model output; translate numbers into natural language or intuitive visuals.

### 1.3 Navigation & Help Features
*(10 % of implementation grade)*

- Persistent top-level navigation covering at minimum: Home / Recommendations / How It Works (XAI explainer) / Help.
- In-context help: tooltips or info icons on every non-obvious UI element.
- A dedicated **Help / FAQ** section explaining how to use the platform and how to interpret recommendations.
- Breadcrumbs or clear back-navigation on all secondary views.
- Search and/or filter controls for browsing food products.

### 1.4 Dashboard
The central UI is described as a **dashboard** throughout the assignment. It must include:

- A personalized recommendation feed with XAI annotations.
- Summary statistics or visual indicators (e.g., match score, nutritional highlights).
- Usability-tested interaction flows (see UX notes below).

---

## 2. Non-Functional Requirements

### 2.1 Responsiveness
*(10 % of implementation grade)*

- The platform must work correctly across **mobile, tablet, and desktop** screen sizes.
- Use responsive CSS (flexbox / grid / media queries or a utility-first framework).
- No horizontal scroll, no broken layouts, no truncated XAI elements at any common breakpoint.
- Test at minimum: 375 px (mobile), 768 px (tablet), 1280 px (desktop).

### 2.2 Accessibility
Inferred from the User-Centered Design process:

- Sufficient color contrast (WCAG AA minimum).
- Keyboard navigable.
- Semantic HTML / ARIA labels on interactive elements.

### 2.3 Performance
- XAI visualizations should not block initial page load; lazy-load or progressively reveal them.
- Aim for a perceived time-to-interactive under 3 s on a standard connection.

---

## 3. Code & Repository Requirements
*(10 % of implementation grade)*

- All code lives in a **GitHub repository**.
- Include a `README.md` with:
  - Project description and tech stack.
  - Setup and run instructions (local dev + production build).
  - Dataset source and any preprocessing steps.
  - Overview of the XAI techniques used and where to find them in the code.
- Code must be **fully documented**: JSDoc / docstrings on all non-trivial functions, inline comments on XAI logic.
- Follow a consistent style (linter config committed alongside code).
- No secrets or API keys committed — use `.env` / environment variables.

---

## 4. UX / Design Constraints
*(Derived from the User-Centered Design and usability testing sections)*

- The design process included **user testing**; the implemented UI must reflect findings from those sessions. Any known pain points should be documented as resolved or tracked as issues.
- Prioritize **task completion**: a first-time user should be able to get a recommendation and understand why it was made without external guidance.
- Avoid jargon in labels and messages — the target audience is general consumers, not data scientists.
- Maintain visual consistency: a single design language / component library throughout.

---

## 5. Presentation / Demo Requirements (context only — not code deliverables)

The following are *not* coding tasks but inform what the implementation must support live:

- A **15-minute live demo** will walk through: design rationale → XAI method selection → dashboard demonstration → user testing insights → challenges → future work.
- The platform must be demo-ready: no placeholder data, no broken states, stable under a live walkthrough.
- Be prepared to explain every technical and design decision.

---

## 6. Out of Scope for Implementation

The following are required for the full assignment grade but are not implementation tasks:

- The 10-page IEEE-format paper (documentation deliverable).
- Formal user testing reports and usability test scripts.
- Presentation slides.

These are listed here only so an implementing agent knows they exist and can write code that makes them easier to produce (e.g., exporting usability metrics, logging interaction events).

---

## 7. Acceptance Checklist

- [ ] Responsive layout verified at 375 px, 768 px, 1280 px.
- [ ] Navigation and help features present and functional.
- [ ] At least one XAI technique implemented and rendered in the UI.
- [ ] XAI output is human-readable (no raw model dumps visible to users).
- [ ] All code committed to GitHub with a complete `README.md`.
- [ ] Code is documented (comments + docstrings).
- [ ] No hardcoded secrets.
- [ ] Platform runs end-to-end without errors in a clean environment.
- [ ] Dashboard is demo-stable (no placeholder data, no broken states).
