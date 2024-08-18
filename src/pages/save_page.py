import streamlit as st
import json
from src.database.google_drive_db import save_to_google_drive
from src.database.sqlite_db import save_events
from src.utils.json_parser import extract_events_from_summary
from src.database.vector_db import vector_db

def render():
    st.title("📄 Upload and Save PDF to Google Drive")

    uploaded_file = st.session_state.uploaded_file
    ocr_result = st.session_state.get('ocr_result', '')

    if uploaded_file is not None and ocr_result:
        summary_result = json.loads(st.session_state.summary_result)
        
        st.markdown(f"""
        <div style="border: 1px solid #E5E7EB; border-radius: 0.375rem; padding: 1rem; margin-bottom: 2rem;">
        <h3 style="margin-top: 0;">📋 {summary_result["title"]} {"Contact" if "contact" not in summary_result["title"].lower() else ""}</h3>
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

            if saveBtn:
                with st.spinner("Saving contract and events..."):
                    file_id = save_to_google_drive(uploaded_file)
                    events = extract_events_from_summary(summary_result)
                    save_events(events, file_id)
                    
                    # Save to Chroma Vector DB
                    vector_db_id = vector_db.save_to_vector_db(summary_result, ocr_result)
                    
                    st.success(f"Contract and events saved successfully. File ID: {file_id}, Vector DB ID: {vector_db_id}")
                    st.session_state.page = 'upload'
                    st.session_state.ocr_result = None
                    st.session_state.summary_result = None
                    st.session_state.uploaded_file = None
                    st.rerun()
    else:
        st.info("Please upload a PDF file to proceed.")

if __name__ == "__main__":
    render()