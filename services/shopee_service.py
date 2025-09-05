#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service cào dữ liệu Shopee
Xử lý việc crawl thông tin cửa hàng và sản phẩm từ Shopee
"""

import logging
import time
import threading
from typing import List, Optional, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import utils từ project
from utils.selenium_utils import (
    create_driver_with_lock,
    wait_for_page_ready,
    save_cookies,
    load_cookies,
    handle_popup,
    comprehensive_popup_handler,
    wait_and_handle_popup,
    smart_popup_detection,
    get_random_delay,
    get_random_user_agent,
    set_user_agent_for_driver,
    driver_lock
)

logger = logging.getLogger(__name__)


class ShopeeService:
    """
    Service chính để crawl dữ liệu từ Shopee
    """

    def __init__(self, config: Dict):
        """
        Khởi tạo Shopee service với cấu hình
        """
        self.config = config
        self.driver = None
        self.lock = threading.Lock()

    def change_user_agent(self) -> str:
        """
        Thay đổi user agent để tránh detection
        """
        try:
            if not self.driver:
                logger.warning("Driver không tồn tại, không thể thay đổi user agent")
                return None

            new_user_agent = set_user_agent_for_driver(self.driver)
            if new_user_agent:
                logger.info(f"Đã thay đổi User-Agent: {new_user_agent[:80]}...")
                return new_user_agent
            else:
                logger.warning("Không thể thay đổi user agent")
                return None
        except Exception as e:
            logger.error(f"Lỗi khi thay đổi user agent: {e}")
            return None

    def setup_driver(self, profile_idx: int = 0):
        """
        Khởi tạo undetected Chrome driver với profile riêng và thread-safe lock
        """
        try:
            logger.info(f"Đang khởi tạo driver cho thread {profile_idx}")

            # Sử dụng hàm mới với driver_lock
            self.driver = create_driver_with_lock(profile_idx, self.config.get('selenium', {}))

            if not self.driver:
                logger.error(f"Không thể khởi tạo driver cho profile {profile_idx}")
                return False

            logger.info(f"Đã khởi tạo thành công driver cho profile {profile_idx}")
            return True

        except Exception as e:
            logger.error(f"Lỗi khi setup driver: {e}")
            return False

    def access_shopee(self, load_saved_cookies: bool = True) -> bool:
        """
        Truy cập vào trang chủ Shopee với fake user agent
        """
        try:
            if not self.driver:
                logger.error("Driver chưa được khởi tạo")
                return False

            # Thay đổi user agent trước khi truy cập
            logger.info("Đang thay đổi User-Agent để tránh detection...")
            self.change_user_agent()

            shopee_url = self.config.get('shopee', {}).get('BASE_URL', 'https://shopee.vn/mall')
            logger.info(f"Đang truy cập vào {shopee_url}")

            # Truy cập trang chủ Shopee với timeout
            try:
                self.driver.set_page_load_timeout(20)  # Giảm timeout xuống
                self.driver.get(shopee_url)
                logger.info("Đã tải trang Shopee thành công")

            except Exception as load_error:
                logger.warning(f"Lỗi khi tải trang: {load_error}")
                # Thử lại với trang đơn giản hơn
                try:
                    logger.info("Thử truy cập trang đơn giản hơn...")
                    self.driver.get("https://google.com")
                    time.sleep(2)
                    self.driver.get(shopee_url)
                    logger.info("Đã tải trang Shopee thành công (lần 2)")
                except Exception as retry_error:
                    logger.error(f"Vẫn không thể tải trang: {retry_error}")
                    return False

            # Chờ trang load hoàn tất
            logger.info("Đang chờ trang load hoàn tất...")
            if not wait_for_page_ready(self.driver, timeout=15):  # Giảm timeout
                logger.warning("Trang Shopee có thể chưa load hoàn tất")
            else:
                logger.info("Trang đã load hoàn tất")            # Load cookies đã lưu (nếu có)
            if load_saved_cookies:
                logger.info("Đang load cookies đã lưu...")
                if self.load_cookies("shopee_main"):
                    logger.info("Đã load cookies thành công")
                    # Refresh trang sau khi load cookies
                    try:
                        self.driver.refresh()
                        wait_for_page_ready(self.driver, timeout=10)
                        logger.info("Đã refresh trang với cookies")
                    except Exception as refresh_error:
                        logger.warning(f"Lỗi khi refresh: {refresh_error}")
                else:
                    logger.info("Không có cookies để load hoặc load không thành công")

            # Xử lý popup nếu có - sử dụng phương pháp đơn giản và nhanh
            logger.info("Đang kiểm tra và xử lý popup...")

            try:
                # Sử dụng comprehensive handler với timeout ngắn
                popup_handled = comprehensive_popup_handler(self.driver, max_time=10)
                if popup_handled:
                    logger.info("Đã xử lý popup thành công")
                else:
                    logger.info("Không có popup nào cần xử lý")

            except Exception as popup_error:
                logger.warning(f"Lỗi khi xử lý popup: {popup_error}")
                logger.info("Tiếp tục mà không xử lý popup")

            logger.info("Hoàn thành xử lý popup")

            # Delay ngẫu nhiên để tránh detection
            delay = get_random_delay()
            logger.info(f"Delay {delay:.1f}s để tránh detection...")
            time.sleep(delay)

            logger.info("Đã truy cập thành công vào Shopee")
            return True

        except Exception as e:
            logger.error(f"Lỗi khi truy cập Shopee: {e}")
            return False

    def get_category_links(self) -> List[Dict[str, str]]:
        """
        Lấy các đường dẫn category từ image carousel trên trang Shopee mall với fake user agent
        Returns: List of dict containing category info {"name": str, "href": str}
        """
        try:
            if not self.driver:
                logger.error("Driver chưa được khởi tạo")
                return []

            # Thay đổi user agent trước khi crawl category
            logger.info("Đang thay đổi User-Agent trước khi crawl category...")
            self.change_user_agent()

            logger.info("Đang tìm image carousel và lấy category links...")

            # Chờ carousel load
            time.sleep(2)

            # Danh sách các selector để tìm carousel
            carousel_selectors = [
                "ul.image-carousel__item-list",
                "ul[class*='image-carousel__item-list']",
                ".image-carousel__item-list",
                "[class*='image-carousel'] ul",
                ".carousel ul",
                "[data-testid*='carousel'] ul",
                "ul[class*='carousel']"
            ]

            carousel_element = None
            used_selector = None

            # Thử tìm carousel với các selector khác nhau
            for selector in carousel_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        # Lấy element đầu tiên có chứa links
                        for elem in elements:
                            links = elem.find_elements(By.TAG_NAME, "a")
                            if links:
                                carousel_element = elem
                                used_selector = selector
                                logger.info(f"Tìm thấy carousel với selector: {selector}")
                                break
                        if carousel_element:
                            break
                except Exception as e:
                    logger.debug(f"Lỗi khi tìm carousel với selector {selector}: {e}")
                    continue

            if not carousel_element:
                logger.warning("Không tìm thấy image carousel")
                return []

            # Lấy tất cả các link trong carousel
            category_links = []

            try:
                # Tìm tất cả các thẻ a trong carousel
                link_elements = carousel_element.find_elements(By.TAG_NAME, "a")
                logger.info(f"Tìm thấy {len(link_elements)} link trong carousel")

                for i, link_elem in enumerate(link_elements):
                    try:
                        href = link_elem.get_attribute('href')
                        if href and href.startswith('http'):
                            # Thử lấy tên category từ text hoặc title hoặc img alt
                            category_name = ""

                            # Thử lấy text của link
                            text = link_elem.text.strip()
                            if text:
                                category_name = text

                            # Nếu không có text, thử lấy từ title attribute
                            if not category_name:
                                title = link_elem.get_attribute('title')
                                if title:
                                    category_name = title.strip()

                            # Nếu vẫn không có, thử lấy alt text của image bên trong
                            if not category_name:
                                try:
                                    img = link_elem.find_element(By.TAG_NAME, "img")
                                    alt_text = img.get_attribute('alt')
                                    if alt_text:
                                        category_name = alt_text.strip()
                                except:
                                    pass

                            # Nếu vẫn không có tên, sử dụng index
                            if not category_name:
                                category_name = f"Category_{i+1}"

                            category_info = {
                                "name": category_name,
                                "href": href,
                                "index": i + 1
                            }

                            category_links.append(category_info)
                            logger.debug(f"Link {i+1}: {category_name} -> {href}")

                    except Exception as link_error:
                        logger.warning(f"Lỗi khi xử lý link {i+1}: {link_error}")
                        continue

                logger.info(f"Đã lấy thành công {len(category_links)} category links")

                # In ra danh sách category để kiểm tra
                if category_links:
                    logger.info("Danh sách categories tìm thấy:")
                    for cat in category_links:
                        logger.info(f"  - {cat['name']}: {cat['href']}")

                return category_links

            except Exception as extract_error:
                logger.error(f"Lỗi khi trích xuất links từ carousel: {extract_error}")
                return []

        except Exception as e:
            logger.error(f"Lỗi khi lấy category links: {e}")
            return []

    def search_shops(self, keyword: str, max_pages: int = 10) -> List[str]:
        """
        Tìm kiếm các cửa hàng theo từ khóa
        """
        # TODO: Implement shop search logic
        pass

    def get_shop_info(self, shop_url: str) -> Optional[Dict]:
        """
        Lấy thông tin chi tiết của cửa hàng
        """
        # TODO: Implement shop info extraction
        pass

    def get_shop_products(self, shop_url: str, max_products: int = 100) -> List[Dict]:
        """
        Lấy danh sách sản phẩm của cửa hàng
        """
        # TODO: Implement product list extraction
        pass

    def get_product_details(self, product_url: str) -> Optional[Dict]:
        """
        Lấy thông tin chi tiết của sản phẩm
        """
        # TODO: Implement product details extraction
        pass

    def safe_click_element(self, selectors: List[str], timeout: int = 10) -> bool:
        """
        Click element với nhiều selector fallback
        """
        # TODO: Implement safe element clicking
        pass

    def safe_get_text(self, selectors: List[str], default_value: str = "") -> str:
        """
        Lấy text với multiple fallback selectors
        """
        # TODO: Implement safe text extraction
        pass

    def wait_for_page_ready(self, timeout: int = 30) -> bool:
        """
        Chờ page load hoàn tất
        """
        # TODO: Implement page ready detection
        pass

    def save_cookies(self, profile_name: str):
        """
        Lưu cookies để sử dụng lại
        """
        try:
            if self.driver:
                save_cookies(self.driver, profile_name)
            else:
                logger.warning("Driver không tồn tại, không thể lưu cookies")
        except Exception as e:
            logger.error(f"Lỗi khi lưu cookies: {e}")

    def load_cookies(self, profile_name: str) -> bool:
        """
        Load cookies từ file
        """
        try:
            if self.driver:
                return load_cookies(self.driver, profile_name)
            else:
                logger.warning("Driver không tồn tại, không thể load cookies")
                return False
        except Exception as e:
            logger.error(f"Lỗi khi load cookies: {e}")
            return False

    def cleanup(self):
        """
        Dọn dẹp resources với xử lý lỗi tốt hơn
        """
        try:
            if self.driver:
                # Lưu cookies trước khi đóng
                try:
                    self.save_cookies("shopee_main")
                    logger.debug("Đã lưu cookies trước khi đóng")
                except Exception as cookie_error:
                    logger.warning(f"Không thể lưu cookies: {cookie_error}")

                # Đóng driver với multiple attempts
                self._safe_quit_driver()
                logger.info("Đã đóng driver và dọn dẹp resources")
            else:
                logger.debug("Driver không tồn tại, không cần cleanup")
        except Exception as e:
            logger.error(f"Lỗi khi cleanup: {e}")

    def _safe_quit_driver(self):
        """
        Đóng driver một cách an toàn với multiple attempts
        """
        if not self.driver:
            return

        attempts = 0
        max_attempts = 3

        while attempts < max_attempts:
            try:
                # Thử đóng tất cả cửa sổ trước
                try:
                    self.driver.close()
                    logger.debug("Đã đóng cửa sổ hiện tại")
                except:
                    pass

                # Thử quit driver
                self.driver.quit()
                logger.debug(f"Driver quit thành công (attempt {attempts + 1})")
                self.driver = None
                return

            except Exception as e:
                attempts += 1
                logger.debug(f"Attempt {attempts} quit driver thất bại: {e}")

                if attempts < max_attempts:
                    import time
                    time.sleep(0.5)  # Đợi ngắn trước khi thử lại
                else:
                    logger.warning(f"Không thể quit driver sau {max_attempts} attempts")
                    self.driver = None
