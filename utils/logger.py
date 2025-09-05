#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger utility
Cấu hình logging cho toàn bộ hệ thống
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(name: str, config: dict, console_output: bool = True) -> logging.Logger:
    """
    Thiết lập logger với cấu hình tùy chỉnh
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config['LOG_LEVEL']))

    # Tạo thư mục logs nếu chưa tồn tại
    log_dir = config['LOG_DIR']
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # File handler với rotation
    log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config['MAX_LOG_SIZE'],
        backupCount=config['BACKUP_COUNT'],
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Định dạng cho console (có màu)
        try:
            import colorlog
            console_formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
        except ImportError:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)

        logger.addHandler(console_handler)

    # Định dạng cho file
    file_formatter = logging.Formatter(
        config['LOG_FORMAT'],
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    logger.addHandler(file_handler)

    # Ngăn không cho log duplicate
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Lấy logger đã được cấu hình
    """
    return logging.getLogger(name)


def log_function_call(func):
    """
    Decorator để log function calls
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Gọi function: {func.__name__} với args: {args}, kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Function {func.__name__} hoàn thành thành công")
            return result
        except Exception as e:
            logger.error(f"Lỗi trong function {func.__name__}: {e}")
            raise
    return wrapper
