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
import random
from typing import List, Optional, Dict
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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

# Danh sách user agents để tránh detection
USER_AGENTS = [
    # Chrome Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',

    # Chrome macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',

    # Firefox Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',

    # Edge Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',

    # Chrome Linux
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',

    # Safari macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15'
]


def get_random_user_agent() -> str:
    """
    Lấy random user agent để tránh detection
    """
    return random.choice(USER_AGENTS)


def set_user_agent_for_driver(driver, user_agent: str = None):
    """
    Thay đổi user agent cho driver (chỉ áp dụng cho request tiếp theo)
    """
    if not user_agent:
        user_agent = get_random_user_agent()

    try:
        # Thực thi JavaScript để thay đổi user agent
        script = f"""
        Object.defineProperty(navigator, 'userAgent', {{
            get: function () {{ return '{user_agent}'; }}
        }});
        """
        driver.execute_script(script)
        logger.debug(f"Đã thay đổi user agent thành: {user_agent[:80]}...")
        return user_agent
    except Exception as e:
        logger.warning(f"Không thể thay đổi user agent: {e}")
        return None


def create_driver_with_lock(profile_idx: int = 0, config: Dict = None):
    """
    Tạo driver thread-safe với profile directory và random user agent - PHƯƠNG PHÁP DUY NHẤT
    """
    try:
        logger.info(f"Khởi tạo driver thread-safe cho profile {profile_idx}")

        # Tạo profile directory
        profile_directory = f"Profile_{profile_idx}"
        if not os.path.exists(profile_directory):
            os.makedirs(profile_directory)
            logger.info(f"Đã tạo profile directory: {profile_directory}")

        # Lấy random user agent
        user_agent = get_random_user_agent()
        logger.info(f"Sử dụng User-Agent: {user_agent[:80]}...")

        # Cấu hình options
        options = uc.ChromeOptions()
        options.add_argument(f"--user-agent={user_agent}")
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
                driver.get("https://shopee.vn/mall")
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


def handle_popup(driver, timeout: int = 5) -> bool:
    """
    Xử lý popup có thể xuất hiện trên Shopee - cải tiến với nhiều loại popup và timeout
    """
    try:
        logger.debug("Bắt đầu kiểm tra và xử lý popup...")
        start_time = time.time()

        # Danh sách các CSS selector cho popup Shopee thường gặp
        css_selectors = [
            # Popup đóng chung
            "button[class*='close']",
            ".popup-close",
            "[data-dismiss='modal']",
            ".modal-close",

            # Shopee specific popups
            ".shopee-popup__close-btn",
            ".shopee-drawer__close-btn",
            "button[aria-label='close']",
            "button[aria-label='Đóng']",
            "button[data-testid='button']",

            # Cookie consent
            ".cookie-consent button",

            # App download popup
            ".app-download-close",

            # Notification popups
            ".notification-close",
            ".alert-close",

            # Generic close buttons
            "button[title='Close']",
            "button[title='Đóng']",
            ".btn-close",
            "[class*='icon-close']",
            "[class*='close-btn']",
            "[class*='modal-close']"
        ]

        # Danh sách XPath selectors cho text-based buttons
        xpath_selectors = [
            "//button[contains(text(), 'Xác nhận')]",
            "//button[contains(text(), 'Đồng ý')]",
            "//button[contains(text(), 'OK')]",
            "//button[contains(text(), 'Bỏ qua')]",
            "//button[contains(text(), 'Skip')]",
            "//button[contains(text(), 'Chấp nhận')]",
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'Không, cảm ơn')]",
            "//button[contains(text(), 'No thanks')]",
            "//button[contains(text(), 'Đóng')]",
            "//button[contains(text(), 'Close')]",
            "//div[contains(@class, 'close') or contains(@class, 'dismiss')]",
            "//span[contains(@class, 'close')]//parent::button"
        ]

        popup_found = False

        # Thử đóng popup bằng CSS selectors với timeout
        for selector in css_selectors:
            if (time.time() - start_time) > timeout:
                logger.debug(f"Timeout {timeout}s trong CSS selector handling")
                break

            try:
                element = WebDriverWait(driver, 0.3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )

                # Scroll đến element và click
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.1)
                element.click()

                logger.info(f"Đã đóng popup với CSS selector: {selector}")
                time.sleep(0.2)
                popup_found = True

            except TimeoutException:
                continue
            except ElementClickInterceptedException:
                try:
                    driver.execute_script("arguments[0].click();", element)
                    logger.info(f"Đã đóng popup bằng JS với CSS selector: {selector}")
                    popup_found = True
                    time.sleep(0.2)
                except Exception:
                    continue
            except Exception:
                continue

        # Thử đóng popup bằng XPath selectors với timeout
        for xpath in xpath_selectors:
            if (time.time() - start_time) > timeout:
                logger.debug(f"Timeout {timeout}s trong XPath handling")
                break

            try:
                element = WebDriverWait(driver, 0.3).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )

                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.1)
                element.click()

                logger.info(f"Đã đóng popup với XPath: {xpath}")
                time.sleep(0.2)
                popup_found = True

            except TimeoutException:
                continue
            except ElementClickInterceptedException:
                try:
                    driver.execute_script("arguments[0].click();", element)
                    logger.info(f"Đã đóng popup bằng JS với XPath: {xpath}")
                    popup_found = True
                    time.sleep(0.2)
                except Exception:
                    continue
            except Exception:
                continue

        # Thử xử lý overlay/backdrop với timeout
        if (time.time() - start_time) <= timeout:
            try:
                overlays = driver.find_elements(By.CSS_SELECTOR, ".modal-backdrop, .overlay, .mask, [class*='backdrop']")
                for overlay in overlays:
                    try:
                        if overlay.is_displayed():
                            driver.execute_script("arguments[0].click();", overlay)
                            logger.info("Đã đóng overlay bằng cách click backdrop")
                            popup_found = True
                            time.sleep(0.2)
                            break
                    except:
                        continue
            except Exception:
                pass

        # Thử nhấn ESC key với timeout
        if (time.time() - start_time) <= timeout:
            try:
                body = driver.find_element(By.TAG_NAME, 'body')
                body.send_keys(Keys.ESCAPE)
                logger.debug("Đã thử nhấn ESC để đóng popup")
                time.sleep(0.2)
            except Exception:
                pass

        elapsed = time.time() - start_time
        if popup_found:
            logger.info(f"Đã xử lý thành công popup trong {elapsed:.1f}s")
        else:
            logger.debug(f"Không tìm thấy popup nào cần xử lý ({elapsed:.1f}s)")

        return popup_found

    except Exception as e:
        logger.error(f"Lỗi khi xử lý popup: {e}")
        return False


def get_random_delay() -> float:
    """
    Tạo random delay để tránh detection
    """
    import random
    return random.uniform(1.0, 3.0)


def handle_shopee_specific_popups(driver, timeout: int = 5) -> bool:
    """
    Xử lý các popup đặc thù của Shopee như age verification, location popup, v.v. với timeout
    """
    try:
        logger.debug("Kiểm tra popup đặc thù của Shopee...")
        start_time = time.time()
        popup_handled = False

        # Xử lý popup xác nhận tuổi
        age_verification_selectors = [
            "//button[contains(text(), 'Tôi đã đủ 18 tuổi')]",
            "//button[contains(text(), 'I am 18+')]",
            "//div[@data-testid='age-gate']//button",
            "//button[@data-testid='confirm-age']",
        ]

        for selector in age_verification_selectors:
            if (time.time() - start_time) > timeout:
                logger.debug(f"Timeout {timeout}s trong age verification")
                break

            try:
                element = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                element.click()
                logger.info(f"Đã xử lý popup xác nhận tuổi: {selector}")
                popup_handled = True
                time.sleep(0.5)
                break
            except TimeoutException:
                continue
            except Exception as e:
                logger.debug(f"Lỗi khi xử lý age verification với {selector}: {e}")
                continue

        # Xử lý popup location/địa điểm
        if (time.time() - start_time) <= timeout:
            location_selectors = [
                "//button[contains(text(), 'Cho phép')]",
                "//button[contains(text(), 'Allow')]",
                "//button[contains(text(), 'Đồng ý')]",
                "//button[contains(@class, 'location')]",
                "//div[contains(@class, 'location-modal')]//button[last()]"
            ]

            for selector in location_selectors:
                if (time.time() - start_time) > timeout:
                    break

                try:
                    element = WebDriverWait(driver, 1).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    element.click()
                    logger.info(f"Đã xử lý popup địa điểm: {selector}")
                    popup_handled = True
                    time.sleep(0.5)
                    break
                except TimeoutException:
                    continue
                except Exception as e:
                    logger.debug(f"Lỗi khi xử lý location popup với {selector}: {e}")
                    continue

        # Xử lý popup cookie consent
        if (time.time() - start_time) <= timeout:
            cookie_selectors = [
                "//button[contains(text(), 'Chấp nhận tất cả')]",
                "//button[contains(text(), 'Accept All')]",
                "//button[@data-testid='cookie-accept']",
                "//div[@id='cookie-banner']//button[last()]"
            ]

            for selector in cookie_selectors:
                if (time.time() - start_time) > timeout:
                    break

                try:
                    element = WebDriverWait(driver, 0.5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    element.click()
                    logger.info(f"Đã xử lý cookie consent: {selector}")
                    popup_handled = True
                    time.sleep(0.3)
                    break
                except TimeoutException:
                    continue
                except Exception as e:
                    logger.debug(f"Lỗi khi xử lý cookie popup với {selector}: {e}")
                    continue

        # Xử lý popup tải app
        if (time.time() - start_time) <= timeout:
            app_download_selectors = [
                "//button[contains(text(), 'Bỏ qua')]",
                "//button[contains(text(), 'Skip')]",
                "//button[contains(text(), 'Không, cám ơn')]",
                "//button[contains(text(), 'No thanks')]",
                "//div[contains(@class, 'app-banner')]//button[@class*='close']",
                "//div[@data-testid='download-app']//button[last()]"
            ]

            for selector in app_download_selectors:
                if (time.time() - start_time) > timeout:
                    break

                try:
                    element = WebDriverWait(driver, 0.5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    element.click()
                    logger.info(f"Đã từ chối tải app: {selector}")
                    popup_handled = True
                    time.sleep(0.3)
                    break
                except TimeoutException:
                    continue
                except Exception as e:
                    logger.debug(f"Lỗi khi xử lý app download popup với {selector}: {e}")
                    continue

        elapsed = time.time() - start_time
        if popup_handled:
            logger.info(f"Đã xử lý popup đặc thù Shopee trong {elapsed:.1f}s")
        else:
            logger.debug(f"Không có popup đặc thù Shopee nào ({elapsed:.1f}s)")

        return popup_handled

    except Exception as e:
        logger.error(f"Lỗi khi xử lý popup Shopee đặc thù: {e}")
        return False


def wait_and_handle_popup(driver, timeout: int = 10) -> bool:
    """
    Chờ popup xuất hiện và xử lý ngay lập tức
    """
    try:
        logger.debug(f"Chờ popup xuất hiện trong {timeout}s...")

        # Các selector cho popup thường gặp trên Shopee
        popup_indicator_selectors = [
            "div[class*='modal'][style*='display: block']",
            "div[class*='modal']:not([style*='display: none'])",
            "div[class*='popup'][style*='display: block']",
            "div[role='dialog']",
            "div[aria-modal='true']",
            ".shopee-modal:not([style*='display: none'])",
            ".shopee-popup:not([style*='display: none'])",
            "[class*='age-gate']",
            "[class*='location-modal']",
            "[data-testid*='modal']",
        ]

        popup_found = False
        start_time = time.time()

        # Chờ popup xuất hiện
        while (time.time() - start_time) < timeout:
            for selector in popup_indicator_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            logger.info(f"Phát hiện popup hiển thị với selector: {selector}")
                            popup_found = True
                            break
                    if popup_found:
                        break
                except Exception:
                    continue

            if popup_found:
                break

            time.sleep(0.5)  # Chờ 0.5s trước khi kiểm tra lại

        if popup_found:
            logger.info("Popup đã xuất hiện, bắt đầu xử lý...")
            # Chờ thêm một chút để popup load hoàn toàn
            time.sleep(1)

            # Xử lý popup trực tiếp
            handled = False
            if handle_popup(driver):
                handled = True
                logger.info("✅ Đã xử lý popup thành công bằng handle_popup")

            if handle_shopee_specific_popups(driver):
                handled = True
                logger.info("✅ Đã xử lý popup đặc thù Shopee")

            return handled
        else:
            logger.debug("Không có popup nào xuất hiện")
            return False

    except Exception as e:
        logger.error(f"Lỗi trong wait_and_handle_popup: {e}")
        return False


def smart_popup_detection(driver, timeout: int = 5) -> bool:
    """
    Phát hiện popup thông minh bằng cách kiểm tra DOM và JavaScript với timeout
    """
    try:
        logger.debug("Bắt đầu phát hiện popup thông minh...")
        start_time = time.time()

        # Kiểm tra các indicator của popup
        popup_indicators = [
            # Body có class modal-open (nhiều site sử dụng)
            "return document.body.classList.contains('modal-open')",

            # Có overlay/backdrop hiển thị
            "return document.querySelector('.modal-backdrop, .overlay, [class*=\"backdrop\"]') !== null",

            # Có element với z-index cao (thường là popup)
            """
            const elements = document.querySelectorAll('*');
            for (let elem of elements) {
                const zIndex = window.getComputedStyle(elem).zIndex;
                if (zIndex && parseInt(zIndex) > 1000 && elem.offsetWidth > 0 && elem.offsetHeight > 0) {
                    return true;
                }
            }
            return false;
            """,

            # Có element với position fixed/absolute hiển thị
            """
            const modals = document.querySelectorAll('[class*="modal"], [class*="popup"], [role="dialog"]');
            for (let modal of modals) {
                const style = window.getComputedStyle(modal);
                if ((style.position === 'fixed' || style.position === 'absolute') && 
                    style.display !== 'none' && 
                    style.visibility !== 'hidden' && 
                    modal.offsetWidth > 0 && modal.offsetHeight > 0) {
                    return true;
                }
            }
            return false;
            """
        ]

        popup_detected = False

        for script in popup_indicators:
            # Kiểm tra timeout
            if (time.time() - start_time) > timeout:
                logger.debug(f"Timeout {timeout}s trong smart detection")
                break

            try:
                result = driver.execute_script(script)
                if result:
                    logger.info("Phát hiện popup bằng JavaScript detection")
                    popup_detected = True
                    break
            except Exception as e:
                logger.debug(f"JS detection script failed: {e}")
                continue

        return popup_detected

    except Exception as e:
        logger.error(f"Lỗi trong smart popup detection: {e}")
        return False


def comprehensive_popup_handler(driver, max_time: int = 15) -> bool:
    """
    Xử lý toàn diện tất cả loại popup có thể xuất hiện - có timeout cứng
    """
    try:
        logger.info("Bắt đầu xử lý popup toàn diện...")
        start_time = time.time()

        popup_handled = False
        max_attempts = 3

        for attempt in range(max_attempts):
            # Kiểm tra timeout cứng
            if (time.time() - start_time) > max_time:
                logger.warning(f"Timeout {max_time}s - dừng xử lý popup")
                break

            logger.debug(f"Lần thử {attempt + 1}/{max_attempts}")

            # Chờ một chút để popup có thể xuất hiện
            time.sleep(0.5)

            try:
                # Phát hiện popup thông minh với timeout
                if smart_popup_detection(driver):
                    logger.info("Smart detection phát hiện popup")

                # Xử lý popup chung với timeout ngắn
                if handle_popup(driver):
                    popup_handled = True
                    logger.info("Đã xử lý popup chung")

                # Xử lý popup đặc thù Shopee với timeout ngắn
                if handle_shopee_specific_popups(driver):
                    popup_handled = True
                    logger.info("Đã xử lý popup đặc thù Shopee")

                # Nếu không có popup nào được xử lý trong lần này, break
                current_handled = popup_handled
                if not current_handled and attempt > 0:  # Sau lần đầu
                    break

            except Exception as attempt_error:
                logger.warning(f"Lỗi trong attempt {attempt + 1}: {attempt_error}")
                continue

        elapsed = time.time() - start_time
        logger.info(f"Hoàn thành xử lý popup toàn diện trong {elapsed:.1f}s")
        return popup_handled

    except Exception as e:
        logger.error(f"Lỗi trong comprehensive popup handler: {e}")
        return False


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

                # Xử lý popup toàn diện
                comprehensive_popup_handler(driver)

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
