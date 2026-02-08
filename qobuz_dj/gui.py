import os
import re
import sys

from PySide6.QtCore import QByteArray, QProcess
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("qobuz-dj GUI")
        self.resize(800, 600)

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Toolbar
        button_layout = QHBoxLayout()
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
            button_layout.addWidget(btn)

        main_layout.addLayout(button_layout)

        # Console
        self.console = ConsoleWidget()
        main_layout.addWidget(self.console)

    def run_command(self, cmd):
        if self.process.state() != QProcess.NotRunning:
            self.console.append_ansi("\x1b[31mProcess already running...\x1b[0m\n")
            return

        self.console.append_ansi(f"\x1b[32mRunning: qobuz-dj {cmd}\x1b[0m\n")

        # In development, use uv run. In production, use the executable.
        if getattr(sys, "frozen", False):
            program = os.path.join(os.path.dirname(sys.executable), "qobuz-dj")
            if os.name == "nt":
                program += ".exe"
        else:
            program = "uv"
            args = ["run", "qobuz-dj", cmd]

        if not getattr(sys, "frozen", False):
            self.process.start(program, args)
        else:
            self.process.start(program, [cmd])

    def read_output(self):
        data = self.process.readAllStandardOutput()
        text = str(QByteArray(data), "utf-8", errors="replace")
        self.console.append_ansi(text)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
