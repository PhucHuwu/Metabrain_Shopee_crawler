from pathlib import Path
import json
import logging
import threading
import time
import re
import urllib.parse

try:
    import config
except Exception:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def category_chunking(chunk_size: int = 5, file_path: str | Path | None = None):
    try:
        base = Path(__file__).parent
        fp = Path(file_path) if file_path else base / 'categories' / 'category_hrefs.json'

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


def get_infor_product(driver) -> list:
    from selenium.webdriver.common.by import By

    results: list = []

    try:
        container = driver.find_element(By.XPATH, "//div[contains(@class,'ofs-recommend-page')]")
    except Exception as e:
        logger.warning(f"Không tìm thấy container 'ofs-recommend-page': {e}")
        return results

    try:
        anchors = container.find_elements(By.XPATH, ".//a[@href][.//img or .//div]")
    except Exception as e:
        logger.debug(f"Lỗi khi tìm anchors trong container: {e}")
        return results

    for a in anchors:
        try:
            href = a.get_attribute('href') or ''

            name = ''
            try:
                img = a.find_element(By.XPATH, ".//img[@alt]")
                name = (img.get_attribute('alt') or '').strip()
            except Exception:
                name = ''

            if not name:
                try:
                    name = (a.text or '').strip()
                except Exception:
                    name = ''

            if not name:
                try:
                    div = a.find_element(By.XPATH, ".//div[normalize-space(text())!='']")
                    name = (div.text or '').strip()
                except Exception:
                    name = ''

            results.append({'href': href, 'name': name})
        except Exception as e:
            logger.debug(f"Lỗi khi xử lý 1 product anchor: {e}")
            continue

    return results


def extract_category_name_from_url(url: str) -> str:
    try:
        seg = urllib.parse.unquote(str(url).rstrip('/').split('/')[-1])
        name = re.sub(r'-cat\.\d+$', '', seg)
        name = name.replace('-', ' ').strip()
        return name or seg
    except Exception as e:
        logger.debug(f"Lỗi khi trích tên category từ url {url}: {e}")
        return 'category'


def sanitize_filename(name: str, max_len: int = 200) -> str:
    try:
        invalid = '<>:"/\\|?*\n\r\t'
        cleaned = ''.join('_' if c in invalid else c for c in str(name))
        cleaned = cleaned.strip()
        if len(cleaned) > max_len:
            cleaned = cleaned[:max_len]
        cleaned = cleaned.rstrip(' .')
        return cleaned or 'category'
    except Exception as e:
        logger.debug(f"Lỗi khi sanitize filename '{name}': {e}")
        return 'category'


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
    position_x = thread_idx * window_width  # thread_idx * window_width // 5
    position_y = 0

    driver.set_window_size(window_width, window_height)
    driver.set_window_position(position_x, position_y)

    driver.execute_script("document.body.style.zoom='100%'")

    for cat in categories:
        logger.info(f"[Thread {thread_idx}] Bắt đầu lấy sản phẩm trong category: {cat}")

        cat_name = extract_category_name_from_url(cat)
        safe_name = sanitize_filename(cat_name)
        out_dir = Path(__file__).parent / 'products'
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.debug(f"Không thể tạo thư mục products: {e}")

        out_file = out_dir / f"{safe_name}.json"

        products_all: list = []

        for i in range(1, page_num + 1):
            driver.get(f"{cat}/popular?pageNumber={i}")
            load_cookies_to_driver(driver)
            time.sleep(3)
            driver.refresh()
            driver.execute_script("document.body.style.zoom='25%'")

            random_sleep()
            hover_element(driver, driver.find_element('tag name', 'body'))
            random_scroll(driver)

            products = get_infor_product(driver)
            logger.info(f"[Thread {thread_idx}] Category: {cat} - Page {i} - Found {len(products)} products")

            try:
                if products:
                    products_all.extend(products)
            except Exception as e:
                logger.debug(f"Lỗi khi gộp sản phẩm vào list tổng: {e}")

            random_sleep()
            hover_element(driver, driver.find_element('tag name', 'body'))
            random_scroll(driver)

        try:
            with out_file.open('w', encoding='utf-8') as f:
                json.dump(products_all, f, ensure_ascii=False, indent=2)
            logger.info(f"[Thread {thread_idx}] Đã lưu {len(products_all)} products vào {out_file}")
        except Exception as e:
            logger.exception(f"Lỗi khi lưu file {out_file}: {e}")


if __name__ == '__main__':
    list_categories = category_chunking()
    threads = []

    for idx, cat in enumerate(list_categories):
        thread = threading.Thread(target=get_product_in_category, args=(idx, cat, 1))
        thread.start()
        time.sleep(1)
        threads.append(thread)

    for thread in threads:
        thread.join()
