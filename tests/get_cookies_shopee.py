import time
import threading
import logging
import os
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

driver_lock = threading.Lock()


def main(thread_idx):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from funcs.setup_driver import setup_driver

    driver = None
    while driver is None:
        driver = setup_driver(profile_idx=thread_idx)

    screen_width = driver.execute_script("return window.screen.availWidth;")
    screen_height = driver.execute_script("return window.screen.availHeight;")
    window_width = screen_width // 5
    window_height = screen_height // 2
    # position_x = thread_idx * window_width // 5
    position_x = thread_idx * window_width  # for testing
    position_y = 0

    driver.set_window_size(window_width, window_height)
    driver.set_window_position(position_x, position_y)

    driver.get("https://shopee.vn/mall")
    driver.execute_script("document.body.style.zoom='25%'")
    
    if input() == 'q':
        return


NUM_THREADS = 5

threads = []

for idx in range(NUM_THREADS):
    thread = threading.Thread(target=main, args=(idx,))
    thread.start()
    time.sleep(1)
    threads.append(thread)

for thread in threads:
    thread.join()
