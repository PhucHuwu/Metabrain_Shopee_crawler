import json
import logging
import os
from typing import Optional

import config

logger = logging.getLogger(__name__)


def load_cookies_to_driver(driver, cookies_file: Optional[str] = None) -> int:
    """Tải cookie từ file JSON vào driver Selenium.

    - cookies_file: đường dẫn tới file cookie. Nếu None, sẽ lấy `config.COOKIES_FILE_PATH`.
    - Trả về số cookie đã thử thêm thành công.

    Hàm luôn xử lý lỗi và không raise exception (Nguyên tắc NEVER CRASH).
    """
    # Lấy đường dẫn từ tham số hoặc config
    path = cookies_file or getattr(config, "COOKIES_FILE_PATH", "data/cookies.json")

    # Kiểm tra tồn tại file
    if not os.path.exists(path):
        logger.error(f"File cookies không tồn tại: {path}")
        return 0

    try:
        with open(path, "r", encoding="utf-8") as f:
            cookies = json.load(f)
    except Exception as e:
        logger.error(f"Không thể đọc file cookies '{path}': {e}")
        return 0

    if not isinstance(cookies, list):
        logger.warning(f"File cookies không phải list, bỏ qua: {path}")
        return 0

    added = 0
    for cookie in cookies:
        # Chuẩn hoá các trường khác nhau giữa các export formats
        if not isinstance(cookie, dict):
            logger.debug("Bản ghi cookie không phải dict, skip")
            continue

        if "expirationDate" in cookie:
            try:
                cookie["expiry"] = int(cookie["expirationDate"])
                del cookie["expirationDate"]
            except Exception:
                cookie.pop("expirationDate", None)

        # Bỏ các key không hợp lệ cho Selenium
        for k in ["hostOnly", "storeId", "id", "sameSite"]:
            cookie.pop(k, None)

        # Domain bắt đầu bằng '.' có thể gây lỗi cho add_cookie ở một số driver
        if "domain" in cookie and isinstance(cookie["domain"], str) and cookie["domain"].startswith("."):
            cookie["domain"] = cookie["domain"][1:]

        try:
            driver.add_cookie(cookie)
            added += 1
        except Exception as e:
            logger.warning(f"Không thể thêm cookie '{cookie.get('name') or cookie.get('domain')}': {e}")

    logger.info(f"Đã load {added} cookies vào driver (từ {path})")
    return added
