#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script cho driver với lock mechanism - CHỈ SỬ DỤNG profile_directory
"""

import logging
import threading
import time
from utils.selenium_utils import create_driver_with_lock, worker_function

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_single_driver():
    """
    Test tạo driver đơn lẻ với profile_directory
    """
    logger.info("=== Test tạo driver với profile_directory ===")

    driver = create_driver_with_lock(0)
    if driver:
        try:
            logger.info("Driver được tạo thành công với profile_directory!")
            driver.get("https://google.com")
            logger.info(f"Title: {driver.title}")
            time.sleep(2)
        finally:
            driver.quit()
            logger.info("Driver đã được đóng")
    else:
        logger.error("Không thể tạo driver với profile_directory")


def test_multiple_threads():
    """
    Test tạo nhiều driver trong các thread - CHỈ SỬ DỤNG profile_directory
    """
    logger.info("=== Test nhiều driver với profile_directory trong threading ===")

    urls_list = [
        ["https://google.com", "https://github.com"],
        ["https://stackoverflow.com", "https://python.org"],
        ["https://selenium.dev"]
    ]

    threads = []

    for i, urls in enumerate(urls_list):
        thread = threading.Thread(
            target=worker_function,
            args=(i, urls),
            name=f"Worker-{i}"
        )
        threads.append(thread)
        thread.start()
        logger.info(f"Đã khởi động thread {i} với profile_directory")

        # Delay nhỏ giữa các thread
        time.sleep(1)

    # Chờ tất cả threads hoàn thành
    for thread in threads:
        thread.join()
        logger.info(f"Thread {thread.name} đã hoàn thành")

    logger.info("Tất cả threads với profile_directory đã hoàn thành!")


if __name__ == "__main__":
    print("Test Chrome Driver với PROFILE_DIRECTORY DUY NHẤT:")
    print("1. Test driver đơn lẻ với profile")
    print("2. Test multiple threads với profile")

    choice = input("Nhập lựa chọn (1/2): ").strip()

    if choice == "1":
        test_single_driver()
    elif choice == "2":
        test_multiple_threads()
    else:
        logger.info("Chạy cả hai test với profile_directory...")
        test_single_driver()
        time.sleep(3)
        test_multiple_threads()
