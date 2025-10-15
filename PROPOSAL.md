# Duty Management Application Improvement Proposal

## Current Snapshot
- **Stack:** Flask + SQLAlchemy with SQLite persistence (`app.py`).
- **Primary Views:**
  - Pending and received day-off summary (`templates/index.html`).
  - Duty calendar with month filter (`templates/duties.html`).
  - Staff roster with CRUD forms (`templates/staff.html`, `templates/edit_staff.html`).
- **Data Model:** `Staff` and `Duty` tables with relationships for tracking service assignments and compensatory days.

## Pain Points & Risks
1. **Database lifecycle** – Tables are created on every request via `@app.before_request`, which can mask migration issues and slow responses.
2. **Date handling** – Manual parsing/formatting in several routes raises the chance of inconsistent input and locale bugs.
3. **Sorting & filtering logic in templates** – Complex sorting is performed in Python lists after fetching entire collections, limiting scalability.
4. **UI consistency** – Inline styles dominate templates, making theme updates costly and inconsistent across pages.
5. **Auditability** – No tracking for who granted a day off, nor history of edits/deletions.

## Recommended Enhancements
### 1. Backend & Data Integrity
- Move table creation to a dedicated CLI/init script and adopt Alembic migrations to evolve the schema safely.
- Promote stricter data validation by enforcing unique staff names and non-null ranks where applicable.
- Introduce status enums for duty type and compensatory day state to prevent boolean proliferation.
- Normalize day-off auditing by adding fields for `approved_by_staff_id` and timestamps (`created_at`, `updated_at`).

### 2. Scheduling Logic
- Add computed properties or database views for outstanding/fulfilled days off to avoid repeated aggregation code in routes like `/` and `/staff/<id>/duties`.
- Provide conflict detection when assigning duties (e.g., prevent two duties on the same day per staff member).
- Offer bulk assignment tools (e.g., recurring duty generator) for faster schedule creation.

### 3. UX Improvements
- Replace inline CSS with a shared stylesheet under `static/` and leverage a utility framework (e.g., Tailwind via CDN) for consistent styling.
- Add badges and filters directly in the duties table for quick toggling of honorary duties or pending days off.
- Implement modal forms for quick edits, reducing page navigation.
- Localize date inputs with a dedicated picker configured for `el-GR` locale to eliminate manual format typing.

### 4. Reporting & Insights
- Provide export options (CSV/PDF) summarizing duty assignments by month or staff member.
- Surface KPIs (e.g., average days off per month, honorary duty share) on the dashboard for leadership visibility.
- Include printable schedules with signature placeholders for duty approvals.

### 5. Architecture & Deployment
- Structure the Flask app as a package with blueprints (`staff`, `duties`, `dashboard`) for maintainability.
- Add automated tests (PyTest + Flask testing client) covering CRUD flows and aggregation logic.
- Containerize the app with a production-ready server (Gunicorn) and CI pipeline to run tests and linting on push.

## Quick Wins
1. Extract shared CSS into `static/styles.css` and link it from all templates.
2. Refactor `/` route aggregation into helper services that can be unit-tested independently.
3. Replace `@app.before_request` table creation with a CLI command run during deployment.

## Long-Term Vision
- Expand to a REST API that can power a future Godot-based duty planner interface or mobile companion app.
- Integrate authentication and role-based access control so only authorized officers can modify sensitive records.
- Offer notification hooks (email/SMS) to remind staff of upcoming duties or approved day offs.

By prioritizing backend robustness, UX cohesion, and analytics, the duty management tool can scale from a basic tracker to a dependable operational platform.
