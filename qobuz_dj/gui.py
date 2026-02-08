import os
import re
import sys

from PySide6.QtCore import QByteArray, QProcess, Qt
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)


class ConsoleWidget(QPlainTextEdit):
    """
    A custom QPlainTextEdit that acts as a terminal console.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setBackgroundVisible(False)
        self.setStyleSheet("background-color: black; color: white;")
        self.setFont(QFont("Courier New", 10))

        # ANSI color regex
        self.ansi_regex = re.compile(r"\x1b\[([0-9;]*)m")

        self.color_map = {
            "30": QColor("black"),
            "31": QColor("red"),
            "32": QColor("green"),
            "33": QColor("yellow"),
            "34": QColor("blue"),
            "35": QColor("magenta"),
            "36": QColor("cyan"),
            "37": QColor("white"),
            "90": QColor("gray"),
            "91": QColor("lightred"),
            "92": QColor("lightgreen"),
            "93": QColor("lightyellow"),
            "94": QColor("lightblue"),
            "95": QColor("lightmagenta"),
            "96": QColor("lightcyan"),
            "97": QColor("white"),
        }

    def append_ansi(self, text):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)

        parts = self.ansi_regex.split(text)
        current_format = QTextCharFormat()

        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Regular text
                if part:
                    cursor.insertText(part, current_format)
            else:
                # ANSI code
                codes = part.split(";")
                for code in codes:
                    if code == "0" or not code:
                        current_format = QTextCharFormat()
                    elif code in self.color_map:
                        current_format.setForeground(self.color_map[code])
                    elif code == "1":
                        current_format.setFontWeight(QFont.Bold)

        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def keyPressEvent(self, event):
        # Forward key events to the MainWindow's QProcess
        main_win = self.window()
        if hasattr(main_win, "send_input"):
            # Catch Ctrl+C
            if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
                main_win.break_process()
                return

            key = event.text()
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                key = "\n"

            if key:
                main_win.send_input(key)
        # We don't call super().keyPressEvent(event) to keep it read-only


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("qobuz-dj GUI")
        self.resize(1000, 750)

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.process_finished)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Toolbar Row
        toolbar_layout = QHBoxLayout()

        # Mode Buttons
        modes = [
            ("DJ Mode", "dj"),
            ("Download", "dl"),
            ("Sanitize", "sz"),
            ("Lucky", "lucky"),
            ("Interactive", "fun"),
        ]

        for name, cmd in modes:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, c=cmd: self.run_command(c))
            toolbar_layout.addWidget(btn)

        toolbar_layout.addStretch()

        # Config Button (⚙️)
        self.config_btn = QPushButton()
        self.config_btn.setIcon(
            self.style().standardIcon(QStyle.SP_TitleBarMenuButton)
        )  # Closest to gear in SP
        self.config_btn.setToolTip("Configure (Regenerate config.ini)")
        self.config_btn.setFixedWidth(40)
        self.config_btn.clicked.connect(lambda: self.run_command("-r"))
        toolbar_layout.addWidget(self.config_btn)

        main_layout.addLayout(toolbar_layout)

        # Input Row
        input_layout = QHBoxLayout()

        # Top N Tracks
        input_layout.addWidget(QLabel("Top N:"))
        self.top_n_input = QLineEdit()
        self.top_n_input.setPlaceholderText("All")
        self.top_n_input.setFixedWidth(50)
        input_layout.addWidget(self.top_n_input)

        # Source/Args
        input_layout.addWidget(QLabel("Source / Arguments:"))
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Enter URL, keywords, or folder path...")
        input_layout.addWidget(self.source_input)

        # Browse Folder (📁)
        self.browse_btn = QPushButton()
        self.browse_btn.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        self.browse_btn.setToolTip("Browse Folder")
        self.browse_btn.setFixedWidth(40)
        self.browse_btn.clicked.connect(self.browse_folder)
        input_layout.addWidget(self.browse_btn)

        main_layout.addLayout(input_layout)

        # Console
        self.console = ConsoleWidget()
        main_layout.addWidget(self.console)

        # Bottom Controls
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        self.break_btn = QPushButton("🛑 Break Process")
        self.break_btn.clicked.connect(self.break_process)
        self.break_btn.setEnabled(False)
        self.break_btn.setStyleSheet("color: red; font-weight: bold;")
        bottom_layout.addWidget(self.break_btn)

        main_layout.addLayout(bottom_layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            self.source_input.setText(folder)

    def run_command(self, cmd):
        if self.process.state() != QProcess.NotRunning:
            self.console.append_ansi("\x1b[31mProcess already running...\x1b[0m\n")
            return

        cli_args = []

        # Handle special config shortcut
        if cmd == "-r":
            cli_args = ["-r"]
        else:
            cli_args.append(cmd)

            # Handle Top N
            top_n = self.top_n_input.text().strip()
            if top_n:
                cli_args.extend(["-t", top_n])

            # Handle Source/Args
            args_text = self.source_input.text().strip()
            if args_text:
                if cmd == "sz":
                    cli_args.append(args_text)
                else:
                    cli_args.extend(args_text.split())

        self.console.append_ansi(
            f"\x1b[32mRunning: qobuz-dj {' '.join(cli_args)}\x1b[0m\n"
        )

        if getattr(sys, "frozen", False):
            program = os.path.join(os.path.dirname(sys.executable), "qobuz-dj")
            if os.name == "nt":
                program += ".exe"
            if not os.path.exists(program):
                program = "qobuz-dj"
        else:
            program = "uv"
            cli_args = ["run", "qobuz-dj"] + cli_args

        self.break_btn.setEnabled(True)
        self.process.start(program, cli_args)

    def break_process(self):
        if self.process.state() == QProcess.Running:
            self.console.append_ansi("\x1b[31m\n[🛑 BREAKING PROCESS...]\x1b[0m\n")
            self.process.terminate()
            # If it doesn't close in 2 seconds, kill it
            if not self.process.waitForFinished(2000):
                self.process.kill()

    def process_finished(self, exit_code, exit_status):
        self.break_btn.setEnabled(False)
        self.console.append_ansi(
            f"\x1b[33m\n[Process finished with code {exit_code}]\x1b[0m\n"
        )

    def read_output(self):
        data = self.process.readAllStandardOutput()
        text = str(QByteArray(data), "utf-8", errors="replace")
        self.console.append_ansi(text)

    def send_input(self, text):
        if self.process.state() == QProcess.Running:
            self.process.write(text.encode("utf-8"))


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
