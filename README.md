# JorGPT DeepSeek (English Version)

JorGPT DeepSeek is a desktop application for automatic grading and feedback of C programming exam answers using the DeepSeek LLM API. It is designed for university professors or teaching assistants who want to quickly evaluate student code submissions in bulk, using a customizable rubric and AI-powered analysis.

## Features
- **Bulk CSV Grading:** Load a CSV file with student answers and process all submissions automatically.
- **Customizable Rubric:** The grading rubric and exam statement are editable within the app.
- **AI-Powered Feedback:** Uses DeepSeek's LLM to evaluate code and provide concise, category-based feedback and scores.
- **Modern GUI:** Built with PyQt5 for a user-friendly experience.
- **Export Results:** Saves results to an Excel file in the `PUBLICATION` folder.

## Requirements
- Python 3.8+
- [PyQt5](https://pypi.org/project/PyQt5/)
- [pandas](https://pypi.org/project/pandas/)
- [openai](https://pypi.org/project/openai/) (for DeepSeek API)
- A DeepSeek API key (set as the environment variable `DEEPSEEK_API_KEY`)

## Installation
1. Clone or download this repository.
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
   Or manually:
   ```sh
   pip install PyQt5 pandas openai
   ```
3. Set your DeepSeek API key as an environment variable:
   - On Windows (PowerShell):
     ```sh
     $env:DEEPSEEK_API_KEY="your_deepseek_api_key"
     ```
   - On Linux/macOS:
     ```sh
     export DEEPSEEK_API_KEY="your_deepseek_api_key"
     ```

## Usage
1. Run the application:
   ```sh
   python jorgpt_deepseek_v1.2.py
   ```
2. In the GUI:
   - Click **Open CSV** and select your CSV file with student answers.
   - The rubric and exam statement will appear on the right; you can edit them as needed.
   - Click **Send** to start grading. Progress and results will be shown in the left panel.
   - When finished, results are saved as an Excel file in the `PUBLICATION` folder.

### CSV Format
- The CSV should have at least three columns: (e.g., Student Name, Exam Statement, Student Code)
- The program expects the exam statement in column 2 and the code in column 3 (zero-based index).

## Customization
- You can edit the grading rubric and exam statement directly in the app before grading.
- The model used is currently fixed to `deepseek-chat`.

## License
This project is for educational and research purposes. See LICENSE for details.

## Acknowledgments
- Powered by [DeepSeek](https://deepseek.com/) LLM API.
- GUI built with PyQt5.

---
For questions or suggestions, please open an issue or contact the author.
