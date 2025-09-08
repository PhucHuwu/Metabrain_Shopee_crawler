# -*- coding: utf-8 -*-
import re
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger(__name__)


class ShopeeProductExtractor:

    def __init__(self, driver):
        self.driver = driver

    def get_all_product_links(self, timeout=10):
        product_links = []

        selectors = [
            "a[href*='/product/']",
            "a[href*='-i.']",
            "[data-sqe*='name'] a",
            "[data-testid*='product'] a",
            "div[class*='grid'] a[href]",
            "div[class*='item'] a[href]",
            "[class*='shopee'] a[href*='-i.']",
            "[class*='product'] a[href]",
            "a[href][class*='flex']",
            "a[href][role='link']"
        ]

        for selector in selectors:
            try:
                links = self.driver.find_elements(By.CSS_SELECTOR, selector)

                for link in links:
                    try:
                        href = link.get_attribute('href')
                        if self._is_valid_product_url(href):
                            clean_url = self._clean_url(href)
                            if clean_url not in product_links:
                                product_links.append(clean_url)
                    except Exception as e:
                        logger.debug(f"Lỗi khi lấy href: {e}")
                        continue

                if product_links:
                    logger.info(f"Tìm thấy {len(product_links)} links với selector: {selector}")
                    break

            except Exception as e:
                logger.debug(f"Lỗi với selector {selector}: {e}")
                continue

        return product_links

    def _is_valid_product_url(self, url):
        if not url:
            return False

        patterns = [
            r'/product/.*-i\.\d+\.\d+',
            r'shopee\.vn/.*-i\.\d+\.\d+',
            r'/.*-i\.\d+\.\d+$'
        ]

        for pattern in patterns:
            if re.search(pattern, url):
                return True
        return False

    def _clean_url(self, url):
        if '?' in url:
            url = url.split('?')[0]
        if '#' in url:
            url = url.split('#')[0]
        return url.strip()

    def extract_product_info(self, url):
        try:
            match = re.search(r'-i\.(\d+)\.(\d+)', url)
            if match:
                shop_id, product_id = match.groups()
                return {
                    'shop_id': shop_id,
                    'product_id': product_id,
                    'url': url
                }
        except Exception as e:
            logger.debug(f"Lỗi khi extract info từ URL {url}: {e}")

        return None

    def scroll_and_load_more(self, scroll_pause_time=2, max_scrolls=5):
        initial_count = len(self.driver.find_elements(By.CSS_SELECTOR, "a[href*='-i.']"))

        for i in range(max_scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            import time
            time.sleep(scroll_pause_time)

            new_count = len(self.driver.find_elements(By.CSS_SELECTOR, "a[href*='-i.']"))
            if new_count == initial_count:
                logger.info(f"Không có thêm content sau {i+1} lần scroll")
                break
            else:
                logger.info(f"Load thêm {new_count - initial_count} items sau scroll {i+1}")
                initial_count = new_count

    def wait_for_products_load(self, timeout=15):
        selectors = [
            (By.CSS_SELECTOR, "a[href*='-i.']"),
            (By.CSS_SELECTOR, "[data-sqe*='name']"),
            (By.CSS_SELECTOR, "[class*='product']")
        ]

        for by, selector in selectors:
            try:
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, selector))
                )
                logger.info(f"Products đã load với selector: {selector}")
                return True
            except TimeoutException:
                logger.debug(f"Timeout chờ products load với selector: {selector}")
                continue

        logger.warning("Không thể xác nhận products đã load")
        return False


def extract_shopee_products(driver, scroll_for_more=True):
    extractor = ShopeeProductExtractor(driver)

    if not extractor.wait_for_products_load():
        logger.warning("Products có thể chưa load đầy đủ")

    if scroll_for_more:
        extractor.scroll_and_load_more()

    product_links = extractor.get_all_product_links()

    products = []
    for link in product_links:
        product_info = extractor.extract_product_info(link)
        if product_info:
            products.append(product_info)

    logger.info(f"Tổng cộng extract được {len(products)} sản phẩm")
    return products
