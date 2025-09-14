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
    try:
        shops: list[dict] = []

        section = None
        try:
            section = driver.find_element('css selector', 'section.page-product__shop')
        except Exception:
            section = None

        shop_href = ''
        shop_name = ''

        try:
            if section is not None:
                try:
                    anchor = section.find_element('xpath', ".//a[@href][1]")
                except Exception:
                    anchor = None
            else:
                try:
                    anchor = driver.find_element('xpath', "//a[@href][1]")
                except Exception:
                    anchor = None

            if anchor is not None:
                try:
                    href = anchor.get_attribute('href') or ''
                    shop_href = href.strip()
                except Exception:
                    shop_href = ''
        except Exception:
            shop_href = ''

        try:
            candidates = []
            if section is not None:
                elems = section.find_elements('xpath', ".//*[self::div or self::span or self::h1 or self::h2 or self::p][normalize-space()]")
            else:
                elems = driver.find_elements('xpath', "//*[self::div or self::span or self::h1 or self::h2 or self::p][normalize-space()]")

            for el in elems:
                try:
                    txt = el.text.strip()
                    if not txt:
                        continue
                    low = txt.lower()
                    if any(k in low for k in ('chat ngay', 'xem shop', 'online', 'đánh giá', 'tỉ lệ phản hồi', 'tham gia', 'sản phẩm', 'thời gian phản hồi', 'người theo dõi')):
                        continue
                    if len(txt) < 3:
                        continue
                    if re.fullmatch(r'[\d,\.\s]+', txt):
                        continue
                    candidates.append(txt)
                except Exception:
                    continue

            if candidates:
                shop_name = candidates[0]
        except Exception:
            shop_name = ''

        if not shop_name and 'anchor' in locals() and anchor is not None:
            try:
                txt = anchor.text.strip()
                if txt and len(txt) > 0:
                    shop_name = txt
            except Exception:
                pass

        try:
            if shop_href and shop_href.startswith('/'):
                current_url = driver.current_url or ''
                parsed = urllib.parse.urlparse(current_url)
                origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ''
                if origin:
                    shop_href = urllib.parse.urljoin(origin, shop_href)
        except Exception:
            pass

        shop_id = ''
        try:
            if shop_href:
                parsed = urllib.parse.urlparse(shop_href)
                path = parsed.path or ''
                if path:
                    shop_id = path.strip('/').split('/')[-1]
                if not shop_id and parsed.query:
                    q = urllib.parse.parse_qs(parsed.query)
                    for key in ('shopid', 'shopId', 'sellerId'):
                        if key in q and q[key]:
                            shop_id = q[key][0]
                            break
        except Exception:
            shop_id = ''

        shop_name = shop_name or ''
        shop_href = shop_href or ''
        shop_id = shop_id or ''

        if shop_name or shop_href:
            shops.append({
                'shop_name': shop_name,
                'shop_href': shop_href,
                'shop_id': shop_id,
            })

        return shops
    except Exception as e:
        logger.exception(f'Lỗi trong get_infor_shop: {e}')
        return []


def _ensure_shops_dir():
    try:
        base = Path(__file__).parent
        shops_dir = base / 'shops'
        if not shops_dir.exists():
            shops_dir.mkdir(parents=True, exist_ok=True)
        return shops_dir
    except Exception as e:
        logger.exception(f'Không thể tạo thư mục shops: {e}')
        return None


def save_shops_for_category(category_name: str, shops: list[dict]):
    try:
        shops_dir = _ensure_shops_dir()
        if shops_dir is None:
            return False

        safe_name = re.sub(r"[^0-9a-zA-Z_\-\u00C0-\u024F ]+", '', category_name).strip() or category_name
        out_file = shops_dir / f"{safe_name}.json"

        existing: list[dict] = []
        if out_file.exists():
            try:
                with out_file.open('r', encoding='utf-8') as f:
                    existing = json.load(f) or []
            except Exception:
                existing = []

        seen = set()
        merged: list[dict] = []

        def key_of(item: dict) -> str:
            try:
                sid = item.get('shop_id') or ''
                href = item.get('shop_href') or ''
                name = item.get('shop_name') or ''

                sid = str(sid).strip()
                href = str(href).strip().lower()
                name = str(name).strip().lower()

                if sid:
                    return f"id:{sid}"
                if href:
                    return f"href:{href}"
                return f"name:{name}"
            except Exception:
                return ''

        for item in existing + shops:
            try:
                k = key_of(item) or ''
                if not k:
                    k = (item.get('shop_name', '') + '|' + item.get('shop_href', '')).strip()
                if k in seen:
                    continue
                seen.add(k)
                merged.append(item)
            except Exception:
                continue

        with out_file.open('w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

        logger.info(f'Đã lưu {len(shops)} shop vào {out_file} (tổng {len(merged)})')
        return True
    except Exception as e:
        logger.exception(f'Lỗi khi lưu shops cho category {category_name}: {e}')
        return False


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
    # position_x = thread_idx * window_width // 5
    position_x = thread_idx * window_width  # for testing
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

                try:
                    if shops:
                        save_shops_for_category(category_name, shops)
                except Exception as e:
                    logger.exception(f"[Thread {thread_idx}] Lỗi khi lưu shops cho category {category_name}: {e}")

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
