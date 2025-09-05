#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model cho dữ liệu Product Shopee
Định nghĩa cấu trúc dữ liệu cho sản phẩm
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class Product:
    """
    Model cho thông tin sản phẩm Shopee
    """
    product_id: str
    name: str
    url: str
    shop_id: str
    price: Optional[float] = None
    original_price: Optional[float] = None
    discount_percent: Optional[int] = None
    sold_count: Optional[int] = None
    stock_count: Optional[int] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    images: List[str] = field(default_factory=list)
    attributes: Dict = field(default_factory=dict)

    # Metadata
    crawl_date: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    def to_dict(self) -> Dict:
        """
        Chuyển đổi object thành dictionary
        """
        # TODO: Implement conversion logic
        pass

    @classmethod
    def from_dict(cls, data: Dict) -> 'Product':
        """
        Tạo Product object từ dictionary
        """
        # TODO: Implement creation logic
        pass

    def calculate_discount_price(self) -> Optional[float]:
        """
        Tính giá sau khi giảm giá
        """
        # TODO: Implement discount calculation
        pass
