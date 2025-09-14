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


def products_chunking(file_path: str | Path | None = None, num_threads: int | None = None):
    try:
        base = Path(__file__).parent
        products_dir = Path(file_path) if file_path else base / 'products'

        if not products_dir.exists() or not products_dir.is_dir():
            logger.error(f'Thư mục products không tồn tại: {products_dir}')
            return []

        json_files = sorted([p for p in products_dir.iterdir() if p.is_file() and p.suffix.lower() == '.json'])
        if not json_files:
            logger.warning(f'Không tìm thấy file json trong thư mục: {products_dir}')
            return []

        file_groups: list[tuple[Path, list[str]]] = []
        for fp in json_files:
            try:
                with fp.open('r', encoding='utf-8') as f:
                    data = json.load(f)

                hrefs: list[str] = []
                if isinstance(data, list):
                    for item in data:
                        try:
                            if isinstance(item, dict) and 'href' in item:
                                href = item.get('href')
                                if href:
                                    hrefs.append(href)
                        except Exception:
                            logger.debug(f'Lỗi khi đọc item trong {fp}')
                else:
                    logger.debug(f'File json không phải list, bỏ qua: {fp}')

                if hrefs:
                    file_groups.append((fp, hrefs))
                else:
                    logger.debug(f'Không tìm thấy href trong file: {fp}')
            except Exception as e:
                logger.exception(f'Lỗi khi đọc file products {fp}: {e}')

        if not file_groups:
            logger.warning('Không tìm thấy href nào trong các file products')
            return []

        if num_threads is None:
            num_threads = 1

        try:
            nt = int(num_threads)
            if nt <= 0:
                nt = 1
        except Exception:
            nt = 1

        chunks: list[list[Path]] = [[] for _ in range(nt)]
        chunk_counts = [0] * nt

        file_groups_sorted = sorted(file_groups, key=lambda x: len(x[1]), reverse=True)

        for fp, hrefs in file_groups_sorted:
            idx_min = int(min(range(nt), key=lambda i: chunk_counts[i]))
            chunks[idx_min].append(fp)
            chunk_counts[idx_min] += len(hrefs)

        return chunks
    except Exception as e:
        logger.exception(f'Lỗi không mong muốn trong products_chunking: {e}')
        return []


def get_infor_shop(driver) -> list:
    # chưa làm gì cả
    return []


def read_hrefs_from_file(fp: Path) -> tuple[str, list[str]]:
    try:
        with fp.open('r', encoding='utf-8') as f:
            data = json.load(f)

        hrefs: list[str] = []
        if isinstance(data, list):
            for item in data:
                try:
                    if isinstance(item, dict) and 'href' in item:
                        href = item.get('href')
                        if href:
                            hrefs.append(href)
                except Exception:
                    logger.debug(f'Lỗi khi đọc item trong {fp}')
        else:
            logger.debug(f'File json không phải list: {fp}')

        category_name = fp.stem
        return category_name, hrefs
    except Exception as e:
        logger.exception(f'Lỗi khi đọc file {fp}: {e}')
        return fp.stem, []


def get_shop_sell_product(thread_idx, products):
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
    position_x = thread_idx * window_width // 5
    # position_x = thread_idx * window_width # for testing
    position_y = 0

    driver.set_window_size(window_width, window_height)
    driver.set_window_position(position_x, position_y)

    driver.execute_script("document.body.style.zoom='100%'")

    for fp in products:
        category_name, hrefs = read_hrefs_from_file(Path(fp))
        logger.info(f"[Thread {thread_idx}] Xử lý category '{category_name}' với {len(hrefs)} sản phẩm")

        for product in hrefs:
            try:
                driver.get(product)
                load_cookies_to_driver(driver)
                time.sleep(3)
                driver.refresh()
                driver.execute_script("document.body.style.zoom='25%'")

                random_sleep()
                hover_element(driver, driver.find_element('tag name', 'body'))
                random_scroll(driver)

                shops = get_infor_shop(driver)
                logger.info(f"[Thread {thread_idx}] Category '{category_name}' - Lấy được {len(shops)} shop từ sản phẩm.")

                random_sleep()
                hover_element(driver, driver.find_element('tag name', 'body'))
                random_scroll(driver)
            except Exception as e:
                logger.exception(f"[Thread {thread_idx}] Lỗi khi xử lý sản phẩm {product}: {e}")


if __name__ == '__main__':
    NUM_THREADS = 5
    list_products = products_chunking(num_threads=NUM_THREADS)

    threads = []

    for idx, chunk_hrefs in enumerate(list_products):
        thread = threading.Thread(target=get_shop_sell_product, args=(idx, chunk_hrefs))
        thread.start()
        time.sleep(1)
        threads.append(thread)

    for thread in threads:
        thread.join()
