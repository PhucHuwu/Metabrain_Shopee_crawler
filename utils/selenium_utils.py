#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Selenium utilities
Helper functions cho Selenium operations - CHỈ SỬ DỤNG UNDETECTED CHROMEDRIVER
"""

import logging
import time
import json
import os
import threading
from typing import List, Optional, Dict
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException
)

logger = logging.getLogger(__name__)

# Thread-safe driver lock
driver_lock = threading.Lock()


def create_driver_with_lock(profile_idx: int = 0, config: Dict = None):
    """
    Tạo driver thread-safe với profile directory - PHƯƠNG PHÁP DUY NHẤT
    """
    try:
        logger.info(f"Khởi tạo driver thread-safe cho profile {profile_idx}")

        # Tạo profile directory
        profile_directory = f"Profile_{profile_idx}"
        if not os.path.exists(profile_directory):
            os.makedirs(profile_directory)
            logger.info(f"Đã tạo profile directory: {profile_directory}")

        # Cấu hình options
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-default-apps")

        if config and config.get('HEADLESS', False):
            options.add_argument("--headless")
            logger.info("Chế độ headless được bật")

        # Khởi tạo driver với lock theo cấu trúc yêu cầu
        with driver_lock:
            options.user_data_dir = profile_directory
            try:
                driver = uc.Chrome(options=options)
                logger.info(f"Đã khởi tạo Chrome driver với profile: {profile_directory}")

                # Cấu hình timeout
                driver.set_page_load_timeout(30)
                driver.implicitly_wait(10)

                return driver

            except Exception as e:
                logger.error(f"Lỗi khi khởi tạo Chrome driver profile {profile_idx}: {e}")
                time.sleep(180)  # Chờ trước khi thử lại
                return None

    except Exception as e:
        logger.error(f"Lỗi tổng quát khi tạo driver: {e}")
        return None


# Alias cho backward compatibility
setup_robust_driver = create_driver_with_lock


def safe_click_element(driver, selectors: List[str], timeout: int = 10) -> bool:
    """
    Click element với nhiều selector fallback và xử lý lỗi toàn diện
    """
    # TODO: Implement safe element clicking
    pass


def safe_get_text(driver, selectors: List[str], default_value: str = "") -> str:
    """
    Lấy text với multiple fallback selectors
    """
    # TODO: Implement safe text extraction
    pass


def safe_get_attribute(driver, selectors: List[str], attribute: str, default_value: str = "") -> str:
    """
    Lấy attribute với multiple fallback selectors
    """
    # TODO: Implement safe attribute extraction
    pass


def wait_for_page_ready(driver, timeout: int = 30) -> bool:
    """
    Chờ page load hoàn tất với nhiều điều kiện kiểm tra
    """
    try:
        # Chờ document ready
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Chờ jQuery load xong (nếu có)
        try:
            WebDriverWait(driver, 5).until(
                lambda d: d.execute_script("return typeof jQuery == 'undefined' || jQuery.active == 0")
            )
        except TimeoutException:
            logger.debug("Không có jQuery hoặc jQuery vẫn đang active")

        # Buffer time cho dynamic content
        time.sleep(2)
        logger.debug("Page đã load hoàn tất")
        return True

    except TimeoutException:
        logger.warning("Page không load hoàn tất trong thời gian quy định")
        return False
    except Exception as e:
        logger.error(f"Lỗi khi chờ page ready: {e}")
        return False


def save_cookies(driver, profile_name: str):
    """
    Lưu cookies vào file để sử dụng lại
    """
    try:
        cookies = driver.get_cookies()
        cookie_file = f"cookies_{profile_name}.json"
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        logger.info(f"Đã lưu {len(cookies)} cookies vào {cookie_file}")
    except Exception as e:
        logger.error(f"Lỗi khi lưu cookies: {e}")


def load_cookies(driver, profile_name: str) -> bool:
    """
    Load cookies từ file đã lưu
    """
    try:
        cookie_file = f"cookies_{profile_name}.json"
        if os.path.exists(cookie_file):
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)

            # Cần navigate tới domain trước khi add cookies
            current_url = driver.current_url
            if "shopee.vn" not in current_url.lower():
                driver.get("https://shopee.vn")
                wait_for_page_ready(driver, timeout=10)

            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Không thể thêm cookie {cookie.get('name', 'unknown')}: {e}")

            logger.info(f"Đã load {len(cookies)} cookies từ {cookie_file}")
            return True
    except Exception as e:
        logger.error(f"Lỗi khi load cookies: {e}")
    return False


def scroll_to_bottom(driver, pause_time: float = 2.0):
    """
    Scroll xuống cuối trang để load dynamic content
    """
    # TODO: Implement page scrolling
    pass


def handle_popup(driver) -> bool:
    """
    Xử lý popup có thể xuất hiện
    """
    try:
        # Danh sách các selector cho popup thường gặp
        popup_selectors = [
            "button[class*='close']",
            ".popup-close",
            "[data-dismiss='modal']",
            ".modal-close",
            "button:contains('Đóng')",
            "button:contains('Close')",
            ".shopee-popup__close-btn"
        ]

        for selector in popup_selectors:
            try:
                element = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                element.click()
                logger.info(f"Đã đóng popup với selector: {selector}")
                time.sleep(1)
                return True
            except TimeoutException:
                continue
            except Exception as e:
                logger.debug(f"Không thể đóng popup với selector {selector}: {e}")
                continue

        logger.debug("Không tìm thấy popup nào cần đóng")
        return False

    except Exception as e:
        logger.error(f"Lỗi khi xử lý popup: {e}")
        return False


def get_random_delay() -> float:
    """
    Tạo random delay để tránh detection
    """
    import random
    return random.uniform(1.0, 3.0)


def worker_function(thread_idx: int, urls: List[str], config: Dict = None):
    """
    Hàm worker để sử dụng trong threading - CHỈ SỬ DỤNG profile_directory
    """
    driver = create_driver_with_lock(thread_idx, config)
    if not driver:
        logger.error(f"Không thể tạo driver cho thread {thread_idx}")
        return

    try:
        # Load cookies nếu có
        if load_cookies(driver, f"thread_{thread_idx}"):
            logger.info(f"Đã load cookies cho thread {thread_idx}")

        # Thực hiện crawling
        for url in urls:
            try:
                logger.info(f"Thread {thread_idx} đang crawl: {url}")
                # TODO: Thêm logic crawl URL cụ thể ở đây
                driver.get(url)
                wait_for_page_ready(driver)

                # Random delay để tránh detection
                delay = get_random_delay()
                time.sleep(delay)

            except Exception as url_error:
                logger.error(f"Thread {thread_idx} lỗi khi crawl {url}: {url_error}")
                continue

        # Lưu cookies trước khi đóng
        save_cookies(driver, f"thread_{thread_idx}")
        logger.info(f"Đã lưu cookies cho thread {thread_idx}")

    except Exception as e:
        logger.error(f"Lỗi trong worker function thread {thread_idx}: {e}")
    finally:
        if driver:
            try:
                driver.quit()
                logger.info(f"Đã đóng driver cho thread {thread_idx}")
            except Exception as quit_error:
                logger.warning(f"Lỗi khi đóng driver thread {thread_idx}: {quit_error}")
