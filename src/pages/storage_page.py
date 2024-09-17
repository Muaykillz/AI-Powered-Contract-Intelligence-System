import streamlit as st
import pandas as pd
import os
from src.database.google_drive_db import get_files_from_drive, download_file
from src.utils.config import load_environment_variables

load_environment_variables()

FOLDER_ID = os.getenv('DRIVE_FOLDER_ID')

def render():
    st.title("📁 Contract Storage")

    # Fetch files from Google Drive
    files = get_files_from_drive()

    # Search functionality
    search_term = st.text_input("🔍 Search contracts", "")

    # Sorting options
    sort_option = st.selectbox("Sort by:", ["Name", "Size", "Last Modified"])

    # Filter and sort items
    items = [file for file in files if search_term.lower() in file['name'].lower()]

    if sort_option == "Name":
        items.sort(key=lambda x: x["name"])
    elif sort_option == "Size":
        items.sort(key=lambda x: float(x["size"].split()[0]) if x["size"] != 'N/A' else 0, reverse=True)
    else:  # Last Modified
        items.sort(key=lambda x: x["modified"], reverse=True)

    # Display as a table
    df = pd.DataFrame(items)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Add download functionality
    if st.button("🔗 Go to Drive Folder"):
        drive_folder_link = f"https://drive.google.com/drive/folders/{FOLDER_ID}"
        st.markdown(f"[Click here to view the Drive folder]({drive_folder_link})")

if __name__ == "__main__":
    render()