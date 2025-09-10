import undetected_chromedriver as uc
import json
import threading
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import os
import re
import logging
import shutil
from product_url_extractor import extract_shopee_products
import ctypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

driver_lock = threading.Lock()
copy_lock = threading.Lock()
# Đường dẫn profile base đã được login và giải captcha thủ công
BASE_PROFILE_DIR = os.environ.get('BASE_PROFILE_DIR', 'Profile_0')
# Số luồng cố định theo yêu cầu (có fallback nếu số categories < FIXED_NUM_THREADS)
FIXED_NUM_THREADS = 5
# NUM_THREADS sẽ được set trong main() bằng số luồng thực tế (<= FIXED_NUM_THREADS)
NUM_THREADS = 1  # sẽ được set trong main()


def get_screen_size():
    """Lấy kích thước màn hình (width, height). Chỉ Windows được hỗ trợ; fallback nếu lỗi."""
    try:
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        return width, height
    except Exception:
        # Fallback phổ biến
        return 1920, 1080


def compute_window_geometry(idx, total, margin=8, min_w=400, min_h=300):
    """Tính layout grid cho cửa sổ: trả về (w, h, x, y).
    - idx: chỉ số luồng (0-based)
    - total: tổng số luồng
    - margin: khoảng cách giữa các cửa sổ
    """
    try:
        screen_w, screen_h = get_screen_size()

        # Số cột = ceil(sqrt(total)), rows tương ứng
        cols = int((total ** 0.5) + 0.9999)
        rows = (total + cols - 1) // cols

        # Available area per cell
        cell_w = max(min_w, (screen_w - margin * (cols + 1)) // cols)
        cell_h = max(min_h, (screen_h - margin * (rows + 1)) // rows)

        col = idx % cols
        row = idx // cols

        x = margin + col * (cell_w + margin)
        y = margin + row * (cell_h + margin)

        return cell_w, cell_h, x, y
    except Exception:
        return 800, 600, 0, 0


def random_sleep(min_s=1.0, max_s=4.0, jitter=0.0):
    """Ngủ ngẫu nhiên để giả lập hành vi người dùng.
    Các tham số: min_s, max_s (giây), jitter: +/- thay đổi nhỏ.
    Không raise exception để đảm bảo NEVER CRASH.
    """
    try:
        s = random.uniform(min_s, max_s)
        if jitter and jitter > 0:
            s += random.uniform(-jitter, jitter)
            if s < 0:
                s = 0
        logger.debug(f"Random sleep: {s:.2f}s (min={min_s},max={max_s},jitter={jitter})")
        time.sleep(s)
    except Exception as e:
        logger.debug(f"Lỗi khi random_sleep: {e}")
        return


def random_scroll(driver, min_scrolls=1, max_scrolls=4, min_px=200, max_px=800, delay_min=0.2, delay_max=0.8):
    """Thực hiện một chuỗi các hành động cuộn ngẫu nhiên để giả lập người dùng.
    - min_scrolls, max_scrolls: số lần cuộn trong một lượt
    - min_px, max_px: số pixel mỗi lần cuộn
    - delay_min, delay_max: delay giữa các lần cuộn
    Hàm này luôn bắt exception và không raise.
    """
    try:
        n = random.randint(min_scrolls, max_scrolls)
        for _ in range(n):
            px = random.randint(min_px, max_px)
            # Chọn hướng lên/xuống ngẫu nhiên
            direction = random.choice([-1, 1])
            amount = direction * px
            try:
                # Thực hiện cuộn mượt
                driver.execute_script("window.scrollBy({left:0, top: arguments[0], behavior: 'smooth'});", amount)
            except Exception:
                # Fallback: cuộn thô
                try:
                    driver.execute_script(f"window.scrollBy(0, {amount});")
                except Exception:
                    pass

            # Pause nhỏ giữa các lần cuộn
            random_sleep(delay_min, delay_max, jitter=0.05)

        # Thỉnh thoảng scroll to top/bottom để mô phỏng hành vi
        if random.random() < 0.15:
            if random.random() < 0.5:
                try:
                    driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
                except Exception:
                    driver.execute_script("window.scrollTo(0, 0);")
            else:
                try:
                    driver.execute_script("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
                except Exception:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            random_sleep(0.3, 0.9)

    except Exception as e:
        logger.debug(f"Lỗi khi random_scroll: {e}")
        return


def advanced_hover_element(driver, element, max_offset=15, moves=3, pause_min=0.05, pause_max=0.25):
    """Thực hiện hover/di chuyển chuột nâng cao lên element để giả lập hành vi người dùng.
    - max_offset: dao động offset x/y để di chuột quanh element
    - moves: số lần di chuyển nhỏ quanh element
    - pause_min/pause_max: pause giữa các di chuyển
    Hàm bắt mọi lỗi và không raise để không làm crash.
    """
    try:
        if element is None:
            return
        actions = ActionChains(driver)
        # Di tới element chính
        try:
            actions.move_to_element(element).perform()
        except Exception:
            # fallback: try a simple move with offset 0
            try:
                actions.move_to_element_with_offset(element, 0, 0).perform()
            except Exception:
                return

        for _ in range(max(1, moves)):
            try:
                xoff = random.randint(-max_offset, max_offset)
                yoff = random.randint(-max_offset, max_offset)
                actions.move_to_element_with_offset(element, xoff, yoff).perform()
            except Exception:
                try:
                    actions.move_by_offset(xoff, yoff).perform()
                except Exception:
                    pass

            # Pause ngẫu nhiên giữa các bước di chuyển
            random_sleep(pause_min, pause_max, jitter=0.01)

        # Một pause ngắn sau hover
        random_sleep(0.05, 0.18)
    except Exception as e:
        logger.debug(f"Lỗi khi advanced_hover_element: {e}")
        return


def setup_driver(idx):
    options = uc.ChromeOptions()
    profile_directory = f"Profile_{idx}"

    # Nếu có base profile (đã login), copy ra một bản sao để tránh mở cùng 1 thư mục đồng thời
    def prepare_profile_copy(base_dir, dest_dir):
        # Nếu không có base, tạo dest nếu cần
        if not os.path.exists(base_dir):
            try:
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
            except Exception:
                pass
            return True

        if os.path.exists(dest_dir):
            # nếu đã tồn tại, coi như sẵn sàng
            return True

        with copy_lock:
            # Double-check sau khi có lock
            if os.path.exists(dest_dir):
                return True
            logger.info(f"Sao chép base profile '{base_dir}' -> '{dest_dir}'")
            try:
                shutil.copytree(base_dir, dest_dir)
                return True
            except Exception as e:
                logger.warning(f"Không copy được base profile: {e}")
                # Thử tạo dest rỗng
                try:
                    os.makedirs(dest_dir, exist_ok=True)
                except Exception:
                    pass
                return False

    prepare_profile_copy(BASE_PROFILE_DIR, profile_directory)

    options.user_data_dir = profile_directory
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # options.add_argument("--headless=new")

    try:
        with driver_lock:
            driver = uc.Chrome(options=options)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            driver.execute_script("document.body.style.zoom='25%'")
        # Cố gắng set window position/size dựa trên index và số luồng
        try:
            total = NUM_THREADS if NUM_THREADS and NUM_THREADS > 0 else 1
            w, h, x, y = compute_window_geometry(idx, total)
            try:
                driver.set_window_size(w, h)
            except Exception:
                pass
            try:
                driver.set_window_position(x, y)
            except Exception:
                pass
        except Exception:
            pass
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
    # Thêm delay ngắn ngẫu nhiên để giả lập hành vi người dùng
    random_sleep(0.5, 1.5, jitter=0.2)
    # Thực hiện vài lần scroll ngẫu nhiên trong recommend container
    try:
        random_scroll(driver, min_scrolls=1, max_scrolls=3, min_px=150, max_px=600, delay_min=0.2, delay_max=0.6)
    except Exception as e:
        logger.debug(f"random_scroll lỗi trong recommend container: {e}")

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
                        # Hover nhẹ lên link trước khi lấy href
                        try:
                            advanced_hover_element(driver, link, max_offset=6, moves=2, pause_min=0.02, pause_max=0.08)
                        except Exception:
                            pass

                        href = link.get_attribute('href')
                        if href and ('/product/' in href or '-i.' in href):
                            clean_href = href.split('?')[0]
                            if clean_href not in product_hrefs:
                                product_hrefs.append(clean_href)
                                logger.debug(f"Thêm product href: {clean_href}")
                        # Thêm pause nhỏ giữa các thao tác đọc link
                        random_sleep(0.01, 0.06, jitter=0.02)
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


def extract_product_ids_v2(driver, category_url, page_number=1):
    try:
        # Build paged URL: append /popular?pageNumber={n}
        page_url = category_url.rstrip('/') + f"/popular?pageNumber={page_number}"
        logger.info(f"Truy cập category URL (page {page_number}): {page_url}")
        driver.execute_script("document.body.style.zoom='25%'")
        driver.get(page_url)

        # Thêm delay ngẫu nhiên sau khi tải trang category
        random_sleep(2.0, 4.0, jitter=0.5)
        # Thực hiện hover ngắn lên body để kích hoạt event hover nếu cần
        try:
            body = driver.find_element(By.TAG_NAME, 'body')
            advanced_hover_element(driver, body, max_offset=50, moves=2)
        except Exception:
            pass
        # Thực hiện scroll để load thêm nội dung động
        try:
            random_scroll(driver, min_scrolls=2, max_scrolls=6, min_px=300, max_px=900, delay_min=0.3, delay_max=1.0)
        except Exception as e:
            logger.debug(f"random_scroll lỗi trong extract_product_ids_v2: {e}")

        products = extract_shopee_products(driver, scroll_for_more=True)

        if products:
            logger.info(f"Extract được {len(products)} sản phẩm từ {category_url}")
        else:
            logger.warning(f"Không extract được sản phẩm nào từ {category_url}")

        # annotate products with page
        for prod in products:
            prod['page'] = page_number
        return products

    except Exception as e:
        logger.error(f"Lỗi khi extract products từ {category_url}: {e}")
        return []


def extract_product_ids(driver, category_url, page_number=1):
    try:
        page_url = category_url.rstrip('/') + f"/popular?pageNumber={page_number}"
        logger.info(f"Truy cập category URL (page {page_number}): {page_url}")
        driver.execute_script("document.body.style.zoom='25%'")
        driver.get(page_url)

        # Thêm delay ngẫu nhiên sau khi tải trang category
        random_sleep(2.0, 4.0, jitter=0.5)
        # Thực hiện hover ngắn lên body để kích hoạt event hover nếu cần
        try:
            body = driver.find_element(By.TAG_NAME, 'body')
            advanced_hover_element(driver, body, max_offset=40, moves=2)
        except Exception:
            pass
        # Thực hiện scroll để load thêm nội dung động
        try:
            random_scroll(driver, min_scrolls=2, max_scrolls=5, min_px=250, max_px=800, delay_min=0.3, delay_max=0.9)
        except Exception as e:
            logger.debug(f"random_scroll lỗi trong extract_product_ids: {e}")

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
                # Thêm pause nhỏ giữa các thao tác xử lý href
                random_sleep(0.01, 0.05, jitter=0.02)
            except Exception as e:
                logger.debug(f"Lỗi khi extract ID từ href {href}: {e}")
                continue

        logger.info(f"Extract được {len(product_ids)} product IDs")
        # annotate product ids with page
        for pid in product_ids:
            pid['page'] = page_number
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


def make_safe_filename(category_name, orig_idx=None):
    """Tạo filename an toàn từ tên category.
    - Loại bỏ ký tự không hợp lệ trên Windows
    - Thay dấu cách bằng underscore, giữ alnum, underscore, dash và dot
    - Nếu rỗng, fallback thành 'category_{idx}'
    - Để tránh trùng tên, append orig_idx nếu được cung cấp
    """
    try:
        if not category_name:
            base = f"category_{orig_idx if orig_idx is not None else 'unknown'}"
        else:
            # Loại bỏ các ký tự đặc biệt không cho phép trên file system
            base = re.sub(r'[<>:\\"/\\|?*]', '', str(category_name))
            base = base.strip()
            base = base.replace(' ', '_')
            # Giữ lại chỉ các ký tự an toàn
            base = re.sub(r'[^0-9A-Za-z._\-]', '', base)
            if not base:
                base = f"category_{orig_idx if orig_idx is not None else 'unknown'}"

        if orig_idx is not None:
            filename = f"{base}_{orig_idx}.json"
        else:
            filename = f"{base}.json"

        # Giới hạn độ dài tên file để tránh filesystem issues
        if len(filename) > 200:
            filename = filename[:200]
            if not filename.lower().endswith('.json'):
                filename = filename + '.json'

        return filename
    except Exception:
        return f"category_{orig_idx if orig_idx is not None else 'unknown'}.json"


def process_category_thread(idx, category_url):
    """Worker cho mỗi luồng xử lý một category và lưu kết quả vào '{idx}.json'."""
    try:
        try:
            category_name = category_url.split('/mall/')[-1].split('-cat.')[0].replace('%', ' ')
        except Exception:
            category_name = f"Category_{idx}"

        logger.info(f"[Thread {idx}] Bắt đầu crawl category: {category_name}")

        driver = setup_driver(idx)
        if not driver:
            logger.error(f"[Thread {idx}] Không thể khởi tạo driver")
            # Lưu file rỗng để báo trạng thái
            empty_fname = make_safe_filename(None, idx)
            save_product_data([], empty_fname)
            return

        results = []
        try:
            for page_number in range(1, 11):
                try:
                    products = extract_product_ids_v2(driver, category_url, page_number)
                    if products:
                        for product in products:
                            product['category'] = category_name
                            product['category_url'] = category_url
                        results.extend(products)
                        logger.info(f"[Thread {idx}] Lấy {len(products)} sản phẩm từ {category_name} (page {page_number})")
                    else:
                        logger.warning(f"[Thread {idx}] Không có sản phẩm từ {category_name} (page {page_number})")

                    random_sleep(0.5, 1.5, jitter=0.3)
                except Exception as e:
                    logger.error(f"[Thread {idx}] Lỗi khi crawl page {page_number} của {category_name}: {e}")
                    continue

        except Exception as e:
            logger.error(f"[Thread {idx}] Lỗi tổng quát khi crawl category {category_name}: {e}")
        finally:
            # Luôn lưu kết quả (có thể rỗng) và dọn driver
            try:
                out_fname = make_safe_filename(category_name, idx)
                save_product_data(results, out_fname)
            except Exception as e:
                logger.error(f"[Thread {idx}] Lỗi khi lưu file kết quả: {e}")
            try:
                driver.quit()
            except Exception:
                pass

    except Exception as e:
        logger.error(f"[Thread {idx}] Exception không lường trước: {e}")
        try:
            empty_fname = make_safe_filename(None, idx)
            save_product_data([], empty_fname)
        except Exception:
            pass


def process_category_chunk(thread_idx, category_tuples):
    """Worker cho mỗi luồng xử lý một danh sách (chunk) category.
    - category_tuples: list of (original_index, category_url)
    Mỗi category sẽ lưu kết quả vào '{original_index}.json' như trước.
    """
    try:
        logger.info(f"[Chunk {thread_idx}] Bắt đầu xử lý chunk gồm {len(category_tuples)} categories")

        driver = setup_driver(thread_idx)
        if not driver:
            logger.error(f"[Chunk {thread_idx}] Không thể khởi tạo driver cho chunk, ghi file rỗng cho các category trong chunk")
            for orig_idx, _ in category_tuples:
                try:
                    empty_fname = make_safe_filename(None, orig_idx)
                    save_product_data([], empty_fname)
                except Exception:
                    pass
            return

        try:
            for orig_idx, category_url in category_tuples:
                try:
                    try:
                        category_name = category_url.split('/mall/')[-1].split('-cat.')[0].replace('%', ' ')
                    except Exception:
                        category_name = f"Category_{orig_idx}"

                    logger.info(f"[Chunk {thread_idx}] [Category {orig_idx}] Bắt đầu crawl: {category_name}")

                    results = []
                    for page_number in range(1, 11):
                        try:
                            products = extract_product_ids_v2(driver, category_url, page_number)
                            if products:
                                for product in products:
                                    product['category'] = category_name
                                    product['category_url'] = category_url
                                results.extend(products)
                                logger.info(f"[Chunk {thread_idx}] [Category {orig_idx}] Lấy {len(products)} sản phẩm (page {page_number})")
                            else:
                                logger.warning(f"[Chunk {thread_idx}] [Category {orig_idx}] Không có sản phẩm (page {page_number})")

                            random_sleep(0.5, 1.5, jitter=0.3)
                        except Exception as e:
                            logger.error(f"[Chunk {thread_idx}] [Category {orig_idx}] Lỗi khi crawl page {page_number}: {e}")
                            continue

                    # Lưu kết quả cho từng category theo index ban đầu
                    try:
                        out_fname = make_safe_filename(category_name, orig_idx)
                        save_product_data(results, out_fname)
                    except Exception as e:
                        logger.error(f"[Chunk {thread_idx}] [Category {orig_idx}] Lỗi khi lưu file kết quả: {e}")

                    # Ngủ ngắn giữa các category để giảm tải và tránh bị block
                    random_sleep(0.5, 1.2, jitter=0.2)

                except Exception as e:
                    logger.error(f"[Chunk {thread_idx}] [Category {orig_idx}] Exception không lường trước: {e}")
                    try:
                        empty_fname = make_safe_filename(None, orig_idx)
                        save_product_data([], empty_fname)
                    except Exception:
                        pass
                    continue

        finally:
            try:
                driver.quit()
            except Exception:
                pass

    except Exception as e:
        logger.error(f"[Chunk {thread_idx}] Exception tổng quát: {e}")
        for orig_idx, _ in category_tuples:
            try:
                empty_fname = make_safe_filename(None, orig_idx)
                save_product_data([], empty_fname)
            except Exception:
                pass


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

    # Chia danh sách categories thành FIXED_NUM_THREADS chunk và chạy mỗi chunk trên 1 luồng
    global NUM_THREADS
    categories_to_process = [(i, c) for i, c in enumerate(categories) if c]
    if not categories_to_process:
        logger.error("Không có category hợp lệ để xử lý")
        return

    # Số luồng thực tế = min(FIXED_NUM_THREADS, số categories)
    NUM_THREADS = min(FIXED_NUM_THREADS, len(categories_to_process))

    # Tạo các chunk: cố gắng phân đều; mỗi chunk là list of (original_index, category_url)
    chunks = [[] for _ in range(NUM_THREADS)]
    for idx, tup in enumerate(categories_to_process):
        chunk_idx = idx % NUM_THREADS
        chunks[chunk_idx].append(tup)

    threads = []
    for thread_idx in range(NUM_THREADS):
        chunk = chunks[thread_idx]
        if not chunk:
            continue
        t = threading.Thread(target=process_category_chunk, args=(thread_idx, chunk), daemon=False)
        threads.append(t)
        t.start()
        # Nhỏ delay để tránh khởi tạo driver đồng thời quá nhanh
        random_sleep(0.2, 0.6, jitter=0.05)

    # Với các category rỗng ban đầu (nơi categories list chứa None/empty), tạo file rỗng tương ứng
    for i, c in enumerate(categories):
        if not c:
            try:
                empty_fname = make_safe_filename(None, i)
                save_product_data([], empty_fname)
            except Exception:
                pass

    # Chờ tất cả luồng hoàn thành
    for t in threads:
        try:
            t.join()
        except Exception:
            continue

    logger.info(f"Hoàn thành tất cả chunk luồng. Tổng luồng: {len(threads)} (FIXED target: {FIXED_NUM_THREADS})")


if __name__ == "__main__":
    main()
