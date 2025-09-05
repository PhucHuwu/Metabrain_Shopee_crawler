#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để kiểm tra và xử lý popup Shopee
"""

import logging
import time
from services.shopee_service import ShopeeService
from config.config import SELENIUM_CONFIG, SHOPEE_CONFIG

# Setup logging chỉ INFO level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def test_popup_handling():
    """
    Test xử lý popup Shopee
    """
    print("=== BẮT ĐẦU TEST XỬ LÝ POPUP ===")

    # Tạo config
    config = {
        'selenium': SELENIUM_CONFIG,
        'shopee': SHOPEE_CONFIG
    }

    # Khởi tạo service
    service = ShopeeService(config)

    try:
        print("1. Đang setup driver...")
        if not service.setup_driver(0):
            print("❌ Không thể setup driver")
            return False

        print("2. Đang truy cập Shopee...")
        if not service.access_shopee():
            print("❌ Không thể truy cập Shopee")
            return False

        print("3. Popup đã được xử lý trong quá trình access_shopee()")
        print("4. Chờ 3 giây để quan sát...")
        time.sleep(3)

        print("5. Test thêm popup handler một lần nữa...")
        from utils.selenium_utils import comprehensive_popup_handler

        if comprehensive_popup_handler(service.driver):
            print("✅ Đã xử lý thêm popup")
        else:
            print("ℹ️  Không có popup nào cần xử lý thêm")

        print("✅ Test hoàn tất thành công!")
        return True

    except Exception as e:
        print(f"❌ Lỗi trong quá trình test: {e}")
        return False

    finally:
        print("6. Đang cleanup...")
        service.cleanup()
        print("=== KẾT THÚC TEST ===")


if __name__ == "__main__":
    test_popup_handling()
