import os

def save_pdf(uploaded_file, filename):
    save_path = os.path.join('data', 'contracts', filename)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return save_path

def get_pdf_path(filename):
    return os.path.join('data', 'contracts', filename)