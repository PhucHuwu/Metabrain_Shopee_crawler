import time
import random
import logging
from typing import Optional, Sequence, List
from selenium.webdriver.common.action_chains import ActionChains


logger = logging.getLogger(__name__)


def random_sleep(min_s: float = 1.0, max_s: float = 4.0, jitter: float = 0.5,
                 rng: Optional[random.Random] = None) -> float:
    """Ngủ ngẫu nhiên giống hành vi người dùng.

    Trả về số giây đã sleep để caller có thể ghi lại hoặc test.
    Cho phép truyền `rng` để reproducible (ví dụ: random.Random(0)).
    """
    try:
        r = rng or random
        s = r.uniform(min_s, max_s)
        if jitter and jitter > 0:
            s += r.uniform(-jitter, jitter)
            if s < 0:
                s = 0.0
        logger.debug("random_sleep %.2fs", s)
        time.sleep(s)
        return s
    except Exception as e:
        logger.debug("random_sleep error: %s", e)
        return 0.0


def hover_element(driver, element, max_offset: int = 15, moves: int = random.randint(5, 20),
                  pause_min: float = 0.05, pause_max: float = 0.25,
                  rng: Optional[random.Random] = None) -> bool:
    """Di chuột qua element với vài chuyển động nhỏ để mô phỏng người dùng.

    Trả về True nếu không có lỗi nghiêm trọng (không raise exception).
    """
    if element is None:
        logger.debug("hover_element: element is None")
        return False

    r = rng or random
    try:
        actions = ActionChains(driver)
        try:
            actions.move_to_element(element).perform()
        except Exception:
            try:
                actions.move_to_element_with_offset(element, 0, 0).perform()
            except Exception as e:
                logger.debug("hover_element: cannot move to element: %s", e)
                return False

        for _ in range(max(1, moves)):
            xoff = r.randint(-max_offset, max_offset)
            yoff = r.randint(-max_offset, max_offset)
            try:
                actions.move_to_element_with_offset(element, xoff, yoff).perform()
            except Exception:
                try:
                    actions.move_by_offset(xoff, yoff).perform()
                except Exception:
                    pass

            random_sleep(pause_min, pause_max, jitter=0.01, rng=r)

        random_sleep(0.05, 0.18, rng=r)
        return True
    except Exception as e:
        logger.debug("hover_element error: %s", e)
        return False


def random_scroll(driver, min_scrolls: int = 5, max_scrolls: int = 20,
                  min_px: int = 200, max_px: int = 800,
                  delay_min: float = 0.2, delay_max: float = 0.8,
                  rng: Optional[random.Random] = None) -> List[int]:
    """Thực hiện một chuỗi scroll ngẫu nhiên, trả về danh sách số pixels đã scroll (có dấu).

    Không raise exception; luôn trả về list (rỗng nếu lỗi).
    """
    r = rng or random
    results: List[int] = []
    try:
        n = r.randint(min_scrolls, max_scrolls)
        for _ in range(n):
            px = r.randint(min_px, max_px)
            direction = r.choice([-1, 1])
            amount = direction * px
            try:
                driver.execute_script("window.scrollBy({left:0, top: arguments[0], behavior: 'smooth'});", amount)
            except Exception:
                try:
                    driver.execute_script(f"window.scrollBy(0, {amount});")
                except Exception as e:
                    logger.debug("random_scroll execute_script failed: %s", e)
                    continue

            results.append(amount)
            random_sleep(delay_min, delay_max, jitter=0.05, rng=r)

        if r.random() < 0.15:
            try:
                if r.random() < 0.5:
                    driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
                    results.append(-999999)
                else:
                    driver.execute_script("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
                    results.append(999999)
                random_sleep(0.3, 0.9, rng=r)
            except Exception as e:
                logger.debug("random_scroll end jump failed: %s", e)

        return results
    except Exception as e:
        logger.debug("random_scroll error: %s", e)
        return results
