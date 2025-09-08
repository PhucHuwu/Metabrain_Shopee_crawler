import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import threading
import os
import pandas as pd
from random import uniform, choice
from click_fn import click


driver_lock = threading.Lock()
confirmation_received = threading.Event()


def check_verification_page(driver):
    current_url = driver.current_url
    verification_patterns = [
        "verify/traffic",
        "verify/captcha",
        "error",
        "anti_bot_tracking_id"
    ]

    for pattern in verification_patterns:
        if pattern in current_url:
            return True, pattern
    return False, None


def handle_verification_page(driver, verification_type="unknown", max_wait=600):
    print("Phat hien trang verification. Vui long giai thu cong trong trinh duyet.")
    print("Chuong trinh se tu dong tiep tuc sau khi hoan tat.")

    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            is_verification, _ = check_verification_page(driver)
            if not is_verification:
                if "shopee.vn" in driver.current_url:
                    print("Da giai quyet verification thanh cong.")
                    time.sleep(2)
                    return True
            time.sleep(2)
        except:
            time.sleep(5)

    print("Qua thoi gian cho. Thu lai sau.")
    return False


def safe_navigate_to_shopee(driver, max_retries=3):
    for attempt in range(max_retries):
        try:
            time.sleep(uniform(2, 5))
            driver.get("https://shopee.vn/mall/")

            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(3)

            is_verification, verification_type = check_verification_page(driver)
            if is_verification:
                if not handle_verification_page(driver, verification_type):
                    continue

            current_url = driver.current_url
            if "shopee.vn" in current_url and "verify" not in current_url:
                return True

        except TimeoutException:
            pass
        except Exception:
            pass

        if attempt < max_retries - 1:
            wait_time = (attempt + 1) * 15
            time.sleep(wait_time)

    return False


def get_fake_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0"
    ]
    return choice(user_agents)


def setup_chrome_options(idx):
    options = uc.ChromeOptions()

    profile_directory = f"Profile_{idx}"
    if not os.path.exists(profile_directory):
        os.makedirs(profile_directory)

    options.user_data_dir = profile_directory
    fake_user_agent = get_fake_user_agent()
    options.add_argument(f"--user-agent={fake_user_agent}")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-sync")
    options.add_argument("--metrics-recording-only")
    options.add_argument("--no-report-upload")
    options.add_argument("--disable-logging")
    options.add_argument("--silent")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-plugins-discovery")
    options.add_argument("--disable-prerender-local-predictor")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-ipc-flooding-protection")

    prefs = {
        "profile.default_content_setting_values": {
            "notifications": 2,
            "geolocation": 2,
            "media_stream": 2,
        },
        "profile.managed_default_content_settings": {
            "images": 1
        },
        "profile.content_settings.exceptions.automatic_downloads": {
            "*,*": {"setting": 2}
        }
    }
    options.add_experimental_option("prefs", prefs)
    options.page_load_strategy = 'eager'

    return options


def simulate_human_behavior(driver):
    try:
        for _ in range(3):
            scroll_amount = uniform(300, 800)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(uniform(1, 3))

        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(uniform(1, 2))

        try:
            actions = ActionChains(driver)
            element = driver.find_element(By.TAG_NAME, "body")
            actions.move_to_element(element).perform()
        except:
            pass
    except:
        pass


def main(idx):
    driver = None
    try:
        options = setup_chrome_options(idx)

        with driver_lock:
            try:
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        driver = uc.Chrome(options=options)
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            time.sleep(5)
                        else:
                            raise e

                if driver is None:
                    return False

                try:
                    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                except:
                    pass

            except Exception:
                return False

        if not safe_navigate_to_shopee(driver):
            if driver:
                driver.quit()
            return False

        simulate_human_behavior(driver)

        user_input = input("Nhan Enter de tiep tuc hoac 'q' de thoat: ")
        if user_input.lower() == 'q':
            if driver:
                driver.quit()
            return False

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "home-popup"))
            )
            click(driver, '//*[@class="shopee-popup__close-btn"]', 10, retries=3)
        except TimeoutException:
            pass
        except Exception:
            pass

        return True

    except Exception:
        return False
    finally:
        if 'driver' in locals() and driver is not None:
            try:
                pass
            except:
                pass


if __name__ == "__main__":
    success = main(0)
    if success:
        print("Crawler hoat dong thanh cong!")
    else:
        print("Crawler gap loi!")
