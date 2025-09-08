import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
import os
import json
import re
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


def extract_category_hrefs(driver):
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "image-carousel__item-list"))
        )

        href_elements = driver.find_elements(By.TAG_NAME, "a")
        mall_pattern = r'^https://shopee\.vn/mall/.+\.\d+$'

        hrefs = []
        for elem in href_elements:
            href = elem.get_attribute("href")
            if href and re.match(mall_pattern, href):
                hrefs.append(href)

        return hrefs
    except Exception as e:
        logger.error(f"Khong tim thay phan tu: {e}")
        return []


def save_hrefs_to_file(hrefs, filename="category_hrefs.json"):
    try:
        data = {
            "total_hrefs": len(hrefs),
            "category_hrefs": hrefs
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Da luu {len(hrefs)} href vao file '{filename}'")
        return True
    except Exception as e:
        logger.error(f"Loi khi luu file JSON: {e}")
        return False


def crawl_shopee_categories(idx=0):
    driver = setup_driver(idx)
    if not driver:
        return False

    try:
        driver.get("https://shopee.vn/mall/")
        hrefs = extract_category_hrefs(driver)

        if hrefs:
            logger.info(f"Tim thay {len(hrefs)} category hrefs")
            save_hrefs_to_file(hrefs)
            return True
        else:
            logger.warning("Khong tim thay href nao")
            return False

    except Exception as e:
        logger.error(f"Loi trong qua trinh crawl: {e}")
        return False
    finally:
        driver.quit()


if __name__ == "__main__":
    crawl_shopee_categories()
