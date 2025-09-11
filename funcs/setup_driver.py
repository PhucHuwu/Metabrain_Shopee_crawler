import undetected_chromedriver as uc
import threading
import os
import time
import logging

logger = logging.getLogger(__name__)
driver_lock = threading.Lock()


def setup_driver(profile_idx: int = 0, headless: bool = False, user_data_base: str = None):
    """Create and return an undetected-chromedriver instance using a profile directory.

    - profile_idx: index to construct a local `Profile_{idx}` folder
    - headless: if True attempts to run headless (best-effort)
    - user_data_base: optional base directory for user data (overrides current dir)
    """
    options = uc.ChromeOptions()
    base = user_data_base if user_data_base else '.'
    profile_directory = os.path.join(base, f"Profile_{profile_idx}")

    os.makedirs(profile_directory, exist_ok=True)
    options.user_data_dir = profile_directory
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    if headless:
        options.add_argument("--headless=new")

    try:
        with driver_lock:
            driver = uc.Chrome(options=options)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
        return driver
    except Exception as e:
        logger.error(f"Cannot initialize driver {profile_idx}: {e}")
        time.sleep(5)
        return None
