import undetected_chromedriver as uc
import time
import threading
import os


driver_lock = threading.Lock()
confirmation_received = threading.Event()


def main(idx):

    options = uc.ChromeOptions()
    profile_directory = f"Profile_{idx}"
    if not os.path.exists(profile_directory):
        os.makedirs(profile_directory)

    with driver_lock:
        options.user_data_dir = profile_directory
        try:
            driver = uc.Chrome(options=options)
        except Exception as e:
            print(f"Lỗi x ở luồng {idx + 1}, {e}")
            time.sleep(180)
            exit()

    driver.get("https://shopee.vn/mall")

    if input() == "ok":
        driver.quit()
        exit()


main(0)
