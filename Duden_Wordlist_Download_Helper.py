#!/usr/bin/env python3

# This tool only generates the url, use it with regular bash tools like wget to download the archives

import requests
from bs4 import BeautifulSoup
import re

# URL der Seite
url = "https://wortschatz.uni-leipzig.de/de/download/German"

# HTTP-Anfrage senden
response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

# Überprüfen, ob die Anfrage erfolgreich war
if response.status_code == 200:
    # HTML-Inhalt analysieren
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Alle Links mit der Klasse "link_corpora_download" suchen
    links = soup.find_all("a", {"class": "link_corpora_download"})
    
    # Durch die gefundenen Links iterieren
    for link in links:
        # Das Attribut "data-corpora-file" auslesen
        file_name = link.get("data-corpora-file")
        
        # Überprüfen, ob der Dateiname mit "deu-de" beginnt und "1M" am Ende hat (vor .tar.gz)
        if re.match(r"deu.*2021.*1M\.tar\.gz", file_name):
            # Die herunterladbare URL erstellen
            download_url = f"https://downloads.wortschatz-leipzig.de/corpora/{file_name}"
            
            # Den Download-Link ausdrucken
            print(download_url)
else:
    print("Fehler beim Abrufen der Seite. Statuscode:", response.status_code)
