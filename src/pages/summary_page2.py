import streamlit as st
from src.utils.xml_parser import display_summary_json

def priority_color(priority):
    if priority == "high":
        return "#FEE2E2"  # light red
    elif priority == "medium":
        return "#FEF3C7"  # light yellow
    else:
        return "#D1FAE5"  # light green

def render():
    st.set_page_config(page_title="Contract Summary")

    # Custom CSS to adjust spacing
    st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
    }
    h1 {
        margin-bottom: 1rem;
    }
    h3 {
        margin-bottom: 0.5rem;
    }
    .section-spacing {
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.session_state.summary_result:
        display_summary_json(st.session_state.summary_result)

        # OCR details
        with st.expander("OCR Details"):
            if "confidence" in st.session_state.ocr_result:
                st.subheader("OCR Confidence Score:")
                st.progress(st.session_state.ocr_result["confidence"])
                st.text(f"Confidence: {st.session_state.ocr_result['confidence']:.2%}")

            if "numBilledPages" in st.session_state.ocr_result:
                st.subheader("Pages Processed:")
                st.text(f"Number of pages: {st.session_state.ocr_result['numBilledPages']}")

            if "modelVersion" in st.session_state.ocr_result:
                st.subheader("OCR Model Version:")
                st.text(st.session_state.ocr_result["modelVersion"])

        with st.expander("Recognized Text"):
            st.text(st.session_state.ocr_result["text"])

    else:
        st.error("Failed to generate summary.")

    # Create three columns for buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    # Place "Back to Upload" button in the first column
    with col1:
        if st.button("Back to Upload"):
            st.session_state.page = 'upload'
            st.session_state.ocr_result = None
            st.session_state.summary_result = None
            st.rerun()
    
    # Leave the middle column empty for spacing
    with col2:
        pass
    with col3:
        pass
    
    # Place "Save" button in the third column with custom styling
    with col4:
        save_button = st.button("Save", key="save_button")
        st.markdown(
            """
            <style>
                div[data-testid="stHorizontalBlock"] > div:nth-child(4) button {
                    width: 100%;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                }
            </style>
            """,
            unsafe_allow_html=True
        )
        if save_button:
            # ฟังก์ชันการบันทึกจะถูกเพิ่มในอนาคต
            st.info("Save functionality will be implemented in the future.")