import undetected_chromedriver as uc
import json
import threading
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import re
import logging
from product_url_extractor import extract_shopee_products

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

driver_lock = threading.Lock()


def setup_driver(idx):
    options = uc.ChromeOptions()
    profile_directory = f"Profile_{idx}"

    if not os.path.exists(profile_directory):
        os.makedirs(profile_directory)

    options.user_data_dir = profile_directory
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    try:
        with driver_lock:
            driver = uc.Chrome(options=options)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
        return driver
    except Exception as e:
        logger.error(f"Khong the khoi tao driver {idx}: {e}")
        time.sleep(180)
        return None


def safe_find_element(driver, selectors, timeout=10):
    for selector_type, selector_value in selectors:
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((selector_type, selector_value))
            )
            logger.debug(f"Tìm thấy element với selector: {selector_value}")
            return element
        except TimeoutException:
            logger.debug(f"Không tìm thấy element với selector: {selector_value}")
            continue
        except Exception as e:
            logger.debug(f"Lỗi khi tìm element {selector_value}: {e}")
            continue
    return None


def safe_find_elements(driver, selectors, timeout=10):
    for selector_type, selector_value in selectors:
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((selector_type, selector_value))
            )
            elements = driver.find_elements(selector_type, selector_value)
            if elements:
                logger.debug(f"Tìm thấy {len(elements)} elements với selector: {selector_value}")
                return elements
        except TimeoutException:
            logger.debug(f"Không tìm thấy elements với selector: {selector_value}")
            continue
        except Exception as e:
            logger.debug(f"Lỗi khi tìm elements {selector_value}: {e}")
            continue
    return []


def get_product_hrefs_from_recommend(driver):
    product_hrefs = []

    recommend_selectors = [
        (By.CLASS_NAME, "container.ofs-recommend-page"),
        (By.CSS_SELECTOR, "[role='main']"),
        (By.CSS_SELECTOR, "div[class*='container'][class*='recommend']"),
        (By.CSS_SELECTOR, "div[class*='ofs-recommend']"),
        (By.TAG_NAME, "main")
    ]

    recommend_container = safe_find_element(driver, recommend_selectors, timeout=15)
    if not recommend_container:
        logger.warning("Không tìm thấy recommend container")
        return product_hrefs

    logger.info("Đã tìm thấy recommend container")

    product_link_selectors = [
        (By.CSS_SELECTOR, "a[href*='/product/']"),
        (By.CSS_SELECTOR, "a[href*='-i.']"),
        (By.XPATH, "//a[contains(@href, '/product/') or contains(@href, '-i.')]"),
        (By.CSS_SELECTOR, "[class*='shopee_ic'] a"),
        (By.CSS_SELECTOR, "div[class*='content'] a[href]"),
        (By.CSS_SELECTOR, "a[data-sqe*='name']"),
        (By.CSS_SELECTOR, "a[href][class*='flex']")
    ]

    for selector_type, selector_value in product_link_selectors:
        try:
            links = recommend_container.find_elements(selector_type, selector_value)
            if links:
                logger.info(f"Tìm thấy {len(links)} product links với selector: {selector_value}")

                for link in links:
                    try:
                        href = link.get_attribute('href')
                        if href and ('/product/' in href or '-i.' in href):
                            clean_href = href.split('?')[0]
                            if clean_href not in product_hrefs:
                                product_hrefs.append(clean_href)
                                logger.debug(f"Thêm product href: {clean_href}")
                    except Exception as e:
                        logger.debug(f"Lỗi khi lấy href: {e}")
                        continue

                if product_hrefs:
                    break

        except Exception as e:
            logger.debug(f"Lỗi khi tìm links với {selector_value}: {e}")
            continue

    if not product_hrefs:
        logger.info("Fallback: Quét toàn bộ trang tìm product links")
        try:
            all_links = driver.find_elements(By.TAG_NAME, "a")
            for link in all_links:
                try:
                    href = link.get_attribute('href')
                    if href and ('/product/' in href or '-i.' in href):
                        clean_href = href.split('?')[0]
                        if clean_href not in product_hrefs:
                            product_hrefs.append(clean_href)
                except:
                    continue
        except Exception as e:
            logger.error(f"Lỗi khi quét fallback: {e}")

    logger.info(f"Tổng cộng tìm thấy {len(product_hrefs)} product hrefs")
    return product_hrefs


def extract_product_ids_v2(driver, category_url):
    try:
        logger.info(f"Truy cập category URL: {category_url}")
        driver.get(category_url)

        time.sleep(3)

        products = extract_shopee_products(driver, scroll_for_more=True)

        if products:
            logger.info(f"Extract được {len(products)} sản phẩm từ {category_url}")
        else:
            logger.warning(f"Không extract được sản phẩm nào từ {category_url}")

        return products

    except Exception as e:
        logger.error(f"Lỗi khi extract products từ {category_url}: {e}")
        return []


def extract_product_ids(driver, category_url):
    try:
        logger.info(f"Truy cập category URL: {category_url}")
        driver.get(category_url)

        time.sleep(3)

        product_hrefs = get_product_hrefs_from_recommend(driver)

        if not product_hrefs:
            logger.warning("Không tìm thấy product hrefs nào")
            return []

        product_ids = []
        for href in product_hrefs:
            try:
                match = re.search(r'-i\.(\d+)\.(\d+)', href)
                if match:
                    shop_id, product_id = match.groups()
                    product_ids.append({
                        'product_id': product_id,
                        'shop_id': shop_id,
                        'href': href
                    })
            except Exception as e:
                logger.debug(f"Lỗi khi extract ID từ href {href}: {e}")
                continue

        logger.info(f"Extract được {len(product_ids)} product IDs")
        return product_ids

    except Exception as e:
        logger.error(f"Lỗi khi extract product IDs từ {category_url}: {e}")
        return []


def save_product_data(product_data, filename="product_hrefs.json"):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Đã lưu {len(product_data)} sản phẩm vào {filename}")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi lưu file {filename}: {e}")
        return False


def main():
    try:
        with open('category_hrefs.json', 'r', encoding='utf-8') as f:
            category_data = json.load(f)
    except FileNotFoundError:
        logger.error("Không tìm thấy file category_hrefs.json")
        return
    except Exception as e:
        logger.error(f"Lỗi khi đọc category file: {e}")
        return

    if isinstance(category_data, dict) and 'category_hrefs' in category_data:
        categories = category_data['category_hrefs']
    elif isinstance(category_data, list):
        categories = category_data
    else:
        logger.error("Định dạng file category_hrefs.json không đúng")
        return

    driver = setup_driver(0)
    if not driver:
        logger.error("Không thể khởi tạo driver")
        return

    all_products = []

    try:
        test_categories = categories[:3] if len(categories) > 3 else categories

        for i, category_url in enumerate(test_categories):
            try:
                category_name = category_url.split('/mall/')[-1].split('-cat.')[0].replace('%', ' ')
            except:
                category_name = f"Category_{i+1}"

            if not category_url:
                continue

            logger.info(f"Đang crawl category: {category_name}")
            logger.info(f"URL: {category_url}")

            products = extract_product_ids_v2(driver, category_url)

            if products:
                for product in products:
                    product['category'] = category_name
                    product['category_url'] = category_url

                all_products.extend(products)
                logger.info(f"Đã lấy được {len(products)} sản phẩm từ {category_name}")
            else:
                logger.warning(f"Không lấy được sản phẩm nào từ {category_name}")

            time.sleep(2)

    except Exception as e:
        logger.error(f"Lỗi trong quá trình crawl: {e}")

    finally:
        if all_products:
            save_product_data(all_products)
            logger.info(f"Hoàn thành! Tổng cộng {len(all_products)} sản phẩm")

        driver.quit()


if __name__ == "__main__":
    main()
