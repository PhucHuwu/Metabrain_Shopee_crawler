#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script debug để tìm popup elements trên Shopee
"""

import logging
import time
from selenium.webdriver.common.by import By
from services.shopee_service import ShopeeService
from config.config import SELENIUM_CONFIG, SHOPEE_CONFIG

# Setup logging
logging.basicConfig(level=logging.WARNING)  # Chỉ hiện warning và error


def find_popup_elements():
    """
    Tìm và liệt kê tất cả popup elements có thể có
    """
    config = {
        'selenium': SELENIUM_CONFIG,
        'shopee': SHOPEE_CONFIG
    }

    service = ShopeeService(config)

    try:
        print("=== KHỞI TẠO DRIVER ===")
        if not service.setup_driver(0):
            print("Không thể setup driver")
            return

        print("=== TRUY CẬP SHOPEE ===")
        # Truy cập nhưng không xử lý popup
        if service.driver:
            service.driver.get('https://shopee.vn/mall')
            time.sleep(3)  # Chờ popup xuất hiện

            print("=== TÌM POPUP ELEMENTS ===")

            # Tìm các elements có thể là popup
            potential_selectors = [
                "div[class*='modal']",
                "div[class*='popup']",
                "div[class*='dialog']",
                "div[class*='overlay']",
                "button[class*='close']",
                "div[role='dialog']",
                "div[aria-modal='true']",
                "[data-testid*='modal']",
                "[data-testid*='popup']",
                ".shopee-modal",
                ".shopee-popup",
                "[class*='age']",
                "[class*='location']",
                "[class*='permission']"
            ]

            found_elements = []

            for selector in potential_selectors:
                try:
                    elements = service.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"✅ Tìm thấy {len(elements)} element(s) với selector: {selector}")
                        for i, elem in enumerate(elements):
                            try:
                                text = elem.text[:100] if elem.text else ""
                                class_name = elem.get_attribute('class')
                                is_displayed = elem.is_displayed()
                                print(f"   - Element {i+1}: displayed={is_displayed}, class='{class_name}', text='{text}'")

                                if is_displayed:
                                    found_elements.append({
                                        'selector': selector,
                                        'element': elem,
                                        'text': text,
                                        'class': class_name
                                    })
                            except Exception as e:
                                print(f"   - Lỗi khi đọc element {i+1}: {e}")
                except Exception as e:
                    # Không hiển thị lỗi cho selector không tìm thấy
                    pass

            print(f"\n=== TỔNG KẾT: Tìm thấy {len(found_elements)} popup element(s) có thể tương tác ===")

            if found_elements:
                print("\n=== THỬ ĐÓNG POPUP ===")
                for item in found_elements:
                    try:
                        # Thử click để đóng
                        elem = item['element']
                        if elem.is_displayed() and elem.is_enabled():
                            elem.click()
                            print(f"✅ Đã click vào element: {item['selector']}")
                            time.sleep(1)
                    except Exception as e:
                        print(f"❌ Không thể click element {item['selector']}: {e}")

            # Chờ một chút để quan sát
            print("\n=== Chờ 5s để quan sát kết quả ===")
            time.sleep(5)

    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        service.cleanup()


if __name__ == "__main__":
    find_popup_elements()
