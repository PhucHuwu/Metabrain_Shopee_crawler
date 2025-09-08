from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def click(driver, xpath, time, retries=1):
    for attempt in range(retries):
        if attempt > 0:
            print(f"Đang thử lại lần {attempt + 1}/{retries}...")

        try:
            button = WebDriverWait(driver, time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            button.click()
            return True
        except Exception:
            try:
                button = WebDriverWait(driver, time).until(EC.presence_of_element_located((By.XPATH, xpath)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                button.click()
                return True
            except Exception:
                pass

        try:
            button = WebDriverWait(driver, time).until(EC.presence_of_element_located((By.XPATH, xpath)))
            driver.execute_script("arguments[0].click();", button)
            return True
        except Exception:
            if attempt < retries - 1:
                print("Không tìm thấy phần tử, đang thử lại...")

    return False
