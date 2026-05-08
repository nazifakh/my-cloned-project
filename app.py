"""
Student-facing Streamlit portal for the Module 8 enrollment app.

Run with:
    streamlit run app.py

Assumptions:
- The student is already authenticated as a simulated student.
- Backend/service functions already exist in student_service.py.
- No login, registration, or password handling is included.
"""

from __future__ import annotations

import streamlit as st

# Service layer imports only. Keep backend changes minimal.
# If your file is still named enrollment_starter.py, replace student_service with enrollment_starter.
from student_service import (
    create_tables,
    seed_sample_data,
    enroll_with_key,
    get_student_enrollments,
    soft_unenroll_student,
)


SIMULATED_STUDENT = {
    "user_id": "u101",
    "name": "Alex Rivers",
    "email": "alex@example.edu",
    "role": "student",
}

PAGE_DASHBOARD = "dashboard"
PAGE_CLASS = "class"


# -----------------------------
# App setup and session state
# -----------------------------

def initialize_database() -> None:
    """Create and seed the local database before rendering the UI."""
    create_tables()
    seed_sample_data()


def initialize_session_state() -> None:
    """Store student role, routing, and selected class in session state."""
    if "student" not in st.session_state:
        st.session_state.student = SIMULATED_STUDENT

    if "role" not in st.session_state:
        st.session_state.role = SIMULATED_STUDENT["role"]

    if "current_page" not in st.session_state:
        st.session_state.current_page = PAGE_DASHBOARD

    if "selected_class_id" not in st.session_state:
        st.session_state.selected_class_id = None


def go_to_dashboard() -> None:
    """Route back to the dashboard view."""
    st.session_state.current_page = PAGE_DASHBOARD
    st.session_state.selected_class_id = None
    st.rerun()


def go_to_class(course_id: str) -> None:
    """Route to a selected class page."""
    st.session_state.selected_class_id = course_id
    st.session_state.current_page = PAGE_CLASS
    st.rerun()


# -----------------------------
# Dashboard page
# -----------------------------

def render_enrollment_key_form(student: dict[str, str]) -> None:
    """Render the enrollment key input inside an expander."""
    with st.expander("Enroll in a class with an enrollment key"):
        enrollment_key = st.text_input(
            "Enrollment Key",
            placeholder="Example: WEB220-SPRING",
            key="enrollment_key_input",
        )

        if st.button("Enroll", type="primary"):
            result = enroll_with_key(
                user_id=student["user_id"],
                email=student["email"],
                enrollment_key=enrollment_key,
            )

            if result:
                st.success(f"Successfully enrolled in {result['course_id']}.")
                st.rerun()
            else:
                st.warning("Enrollment failed. Check that the enrollment key is valid.")


def render_course_cards(student: dict[str, str]) -> None:
    """Display enrolled courses using columns and action buttons."""
    enrolled_courses = get_student_enrollments(student["user_id"])

    st.subheader("My Enrolled Courses")

    if not enrolled_courses:
        st.warning("You are not currently enrolled in any courses.")
        return

    columns_per_row = 2

    for index, course in enumerate(enrolled_courses):
        if index % columns_per_row == 0:
            cols = st.columns(columns_per_row)

        with cols[index % columns_per_row]:
            st.markdown(f"### {course['course_id']}")
            st.markdown(f"**Course:** {course['course_name']}")
            st.markdown(f"**Instructor:** {course['instructor']}")
            st.markdown(f"**Status:** {course['status']}")

            if st.button(
                "Go to Class",
                key=f"go_to_class_{course['course_id']}",
            ):
                go_to_class(course["course_id"])

            if st.button(
                "Unenroll",
                key=f"unenroll_{course['course_id']}",
            ):
                was_unenrolled = soft_unenroll_student(
                    user_id=student["user_id"],
                    course_id=course["course_id"],
                )

                if was_unenrolled:
                    st.success(f"You have been unenrolled from {course['course_id']}.")
                    st.rerun()
                else:
                    st.warning("Unable to unenroll from this course.")


def render_dashboard() -> None:
    """Page 1: Dashboard view."""
    student = st.session_state.student

    st.title(f"Welcome, {student['name']}!")
    st.markdown("Use this student portal to view your classes or enroll with a course key.")

    render_enrollment_key_form(student)
    render_course_cards(student)


# -----------------------------
# Class page
# -----------------------------

def render_class_page() -> None:
    """Page 2: Selected class detail view."""
    student = st.session_state.student
    selected_class_id = st.session_state.selected_class_id

    enrolled_courses = get_student_enrollments(student["user_id"])
    selected_course = next(
        (course for course in enrolled_courses if course["course_id"] == selected_class_id),
        None,
    )

    if st.button("Back"):
        go_to_dashboard()

    if not selected_course:
        st.warning("Class not found or you are no longer enrolled in this class.")
        return

    st.subheader(selected_course["course_name"])
    st.markdown(f"**Course ID:** {selected_course['course_id']}")
    st.markdown(f"**Instructor:** {selected_course['instructor']}")
    st.markdown(f"**Enrollment Status:** {selected_course['status']}")
    st.markdown(f"**Enrolled At:** {selected_course['enrolled_at']}")

    st.markdown("---")
    st.markdown(
        "This class page is a student-facing course detail view. "
        "Future class content, announcements, assignments, or course resources could be added here."
    )


# -----------------------------
# Main app router
# -----------------------------

def main() -> None:
    st.set_page_config(
        page_title="Student Enrollment Portal",
        page_icon="🎓",
        layout="wide",
    )

    initialize_database()
    initialize_session_state()

    if st.session_state.role != "student":
        st.warning("This portal is only available for student users.")
        return

    if st.session_state.current_page == PAGE_CLASS:
        render_class_page()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
