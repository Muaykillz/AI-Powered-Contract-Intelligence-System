# AI-Powered Contract Management Application

This project is part of the exciting [Global AI Week AI Hackathon event](https://www.upstage.ai/global-ai-week-ai-hackathon), where innovative AI solutions are developed to address real-world challenges. Our team is proud to participate in this global competition, showcasing our skills and creativity in the field of artificial intelligence.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/Muaykillz/AI-Powered-Contract-Intelligence-System.git
    cd AI-Powered-Contract-Intelligence-System
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Run the Streamlit application:
    ```sh
    streamlit run main.py
    ```

2. Open your web browser and go to `http://localhost:8501` to view the application.
3. To test the summary functionality and see the system's effectiveness, we recommend using the file `Fuse Medical Inc Distributor Agreement Mar 21 2019 (1).pdf` as a sample contract.

## File Structure

- `main.py`: The main entry point of the application.
- `src/pages/upload_page.py`: Contains the code for the upload page.
- `src/pages/summary_page.py`: Contains the code for the summary page.
- `src/pages/chat_page.py`: Contains the code for the chat interface.
- `src/pages/home_page.py`: Contains the code for the home page.
- `src/utils/config.py`: Contains utility functions, including loading environment variables.
- `src/database/sqlite_db.py`: Handles SQLite database operations.
- `src/services/chat.py`: Contains the Solar class for chat functionality. (But it's not complete yet.)

## Configuration

- Ensure that your environment variables are set up correctly. You can load them using the `load_environment_variables` function from `src/utils/config.py`.
- Create a `.env` file in the root directory of the project.
- Add the following environment variables to the `.env` file:
  ```
  UPSTAGE_API_KEY=your_upstage_api_key
  DRIVE_FOLDER_ID=your_google_drive_folder_id
  ```

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

## Tech-stacks

Here are the tech stacks used in this project:

- ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=Python&logoColor=white) 
- **Upstage**
- ![OpenAI](https://img.shields.io/badge/-OpenAI-412991?style=flat-square&logo=OpenAI&logoColor=white)
- ![Streamlit](https://img.shields.io/badge/-Streamlit-FF4B4B?style=flat-square&logo=Streamlit&logoColor=white)
- **Chroma**
- ![SQLite](https://img.shields.io/badge/-SQLite-003B57?style=flat-square&logo=SQLite&logoColor=white)
- ![GitHub](https://img.shields.io/badge/-GitHub-181717?style=flat-square&logo=GitHub&logoColor=white)
- ![Google Drive](https://img.shields.io/badge/-Google%20Drive-4285F4?style=flat-square&logo=Google%20Drive&logoColor=white)



## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
