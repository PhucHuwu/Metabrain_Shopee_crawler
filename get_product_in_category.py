from pathlib import Path
import json
import logging
import threading
import time

try:
    import config
except Exception:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def category_chunking(chunk_size: int = 5, file_path: str | Path | None = None):
    try:
        base = Path(__file__).parent
        fp = Path(file_path) if file_path else base / 'data' / 'category_hrefs.json'

        with fp.open('r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, dict):
            if 'category_hrefs' in data and isinstance(data['category_hrefs'], list):
                categories = data['category_hrefs']

        return [categories[i:i + chunk_size] for i in range(0, len(categories), chunk_size)]

    except FileNotFoundError:
        logger.error(f'Không tìm thấy file JSON: {fp}')
        return []
    except Exception as e:
        logger.exception(f'Lỗi không mong muốn trong category_chunking: {e}')
        return []


def get_infor_product(driver, *, container_selector: str | None = None, item_selector: str | None = None) -> list:
    results = []
    try:
        from selenium.common.exceptions import NoSuchElementException
        from selenium.webdriver.common.by import By

        try:
            from config import SELECTORS
        except Exception:
            SELECTORS = {}

        container_xpath = SELECTORS.get('product_list_container_xpath')
        container_css = container_selector or SELECTORS.get('product_list_container_css', 'div.ofs-recommend-page')

        containers = []
        if container_xpath:
            try:
                containers = driver.find_elements(By.XPATH, container_xpath)
            except Exception:
                containers = []

        if not containers and container_css:
            containers = driver.find_elements(By.CSS_SELECTOR, container_css)

        if not containers:
            logger.debug(f'Không tìm thấy container với selector (xpath:{container_xpath} css:{container_css})')
            return results

        for cont in containers:
            item_xpath = SELECTORS.get('product_item_xpath')
            item_css = item_selector or SELECTORS.get('product_item_css', 'a.contents')

            items = []
            if item_xpath:
                try:
                    items = cont.find_elements(By.XPATH, item_xpath)
                except Exception:
                    items = []

            if not items and item_css:
                items = cont.find_elements(By.CSS_SELECTOR, item_css)
            for item in items:
                href = None
                name = None
                try:
                    href = item.get_attribute('href')
                except Exception:
                    href = None

                try:
                    text = item.text.strip()
                    if text:
                        name = text
                except Exception:
                    name = None

                if not name:
                    try:
                        sub = item.find_element(By.CSS_SELECTOR, "div[class*='line-clamp']")
                        t = sub.text.strip()
                        if t:
                            name = t
                    except NoSuchElementException:
                        pass
                    except Exception:
                        pass

                if not name:
                    try:
                        img = item.find_element(By.CSS_SELECTOR, 'img')
                        alt = img.get_attribute('alt')
                        if alt and alt.strip():
                            name = alt.strip()
                    except NoSuchElementException:
                        pass
                    except Exception:
                        pass

                if not name:
                    try:
                        title = item.get_attribute('title')
                        if title and title.strip():
                            name = title.strip()
                    except Exception:
                        pass

                results.append({'href': href, 'name': name})

    except Exception as e:
        logger.exception(f'Lỗi khi lấy thông tin sản phẩm: {e}')

    return results


def get_product_in_category(thread_idx, categories, page_num: int = 5):
    from funcs.setup_driver import setup_driver
    from funcs.fake_agent import random_sleep, hover_element, random_scroll
    from funcs.load_cookies_to_driver import load_cookies_to_driver

    driver = None
    while driver is None:
        driver = setup_driver(profile_idx=thread_idx)

    screen_width = driver.execute_script("return window.screen.availWidth;")
    screen_height = driver.execute_script("return window.screen.availHeight;")
    window_width = screen_width // 5
    window_height = screen_height // 2
    position_x = thread_idx * window_width // 20
    position_y = 0

    driver.set_window_size(window_width, window_height)
    driver.set_window_position(position_x, position_y)

    driver.execute_script("document.body.style.zoom='100%'")

    for cat in categories:
        logger.info(f"[Thread {thread_idx}] Bắt đầu lấy sản phẩm trong category: {cat}")

        for i in range(1, page_num + 1):
            driver.get(f"{cat}/popular?pageNumber={i}")
            load_cookies_to_driver(driver)
            time.sleep(3)
            driver.refresh()
            driver.execute_script("document.body.style.zoom='25%'")

            random_sleep()
            hover_element(driver, driver.find_element('tag name', 'body'))
            random_scroll(driver, min_scrolls=3, max_scrolls=6)

            products = get_infor_product(driver)
            logger.info(f"[Thread {thread_idx}] Category: {cat} - Page {i} - Found {len(products)} products")

            random_sleep()
            hover_element(driver, driver.find_element('tag name', 'body'))
            random_scroll(driver, min_scrolls=3, max_scrolls=6)


if __name__ == '__main__':
    list_categories = category_chunking()
    threads = []

    for idx, cat in enumerate(list_categories):
        thread = threading.Thread(target=get_product_in_category, args=(idx, cat, 5))
        thread.start()
        time.sleep(1)
        threads.append(thread)

    for thread in threads:
        thread.join()
