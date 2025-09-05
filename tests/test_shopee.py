#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để kiểm tra truy cập Shopee cụ thể
"""

from utils.selenium_utils import setup_robust_driver, wait_for_page_ready, handle_popup
from utils.logger import setup_logger
from config.config import get_config
import sys
import os
import logging
import time

# Thêm thư mục gốc vào Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_shopee_access():
    """
    Test function để truy cập Shopee
    """
    print("Test Shopee Access")

    # Thiết lập logging
    logging_config = get_config('logging')
    logger = setup_logger('test_shopee', logging_config)

    driver = None
    try:
        # Khởi tạo driver
        logger.info("Đang khởi tạo driver...")
        driver = setup_robust_driver(profile_idx=0)

        if not driver:
            logger.error("Không thể khởi tạo driver")
            return False

        logger.info("Driver đã khởi tạo thành công")

        # Test truy cập Shopee từng bước
        logger.info("Bước 1: Test kết nối cơ bản...")
        driver.set_page_load_timeout(15)

        # Trước tiên truy cập Google để chắc chắn kết nối OK
        logger.info("Kiểm tra kết nối với Google...")
        driver.get("https://www.google.com")
        logger.info(f"Google title: {driver.title}")

        time.sleep(2)

        # Bây giờ thử Shopee
        logger.info("Bước 2: Truy cập Shopee...")
        shopee_url = "https://shopee.vn/mall"

        try:
            driver.get(shopee_url)
            logger.info("Đã gửi request tới Shopee")

            # Chờ trang load
            logger.info("Chờ trang Shopee load...")
            time.sleep(5)  # Chờ cứng trước

            current_url = driver.current_url
            title = driver.title

            logger.info(f"URL hiện tại: {current_url}")
            logger.info(f"Title: {title}")

            # Kiểm tra xem có phải trang Shopee không
            if "shopee" in current_url.lower() or "shopee" in title.lower():
                logger.info("Đã truy cập thành công vào Shopee!")

                # Thử lấy một số thông tin từ trang
                try:
                    page_source_length = len(driver.page_source)
                    logger.info(f"Độ dài page source: {page_source_length} ký tự")

                    if page_source_length > 1000:
                        logger.info("Trang có nội dung phong phú")
                    else:
                        logger.warning("Trang có ít nội dung")

                except Exception as e:
                    logger.warning(f"Không lấy được thông tin trang: {e}")

                return True

            else:
                logger.warning("Không rõ có phải trang Shopee hay không")
                return False

        except Exception as load_error:
            logger.error(f"Lỗi khi load trang Shopee: {load_error}")
            return False

    except Exception as e:
        logger.error(f"Lỗi chung: {e}")
        return False

    finally:
        # Đợi user xem kết quả
        if driver:
            input("Nhấn Enter để đóng driver...")
            try:
                driver.quit()
                logger.info("Đã đóng driver")
            except:
                logger.warning("Có lỗi khi đóng driver")


if __name__ == "__main__":
    success = test_shopee_access()
    sys.exit(0 if success else 1)
