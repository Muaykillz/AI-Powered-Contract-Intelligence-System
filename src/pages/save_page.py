import streamlit as st
import json
from src.database.google_drive_db import save_to_google_drive
from src.database.sqlite_db import save_events
from src.utils.json_parser import extract_events_from_summary
from src.database.vector_db import vector_db
import time

def render():
    st.title("💾 Save the contract")

    # get the uploaded file and OCR result from session state
    uploaded_file = st.session_state.uploaded_file
    ocr_result = st.session_state.get('ocr_result', '')


    if uploaded_file is not None and ocr_result:
        summary_result = json.loads(st.session_state.summary_result)
        
        st.markdown(f"""
        <div style="border: 1px solid #E5E7EB; border-radius: 0.375rem; padding: 1rem; margin-bottom: 2rem;">
        <h3 style="margin-top: 0;">📋 {summary_result["title"]} {"Contract" if "contract" not in summary_result["title"].lower() else ""}</h3>
        <p style="margin-bottom: 0.5rem;"><strong>File Name:</strong> {uploaded_file.name}</p>
        <p style="margin-bottom: 0.5rem;"><strong>File Type:</strong> {uploaded_file.type}</p>
        <p style="margin-bottom: 0;"><strong>File Size:</strong> {uploaded_file.size / 1024:.2f} KB</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        with col1:
            if st.button("Back to Summary"):
                st.session_state.page = 'summary'
                st.rerun()
        
        with col4:
            saveBtn = st.button("💾 Save the contract")
            st.markdown(
                """
                <style>
                    div[data-testid="stHorizontalBlock"] > div:nth-child(4) button {
                        width: 100%;
                        background-color: #000000;
                        color: white;
                        border: none;
                    }
                </style>
                """,
                unsafe_allow_html=True
            )

            # When save button is clicked
            if saveBtn:
                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    # Step 1: Save to Google Drive
                    status_text.text("Saving to Google Drive...")
                    file_id = save_to_google_drive(uploaded_file)
                    progress_bar.progress(20)

                    # Step 2: Extract events from summary
                    status_text.text("Extracting events from summary...")
                    events = extract_events_from_summary(summary_result)
                    progress_bar.progress(40)

                    # Step 3: Save events to Global Calendar
                    status_text.text("Saving events to Global Calendar...")
                    save_events(events, file_id)
                    progress_bar.progress(60)

                    # Step 4: Save to Chroma Vector DB
                    status_text.text("Saving to Chroma Vector DB...")
                    vector_db_id = vector_db.save_to_vector_db(summary_result, ocr_result, uploaded_file.name)
                    progress_bar.progress(80)

                    # Step 5: Reset session state
                    status_text.text("Resetting session state...")
                    st.session_state.page = 'upload'
                    st.session_state.ocr_result = None
                    st.session_state.summary_result = None
                    st.session_state.uploaded_file = None
                    progress_bar.progress(100)

                    status_text.text("Process completed successfully!")
                    st.success(f"Contract and events saved successfully. File ID: {file_id}, Vector DB ID: {vector_db_id}")

                except Exception as e:
                    progress_bar.progress(100)
                    status_text.text(f"Error occurred: {str(e)}")
                    st.error(f"An error occurred while saving: {str(e)}")

                finally:
                    time.sleep(2)  # ให้ผู้ใช้เห็นสถานะสุดท้ายสักครู่
                    status_text.empty()
                    progress_bar.empty()
                    st.rerun()
    else:
        st.info("Please upload a PDF file to proceed.")

if __name__ == "__main__":
    render()