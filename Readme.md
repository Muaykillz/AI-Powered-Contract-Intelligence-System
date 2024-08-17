## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/your-repo-name.git
    cd your-repo-name
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

## File Structure

- `main.py`: The main entry point of the application.
- `src/pages/upload_page.py`: Contains the code for the upload page.
- `src/pages/summary_page.py`: Contains the code for the summary page.
- `src/utils/config.py`: Contains utility functions, including loading environment variables.

## Configuration

Ensure that your environment variables are set up correctly. You can load them using the `load_environment_variables` function from `src/utils/config.py`.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.