import streamlit as st
from streamlit_option_menu import option_menu
from src.pages import summary_page, upload_page, storage_page, calendar_page, save_page, chat_page
from src.utils.config import load_environment_variables

def main():

    # Style
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        max-width: 360px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Set sidebar
    with st.sidebar:
        select = option_menu(
            menu_title="Navigation",
            options=["Contract Summarizer", "Calendar", "Contract Storage", "Chatbot"],
            default_index=0,
            icons=["file-earmark-pdf", "calendar3", "folder", "robot"],
            menu_icon="-"
        )


    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = 'upload'

    if select == "Contract Summarizer" and st.session_state.page != 'summary' and st.session_state.page != 'save':
        st.session_state.page = 'upload'
    if select == "Contract Storage":
        st.session_state.page = 'storage'
    if select == "Calendar":
        st.session_state.page = 'calendar'
    if select == "Chatbot":
        st.session_state.page = 'chat'

    # Load environment variables
    load_environment_variables()

    # Render appropriate page
    if st.session_state.page == 'upload':
        upload_page.render()
    elif st.session_state.page == 'summary':
        summary_page.render()
    elif st.session_state.page == 'storage':
        storage_page.render()
    elif st.session_state.page == 'calendar':
        calendar_page.render()
    elif st.session_state.page == 'save':
        save_page.render()
    elif st.session_state.page == 'chat':
        chat_page.render()
    else:
        st.error("Invalid page selection.")


if __name__ == "__main__":
    main()