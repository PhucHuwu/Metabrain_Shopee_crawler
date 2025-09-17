from pathlib import Path
import logging
import threading
import time
import re
import urllib.parse
import csv

try:
    import config
except Exception:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def ggmap_search_chunking(file_path: str | Path | None = None, num_threads: int | None = None):
    try:
        base = Path(file_path) if file_path else Path("ggmap_search")
    except Exception:
        base = Path("ggmap_search")

    if num_threads is None or (isinstance(num_threads, int) and num_threads < 1):
        num_threads = 5

    if not base.exists() or not base.is_dir():
        logger.error(f"Thư mục ggmap_search không tồn tại: {base}")
        return []

    all_files = sorted([str(p) for p in base.iterdir() if p.is_file() and p.suffix.lower() == ".csv"])

    if not all_files:
        logger.warning(f"Không tìm thấy file CSV trong thư mục: {base}")
        return [[] for _ in range(num_threads)]

    chunks: list[list[str]] = [[] for _ in range(num_threads)]

    for idx, f in enumerate(all_files):
        chunks[idx % num_threads].append(f)

    logger.info(f"Đã chia {len(all_files)} file CSV thành {num_threads} chunks")
    return chunks


def get_phonenum_adress(thread_idx, mapsearch):
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

    driver.get("https://www.google.com/maps")
    driver.execute_script("document.body.style.zoom='25%'")
    load_cookies_to_driver(driver, type='ggmap')
    time.sleep(3)
    driver.refresh()
    shops_map = load_shops_mapping()

    for csv_file in mapsearch:
        try:
            logger.info(f"[Thread {thread_idx}] Mở file: {csv_file}")
            with open(csv_file, newline='', encoding='utf-8') as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    raw = row.get('list_href') or ''
                    if not raw:
                        logger.debug(f"[Thread {thread_idx}] Dòng không có list_href, bỏ qua")
                        continue

                    hrefs = [h.strip() for h in raw.split(';') if h.strip()]
                    for href in hrefs:
                        if not href.lower().startswith('http'):
                            logger.warning(f"[Thread {thread_idx}] Href không hợp lệ, bỏ qua: {href}")
                            continue

                        driver.get(href)
                        driver.execute_script("document.body.style.zoom='25%'")
                        time.sleep(3)
                        shop_name = (row.get('shop_name') or '').strip()
                        if not shop_name:
                            try:
                                shop_name = safe_get_text_from_ggmap(driver, ['Tên cửa hàng', 'h1', "[aria-label*='Tên']"]) or ''
                            except Exception:
                                shop_name = ''

                        if shop_name:
                            mapped = shops_map.get(shop_name.lower())
                            if mapped:
                                shop_name = mapped

                        try:
                            phones = extract_aria_values(driver, 'Số điện thoại:')
                        except Exception:
                            phones = []

                        try:
                            addresses = extract_aria_values(driver, 'Địa chỉ:')
                        except Exception:
                            addresses = []

                        category = row.get('category') or Path(csv_file).stem
                        ensure_shop_info_dir()
                        save_shop_info(category, shop_name, phones, addresses)
        except FileNotFoundError:
            logger.error(f"[Thread {thread_idx}] File không tồn tại: {csv_file}")
        except Exception as e:
            logger.error(f"[Thread {thread_idx}] Lỗi khi xử lý file {csv_file}: {e}")


def ensure_shop_info_dir():
    d = Path('shop_info')
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Không thể tạo thư mục shop_info: {e}")


def load_shops_mapping() -> dict:
    mapping = {}
    base = Path('shops')
    if not base.exists() or not base.is_dir():
        return mapping

    for p in base.iterdir():
        if not p.is_file() or p.suffix.lower() != '.csv':
            continue
        try:
            with p.open('r', encoding='utf-8') as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    name = (row.get('shop_name') or '').strip()
                    if name:
                        mapping[name.lower()] = name
        except Exception:
            continue

    return mapping


def save_shop_info(category: str, shop_name: str, phones: list, addresses: list):
    safe_category = re.sub(r"[^0-9A-Za-z\-_ ]", '_', category or 'unknown')
    out_file = Path('shop_info') / f"{safe_category}.csv"
    fieldnames = ['shop_name', 'phone', 'address']

    phones = phones or []
    addresses = addresses or []

    rows = []
    if not phones and not addresses:
        return

    if phones and not addresses:
        for p in phones:
            rows.append({'shop_name': shop_name, 'phone': p, 'address': ''})
    elif addresses and not phones:
        for a in addresses:
            rows.append({'shop_name': shop_name, 'phone': '', 'address': a})
    else:
        for p in phones:
            for a in addresses:
                rows.append({'shop_name': shop_name, 'phone': p, 'address': a})

    try:
        write_header = not out_file.exists()
        with out_file.open('a', newline='', encoding='utf-8') as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            for r in rows:
                writer.writerow(r)
        logger.info(f"Lưu {len(rows)} hàng vào {out_file}")
    except Exception as e:
        logger.error(f"Không thể lưu file {out_file}: {e}")


def extract_aria_values(driver, label_prefix: str) -> list:
    results = []

    def normalize(s: str) -> str:
        try:
            s = str(s)
        except Exception:
            return ''
        s = s.strip()
        if s.startswith(label_prefix):
            s = s[len(label_prefix):].strip()
        s = re.sub(r"[,\.\s]+$", '', s)
        s = re.sub(r"\s+", ' ', s)
        return s

    try:
        elements = driver.find_elements('xpath', f"//*[contains(@aria-label, '{label_prefix}')]")
        for el in elements:
            try:
                al = el.get_attribute('aria-label') or ''
                if label_prefix in al:
                    val = al.split(label_prefix, 1)[1]
                    if 'Địa chỉ' in label_prefix:
                        parts = [val]
                    else:
                        parts = re.split(r"[;,/|\\n]+", val)
                    for p in parts:
                        p = normalize(p)
                        if p:
                            results.append(p)
            except Exception as e:
                logger.debug(f"Lỗi khi đọc aria-label: {e}")

    except Exception as e:
        logger.debug(f"extract_aria_values lỗi: {e}")
    seen = set()
    dedup = []
    for r in results:
        if r not in seen:
            seen.add(r)
            dedup.append(r)
    return dedup


def safe_get_text_from_ggmap(driver, keys, default=''):
    try:
        for key in keys:
            try:
                els = driver.find_elements('xpath', f"//*[contains(@aria-label, '{key}')]")
                for el in els:
                    txt = (el.get_attribute('aria-label') or '').strip()
                    if txt:
                        if ':' in txt:
                            return txt.split(':', 1)[1].strip()
                        return txt
            except Exception:
                pass
    except Exception as e:
        logger.debug(f"safe_get_text_from_ggmap lỗi: {e}")
    return default


if __name__ == '__main__':
    NUM_THREADS = 5
    list_mapsearch = ggmap_search_chunking(num_threads=NUM_THREADS)

    for i, chunk in enumerate(list_mapsearch):
        logger.info(f"Chunk {i}: {len(chunk)} files")

    threads = []

    for idx, mapsearch in enumerate(list_mapsearch):
        if not mapsearch:
            logger.info(f"Bỏ qua luồng {idx} vì không có file để xử lý")
            continue

        thread = threading.Thread(target=get_phonenum_adress, args=(idx, mapsearch))
        thread.start()
        time.sleep(1)
        threads.append(thread)

    for thread in threads:
        thread.join()
