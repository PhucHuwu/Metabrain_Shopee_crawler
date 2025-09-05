#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để kiểm tra fake user agent có hoạt động không
"""

from utils.logger import get_logger
from utils.selenium_utils import get_random_user_agent, setup_robust_driver
from services.shopee_service import ShopeeService
import sys
import os
import time

# Thêm thư mục gốc vào path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


logger = get_logger(__name__)


def test_user_agent():
    """Test việc thay đổi user agent"""
    print("=" * 60)
    print("TEST FAKE USER AGENT")
    print("=" * 60)

    # Tạo driver đầu tiên
    print("1. Tạo driver với user agent ngẫu nhiên...")
    driver1 = setup_robust_driver(0)

    if not driver1:
        print("❌ Không thể tạo driver")
        return False

    try:
        # Lấy user agent hiện tại
        current_ua = driver1.execute_script("return navigator.userAgent;")
        print(f"User Agent ban đầu: {current_ua}")

        # Thay đổi user agent
        print("\n2. Thay đổi user agent...")
        new_ua = get_random_user_agent()
        print(f"User Agent mới: {new_ua}")

        # Cập nhật user agent bằng CDP
        driver1.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": new_ua
        })

        time.sleep(1)

        # Kiểm tra user agent sau khi thay đổi
        updated_ua = driver1.execute_script("return navigator.userAgent;")
        print(f"User Agent sau khi thay đổi: {updated_ua}")

        # Kiểm tra xem có thay đổi không
        if updated_ua == new_ua:
            print("✅ User Agent đã được thay đổi thành công!")
            return True
        else:
            print("❌ User Agent không được thay đổi!")
            return False

    except Exception as e:
        print(f"❌ Lỗi khi test: {e}")
        return False
    finally:
        try:
            driver1.quit()
        except:
            pass


def test_shopee_service_user_agent():
    """Test user agent trong ShopeeService"""
    print("\n" + "=" * 60)
    print("TEST USER AGENT TRONG SHOPEE SERVICE")
    print("=" * 60)

    try:
        # Import config theo cách main.py làm
        from config.config import get_config

        # Tạo config object giống main.py
        crawler_config = get_config('crawler')
        selenium_config = get_config('selenium')
        shopee_config = get_config('shopee')

        config = {
            'crawler': crawler_config,
            'selenium': selenium_config,
            'shopee': shopee_config
        }

        # Tạo service với config
        service = ShopeeService(config)

        # Khởi tạo driver
        print("1. Khởi tạo driver...")
        success = service.setup_driver()
        if not success:
            print("❌ Không thể khởi tạo driver")
            return False

        # Lấy user agent hiện tại
        current_ua = service.driver.execute_script("return navigator.userAgent;")
        print(f"User Agent ban đầu: {current_ua}")

        # Test method change_user_agent
        print("\n2. Gọi change_user_agent()...")
        service.change_user_agent()

        time.sleep(1)

        # Kiểm tra user agent sau khi thay đổi
        updated_ua = service.driver.execute_script("return navigator.userAgent;")
        print(f"User Agent sau khi thay đổi: {updated_ua}")

        # Kiểm tra xem có khác nhau không
        if updated_ua != current_ua:
            print("✅ ShopeeService.change_user_agent() hoạt động thành công!")
            return True
        else:
            print("⚠️ User Agent không thay đổi hoặc giống như trước")
            return False

    except Exception as e:
        print(f"❌ Lỗi khi test ShopeeService: {e}")
        return False
    finally:
        try:
            if 'service' in locals() and hasattr(service, 'driver') and service.driver:
                service.driver.quit()
        except:
            pass


if __name__ == "__main__":
    try:
        print("Bắt đầu test fake user agent...")

        # Test 1: Test cơ bản
        result1 = test_user_agent()

        # Test 2: Test trong service
        result2 = test_shopee_service_user_agent()

        print("\n" + "=" * 60)
        print("KẾT QUẢ TEST")
        print("=" * 60)
        print(f"Test cơ bản: {'✅ PASS' if result1 else '❌ FAIL'}")
        print(f"Test service: {'✅ PASS' if result2 else '❌ FAIL'}")

        if result1 and result2:
            print("\n🎉 Tất cả test đều PASS! Fake user agent hoạt động tốt!")
        else:
            print("\n⚠️ Một số test FAIL! Cần kiểm tra lại.")

    except Exception as e:
        print(f"❌ Lỗi chung khi chạy test: {e}")

    input("\nNhấn Enter để thoát...")
