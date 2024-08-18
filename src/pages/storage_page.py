import streamlit as st
import pandas as pd
from src.database.google_drive_db import get_files_from_drive, download_file

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
    if st.button("⬇️ Download Selected File"):
        selected_files = df[df.select_dtypes(['bool']).any(axis=1)]
        if not selected_files.empty:
            file_id = selected_files.iloc[0]['id']
            file_content = download_file(file_id)
            st.download_button(
                label="Download File",
                data=file_content,
                file_name=selected_files.iloc[0]['name'],
                mime="application/octet-stream"
            )
        else:
            st.warning("Please select a file to download.")

if __name__ == "__main__":
    render()