import time
import json
import random
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- SCRAPER CONFIGURATION ---
SCROLL_MINUTES         = 10   # Duration of the infinite-scroll phase (minutes)
DELAY_BETWEEN_THREADS  = 1.5  # Seconds to wait between thread downloads
OUTPUT_FILE            = "rozed_dataset_masivo.json"
SAVE_EVERY             = 20   # Flush to disk after every N threads


def init_browser():
    print("[*] Setting up browser...")
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment to run without a visible window
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--log-level=3")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.maximize_window()
    return driver


def collection_phase(driver):
    print(f"[*] --- PHASE 1: INFINITE SCROLL ({SCROLL_MINUTES} MINUTES) ---")
    driver.get("https://rozed.pro/")
    time.sleep(5)  # Initial page load

    time_limit = datetime.now() + timedelta(minutes=SCROLL_MINUTES)
    scrolls = 0

    while datetime.now() < time_limit:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1.5, 3.0))  # Random delay to mimic human behaviour
        scrolls += 1

        if scrolls % 10 == 0:
            remaining = time_limit - datetime.now()
            remaining_str = str(remaining).split('.')[0]
            print(f"[Scroll #{scrolls}] Time remaining: {remaining_str}")

    print("[*] Scroll phase finished. Collecting thread links from DOM...")

    elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/Hilo/']")
    unique_links = set()

    for elem in elements:
        try:
            url = elem.get_attribute('href')
            if url:
                unique_links.add(url)
        except:
            pass

    print(f"[*] Collection complete. Found {len(unique_links)} unique threads.")
    return list(unique_links)


def download_phase(driver, urls):
    print(f"[*] --- PHASE 2: DOWNLOADING THREADS ({len(urls)} total) ---")

    all_data = []

    # Resume from a previous run if the output file already exists
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
                print(f"[*] Resuming: {len(all_data)} threads already downloaded.")
        except:
            print("[!] Existing output file is corrupted or empty. Starting fresh.")

    processed_ids = {d['url'] for d in all_data}
    count = 0

    for i, url in enumerate(urls):
        if url in processed_ids:
            continue

        try:
            driver.get(url)
            time.sleep(DELAY_BETWEEN_THREADS)

            data = {
                "id": url.split("/")[-1],
                "url": url,
                "titulo": "",
                "contenido": [],
                "imagenes": []
            }

            # Title
            try:
                data["titulo"] = driver.find_element(By.TAG_NAME, "h1").text
            except:
                pass

            # Post text blocks
            blocks = driver.find_elements(By.CSS_SELECTOR, "p, div.contenido, blockquote")
            for b in blocks:
                txt = b.text.strip()
                if txt and txt not in data["contenido"]:
                    data["contenido"].append(txt)

            # Images from <img> tags
            for img in driver.find_elements(By.TAG_NAME, "img"):
                src = img.get_attribute("src")
                if src and len(src) > 20 and any(ext in src for ext in [".jpg", ".png", ".gif", ".webp"]):
                    if src not in data["imagenes"]:
                        data["imagenes"].append(src)

            # Media links from <a> tags
            for a in driver.find_elements(By.TAG_NAME, "a"):
                href = a.get_attribute("href")
                if href and any(ext in href.lower() for ext in [".jpg", ".png", ".mp4", ".webm"]):
                    if href not in data["imagenes"]:
                        data["imagenes"].append(href)

            all_data.append(data)
            count += 1
            print(f"[+] ({i+1}/{len(urls)}) Downloaded: {data['id']} — images: {len(data['imagenes'])}")

            if count % SAVE_EVERY == 0:
                print(f"[*] Saving progress to {OUTPUT_FILE}...")
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, ensure_ascii=False, indent=4)

        except Exception as e:
            print(f"[!] Error on {url}: {e}")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

    print(f"\n[*] Done. Total threads in dataset: {len(all_data)}")


def main():
    driver = init_browser()
    try:
        links = collection_phase(driver)

        if links:
            download_phase(driver, links)
        else:
            print("[!] No thread links found. The scroll phase may have failed.")

    except Exception as e:
        print(f"[!] Critical error: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
