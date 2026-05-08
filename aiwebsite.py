import streamlit as st
import pandas as pd

import enrollment_starter as es
from enrollment_starter import CURRENT_STUDENT


class EnrollmentDatabase:
    """Wrapper around enrollment_starter functions for database operations."""
    
    def setup(self):
        es.create_tables()
        es.seed_sample_data()
    
    def get_student_enrollments(self, user_id: str):
        return es.get_student_enrollments(user_id)


class EnrollmentService:
    """Service layer for enrollment operations."""
    
    def __init__(self, database: EnrollmentDatabase):
        self.database = database
    
    def enroll_with_key(self, user_id: str, email: str, enrollment_key: str):
        return es.enroll_with_key(user_id, enrollment_key)
    
    def soft_unenroll_student(self, user_id: str, course_id: str) -> bool:
        return es.soft_unenroll_student(user_id, course_id)
    
    def get_student_summary(self, user_id: str):
        return es.get_student_summary(user_id)


st.set_page_config(
    page_title="Student Enrollment Manager",
    page_icon="🎓",
    layout="wide",
)


database = EnrollmentDatabase()
database.setup()
service = EnrollmentService(database)


def rerun_app():
    """Rerun helper for different Streamlit versions."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


def initialize_session_state():
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"

    if "student" not in st.session_state:
        st.session_state.student = CURRENT_STUDENT

    if "role" not in st.session_state:
        st.session_state.role = "student"

    if "selected_class" not in st.session_state:
        st.session_state.selected_class = None

    if "feedback_message" not in st.session_state:
        st.session_state.feedback_message = None

    if "feedback_type" not in st.session_state:
        st.session_state.feedback_type = None


def show_feedback_message():
    if st.session_state.feedback_message:
        if st.session_state.feedback_type == "success":
            st.success(st.session_state.feedback_message)
        elif st.session_state.feedback_type == "error":
            st.error(st.session_state.feedback_message)
        elif st.session_state.feedback_type == "warning":
            st.warning(st.session_state.feedback_message)

        st.session_state.feedback_message = None
        st.session_state.feedback_type = None


def set_feedback(message: str, message_type: str):
    st.session_state.feedback_message = message
    st.session_state.feedback_type = message_type


def go_to_dashboard():
    st.session_state.page = "dashboard"
    st.session_state.selected_class = None
    rerun_app()


def go_to_class(course_record: dict):
    st.session_state.selected_class = course_record
    st.session_state.page = "class_detail"
    rerun_app()


def dashboard_page():
    student = st.session_state.student
    user_id = student["user_id"]

    st.title("Student Enrollment Dashboard")
    st.caption("View your enrolled classes, enter an enrollment key, or open a class page.")

    show_feedback_message()

    st.divider()

    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.subheader("Current Student")
        st.write(f"**Name:** {student['name']}")
        st.write(f"**Email:** {student['email']}")
        st.write(f"**Role:** {st.session_state.role}")

    with right_col:
        summary = service.get_student_summary(user_id)

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Total Records", summary["total_records"])
        with metric_col2:
            st.metric("Enrolled", summary["enrolled"])
        with metric_col3:
            st.metric("Unenrolled", summary["unenrolled"])

    st.divider()

    st.subheader("Enroll With a Course Key")

    with st.form("enrollment_form"):
        enrollment_key = st.text_input(
            "Enter enrollment key",
            placeholder="Example: DATA210-SPRING",
        )
        submitted = st.form_submit_button("Enroll / Re-enroll")

    if submitted:
        result = service.enroll_with_key(
            user_id=student["user_id"],
            email=student["email"],
            enrollment_key=enrollment_key,
        )

        if result:
            set_feedback(
                f"You are now enrolled in {result['course_id']} - {result['course_name']}.",
                "success",
            )
        else:
            set_feedback("Invalid enrollment key. Please try again.", "error")

        rerun_app()

    st.divider()

    st.subheader("My Enrolled Classes")

    enrolled_classes = database.get_student_enrollments(user_id)

    if not enrolled_classes:
        st.warning("You are not currently enrolled in any classes.")
        return

    df = pd.DataFrame(enrolled_classes)
    st.dataframe(
        df[
            [
                "course_id",
                "course_name",
                "instructor",
                "status",
                "enrolled_at",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.caption("Select a class below to open it or soft-unenroll.")

    class_options = {
        f"{course['course_id']} - {course['course_name']}": course
        for course in enrolled_classes
    }

    selected_label = st.selectbox(
        "Choose a class",
        options=list(class_options.keys()),
    )

    selected_course = class_options[selected_label]

    action_col1, action_col2 = st.columns(2)

    with action_col1:
        if st.button("Go to Class"):
            go_to_class(selected_course)

    with action_col2:
        if st.button("Unenroll"):
            success = service.soft_unenroll_student(
                user_id=student["user_id"],
                course_id=selected_course["course_id"],
            )

            if success:
                set_feedback(
                    f"You have been unenrolled from {selected_course['course_id']}.",
                    "success",
                )
            else:
                set_feedback("Could not unenroll from this class.", "error")

            rerun_app()


def class_detail_page():
    student = st.session_state.student
    selected_class = st.session_state.selected_class

    if not selected_class:
        set_feedback("Please select a class first.", "warning")
        go_to_dashboard()

    st.title("Selected Class Page")
    st.caption("Basic information about the selected class.")

    show_feedback_message()

    st.divider()

    with st.container():
        st.subheader(selected_class["course_name"])
        st.write(f"**Course ID:** {selected_class['course_id']}")
        st.write(f"**Instructor:** {selected_class['instructor']}")
        st.write(f"**Status:** {selected_class['status']}")
        st.write(f"**Enrolled At:** {selected_class['enrolled_at']}")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Back to Dashboard"):
            go_to_dashboard()

    with col2:
        if st.button("Unenroll From This Class"):
            success = service.soft_unenroll_student(
                user_id=student["user_id"],
                course_id=selected_class["course_id"],
            )

            if success:
                set_feedback(
                    f"You have been unenrolled from {selected_class['course_id']}.",
                    "success",
                )
            else:
                set_feedback("Could not unenroll from this class.", "error")

            go_to_dashboard()


def main():
    initialize_session_state()

    if st.session_state.role != "student":
        st.error("Only students can use this app.")
        return

    if st.session_state.page == "dashboard":
        dashboard_page()
    elif st.session_state.page == "class_detail":
        class_detail_page()
    else:
        st.session_state.page = "dashboard"
        rerun_app()


if __name__ == "__main__":
    main()