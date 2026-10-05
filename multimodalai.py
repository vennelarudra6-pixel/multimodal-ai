import os
import tempfile

import streamlit as st

from services.database_service import (
    init_db,
    create_complaint,
    get_complaints,
    update_status
)

from services.ai_service import analyze_complaint

from services.voice_service import transcribe_audio

from services.image_service import analyze_image

from services.rag_service import (
    create_vector_database,
    retrieve_knowledge
)

from utils.helpers import save_uploaded_file


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Campus AI Assistant",
    page_icon="🎓",
    layout="wide"
)


# --------------------------------------------------
# INITIALIZATION
# --------------------------------------------------

init_db()


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "complaint_text" not in st.session_state:
    st.session_state.complaint_text = ""

if "ai_result" not in st.session_state:
    st.session_state.ai_result = None

if "image_analysis" not in st.session_state:
    st.session_state.image_analysis = ""


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title(
    "🎓 Multimodal AI-Based Campus Troubleshooting Assistant"
)

st.write(
    "Report campus problems using text, voice or images."
)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select Module",
    [
        "🏠 Student Complaint",
        "📋 Complaint Tracking",
        "👨‍💼 Admin Dashboard"
    ]
)


# ==================================================
# STUDENT COMPLAINT
# ==================================================

if page == "🏠 Student Complaint":

    st.header("📝 Submit Campus Problem")

    col1, col2 = st.columns(2)

    with col1:

        student_name = st.text_input(
            "Student Name"
        )

        student_id = st.text_input(
            "Student ID"
        )

    with col2:

        location = st.text_input(
            "Campus Location / Room"
        )

        input_type = st.selectbox(
            "Complaint Input",
            [
                "Text",
                "Voice",
                "Image"
            ]
        )


    # --------------------------------------------------
    # TEXT INPUT
    # --------------------------------------------------

    if input_type == "Text":

        complaint = st.text_area(
            "Describe your problem",
            height=150,
            placeholder=
            "Example: The fan in Room 204 is not working."
        )

        if st.button(
            "🤖 Analyze Complaint",
            type="primary"
        ):

            if not complaint:

                st.warning(
                    "Please enter a complaint."
                )

            else:

                with st.spinner(
                    "AI is analyzing your complaint..."
                ):

                    knowledge = retrieve_knowledge(
                        complaint
                    )

                    result = analyze_complaint(
                        complaint,
                        knowledge
                    )

                    st.session_state.ai_result = result
                    st.session_state.complaint_text = complaint


    # --------------------------------------------------
    # VOICE INPUT
    # --------------------------------------------------

    elif input_type == "Voice":

        audio_file = st.file_uploader(
            "Upload voice recording",
            type=[
                "wav",
                "mp3",
                "m4a",
                "ogg"
            ]
        )

        if audio_file:

            st.audio(
                audio_file
            )

            if st.button(
                "🎤 Convert Voice to Text"
            ):

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".wav"
                ) as temp_file:

                    temp_file.write(
                        audio_file.read()
                    )

                    audio_path = temp_file.name

                with st.spinner(
                    "Whisper is transcribing..."
                ):

                    text = transcribe_audio(
                        audio_path
                    )

                st.session_state.complaint_text = text

                st.success(
                    "Voice converted successfully!"
                )

                st.write(
                    "### Transcribed Complaint"
                )

                st.write(text)

                os.unlink(audio_path)


                knowledge = retrieve_knowledge(
                    text
                )

                result = analyze_complaint(
                    text,
                    knowledge
                )

                st.session_state.ai_result = result


    # --------------------------------------------------
    # IMAGE INPUT
    # --------------------------------------------------

    elif input_type == "Image":

        image_file = st.file_uploader(
            "Upload image of the campus problem",
            type=[
                "jpg",
                "jpeg",
                "png"
            ]
        )

        if image_file:

            st.image(
                image_file,
                caption="Uploaded Problem"
            )

            if st.button(
                "📷 Analyze Image"
            ):

                image_path = save_uploaded_file(
                    image_file
                )

                with st.spinner(
                    "Vision AI is analyzing the image..."
                ):

                    image_result = analyze_image(
                        image_path
                    )

                st.session_state.image_analysis = (
                    image_result
                )

                st.success(
                    "Image analysis completed."
                )

                st.write(
                    "### AI Image Analysis"
                )

                st.write(
                    image_result
                )

                # Use image analysis as complaint text
                st.session_state.complaint_text = (
                    image_result
                )

                knowledge = retrieve_knowledge(
                    image_result
                )

                result = analyze_complaint(
                    image_result,
                    knowledge
                )

                st.session_state.ai_result = result


    # --------------------------------------------------
    # DISPLAY AI RESULT
    # --------------------------------------------------

    if st.session_state.ai_result:

        result = st.session_state.ai_result

        st.divider()

        st.header("🤖 AI Analysis")

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Category",
                result.get(
                    "category",
                    "Unknown"
                )
            )

        with col2:

            st.metric(
                "Department",
                result.get(
                    "department",
                    "Unknown"
                )
            )

        with col3:

            st.metric(
                "Priority",
                result.get(
                    "priority",
                    "Medium"
                )
            )


        st.subheader("🔎 Identified Problem")

        st.write(
            result.get(
                "problem",
                ""
            )
        )


        st.subheader(
            "🛠️ Suggested Troubleshooting"
        )

        st.write(
            result.get(
                "solution",
                ""
            )
        )


        st.divider()


        # --------------------------------------------------
        # CREATE TICKET
        # --------------------------------------------------

        if result.get(
            "needs_ticket",
            True
        ):

            st.warning(
                "This problem may require campus staff intervention."
            )

            if st.button(
                "🎫 Create Complaint Ticket",
                type="primary"
            ):

                ticket_id = create_complaint(

                    student_name=student_name,

                    student_id=student_id,

                    department=result.get(
                        "department",
                        "General Maintenance"
                    ),

                    category=result.get(
                        "category",
                        "Other"
                    ),

                    location=location,

                    description=st.session_state.complaint_text,

                    priority=result.get(
                        "priority",
                        "Medium"
                    ),

                    ai_solution=result.get(
                        "solution",
                        ""
                    )
                )

                st.success(
                    f"Complaint created successfully! "
                    f"Ticket ID: CMP{ticket_id:04d}"
                )

                st.session_state.ai_result = None


# ==================================================
# COMPLAINT TRACKING
# ==================================================

elif page == "📋 Complaint Tracking":

    st.header("📋 Complaint Tracking")

    complaints = get_complaints()

    if not complaints:

        st.info(
            "No complaints have been submitted yet."
        )

    else:

        for complaint in complaints:

            (
                complaint_id,
                student_name,
                student_id,
                department,
                category,
                location,
                description,
                priority,
                status,
                created_at
            ) = complaint


            with st.expander(
                f"🎫 CMP{complaint_id:04d} | "
                f"{category} | {status}"
            ):

                st.write(
                    f"**Student:** {student_name}"
                )

                st.write(
                    f"**Student ID:** {student_id}"
                )

                st.write(
                    f"**Department:** {department}"
                )

                st.write(
                    f"**Location:** {location}"
                )

                st.write(
                    f"**Priority:** {priority}"
                )

                st.write(
                    f"**Problem:** {description}"
                )

                st.write(
                    f"**Created:** {created_at}"
                )

                st.write(
                    f"**Current Status:** {status}"
                )


# ==================================================
# ADMIN DASHBOARD
# ==================================================

elif page == "👨‍💼 Admin Dashboard":

    st.header("👨‍💼 Admin Dashboard")

    complaints = get_complaints()

    total = len(complaints)

    pending = sum(
        1 for c in complaints
        if c[8] == "Pending"
    )

    progress = sum(
        1 for c in complaints
        if c[8] == "In Progress"
    )

    resolved = sum(
        1 for c in complaints
        if c[8] == "Resolved"
    )


    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total",
        total
    )

    col2.metric(
        "Pending",
        pending
    )

    col3.metric(
        "In Progress",
        progress
    )

    col4.metric(
        "Resolved",
        resolved
    )


    st.divider()


    for complaint in complaints:

        (
            complaint_id,
            student_name,
            student_id,
            department,
            category,
            location,
            description,
            priority,
            status,
            created_at
        ) = complaint


        with st.container():

            st.subheader(
                f"CMP{complaint_id:04d}"
            )

            st.write(
                f"**Department:** {department}"
            )

            st.write(
                f"**Problem:** {description}"
            )

            st.write(
                f"**Priority:** {priority}"
            )

            new_status = st.selectbox(

                "Update Status",

                [
                    "Pending",
                    "Assigned",
                    "In Progress",
                    "Resolved"
                ],

                index=[
                    "Pending",
                    "Assigned",
                    "In Progress",
                    "Resolved"
                ].index(status),

                key=f"status_{complaint_id}"
            )


            if st.button(
                "Update",
                key=f"update_{complaint_id}"
            ):

                update_status(
                    complaint_id,
                    new_status
                )

                st.success(
                    "Status updated successfully."
                )

                st.rerun()

            st.divider()