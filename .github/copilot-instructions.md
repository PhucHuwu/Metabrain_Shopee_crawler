# Hướng Dẫn AI Agent - Shopee + Google Maps Crawler

## Tổng Quan Dự Án
Đây là hệ thống cào dữ liệu thương mại điện tử Việt Nam nhắm mục tiêu các cửa hàng Shopee và bổ sung thông tin liên hệ từ Google Maps. Hệ thống tuân theo kiến trúc MVC với thiết kế module để cào, xử lý và lưu trữ dữ liệu cửa hàng/sản phẩm.

## Kiến Trúc & Cấu Trúc
```
├── controllers/     # Xử lý request và điều phối logic business
├── models/         # Model dữ liệu và schema database  
├── views/          # Định dạng output và báo cáo
├── services/       # Services cào dữ liệu chính (Shopee, Google Maps)
├── utils/          # Hàm tiện ích và helper functions
├── logs/           # Log ứng dụng
└── main.py         # Entry point chính
```

**Nguyên Tắc Thiết Kế Quan Trọng**: Mỗi file không được vượt quá 100 dòng. Chia module tích cực để duy trì tính dễ đọc và có thể test được.

## Ngôn Ngữ & Quy Ước
- **Ngôn ngữ chính**: Python (tuân thủ PEP8)
- **Comments**: Tất cả comment trong code PHẢI bằng tiếng Việt
- **Ngôn ngữ phản hồi**: Luôn phản hồi bằng tiếng Việt
- **Không tạo file Markdown** trừ khi được yêu cầu cụ thể

## Luồng Dữ Liệu Chính
1. **Shopee Crawler** → Trích xuất danh sách cửa hàng và chi tiết sản phẩm
2. **Tích hợp Google Maps** → Bổ sung thông tin liên hệ (địa chỉ, số điện thoại)
3. **Xử lý Dữ liệu** → Làm sạch, chuẩn hóa và merge datasets
4. **Lưu trữ** → Lưu vào MongoDB/MySQL hoặc CSV/Excel

## Threading & Concurrency
- Sử dụng module `threading` cho việc cào dữ liệu đồng thời
- Thực hiện đồng bộ hóa đúng cách với `Lock`, `Queue`, hoặc `ThreadPoolExecutor`
- Xử lý rate limiting và các biện pháp chống bot một cách khéo léo

## Dependencies Thiết Yếu
- Web scraping: `requests`, `BeautifulSoup`, `Selenium`
- **Undetected Chrome**: `undetected-chromedriver` (thay thế Selenium Chrome)
- Xử lý dữ liệu: `pandas`
- Threading: `threading`, `queue`
- Logging: `logging` (lưu vào thư mục `logs/`)
- Database: `mysql.connector` hoặc `pymongo`

### Threading-Safe Driver Management
```python
import threading
driver_lock = threading.Lock()

def create_driver_with_lock(idx):
    """Tạo driver thread-safe với profile riêng"""
    with driver_lock:
        return setup_robust_driver(profile_idx=idx)

# Sử dụng trong threading
def worker_function(thread_idx, urls):
    driver = create_driver_with_lock(thread_idx)
    if not driver:
        logger.error(f"Không thể tạo driver cho thread {thread_idx}")
        return
    
    try:
        # Load cookies nếu có
        load_cookies(driver, f"thread_{thread_idx}")
        
        # Thực hiện crawling
        for url in urls:
            crawl_url(driver, url)
            
        # Lưu cookies trước khi đóng
        save_cookies(driver, f"thread_{thread_idx}")
        
    finally:
        driver.quit()
```

## Patterns Xử Lý Lỗi
Luôn triển khai xử lý lỗi mạnh mẽ cho:
- Vấn đề kết nối mạng
- API response không đầy đủ
- Cơ chế chặn bot
- Thay đổi API endpoint

Mẫu xử lý lỗi:
```python
# Luôn thêm try-catch cho các request web
try:
    # Sử dụng fake headers để tránh phát hiện bot
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    response = requests.get(url, headers=headers, timeout=10)
    # Xử lý response
except requests.RequestException as e:
    logger.error(f"Lỗi khi crawl {url}: {e}")
    return None
```

## 🚨 YÊU CẦU QUAN TRỌNG NHẤT: TÍNH ỔN ĐỊNH TUYỆT ĐỐI
**Chương trình PHẢI hoạt động đúng trong MỌI TRƯỜNG HỢP**. Không được phép crash hoặc dừng đột ngột. Triển khai:

### Xử Lý Tất Cả Scenarios Lỗi
- **Không có internet**: Chương trình retry và tiếp tục khi có kết nối lại
- **Server trả về lỗi 404/500**: Skip item hiện tại, continue với item tiếp theo
- **Anti-bot blocking**: Tự động đổi user-agent, proxy, delay longer
- **Dữ liệu thiếu/sai format**: Sử dụng default values, log warning và tiếp tục
- **Database connection fail**: Lưu vào file tạm, retry connection sau
- **Memory/disk full**: Cleanup temp files, compress data, alert user

### Fallback Strategies
```python
def safe_crawl_with_fallback(url, max_retries=3):
    """Cào dữ liệu với nhiều phương án dự phòng"""
    for attempt in range(max_retries):
        try:
            # Thử phương án chính
            result = primary_crawl_method(url)
            if result:
                return result
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            
        # Thử phương án dự phòng
        try:
            result = fallback_crawl_method(url)
            if result:
                return result
        except Exception as e:
            logger.warning(f"Fallback attempt {attempt + 1} failed: {e}")
            
        time.sleep(2 ** attempt)  # Exponential backoff
    
    logger.error(f"All attempts failed for {url}")
    return None  # Không được raise exception
```

### Recovery Mechanisms
- **Checkpoint system**: Lưu tiến trình sau mỗi batch để có thể resume
- **Data validation**: Check dữ liệu trước khi lưu, reject invalid entries
- **Graceful degradation**: Nếu một module fail, các module khác vẫn chạy
- **Auto-restart**: Tự động restart components bị lỗi

## Quản Lý Cấu Hình
- Tách tất cả cấu hình ra file `config.py`
- Không bao giờ hard-code API keys hoặc dữ liệu nhạy cảm
- Hỗ trợ cả việc chạy `main.py` và CLI interfaces
- Cấu hình dựa trên environment để sẵn sàng deploy

## Yêu Cầu Logging
- Logging toàn diện vào thư mục `logs/` sử dụng Python `logging` module
- Log levels: DEBUG (tiến trình crawl), INFO (các bước chính), ERROR (lỗi)
- Bao gồm timestamps và thread IDs cho các hoạt động đồng thời

## Chiến Lược Testing
Tạo các hàm test bao gồm:
- Scenarios lỗi mạng
- Response dữ liệu malformed
- Rate limiting và blocking
- Validation và cleaning dữ liệu

## Ví Dụ Cấu Trúc Dữ Liệu
```python
shop_data = {
    "shop_id": "12345",
    "shop_name": "ABC Store",
    "products": [
        {"name": "Áo thun nam", "price": 120000, "sold": 500}
    ],
    "address": "123 Nguyễn Văn A, Quận 1, TP.HCM",
    "phone": "0123456789"
}
```

## Ghi Chú Triển Khai Quan Trọng
- **Sử dụng undetected-chromedriver** thay vì Selenium Chrome thông thường để bypass anti-bot
- **Profile Management**: Tạo profile riêng cho từng thread để lưu cookies/cache
- Triển khai delays phù hợp giữa các request (tôn trọng rate limits)
- **Fake User Agent**: Luôn sử dụng fake headers và user-agent để tránh phát hiện bot
- Xoay vòng nhiều user-agent khác nhau và proxy nếu cần thiết
- Mô phỏng hành vi người dùng thật (scroll, click, delay tự nhiên)
- Ưu tiên tích hợp Google Maps API hơn scraping để lấy dữ liệu liên hệ
- Lựa chọn database: MongoDB cho schema linh hoạt, MySQL cho dữ liệu có cấu trúc
- Luôn validate và làm sạch dữ liệu được cào trước khi lưu trữ

## 🤖 Xử Lý Selenium Chuyên Sâu
### Robust Element Handling
- **Không bao giờ assume element tồn tại** - luôn check trước khi thao tác
- **Multiple locator strategies** - dự phòng nhiều cách tìm element
- **Graceful fallback** khi không tìm thấy element cần thiết
- **Smart timeout management** - tối ưu thời gian chờ theo từng trường hợp

```python
def safe_click_element(driver, selectors, timeout=10):
    """Click element với nhiều selector fallback và xử lý lỗi toàn diện"""
    for selector in selectors:
        try:
            # Thử tìm element với explicit wait
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            logger.debug(f"Đã click thành công selector: {selector}")
            return True
        except TimeoutException:
            logger.warning(f"Timeout khi chờ element: {selector}")
        except ElementClickInterceptedException:
            # Thử scroll đến element và click lại
            try:
                driver.execute_script("arguments[0].scrollIntoView();", element)
                time.sleep(0.5)
                element.click()
                return True
            except Exception as e:
                logger.warning(f"Không thể click sau khi scroll: {e}")
        except Exception as e:
            logger.warning(f"Lỗi khi click {selector}: {e}")
    
    logger.error("Không thể click bất kỳ selector nào")
    return False  # Không crash, return False để caller xử lý tiếp

def safe_get_text(driver, selectors, default_value=""):
    """Lấy text với multiple fallback selectors"""
    for selector in selectors:
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            text = element.text.strip()
            if text:  # Chỉ return nếu có nội dung
                return text
        except Exception as e:
            logger.debug(f"Không lấy được text từ {selector}: {e}")
    
    logger.warning(f"Không lấy được text từ tất cả selectors, dùng default: {default_value}")
    return default_value
```

### Performance & Timeout Optimization
- **Dynamic timeout**: Timeout ngắn cho element nhanh, timeout dài cho content loading
- **Early termination**: Dừng sớm nếu phát hiện page load fail
- **Batch operations**: Group các thao tác để giảm wait time
- **Smart retry**: Retry với increasing delay, skip nếu quá nhiều lần fail

### Element Discovery Strategies
```python
# Ví dụ multiple selector strategies
PRODUCT_SELECTORS = [
    "div[data-sqe='name']",  # Selector chính
    ".product-title",        # Backup selector
    "h1.product-name",       # Fallback khác
    "[class*='product'][class*='name']"  # Regex-like fallback
]

PRICE_SELECTORS = [
    ".price-current",
    "[data-price]",
    ".product-price .current",
    "span:contains('₫')"  # Last resort với text matching
]
```

### Selenium Performance & Reliability Best Practices
- **Page load detection**: Kiểm tra page đã load xong trước khi thao tác
- **Network condition handling**: Xử lý slow network, timeout gracefully
- **Memory management**: Đóng driver properly, clear cache khi cần
- **Headless optimization**: Sử dụng headless mode để tăng tốc độ
- **Connection pooling**: Tái sử dụng browser session khi có thể

```python
def wait_for_page_ready(driver, timeout=30):
    """Chờ page load hoàn tất với nhiều điều kiện kiểm tra"""
    try:
        # Chờ document ready
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Chờ jQuery load xong (nếu có)
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script("return typeof jQuery == 'undefined' || jQuery.active == 0")
        )
        
        # Chờ các AJAX request hoàn tất
        time.sleep(2)  # Buffer time cho dynamic content
        return True
    except TimeoutException:
        logger.warning("Page không load hoàn tất trong thời gian quy định")
        return False
    except Exception as e:
        logger.error(f"Lỗi khi chờ page ready: {e}")
        return False

def setup_robust_driver(profile_idx=0):
    """Cấu hình driver với undetected-chromedriver và profile management"""
    import undetected_chromedriver as uc
    import os
    
    options = uc.ChromeOptions()
    
    # Tạo profile directory riêng cho từng instance
    profile_directory = f"Profile_{profile_idx}"
    if not os.path.exists(profile_directory):
        os.makedirs(profile_directory)
    
    # Cấu hình profile để lưu cookie và cache
    options.user_data_dir = profile_directory
    
    # Các option để tránh phát hiện
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-default-apps")
    
    # Khởi tạo driver với error handling
    try:
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        logger.info(f"Đã khởi tạo Chrome driver với profile: {profile_directory}")
        return driver
        
    except Exception as e:
        logger.error(f"Lỗi khi khởi tạo Chrome driver profile {profile_idx}: {e}")
        time.sleep(180)  # Chờ trước khi thử lại
        return None
```

### Cookie & Session Management
```python
def save_cookies(driver, profile_name):
    """Lưu cookies vào file để sử dụng lại"""
    try:
        cookies = driver.get_cookies()
        cookie_file = f"cookies_{profile_name}.json"
        with open(cookie_file, 'w') as f:
            json.dump(cookies, f)
        logger.info(f"Đã lưu {len(cookies)} cookies vào {cookie_file}")
    except Exception as e:
        logger.error(f"Lỗi khi lưu cookies: {e}")

def load_cookies(driver, profile_name):
    """Load cookies từ file đã lưu"""
    try:
        cookie_file = f"cookies_{profile_name}.json"
        if os.path.exists(cookie_file):
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
            logger.info(f"Đã load {len(cookies)} cookies từ {cookie_file}")
            return True
    except Exception as e:
        logger.error(f"Lỗi khi load cookies: {e}")
    return False
```

## 🛡️ Nguyên Tắc "NEVER CRASH"
- **Mọi function đều phải có return value hợp lệ** (thậm chí khi lỗi)
- **Không bao giờ để exception bubble up** mà không được handle
- **Luôn có plan B, C, D** cho mọi operation quan trọng  
- **Log mọi thứ** để có thể debug và monitor
- **Test với bad data, slow network, full disk** trước khi deploy
