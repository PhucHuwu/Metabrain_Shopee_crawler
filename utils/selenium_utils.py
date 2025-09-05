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


def setup_robust_driver(profile_idx: int = 0, config: Dict = None):
    """
    Cấu hình driver với undetected-chromedriver ONLY (theo yêu cầu)
    """
    logger.info(f"Khởi tạo UNDETECTED ChromeDriver cho profile {profile_idx}")
    
    # Chỉ sử dụng undetected ChromeDriver - không có fallback
    logger.info("Sử dụng UNDETECTED ChromeDriver (bắt buộc)...")
    driver = try_undetected_chrome_robust(profile_idx, config)
    
    if driver:
        logger.info("UNDETECTED ChromeDriver khởi tạo thành công!")
        return driver
    
    logger.error("Không thể khởi tạo UNDETECTED ChromeDriver")
    logger.error("Gợi ý: Kiểm tra Chrome version và undetected-chromedriver version")
    return None


def try_undetected_chrome_robust(profile_idx: int = 0, config: Dict = None):
    """
    Khởi tạo undetected ChromeDriver với nhiều phương pháp robust
    """
    logger.info("Chuẩn bị UNDETECTED Chrome với cấu hình tối ưu...")
    
    # Phương pháp 1: Cấu hình đơn giản nhất
    driver = try_simple_undetected_chrome(profile_idx, config)
    if driver:
        logger.info("Phương pháp 1 (đơn giản) thành công!")
        return driver
    
    # Phương pháp 2: Cấu hình với profile directory
    driver = try_profile_undetected_chrome(profile_idx, config)
    if driver:
        logger.info("Phương pháp 2 (với profile) thành công!")
        return driver
    
    # Phương pháp 3: Cấu hình với auto version detection
    driver = try_auto_version_undetected_chrome(profile_idx, config)
    if driver:
        logger.info("Phương pháp 3 (auto version) thành công!")
        return driver
    
    logger.error("Tất cả phương pháp undetected Chrome đều thất bại")
    return None


def try_simple_undetected_chrome(profile_idx: int = 0, config: Dict = None):
    """
    Phương pháp 1: Undetected Chrome đơn giản nhất
    """
    try:
        logger.info("Thử undetected Chrome với cấu hình tối thiểu...")
        
        # Tạo options đơn giản nhất
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Kiểm tra headless mode
        if config and config.get('HEADLESS', False):
            options.add_argument("--headless")
            logger.info("Chế độ headless")
        
        # Khởi tạo với timeout
        driver = create_uc_driver_with_timeout(options, timeout=20)
        
        if driver:
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            logger.info("Simple undetected Chrome thành công")
            return driver
            
    except Exception as e:
        logger.warning(f"Simple undetected Chrome thất bại: {e}")
    
    return None


def try_profile_undetected_chrome(profile_idx: int = 0, config: Dict = None):
    """
    Phương pháp 2: Undetected Chrome với profile directory
    """
    try:
        logger.info("Thử undetected Chrome với profile directory...")
        
        # Tạo profile directory
        profile_directory = f"Profile_{profile_idx}"
        if not os.path.exists(profile_directory):
            os.makedirs(profile_directory)
            logger.info(f"Đã tạo profile: {profile_directory}")
        
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Thêm anti-detection options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-first-run")
        
        if config and config.get('HEADLESS', False):
            options.add_argument("--headless")
        
        # Khởi tạo với user data dir
        driver = uc.Chrome(
            options=options,
            user_data_dir=os.path.abspath(profile_directory)
        )
        
        if driver:
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            logger.info("Profile undetected Chrome thành công")
            return driver
            
    except Exception as e:
        logger.warning(f"Profile undetected Chrome thất bại: {e}")
    
    return None


def try_auto_version_undetected_chrome(profile_idx: int = 0, config: Dict = None):
    """
    Phương pháp 3: Undetected Chrome với auto version detection
    """
    try:
        logger.info("� Thử undetected Chrome với auto version detection...")
        
        options = uc.ChromeOptions()
        
        # Cấu hình options cơ bản
        basic_options = [
            "--no-sandbox",
            "--disable-dev-shm-usage", 
            "--disable-gpu",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--remote-debugging-port=0"
        ]
        
        for opt in basic_options:
            options.add_argument(opt)
        
        if config and config.get('HEADLESS', False):
            options.add_argument("--headless")
        
        # Khởi tạo với version_main=None để auto detect
        driver = uc.Chrome(
            options=options,
            version_main=None,
            driver_executable_path=None
        )
        
        if driver:
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            logger.info("Auto version undetected Chrome thành công")
            return driver
            
    except Exception as e:
        logger.warning(f"Auto version undetected Chrome thất bại: {e}")
    
    return None


def create_uc_driver_with_timeout(options, timeout: int = 20):
    """
    Tạo undetected Chrome driver với timeout để tránh hang
    """
    import threading
    
    driver_result = [None]
    exception_result = [None]
    
    def create_driver():
        try:
            driver = uc.Chrome(options=options)
            driver_result[0] = driver
            logger.debug("Driver thread tạo thành công")
        except Exception as e:
            exception_result[0] = e
    
    # Tạo thread với timeout
    thread = threading.Thread(target=create_driver)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        logger.warning(f"Timeout {timeout}s khi tạo driver")
        return None
    
    if exception_result[0]:
        logger.warning(f"Exception trong thread: {exception_result[0]}")
        return None
    
    return driver_result[0]


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
