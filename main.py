#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shopee + Google Maps Crawler - Entry Point
Hệ thống cào dữ liệu thương mại điện tử Việt Nam
"""

from services.shopee_service import ShopeeService
from utils.logger import setup_logger
from config.config import get_config
import sys
import os
import logging
from datetime import datetime

# Thêm thư mục gốc vào Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def main():
    """
    Entry point chính của ứng dụng
    """
    print("=" * 60)
    print("SHOPEE + GOOGLE MAPS CRAWLER")
    print("Hệ thống cào dữ liệu thương mại điện tử Việt Nam")
    print("=" * 60)
    
    # Thiết lập logging
    logging_config = get_config('logging')
    logger = setup_logger('main', logging_config)
    logger.info("Khởi động hệ thống crawler...")    # Load các cấu hình
    crawler_config = get_config('crawler')
    selenium_config = get_config('selenium')
    shopee_config = get_config('shopee')

    # Tạo cấu hình tổng hợp
    config = {
        'crawler': crawler_config,
        'selenium': selenium_config,
        'shopee': shopee_config
    }

    # Khởi tạo Shopee service
    logger.info("Khởi tạo Shopee service...")
    shopee_service = ShopeeService(config)
    
    try:
        # Bước 1: Khởi tạo driver
        logger.info("Bước 1: Khởi tạo Chrome driver...")
        if not shopee_service.setup_driver(profile_idx=0):
            logger.error("Không thể khởi tạo driver. Thoát chương trình.")
            return False
        
        # Bước 2: Truy cập vào trang Shopee
        logger.info("Bước 2: Truy cập vào trang Shopee...")
        if not shopee_service.access_shopee(load_saved_cookies=False):  # Không load cookies lần đầu
            logger.error("Không thể truy cập Shopee. Thoát chương trình.")
            return False
        
        logger.info("Đã khởi tạo driver và truy cập Shopee thành công!")
        logger.info("Sẵn sàng cho các bước crawl tiếp theo...")        # Giữ driver mở để kiểm tra (có thể bỏ sau)
        input("⏸️  Nhấn Enter để đóng driver và thoát...")

        return True

    except KeyboardInterrupt:
        logger.info("Người dùng dừng chương trình")
        return False
        
    except Exception as e:
        logger.error(f"Lỗi không mong muốn: {e}")
        return False
        
    finally:
        # Dọn dẹp resources
        logger.info("Dọn dẹp resources...")
        shopee_service.cleanup()
        logger.info("Hoàn tất!")
if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
