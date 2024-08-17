import streamlit as st
from src.pages import upload_page, summary_page
from src.utils.config import load_environment_variables

def main():
    st.title("Contract OCR and Summarization with Upstage")

    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = 'upload'

    # Load environment variables
    load_environment_variables()

    # Render appropriate page
    if st.session_state.page == 'upload':
        upload_page.render()
    elif st.session_state.page == 'summary':
        summary_page.render()

if __name__ == "__main__":
    main()