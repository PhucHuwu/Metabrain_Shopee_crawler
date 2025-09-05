#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cấu hình chính cho Shopee + Google Maps Crawler
Chứa tất cả các thiết lập cần thiết cho hệ thống
"""

import os
from typing import Dict, List

# ======================== DATABASE CONFIG ========================
DATABASE_CONFIG = {
    'MYSQL': {
        'host': 'localhost',
        'port': 3306,
        'database': 'shopee_crawler',
        'user': 'root',
        'password': '',
        'charset': 'utf8mb4'
    },
    'MONGODB': {
        'host': 'localhost',
        'port': 27017,
        'database': 'shopee_crawler',
        'collection': 'shopee_crawler'
    }
}

# ======================== CRAWLER CONFIG ========================
CRAWLER_CONFIG = {
    'MAX_THREADS': 5,
    'REQUEST_DELAY': (1, 3),  # Random delay giữa các request (min, max)
    'MAX_RETRIES': 3,
    'TIMEOUT': 30,
    'BATCH_SIZE': 100,
    'CHECKPOINT_INTERVAL': 50  # Lưu checkpoint sau mỗi X items
}

# ======================== SELENIUM CONFIG ========================
SELENIUM_CONFIG = {
    'HEADLESS': False,
    'WINDOW_SIZE': (1920, 1080),
    'PAGE_LOAD_TIMEOUT': 30,
    'IMPLICIT_WAIT': 10,
    'PROFILE_DIR': './selenium_profiles'
}

# ======================== SHOPEE CONFIG ========================
SHOPEE_CONFIG = {
    'BASE_URL': 'https://shopee.vn/mall',
    'SEARCH_ENDPOINT': '/search',
    'SHOP_ENDPOINT': '/shop',
    'MAX_PAGES_PER_SEARCH': 50,
    'CATEGORIES': [
        'thoi-trang-nu', 'dien-thoai-phu-kien',
        'thoi-trang-nam', 'may-tinh-laptop',
        'nha-cua-doi-song', 'me-be'
    ]
}

# ======================== GOOGLE MAPS CONFIG ========================
GOOGLE_MAPS_CONFIG = {
    'API_KEY': '',  # Cần thiết lập từ environment variable
    'SEARCH_RADIUS': 50000,  # 50km
    'MAX_RESULTS_PER_SEARCH': 20
}

# ======================== OUTPUT CONFIG ========================
OUTPUT_CONFIG = {
    'DATA_DIR': './data',
    'OUTPUT_FORMATS': ['csv', 'excel', 'json'],
    'FILENAME_PREFIX': 'shopee_data',
    'DATE_FORMAT': '%Y%m%d_%H%M%S'
}

# ======================== LOGGING CONFIG ========================
LOGGING_CONFIG = {
    'LOG_DIR': './logs',
    'LOG_LEVEL': 'INFO',
    'LOG_FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'MAX_LOG_SIZE': 10 * 1024 * 1024,  # 10MB
    'BACKUP_COUNT': 5
}

# ======================== USER AGENTS ========================
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

# ======================== HELPER FUNCTIONS ========================


def get_config(section: str) -> Dict:
    """
    Lấy cấu hình theo section
    """
    config_map = {
        'database': DATABASE_CONFIG,
        'crawler': CRAWLER_CONFIG,
        'selenium': SELENIUM_CONFIG,
        'shopee': SHOPEE_CONFIG,
        'gmaps': GOOGLE_MAPS_CONFIG,
        'output': OUTPUT_CONFIG,
        'logging': LOGGING_CONFIG
    }
    return config_map.get(section.lower(), {})


def get_user_agent() -> str:
    """
    Lấy random user agent
    """
    import random
    return random.choice(USER_AGENTS)


# Load environment variables nếu có
GOOGLE_MAPS_CONFIG['API_KEY'] = os.getenv('GOOGLE_MAPS_API_KEY', '')
