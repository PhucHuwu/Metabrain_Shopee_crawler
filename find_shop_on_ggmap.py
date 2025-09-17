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


def shop_chunking(file_path: str | Path | None = None, num_threads: int | None = None):
    try:
        base = Path(file_path) if file_path else Path("shops")
    except Exception:
        base = Path("shops")

    if num_threads is None or (isinstance(num_threads, int) and num_threads < 1):
        num_threads = 5

    if not base.exists() or not base.is_dir():
        logger.error(f"Thư mục shops không tồn tại: {base}")
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


def get_product_in_category(thread_idx, shops):
    from funcs.setup_driver import setup_driver
    from funcs.fake_agent import random_sleep, hover_element, random_scroll
    from funcs.load_cookies_to_driver import load_cookies_to_driver
    from funcs.click import auto_click

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

    def read_shop_names_from_csv(path):
        names = []
        try:
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not isinstance(row, dict):
                        continue
                    name = row.get('shop_name') or row.get('name') or row.get('shop')
                    if name:
                        names.append(name.strip())
        except Exception as e:
            logger.error(f"Lỗi đọc file CSV {path}: {e}")
        return names

    for shop_csv in shops:
        shop_names = read_shop_names_from_csv(shop_csv)
        if not shop_names:
            logger.info(f"Không tìm thấy tên shop trong file: {shop_csv}")
            continue

        for shop_name in shop_names:
            try:
                driver.get("https://www.google.com/maps")
                driver.execute_script("document.body.style.zoom='25%'")
                time.sleep(3)

                try:
                    searchbox = driver.find_element('id', 'searchbox')

                    if searchbox:
                        hover_element(driver, searchbox)

                        clicked = False
                        try:
                            clicked = auto_click(driver, "//*[@id='searchbox']", 5, retries=2, log_callback=logger.info)
                        except Exception:
                            clicked = False

                        if clicked:
                            success_type = None
                            try:
                                driver.execute_script('arguments[0].focus();', searchbox)
                            except Exception:
                                pass

                            try:
                                from selenium.webdriver import ActionChains
                                ac = ActionChains(driver)
                                ac.click(searchbox)
                                for ch in shop_name:
                                    ac.send_keys(ch)
                                ac.send_keys('\ue007')
                                ac.perform()
                                success_type = 'actionchains'
                            except Exception as e:
                                logger.debug(f"ActionChains failed for '{shop_name}': {e}")

                            logger.info(f"[Thread {thread_idx}] Input method used for '{shop_name}': {success_type}")

                except Exception as e:
                    logger.debug(f"Lỗi khi thao tác searchbox: {e}")

            except Exception as e:
                logger.error(f"Lỗi khi xử lý shop '{shop_name}': {e}")
                continue

            try:
                random_sleep()
                hover_element(driver, driver.find_element('tag name', 'body'))
                random_scroll(driver)

                page_source = driver.page_source
                results = parse_ggmap_results(page_source, max_items=5)

                category_name = Path(shop_csv).stem
                save_ggmap_results(category_name, shop_name, results)

            except Exception as e:
                logger.error(f"Lỗi khi trích xuất kết quả ggmap cho '{shop_name}': {e}")
                continue

    try:
        driver.quit()
    except Exception:
        pass


def parse_ggmap_results(page_source: str, max_items: int = 5) -> list[dict]:
    from bs4 import BeautifulSoup

    try:
        soup = BeautifulSoup(page_source, 'html.parser')
        container = soup.find('div', attrs={'role': 'feed'})
        if not container:
            container = soup.find(lambda tag: tag.name == 'div' and tag.get('aria-label', '').lower().startswith('kết quả'))

        if not container:
            return []

        anchors = []
        for a in container.find_all('a', href=True):
            href = a['href']
            if ('/maps/place' in href) or ('/place/' in href) or ('/maps?cid=' in href):
                anchors.append(a)

        results = []
        seen = set()
        for a in anchors:
            if len(results) >= max_items:
                break

            href = a['href']
            if href.startswith('/'):
                href = urllib.parse.urljoin('https://www.google.com', href)

            name = a.get('aria-label') or a.get_text(strip=True) or ''

            if not name:
                parent = a.parent
                found_name = ''
                for _ in range(4):
                    if not parent:
                        break
                    text = parent.get_text(separator=' ', strip=True)
                    if text and len(text) > 2:
                        found_name = text
                        break
                    parent = parent.parent
                name = found_name

            if href in seen:
                continue
            seen.add(href)

            results.append({'name': name, 'href': href})

        return results
    except Exception as e:
        logger.error(f"Lỗi khi parse page_source: {e}")
        return []


def save_ggmap_results(category: str, query_name: str, results: list[dict]):
    try:
        out_dir = Path('ggmap_search')
        out_dir.mkdir(parents=True, exist_ok=True)

        out_file = out_dir / f"{category}.csv"
        write_header = not out_file.exists()

        with open(out_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(['shop_name', 'list_href'])

            hrefs = [r.get('href', '') for r in results]
            hrefs_join = ';'.join(hrefs)
            writer.writerow([query_name, hrefs_join])
        logger.info(f"Đã lưu {len(results)} kết quả ggmap cho '{query_name}' vào {out_file}")
    except Exception as e:
        logger.error(f"Lỗi khi lưu kết quả ggmap: {e}")


if __name__ == '__main__':
    NUM_THREADS = 5
    list_shops = shop_chunking(num_threads=NUM_THREADS)

    for i, chunk in enumerate(list_shops):
        logger.info(f"Chunk {i}: {len(chunk)} files")

    threads = []

    for idx, shop in enumerate(list_shops):
        if not shop:
            logger.info(f"Bỏ qua luồng {idx} vì không có file để xử lý")
            continue

        thread = threading.Thread(target=get_product_in_category, args=(idx, shop))
        thread.start()
        time.sleep(1)
        threads.append(thread)

    for thread in threads:
        thread.join()
