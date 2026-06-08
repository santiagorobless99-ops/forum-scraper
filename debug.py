import cloudscraper
from bs4 import BeautifulSoup
import re

BASE_URL = "https://rozed.pro"
BOARD    = "b"

scraper = cloudscraper.create_scraper()


def debug_board():
    """
    Early-stage prototype that probes a board page via cloudscraper to inspect
    the raw HTML and identify thread link patterns before switching to Selenium.
    """
    board_url = f"{BASE_URL}/{BOARD}/"
    print(f"[*] Connecting to: {board_url} ...")

    try:
        response = scraper.get(board_url)
        print(f"[*] HTTP status code: {response.status_code}")

        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("[*] 'debug.html' saved. Open it in a browser to inspect the bot's view.")

        soup  = BeautifulSoup(response.text, 'html.parser')
        links = set()
        print("[*] Searching for thread links...")

        for a in soup.find_all('a', href=True):
            href = a['href']
            if re.search(r'\d+\.html', href):
                if "index" not in href:
                    full_link = href if href.startswith("http") else f"{BASE_URL}/{BOARD}/{href.lstrip('/')}"
                    if href.startswith(f"/{BOARD}/"):
                        full_link = f"{BASE_URL}{href}"
                    links.add(full_link)

        print(f"[*] Links found: {len(links)}")
        if links:
            print(f"[*] Example: {list(links)[0]}")

    except Exception as e:
        print(f"[!] Error: {e}")


if __name__ == "__main__":
    debug_board()
