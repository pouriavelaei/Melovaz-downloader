import sys
import requests
from bs4 import BeautifulSoup
import os
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QSizePolicy, QSpacerItem, 
                            QLabel, QMainWindow, QListWidget, QLineEdit, QVBoxLayout, 
                            QWidget, QPushButton, QProgressBar, QMessageBox, QListWidgetItem)
from Downloader import Data_Melovaz, CreateNewTable
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QObject
import sqlite3
import platform
import threading


# کلاس سیگنال برای ارتباط بین ترد‌ها و رابط کاربری
class DownloadSignals(QObject):
    progress = pyqtSignal(str, int)  # سیگنال برای نمایش پیشرفت (نام فایل، درصد)
    finished = pyqtSignal(str, bool)  # سیگنال برای اعلام اتمام دانلود (نام فایل، موفقیت/شکست)
    all_finished = pyqtSignal(bool)  # سیگنال برای اعلام اتمام همه دانلودها (همه موفق/برخی ناموفق)
    search_completed = pyqtSignal()  # سیگنال برای اعلام اتمام جستجو
    search_error = pyqtSignal(str)  # سیگنال برای اعلام خطا در جستجو


# ویجت سفارشی برای نمایش آیتم با نوار پیشرفت
# ویجت سفارشی برای نمایش آیتم با نوار پیشرفت
class SongItemWidget(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        self.title_label = QLabel(title)
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.title_label.setMinimumHeight(30)
        
        # Create a horizontal layout for progress bar and retry button
        self.progress_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setMinimumHeight(20)
        self.progress_layout.addWidget(self.progress_bar)
        
        # Add retry button (initially hidden)
        self.retry_button = QPushButton("تلاش مجدد")
        self.retry_button.setVisible(False)
        self.retry_button.setStyleSheet("""
            QPushButton {
                background-color: #FF3D00;
                color: white;
                border-radius: 4px;
                padding: 3px;
                min-width: 80px;
                max-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #DD2C00;
            }
        """)
        self.progress_layout.addWidget(self.retry_button)
        
        layout.addWidget(self.title_label)
        layout.addLayout(self.progress_layout)
        
    def set_progress(self, value):
        self.progress_bar.setVisible(True)
        self.retry_button.setVisible(False)
        self.progress_bar.setStyleSheet("")  # Reset style
        self.progress_layout.setStretch(0, 1)  # Full width for progress bar
        self.progress_layout.setStretch(1, 0)  # No space for retry button
        self.progress_bar.setValue(value)
        
    def hide_progress(self):
        self.progress_bar.setVisible(False)
        self.retry_button.setVisible(False)
        
    def mark_completed(self):
        self.progress_bar.setValue(100)
        self.title_label.setText(f"{self.title} ✓")
        self.retry_button.setVisible(False)
        self.progress_layout.setStretch(0, 1)  # Full width for progress bar
        self.progress_layout.setStretch(1, 0)  # No space for retry button
        
    def mark_failed(self):
        # Make progress bar smaller and show retry button
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #2196F3; }")
        self.title_label.setText(f"{self.title} ❌")
        self.retry_button.setVisible(True)
        
        # Adjust layout to give space for retry button
        self.progress_layout.setStretch(0, 2)  # 2/3 width for progress bar
        self.progress_layout.setStretch(1, 1)  # 1/3 width for retry button


class MelovazDownloader(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Melovaz Downloader")
        self.setGeometry(100, 100, 600, 400)
        self.download_signals = DownloadSignals()
        self.download_signals.progress.connect(self.update_song_progress)
        self.download_signals.finished.connect(self.on_download_finished)
        self.download_signals.all_finished.connect(self.on_all_downloads_finished)
        self.download_signals.search_completed.connect(self.fetch_songs)
        self.download_signals.search_error.connect(self.on_search_error)
        self.active_downloads = 0  # شمارنده دانلودهای فعال
        self.failed_downloads = 0  # شمارنده دانلودهای ناموفق
        self.song_widgets = {}  # نگهداری ویجت‌های آهنگ
        self.song_sources = {}  # نگهداری آدرس منبع آهنگ‌ها
        
        self.initUI()

    def initUI(self):
        # Create widgets for searching, displaying, and downloading songs
        self.list_widget = QListWidget()
        self.list_widget.setSpacing(2)
        self.download_button = QPushButton("Download Selected")
        self.download_button.clicked.connect(self.download_selected)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for songs...")
        self.search_input.setFixedSize(QSize(300, 30))
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_songs)

        # Set the window icon and style
        self.setWindowIcon(QIcon('icon.png'))
        self.setStyleSheet("""
            QMainWindow {background-color: #1a1a1a;}
            QListWidget {background-color: #2a2a2a; color: white; border-radius: 5px;}
            QProgressBar {
                border: 1px solid #FF3D00;
                border-radius: 3px;
                text-align: center;
                background-color: #1a1a1a;
            }
            QProgressBar::chunk {
                background-color: #FF3D00;
                width: 10px;
            }
            QPushButton {
                background-color: #FF3D00;
                color: white;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #DD2C00;
            }
            QLineEdit {
                border: 1px solid #FF3D00;
                border-radius: 4px;
                padding: 5px;
            }
            QLabel {
                color: white;
            }
        """)

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

        # اضافه کردن برچسب وضعیت
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Add buttons for downloading selected and all songs
        self.download_all_button = QPushButton("Download All")
        self.download_all_button.clicked.connect(self.download_all)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.download_all_button)
        layout.addLayout(button_layout)

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
        if not search_text:
            QMessageBox.warning(self, "هشدار", "لطفاً یک عبارت جستجو وارد کنید.")
            return
            
        self.list_widget.clear()
        self.song_widgets.clear()
        self.status_label.setText("در حال جستجو...")
        self.search_button.setEnabled(False)
        
        # اجرای جستجو در یک ترد جداگانه
        threading.Thread(target=self.search_thread, args=(search_text,), daemon=True).start()

    # Method to search in a separate thread
    def search_thread(self, search_text):
        try:
            CreateNewTable()
            Data_Melovaz(search_text)
            # استفاده از سیگنال برای فراخوانی متد fetch_songs در ترد اصلی
            self.download_signals.search_completed.emit()
        except Exception as e:
            self.download_signals.search_error.emit(str(e))

    # Method to handle search errors
    def on_search_error(self, error_message):
        self.status_label.setText(f"خطا در جستجو: {error_message}")
        self.search_button.setEnabled(True)

    # Method to fetch the songs from the database and display them in the list widget
    def fetch_songs(self):
        db_path = self.get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT title, source FROM playlist")
        rows = cursor.fetchall()

        self.list_widget.clear()
        self.song_widgets.clear()
        self.song_sources.clear()

        for row in rows:
            data_title = row[0]
            data_src = row[1]
            self.song_sources[data_title] = data_src
            
            item = QListWidgetItem()
            self.list_widget.addItem(item)
            
            song_widget = SongItemWidget(data_title)
            song_widget.retry_button.clicked.connect(lambda checked=False, title=data_title: self.retry_download(title))
            item.setSizeHint(song_widget.sizeHint())
            self.list_widget.setItemWidget(item, song_widget)
            self.song_widgets[data_title] = song_widget

        conn.close()
        self.status_label.setText(f"{len(rows)} آهنگ یافت شد.")
        self.search_button.setEnabled(True)

    # Method to download the selected songs
    def download_selected(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "اطلاعات", "لطفاً حداقل یک آهنگ را انتخاب کنید.")
            return
            
        self.status_label.setText("در حال دانلود...")
        self.download_button.setEnabled(False)
        self.download_all_button.setEnabled(False)
        
        self.active_downloads = len(selected_items)
        self.failed_downloads = 0
        
        for index in range(len(selected_items)):
            item = selected_items[index]
            widget = self.list_widget.itemWidget(item)
            data_title = widget.title
            
            # نمایش نوار پیشرفت برای این آیتم
            widget.set_progress(0)
            
            thread = threading.Thread(target=self.download_song_thread, args=(data_title,))
            thread.daemon = True
            thread.start()

    # Method to download a single song in a separate thread
    def download_song_thread(self, data_title):
        data_src = self.song_sources[data_title]
        file_name = os.path.basename(data_src)
        download_path = self.get_download_path(file_name)
        
        # اطمینان از وجود پوشه Music
        os.makedirs(os.path.dirname(download_path), exist_ok=True)
        
        try:
            response = requests.get(data_src, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(download_path, "wb") as file:
                if total_size == 0:  # اگر اندازه فایل مشخص نیست
                    file.write(response.content)
                    self.download_signals.progress.emit(data_title, 100)
                else:
                    downloaded = 0
                    for data in response.iter_content(chunk_size=4096):
                        downloaded += len(data)
                        file.write(data)
                        # محاسبه درصد پیشرفت
                        progress = int(100 * downloaded / total_size)
                        self.download_signals.progress.emit(data_title, progress)
                
            self.download_signals.finished.emit(data_title, True)
        except Exception as e:
            print(f"خطا در دانلود {data_title}: {str(e)}")
            self.download_signals.finished.emit(data_title, False)

    # Method to download all songs
    def download_all(self):
        if self.list_widget.count() == 0:
            QMessageBox.information(self, "اطلاعات", "هیچ آهنگی برای دانلود یافت نشد.")
            return
            
        self.status_label.setText("در حال دانلود همه آهنگ‌ها...")
        self.download_button.setEnabled(False)
        self.download_all_button.setEnabled(False)
        
        self.active_downloads = self.list_widget.count()
        self.failed_downloads = 0
        
        # نمایش نوار پیشرفت برای همه آیتم‌ها
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            widget = self.list_widget.itemWidget(item)
            widget.set_progress(0)
        
        # ایجاد یک ترد برای هر آهنگ
        for data_title, data_src in self.song_sources.items():
            thread = threading.Thread(target=self.download_file_thread, args=(data_title, data_src))
            thread.daemon = True
            thread.start()

    # Method to download a file in a separate thread
    def download_file_thread(self, data_title, data_src):
        file_name = os.path.basename(data_src)
        download_path = self.get_download_path(file_name)
        
        # اطمینان از وجود پوشه Music
        os.makedirs(os.path.dirname(download_path), exist_ok=True)
        
        try:
            response = requests.get(data_src, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(download_path, "wb") as file:
                if total_size == 0:  # اگر اندازه فایل مشخص نیست
                    file.write(response.content)
                    self.download_signals.progress.emit(data_title, 100)
                else:
                    downloaded = 0
                    for data in response.iter_content(chunk_size=4096):
                        downloaded += len(data)
                        file.write(data)
                        # محاسبه درصد پیشرفت
                        progress = int(100 * downloaded / total_size)
                        self.download_signals.progress.emit(data_title, progress)
                
            self.download_signals.finished.emit(data_title, True)
        except Exception as e:
            print(f"خطا در دانلود {data_title}: {str(e)}")
            self.download_signals.finished.emit(data_title, False)

    # Method to update the progress of a song
    def update_song_progress(self, data_title, progress):
        if data_title in self.song_widgets:
            widget = self.song_widgets[data_title]
            widget.set_progress(progress)
            if progress == 100:
                widget.mark_completed()

    # Method called when a download is finished
    def on_download_finished(self, data_title, success):
        self.active_downloads -= 1
        
        if not success:
            self.failed_downloads += 1
            if data_title in self.song_widgets:
                widget = self.song_widgets[data_title]
                widget.mark_failed()
        
        if self.active_downloads == 0:
            self.download_signals.all_finished.emit(self.failed_downloads == 0)

    # Method called when all downloads are finished
    def on_all_downloads_finished(self, all_successful):
        self.download_button.setEnabled(True)
        self.download_all_button.setEnabled(True)
        if all_successful:
            self.status_label.setText("همه دانلودها تکمیل شد!")
            QMessageBox.information(self, "اطلاعات", "همه دانلودها با موفقیت انجام شد.")
        else:
            self.status_label.setText("برخی دانلودها ناموفق بودند.")
            QMessageBox.warning(self, "هشدار", "برخی دانلودها ناموفق بودند. لطفاً دوباره تلاش کنید.")

    # Method to retry downloading a failed song
    def retry_download(self, data_title):
        if data_title in self.song_widgets and data_title in self.song_sources:
            widget = self.song_widgets[data_title]
            widget.set_progress(0)
            
            self.active_downloads += 1
            
            # Start a new thread to download the song
            thread = threading.Thread(
                target=self.download_file_thread, 
                args=(data_title, self.song_sources[data_title])
            )
            thread.daemon = True
            thread.start()
            
            self.status_label.setText(f"در حال تلاش مجدد برای دانلود {data_title}...")


# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    downloader = MelovazDownloader()
    downloader.show()
    sys.exit(app.exec())