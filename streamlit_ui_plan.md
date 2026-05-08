# Streamlit UI Implementation Plan: Student-Facing Enrollment Portal

## Goal

Build a simple Streamlit student portal for an already-authenticated simulated student. The app should assume the student is already logged in, such as `Alex Rivers`, and should not include login, registration, password handling, authentication forms, or account creation.

The UI will focus on the student experience:

1. Viewing currently enrolled courses on a dashboard.
2. Entering an enrollment key to join a course.
3. Opening a specific class page.
4. Soft-unenrolling from a class.
5. Returning from a class page back to the dashboard.

The UI should follow the multi-layer design from Session 1 by keeping Streamlit concerns in the UI layer and calling the existing service layer, such as `student_service.py`, for enrollment behavior. Backend changes should be minimal.

---

## Scope

### In Scope

- Streamlit student dashboard.
- Streamlit class detail page.
- Session-state controlled routing.
- Simulated authenticated student identity.
- Enrollment by enrollment key.
- Current enrolled course display.
- Navigation to a selected class.
- Soft-unenrollment from a course.
- User feedback using Streamlit message components.
- Refreshing the page after state-changing actions with `st.rerun()`.

### Out of Scope

- Login UI.
- Registration UI.
- Password fields.
- Authentication logic.
- User account creation.
- Role-based access control beyond storing a simulated role in session state.
- Major backend redesign.
- Database schema changes unless absolutely necessary.

---

## Required Session State

The Streamlit app must use `st.session_state` for the following values:

| Session State Key | Purpose | Example Value |
|---|---|---|
| `student_role` | Stores the simulated role for the authenticated student. | `"student"` |
| `current_page` | Controls which view is displayed. | `"dashboard"` or `"class_page"` |
| `selected_class_id` | Stores the course ID for the selected class page. | `"MISY350"` |
| `current_student` | Stores the simulated authenticated student profile. | `{ "user_id": "u101", "name": "Alex Rivers", "email": "alex@example.edu" }` |

### Session State Initialization

At the top of the Streamlit app, initialize session state values only if they do not already exist.

Planned logic:

```python
if "student_role" not in st.session_state:
    st.session_state.student_role = "student"

if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

if "selected_class_id" not in st.session_state:
    st.session_state.selected_class_id = None

if "current_student" not in st.session_state:
    st.session_state.current_student = {
        "user_id": "u101",
        "name": "Alex Rivers",
        "email": "alex@example.edu",
    }
```

---

## App Structure

The app should be organized around a simple routing function that checks `st.session_state.current_page`.

Planned structure:

```python
def main():
    initialize_session_state()

    if st.session_state.current_page == "dashboard":
        render_dashboard()
    elif st.session_state.current_page == "class_page":
        render_class_page()
    else:
        st.session_state.current_page = "dashboard"
        st.rerun()
```

This keeps routing simple and avoids introducing extra routing libraries.

---

## Service Layer Usage

The Streamlit UI should call the existing service layer instead of directly performing database work.

Expected service calls:

| UI Action | Service Layer Function |
|---|---|
| Load enrolled courses | `get_student_enrollments(user_id)` |
| Enroll with key | `enroll_with_key(user_id, email, enrollment_key)` |
| Soft-unenroll | `soft_unenroll_student(user_id, course_id)` |
| Display class details | Prefer using enrolled course data from `get_student_enrollments(user_id)` or an existing course lookup function if available. |

If these functions currently exist in a procedural starter file instead of `student_service.py`, the plan is to call the equivalent service-layer functions after the Session 1 refactor. Avoid moving database logic into the Streamlit file.

---

## Page 1: Dashboard

### Purpose

The dashboard is the student’s main landing page. It greets the simulated student, allows them to enter an enrollment key, and shows their enrolled courses.

### Required Components

- `st.title` greeting.
- `st.expander` for enrollment key entry.
- `st.text_input` for enrollment key.
- Enrollment submit button.
- `st.columns` layout for enrolled course cards.
- `Go to Class` button for each course.
- `Unenroll` button for each course.
- `st.success` for successful enrollment.
- `st.warning` for invalid enrollment keys or failed actions.
- `st.rerun()` after successful state-changing actions.

### Dashboard Layout Plan

#### 1. Greeting

Use `st.title` to greet the simulated student.

Example:

```python
student = st.session_state.current_student
st.title(f"Welcome, {student['name']}")
```

#### 2. Enrollment Key Expander

Use `st.expander` to keep the enrollment form compact.

Example:

```python
with st.expander("Enroll in a class"):
    enrollment_key = st.text_input("Enrollment key")
    if st.button("Enroll"):
        result = student_service.enroll_with_key(
            student["user_id"],
            student["email"],
            enrollment_key,
        )

        if result:
            st.success("Enrollment successful.")
            st.rerun()
        else:
            st.warning("Enrollment failed. Check the enrollment key and try again.")
```

#### 3. Enrolled Courses Section

Load currently enrolled courses from the service layer.

Example:

```python
enrollments = student_service.get_student_enrollments(student["user_id"])
```

If the student has no enrolled courses, show a warning or informational message.

Example:

```python
if not enrollments:
    st.warning("You are not currently enrolled in any classes.")
```

#### 4. Course Cards with Columns

Use `st.columns` to display enrolled classes in a simple card-like layout.

Planned behavior:

- Each course displays course ID, course name, instructor, and enrollment status.
- `Go to Class` sets `selected_class_id` and changes `current_page` to `"class_page"`.
- `Unenroll` calls the service layer, shows feedback, and refreshes the page.

Example:

```python
columns = st.columns(2)

for index, course in enumerate(enrollments):
    with columns[index % 2]:
        st.markdown(f"### {course['course_id']}")
        st.markdown(f"**Course:** {course['course_name']}")
        st.markdown(f"**Instructor:** {course['instructor']}")
        st.markdown(f"**Status:** {course['status']}")

        if st.button("Go to Class", key=f"go_{course['course_id']}"):
            st.session_state.selected_class_id = course["course_id"]
            st.session_state.current_page = "class_page"
            st.rerun()

        if st.button("Unenroll", key=f"unenroll_{course['course_id']}"):
            success = student_service.soft_unenroll_student(
                student["user_id"],
                course["course_id"],
            )

            if success:
                st.success("You have been unenrolled from this class.")
                st.rerun()
            else:
                st.warning("Unable to unenroll from this class.")
```

---

## Page 2: Class Page

### Purpose

The class page displays details for the course selected from the dashboard.

### Required Components

- `st.subheader` for the selected class title.
- `st.markdown` for class details.
- `Back` button to return to the dashboard.
- Session-state based selected class loading.
- Warning message if no class is selected.

### Class Page Layout Plan

#### 1. Validate Selected Class

The class page depends on `st.session_state.selected_class_id`.

If no class is selected, show a warning and return to the dashboard.

Example:

```python
selected_class_id = st.session_state.selected_class_id

if not selected_class_id:
    st.warning("No class selected.")
    if st.button("Back to Dashboard"):
        st.session_state.current_page = "dashboard"
        st.rerun()
    return
```

#### 2. Load Class Details

Use the service layer to load the student’s current enrollments, then find the selected class by `course_id`.

Example:

```python
student = st.session_state.current_student
enrollments = student_service.get_student_enrollments(student["user_id"])
selected_course = next(
    (
        course
        for course in enrollments
        if course["course_id"] == selected_class_id
    ),
    None,
)
```

If the selected course is not found, show a warning and allow the student to return to the dashboard.

Example:

```python
if not selected_course:
    st.warning("This class could not be found in your current enrollments.")
    if st.button("Back to Dashboard"):
        st.session_state.current_page = "dashboard"
        st.session_state.selected_class_id = None
        st.rerun()
    return
```

#### 3. Display Class Details

Use `st.subheader` and `st.markdown`.

Example:

```python
st.subheader(selected_course["course_name"])
st.markdown(f"**Course ID:** {selected_course['course_id']}")
st.markdown(f"**Instructor:** {selected_course['instructor']}")
st.markdown(f"**Enrollment Status:** {selected_course['status']}")
st.markdown(f"**Enrolled At:** {selected_course['enrolled_at']}")
```

#### 4. Back Button

The back button should clear the selected class and return to the dashboard.

Example:

```python
if st.button("Back"):
    st.session_state.selected_class_id = None
    st.session_state.current_page = "dashboard"
    st.rerun()
```

---

## Feedback and Refresh Behavior

The UI should provide immediate feedback for student actions.

| Action | Success Feedback | Error Feedback | Refresh Behavior |
|---|---|---|---|
| Enroll with valid key | `st.success("Enrollment successful.")` | N/A | `st.rerun()` |
| Enroll with invalid key | N/A | `st.warning("Enrollment failed. Check the enrollment key and try again.")` | No rerun needed |
| Soft-unenroll success | `st.success("You have been unenrolled from this class.")` | N/A | `st.rerun()` |
| Soft-unenroll failure | N/A | `st.warning("Unable to unenroll from this class.")` | No rerun needed |
| Missing selected class | N/A | `st.warning("No class selected.")` | Back button can rerun |

Because `st.rerun()` refreshes the page immediately, success messages may disappear quickly after rerun. If persistent success messages are required later, add a temporary `session_state.feedback_message` value, display it at the top of the dashboard, then clear it after rendering. This should be considered optional and not required for the first implementation.

---

## Minimal Backend Change Strategy

The Streamlit file should not contain raw SQL or database-specific logic.

Backend changes should be limited to:

1. Ensuring service-layer functions exist and are importable from `student_service.py`.
2. Ensuring the app can initialize the local database before rendering the UI.
3. Adding a small helper function only if necessary to fetch course details by `course_id`.

Preferred approach:

```python
import student_service
```

Then call existing service functions directly from UI event handlers.

Avoid:

- Rewriting the database schema.
- Adding authentication tables.
- Adding password fields.
- Handling login sessions.
- Performing SQL queries directly inside the Streamlit page.

---

## Proposed File Organization

Expected structure after implementation:

```text
project_folder/
├── app.py
├── student_service.py
├── student_repository.py
├── student_enrollment_practice.db
└── streamlit_ui_plan.md
```

If the current project still uses a single procedural file, use the equivalent service-layer functions from the existing refactor target. The UI plan should still assume the Session 1 multi-layer design.

---

## Implementation Order

1. Create `streamlit_ui_plan.md` for review before modifying any code.
2. Confirm existing service-layer function names.
3. Create or update `app.py` only after the plan is reviewed.
4. Add session-state initialization.
5. Add simple session-state router.
6. Build `render_dashboard()`.
7. Build enrollment key expander.
8. Build enrolled course display with `st.columns`.
9. Add `Go to Class` routing behavior.
10. Add `Unenroll` behavior using soft-unenrollment.
11. Build `render_class_page()`.
12. Add `Back` button behavior.
13. Test dashboard loading, enrollment, class navigation, back navigation, and soft-unenrollment.

---

## Acceptance Checklist

The implementation is complete when:

- [ ] The app assumes a simulated authenticated student, such as `Alex Rivers`.
- [ ] There is no login page.
- [ ] There is no registration page.
- [ ] There is no password handling.
- [ ] `st.session_state.student_role` is used.
- [ ] `st.session_state.current_page` is used for routing.
- [ ] `st.session_state.selected_class_id` is used for class selection.
- [ ] Dashboard uses `st.title` for the greeting.
- [ ] Dashboard includes an `st.expander` for enrollment key entry.
- [ ] Enrollment key input uses `st.text_input`.
- [ ] Enrolled courses are displayed using `st.columns`.
- [ ] Each enrolled course has a `Go to Class` button.
- [ ] Each enrolled course has an `Unenroll` button.
- [ ] Class page uses `st.subheader`.
- [ ] Class page uses `st.markdown` for class details.
- [ ] Class page has a `Back` button.
- [ ] Enrollments use the existing service layer.
- [ ] Soft-unenrollments use the existing service layer.
- [ ] `st.success` is used for successful actions.
- [ ] `st.warning` is used for errors or invalid actions.
- [ ] `st.rerun()` refreshes the view after successful state-changing actions.
- [ ] Backend changes are minimal.

---

## Summary

This Streamlit UI should be a lightweight student-facing portal built on top of the existing enrollment service layer. The design intentionally avoids authentication and focuses only on the authenticated student experience. The app will use session-state routing to move between a dashboard and a class detail page, while keeping database and business logic in the backend service layer.
