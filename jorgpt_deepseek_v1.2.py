import sys
import csv
from openai import OpenAI
import pandas as pd
import os

from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, QTextEdit,
                             QRadioButton, QVBoxLayout, QWidget, QGroupBox, QTableWidget, QTableWidgetItem, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import datetime
import os


# Load API key from environment variable for security
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("Please set the DEEPSEEK_API_KEY environment variable.")

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


class APICallThread(QThread):
    progress_signal = pyqtSignal(int, str)

    def __init__(self, selected_model, df, prompt_part1, prompt_part2, prompt_part3):
        super().__init__()
        self.selected_model = selected_model
        self.df = df
        self.prompt_part1 = prompt_part1
        self.prompt_part2 = prompt_part2
        self.prompt_part3 = prompt_part3
    def run(self):
        timestamp_day = datetime.datetime.now().strftime("%Y%m%d_")
        start = datetime.datetime.now()
        timestamp1 = start.strftime("%H%M%S")

        for index, row in self.df.iterrows():
            answer_question1 = self.send_to_chatgpt(row.iloc[2])
            if answer_question1:
                grade, suggestions = grade_response(answer_question1)
                self.df.at[index, 'Question1 Score'] = grade / 5
                self.df.at[index, 'Question1 Answer'] = suggestions
                self.progress_signal.emit(index, f"Answer obtained for index {index}")
            else:
                self.progress_signal.emit(index, "Error obtaining response from the API.")

        end = datetime.datetime.now()
        duration = end - start
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_str = f"{int(hours):02d}_{int(minutes):02d}_{int(seconds):02d}"

        os.makedirs("PUBLICATION", exist_ok=True)
        timestamp = end.strftime("%H%M%S")
        filename = os.path.join("PUBLICATION", f"DEEPSEEK_results_{timestamp_day}_{timestamp1}_{timestamp}_duration_{duration_str}.xlsx")
        self.df.to_excel(filename, index=False)
        self.progress_signal.emit(-1, f"Process completed. File saved at {filename}")


    def send_to_chatgpt(self, code):
        myPrompt = self.prompt_part1 + self.prompt_part2 + self.prompt_part3
        try:
            print(f"Using model: {self.selected_model}")  # Debug
            response = client.chat.completions.create(
                        model=self.selected_model,
                        messages=[
                            {"role": "system", "content": myPrompt},
                            {"role": "user", "content": code}
                        ],
                        temperature=0,
                        stream=False
                    )
            content = response.choices[0].message.content.strip()
            print(f"DEEPSEEK response: {content}")  # Debug
            # Normalize the response so the rest of the code works the same
            class FakeResponse:
                def __init__(self, content):
                    self.choices = [type('obj', (object,), {"message": type('msg', (object,), {"content": content})})]

            return FakeResponse(content)

        except Exception as e:
            print(f"Error sending request to DEEPSEEK: {e}")
            return None


def grade_response(response):
    suggestions =  response.choices[0].message.content
    response_parts =  response.choices[0].message.content.strip().split('\n')
    # Initial grade
    total_sum = 0
    # Check each part of the response and sum the points
    for line in response_parts:
        if any(field + ":" in line for field in allowed_fields):
            # Split by colon
            parts = line.split(':')
            # Extract the numeric value if possible
            if len(parts) == 2:
                value = parts[1].strip()
                # Check if the value is a fraction (e.g., "8/10")
                if '/' in value:
                    # Take only the numerator of the fraction
                    numerator = value.split('/')[0].strip()
                    if numerator.isdigit():
                        total_sum += int(numerator)
                # If not a fraction, proceed normally
                elif value.isdigit():
                    total_sum += int(value)
    return total_sum, suggestions


allowed_fields = ["Logic", "Style", "Efficiency", "Readability", "Requirement compliance",
                 "Logic ", "Style ", "Efficiency ", "Readability ", "Requirement compliance ",
                 "Readability and style", "Comments", "Readability and style ", "Comments "]

class MainWindow(QMainWindow):
    csv_file_name = ""
    df = ""

    prompt_part1 = """ You are the programming course professor at a University.
    You have to evaluate the programming code written by a student, which I will show you at the end.
    Very important: the student already knows how to work with functions and pointers. They do not yet know how to work with recursion.
    The code attempts to solve the following problem that the student must write in C language:
    <exam_statement>"""
    prompt_part2 = ""
    prompt_part3 = """ 
    </exam_statement>
    If the student has not submitted anything, you do not need to respond.
    If they have submitted something, do the following:
    In your evaluation, pay attention to the initialization of variables, because we require them to give an initial value even if it will be overwritten later, for example with a scanf.
    Provide a numerical grade for each of the following categories from 0 to 10 (pay special attention to this point, the format must be ?/10) (it is fine if it is 0 if the student deserves it):
    1. Logic : Evaluate if the logic of the code effectively solves the presented problem. Important: in this category, do not consider syntax errors, they should not subtract points.
    2. Comments : Pay special attention to this category 'Comments'. If there are no comments in the code, the grade for this category must be 0/10. Evaluate the other categories as you normally would. Comments must be explanatory, and note that they may appear at the end of the code line with double slashes //, or on the line above the code, also with double slashes //.
    3. Efficiency : Evaluate if the code uses resources effectively, avoiding redundancies.
    4. Readability and style: Ease of understanding the code, including clarity and structure. Since they do the exam in a notepad, do not consider the lack of indentation.
    5. Requirement compliance : Determine if the code does what the problem asks (without errors)
    Very important: sum all the grades of each section you have scored and give the student a grade that is 'TOTAL: ?/50'
    In your answers, address the student directly as 'you'. Keep your answers short and concise. Pay special attention not to say 'Hello student!' or similar at the beginning of the answer, go directly to the evaluation. You must speak as a close professor.
    Please, do not use bold, it is not necessary.
    I want the answer to be as compact as possible. It should only show the grade for the 5 categories and the total grade.
    """

    selected_model = ""

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('JorGPT')
        self.setGeometry(100, 100, 1420, 920)
        self.setStyleSheet("background-color: #202123;color:white;") 

        self.splitterPrincipal = QSplitter(Qt.Horizontal)
        self.textoMultilinea = QTextEdit()

        self.panelIzquierdo = QWidget()
        self.layoutPanelIzquierdo = QVBoxLayout(self.panelIzquierdo)

        self.botonAbrirCSV = QPushButton('Open CSV')
        self.botonAbrirCSV.setStyleSheet("""QPushButton {color: white;background-color: #28a745;border-style: outset;
                                            border-radius: 12px;border-color: beige;font: bold 14px;min-width: 10em;min-height: 25px;padding: 6px;}""")
        self.botonAbrirCSV.clicked.connect(self.open_dialog)

        self.grupoModelos = self.createModelGroup()

        self.botonEnviar = QPushButton('Send')
        self.botonEnviar.clicked.connect(self.start_processing)
        self.botonEnviar.setStyleSheet("""QPushButton {color: white;background-color: #007bff;border-style: outset;border-radius: 12px;
                                            border-color: beige;font: bold 14px;min-width: 10em;min-height: 25px;padding: 6px;}""")

        self.layoutPanelIzquierdo.addWidget(self.botonAbrirCSV)
        self.layoutPanelIzquierdo.addWidget(self.grupoModelos)
        self.layoutPanelIzquierdo.addWidget(self.botonEnviar)
        self.layoutPanelIzquierdo.addWidget(self.textoMultilinea)
        self.layoutPanelIzquierdo.addStretch(1)
        self.panelIzquierdo.setLayout(self.layoutPanelIzquierdo)

        self.panelDerecho = QWidget()
        self.layoutPanelDerecho = QVBoxLayout(self.panelDerecho)
        self.textoMultilineaRubrica = QTextEdit()
        self.textoMultilineaRubrica.setText(self.prompt_part1 + self.prompt_part2 + self.prompt_part3)
        
        self.textoMultilineaProblema = QTextEdit()
        self.tablaCSV = QTableWidget()

        self.layoutPanelDerecho.addWidget(self.textoMultilineaRubrica)
        self.layoutPanelDerecho.addWidget(self.textoMultilineaProblema)
        self.layoutPanelDerecho.addWidget(self.tablaCSV)
        self.splitterPrincipal.addWidget(self.panelIzquierdo)
        self.splitterPrincipal.addWidget(self.panelDerecho)
        self.splitterPrincipal.setSizes([200, 724])
        self.setCentralWidget(self.splitterPrincipal)

    def open_dialog(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, "Select CSV file", "",
                                                 "CSV Files (*.csv);;All Files (*)", options=options)
        if file:
            self.loadCSV(file)
            self.csv_file_name = file

    def loadCSV(self, file):
        with open(file, "r", newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            data = list(reader)
            self.tablaCSV.setColumnCount(len(data[0]))
            self.tablaCSV.setRowCount(len(data))
            for i, row in enumerate(data):
                for j, cell in enumerate(row):
                    self.tablaCSV.setItem(i, j, QTableWidgetItem(cell))
            self.textoMultilineaProblema.setText(self.tablaCSV.item(0,1).text())
            self.prompt_part2 = self.tablaCSV.item(0,2).text()
            self.df = pd.read_csv(file)

    def createModelGroup(self):
        group = QGroupBox("Choose a model:")
        layout = QVBoxLayout()

        self.modeloDEEPSEEK = QRadioButton("deepseek-chat") #$0.27 per 1,000,000 tokens
        
        layout.addWidget(self.modeloDEEPSEEK)
        
        self.modeloDEEPSEEK.setChecked(True)

        group.setLayout(layout)
        return group

    def start_processing(self):
        self.selected_model = (
            "deepseek-chat"
        )

        self.thread = APICallThread(self.selected_model, self.df, self.prompt_part1, self.prompt_part2, self.prompt_part3)
        self.thread.progress_signal.connect(self.update_progress)
        self.thread.start()
        self.thread.progress_signal.emit(0, "Process started - please wait.")

    def update_progress(self, index, message):
        self.textoMultilinea.append(f"Index {index}: {message}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()