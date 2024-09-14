import requests
from bs4 import BeautifulSoup
import os
import sqlite3

url = "https://melovaz.ir/chill-bel-masry-playlist"

response = requests.get(url)

soup = BeautifulSoup(response.content, "html.parser")

ul_tag = soup.find("ul", class_="audioplayer-audios")

os.makedirs("melovaz", exist_ok=True)


def Data_Melovaz():
    # Connect to the SQLite database
    conn = sqlite3.connect("melovaz/playlist.db")
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT NOT NULL
        )
    """)

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


