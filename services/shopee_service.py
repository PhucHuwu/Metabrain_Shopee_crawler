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
    setup_robust_driver,
    wait_for_page_ready,
    save_cookies,
    load_cookies,
    handle_popup,
    get_random_delay
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

    def setup_driver(self, profile_idx: int = 0):
        """
        Khởi tạo undetected Chrome driver với profile riêng
        """
        try:
            with self.lock:
                logger.info(f"Đang khởi tạo driver cho thread {profile_idx}")
                self.driver = setup_robust_driver(profile_idx, self.config.get('selenium', {}))

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
        Truy cập vào trang chủ Shopee
        """
        try:
            if not self.driver:
                logger.error("Driver chưa được khởi tạo")
                return False

            shopee_url = self.config.get('shopee', {}).get('BASE_URL', 'https://shopee.vn')
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
            
            # Xử lý popup nếu có
            logger.info("Đang kiểm tra popup...")
            if handle_popup(self.driver):
                logger.info("Đã đóng popup")
            else:
                logger.info("Không có popup nào")
            
            # Delay ngẫu nhiên để tránh detection
            delay = get_random_delay()
            logger.info(f"Delay {delay:.1f}s để tránh detection...")
            time.sleep(delay)
            
            logger.info("Đã truy cập thành công vào Shopee")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi truy cập Shopee: {e}")
            return False

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
