import sys
import requests
from bs4 import BeautifulSoup
import os
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QSizePolicy, QSpacerItem, QLabel, QMainWindow, QListWidget, QLineEdit, QVBoxLayout, QWidget, QPushButton
from Downloader import Data_Melovaz, CreateNewTable
from PyQt6.QtCore import Qt, QSize
import sqlite3
import platform


class MelovazDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Melovaz Downloader")
        self.setGeometry(100, 100, 600, 400)

        self.initUI()

    def initUI(self):
        self.list_widget = QListWidget()
        self.download_button = QPushButton("Download Selected")
        self.download_button.clicked.connect(self.download_selected)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for songs...")
        self.search_input.setFixedSize(QSize(300, 30))
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_songs)

        self.setWindowIcon(QIcon('icon.png'))
        self.setStyleSheet("QMainWindow {background-color: #1a1a1a;}")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setPixmap(QPixmap('icon_base.png'))

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)
        
        layout.addWidget(self.list_widget)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.download_all_button = QPushButton("Download All")
        self.download_all_button.clicked.connect(self.download_all)
        
        layout.addWidget(self.download_button)
        layout.addWidget(self.download_all_button)

    def search_songs(self):
        search_text = self.search_input.text()
        self.list_widget.clear()
        CreateNewTable()
        Data_Melovaz(search_text)
        self.fetch_songs()

    def fetch_songs(self):
        conn = sqlite3.connect("playlist.db")
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM playlist")
        rows = cursor.fetchall()

        for row in rows:
            data_title = row[0]
            self.list_widget.addItem(data_title)

        conn.close()

    def download_selected(self):
        selected_items = self.list_widget.selectedItems()
        for item in selected_items:
            data_title = item.text()
            self.download_song(data_title)

    def download_song(self, data_title):
        conn = sqlite3.connect("playlist.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT source FROM playlist WHERE title = ?", (data_title,))
        row = cursor.fetchone()

        if row:
            data_src = row[0]
            file_name = os.path.basename(data_src)
            # Determine the user's home directory and create the download path
            if platform.system() == "Windows":
                user_home = os.path.expanduser("~")
                download_path = os.path.join(user_home, "Music", file_name)
            else:
                user_home = os.path.expanduser("~")
                download_path = os.path.join(user_home, "Music", file_name)

            with open(download_path, "wb") as file:
                response = requests.get(data_src)
                file.write(response.content)
                print(f"Downloaded: {data_title}")

        conn.close()

    def download_all(self):
        conn = sqlite3.connect("playlist.db")
        cursor = conn.cursor()

        cursor.execute("SELECT title, source FROM playlist")
        rows = cursor.fetchall()

        for row in rows:
            data_title = row[0]
            data_src = row[1]
            file_name = os.path.basename(data_src)
            # Determine the user's home directory and create the download path
            if platform.system() == "Windows":
                user_home = os.path.expanduser("~")
                download_path = os.path.join(user_home, "Music", file_name)
            else:
                user_home = os.path.expanduser("~")
                download_path = os.path.join(user_home, "Music", file_name)

            with open(download_path, "wb") as file:
                response = requests.get(data_src)
                file.write(response.content)
                print(f"Downloaded: {data_title}")

        conn.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    downloader = MelovazDownloader()
    downloader.show()
    sys.exit(app.exec())
