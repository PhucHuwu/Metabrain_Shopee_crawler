from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

logger = logging.getLogger(__name__)


def auto_click(driver, xpath, time, retries=1, log_callback=None):
    """
    Thực hiện click tự động với retry và thông báo log
    
    :param driver: WebDriver instance
    :param xpath: XPath của element cần click
    :param time: Thời gian chờ tối đa
    :param retries: Số lần thử lại
    :param log_callback: Hàm callback để ghi log
    :return: True nếu thành công, False nếu thất bại
    """
    for attempt in range(retries):
        if attempt > 0 and log_callback:
            log_callback(f"Đang thử lại lần {attempt + 1}/{retries}...")

        try:
            button = WebDriverWait(driver, time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            button.click()
            if log_callback:
                log_callback("Đã click thành công")
            return True
        except Exception:
            try:
                button = WebDriverWait(driver, time).until(EC.presence_of_element_located((By.XPATH, xpath)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                button.click()
                if log_callback:
                    log_callback("Đã click thành công (phương án 2)")
                return True
            except Exception:
                pass

        try:
            button = WebDriverWait(driver, time).until(EC.presence_of_element_located((By.XPATH, xpath)))
            driver.execute_script("arguments[0].click();", button)
            if log_callback:
                log_callback("Đã click thành công (JavaScript)")
            return True
        except Exception:
            if attempt < retries - 1 and log_callback:
                log_callback("Không tìm thấy phần tử, đang thử lại...")

    if log_callback:
        log_callback(f"Không thể click sau {retries} lần thử")
    return False
