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
        # Create widgets for searching, displaying, and downloading songs
        self.list_widget = QListWidget()
        self.download_button = QPushButton("Download Selected")
        self.download_button.clicked.connect(self.download_selected)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for songs...")
        self.search_input.setFixedSize(QSize(300, 30))
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_songs)
        
        # Set the window icon and style
        self.setWindowIcon(QIcon('icon.png'))
        self.setStyleSheet("QMainWindow {background-color: #1a1a1a;}")

        # Add an image label to display the application logo
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setPixmap(QPixmap('icon_base.png'))

        # Create a layout for the widgets and set it to the main window
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
        
        # Add buttons for downloading selected and all songs
        self.download_all_button = QPushButton("Download All")
        self.download_all_button.clicked.connect(self.download_all)
        
        layout.addWidget(self.download_button)
        layout.addWidget(self.download_all_button)

    # Method to get the path of the database file
    def get_db_path(self):
        if platform.system() == "Windows":
            user_home = os.path.expanduser("~")
            db_path = os.path.join(user_home, "Documents", "playlist.db")
        else:
            user_home = os.path.expanduser("~")
            db_path = os.path.join(user_home, "Documents", "playlist.db")
        return db_path

    # Method to get the download path for a given file name
    def get_download_path(self, file_name):
        if platform.system() == "Windows":
            user_home = os.path.expanduser("~")
            download_path = os.path.join(user_home, "Music", file_name)
        else:
            user_home = os.path.expanduser("~")
            download_path = os.path.join(user_home, "Music", file_name)
        return download_path

    # Method to search for songs and display them in the list widget
    def search_songs(self):
        search_text = self.search_input.text()
        self.list_widget.clear()
        CreateNewTable()
        Data_Melovaz(search_text)
        self.fetch_songs()

    # Method to fetch the songs from the database and display them in the list widget
    def fetch_songs(self):
        db_path = self.get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM playlist")
        rows = cursor.fetchall()

        for row in rows:
            data_title = row[0]
            self.list_widget.addItem(data_title)

        conn.close()

    # Method to download the selected songs
    def download_selected(self):
        selected_items = self.list_widget.selectedItems()
        for item in selected_items:
            data_title = item.text()
            self.download_song(data_title)

    # Method to download a single song
    def download_song(self, data_title):
        db_path = self.get_db_path()
        conn = sqlite3.connect(db_path)
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

    # Method to download all songs
    def download_all(self):
        db_path = self.get_db_path()
        conn = sqlite3.connect(db_path)
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

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    downloader = MelovazDownloader()
    downloader.show()
    sys.exit(app.exec())
