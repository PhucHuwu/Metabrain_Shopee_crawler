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


def products_chunking(chunk_size: int = 5, file_path: str | Path | None = None):
    try:
        base = Path(__file__).parent
        products_dir = Path(file_path) if file_path else base / 'products'

        if not products_dir.exists() or not products_dir.is_dir():
            logger.warning(f"Thư mục products không tồn tại: {products_dir}")
            return [[] for _ in range(chunk_size)]

        all_files = sorted([str(p.resolve()) for p in products_dir.iterdir() if p.is_file() and p.suffix.lower() == '.json'])

        if not all_files:
            return [[] for _ in range(chunk_size)]

        chunks = [[] for _ in range(chunk_size)]
        for idx, fp in enumerate(all_files):
            chunks[idx % chunk_size].append(fp)

        return chunks

    except Exception as e:
        logger.exception(f'Lỗi không mong muốn trong products_chunking: {e}')
        return []


def get_infor_shop(driver) -> list:
    # chưa làm gì cả
    return []


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

    for product in products:
        logger.info(f"[Thread {thread_idx}] Truy cập: {product}")

        driver.get(product)
        load_cookies_to_driver(driver)
        time.sleep(3)
        driver.refresh()
        driver.execute_script("document.body.style.zoom='25%'")

        random_sleep()
        hover_element(driver, driver.find_element('tag name', 'body'))
        random_scroll(driver)

        shops = get_infor_shop(driver)
        logger.info(f"[Thread {thread_idx}] Lấy được {len(shops)} shop từ sản phẩm.")

        random_sleep()
        hover_element(driver, driver.find_element('tag name', 'body'))
        random_scroll(driver)


if __name__ == '__main__':
    NUM_THREADS = 5

    # Mỗi chunk là danh sách file json (đường dẫn)
    list_product_chunks = products_chunking(chunk_size=NUM_THREADS)

    threads = []

    def read_products_from_files(file_paths: list[str]) -> list[str]:
        """Đọc các file json và trả về danh sách URL sản phẩm (mỗi file có thể chứa list hoặc dict of products)."""
        products = []
        for fp in file_paths:
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Giả sử file chứa list sản phẩm hoặc dict với key products
                if isinstance(data, list):
                    products.extend([str(x) for x in data])
                elif isinstance(data, dict):
                    # nếu là dict có key products
                    if 'products' in data and isinstance(data['products'], list):
                        products.extend([str(x) for x in data['products']])
                    else:
                        # flatten values nếu có strings
                        for v in data.values():
                            if isinstance(v, str):
                                products.append(v)
            except Exception as e:
                logger.warning(f"Không đọc được file {fp}: {e}")

        return products

    for idx, chunk_files in enumerate(list_product_chunks):
        # Mỗi luồng sẽ nhận danh sách URL sản phẩm (có thể rỗng)
        product_urls = read_products_from_files(chunk_files)

        thread = threading.Thread(target=get_shop_sell_product, args=(idx, product_urls))
        thread.start()
        time.sleep(0.5)
        threads.append(thread)

    for thread in threads:
        thread.join()
