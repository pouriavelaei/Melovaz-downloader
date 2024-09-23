import requests
from bs4 import BeautifulSoup
import os
import sqlite3
import platform


def CreateNewTable():
    # Determine the user's document directory based on the operating system
    if platform.system() == 'Windows':
        document_dir = os.path.join(os.environ['USERPROFILE'], 'Documents')
    else:
        document_dir = os.path.join(os.environ['HOME'], 'Documents')

    db_path = os.path.join(document_dir, 'playlist.db')

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def Data_Melovaz(search_text):
    search_text1 = search_text
    url = f"https://melovaz.ir/{search_text1}"

    response = requests.get(url)

    soup = BeautifulSoup(response.content, "html.parser")

    ul_tag = soup.find("ul", class_="audioplayer-audios")

    os.makedirs("melovaz", exist_ok=True)
    # Connect to the SQLite database
    if platform.system() == 'Windows':
        document_dir = os.path.join(os.environ['USERPROFILE'], 'Documents')
    else:
        document_dir = os.path.join(os.environ['HOME'], 'Documents')

    db_path = os.path.join(document_dir, 'playlist.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for li_tag in ul_tag.find_all("li"):
        data_src = li_tag.get("data-src")
        data_title = li_tag.get("data-title")

        # Insert the extracted data into the table
        cursor.execute(
            "INSERT INTO playlist (title, source) VALUES (?, ?)", (data_title, data_src))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("Data has been saved to the database.")

# _____tester
# search_text = "arabic-music"
# Data_Melovaz(search_text)
