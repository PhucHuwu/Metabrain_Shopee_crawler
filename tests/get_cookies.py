import undetected_chromedriver as uc
import time
import threading
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

driver_lock = threading.Lock()


def setup_driver(idx):
    options = uc.ChromeOptions()
    profile_directory = f"Profile_{idx}"

    if not os.path.exists(profile_directory):
        os.makedirs(profile_directory)

    options.user_data_dir = profile_directory
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    try:
        with driver_lock:
            driver = uc.Chrome(options=options)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
        return driver
    except Exception as e:
        logger.error(f"Khong the khoi tao driver {idx}: {e}")
        time.sleep(180)
        return None


if __name__ == "__main__":
    driver = setup_driver(0)
    if driver:
        driver.get("https://shopee.vn/")
        if input() == "ok":
            driver.quit()
