import streamlit as st
from src.services.ocr import OCR
from src.services.chat import Solar

def render():
    # Set page title
    st.title("Contract Summarization with Upstage")

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if uploaded_file is not None:
        if st.button("✨ Process and Summarize Document"):

            st.session_state.uploaded_file = uploaded_file

            with st.spinner("Processing..."):
                ocr_service = OCR()
                solar_service = Solar()

                # Call Upstage OCR API
                ocr_result = ocr_service.process_document(uploaded_file)
                print("=== OCR Result ===")
                print(ocr_result["text"])
                print("==================")
                
                if "text" in ocr_result:
                    # Call Solar LLM for summarization
                    summary = solar_service.summarize_text(ocr_result["text"])
                    st.session_state.ocr_result = ocr_result
                    st.session_state.summary_result = summary
                    st.session_state.page = 'summary'
                    st.rerun()
                else:
                    st.error("Failed to extract text from the document.")