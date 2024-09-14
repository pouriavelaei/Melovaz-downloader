import sys
import requests
from bs4 import BeautifulSoup
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidget, QVBoxLayout, QWidget, QPushButton
from Downloader import Data_Melovaz
import sqlite3


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

        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        layout.addWidget(self.download_button)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.Data_Melovaz()
        self.fetch_songs()
        self.download_all_button = QPushButton("Download All")
        self.download_all_button.clicked.connect(self.download_all)
        layout.addWidget(self.download_all_button)
        self.stop_download_button = QPushButton("Stop Download")
        self.stop_download_button.clicked.connect(self.stop_download)
        layout.addWidget(self.stop_download_button)

    def Data_Melovaz(self):
        Data_Melovaz()

    def fetch_songs(self):
        conn = sqlite3.connect("melovaz/playlist.db")
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
        conn = sqlite3.connect("melovaz/playlist.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT source FROM playlist WHERE title = ?", (data_title,))
        row = cursor.fetchone()

        if row:
            data_src = row[0]
            file_name = os.path.basename(data_src)
            file_path = os.path.join("melovaz", file_name)

            with open(file_path, "wb") as file:
                response = requests.get(data_src)
                file.write(response.content)
                print(f"Downloaded: {data_title}")

        conn.close()

    def stop_download(self):
        # Implement your stop download logic here
        print("Download stopped")

    def download_all(self):
        conn = sqlite3.connect("melovaz/playlist.db")
        cursor = conn.cursor()

        cursor.execute("SELECT title, source FROM playlist")
        rows = cursor.fetchall()

        for row in rows:
            data_title = row[0]
            data_src = row[1]
            file_name = os.path.basename(data_src)
            file_path = os.path.join("melovaz", file_name)

            with open(file_path, "wb") as file:
                response = requests.get(data_src)
                file.write(response.content)
                print(f"Downloaded: {data_title}")

        conn.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    downloader = MelovazDownloader()
    downloader.show()
    sys.exit(app.exec())
