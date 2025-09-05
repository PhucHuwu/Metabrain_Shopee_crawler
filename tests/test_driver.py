#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để kiểm tra driver hoạt động
"""

from utils.selenium_utils import setup_robust_driver
from utils.logger import setup_logger
from config.config import get_config
import sys
import os
import logging

# Thêm thư mục gốc vào Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_driver():
    """
    Test function đơn giản để kiểm tra driver
    """
    print("Test Driver Initialization")

    # Thiết lập logging
    logging_config = get_config('logging')
    logger = setup_logger('test', logging_config)

    try:
        # Khởi tạo driver
        logger.info("Đang khởi tạo driver...")
        driver = setup_robust_driver(profile_idx=0)

        if not driver:
            logger.error("Không thể khởi tạo driver")
            return False
        
        logger.info("Driver đã khởi tạo thành công")
        
        # Test truy cập trang đơn giản
        logger.info("Đang test truy cập Google...")
        driver.set_page_load_timeout(10)
        driver.get("https://www.google.com")
        
        title = driver.title
        logger.info(f"Truy cập thành công! Title: {title}")        # Đợi user xem kết quả
        input("Nhấn Enter để đóng driver...")

        # Đóng driver
        driver.quit()
        logger.info("Đã đóng driver")
        
        return True
        
    except Exception as e:
        logger.error(f"Lỗi: {e}")
        return False
if __name__ == "__main__":
    success = test_driver()
    sys.exit(0 if success else 1)
