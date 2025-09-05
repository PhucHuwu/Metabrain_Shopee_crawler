#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model cho dữ liệu Shop Shopee
Định nghĩa cấu trúc dữ liệu cho cửa hàng
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .product import Product


@dataclass
class Shop:
    """
    Model cho thông tin cửa hàng Shopee
    """
    shop_id: str
    shop_name: str
    shop_url: str
    description: Optional[str] = None
    location: Optional[str] = None
    rating: Optional[float] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    response_rate: Optional[int] = None
    response_time: Optional[str] = None
    joined_date: Optional[datetime] = None
    is_verified: bool = False
    is_preferred: bool = False

    # Thông tin từ Google Maps
    gmaps_address: Optional[str] = None
    gmaps_phone: Optional[str] = None
    gmaps_rating: Optional[float] = None
    gmaps_reviews_count: Optional[int] = None
    gmaps_place_id: Optional[str] = None

    # Metadata
    crawl_date: datetime = field(default_factory=datetime.now)
    products: List['Product'] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """
        Chuyển đổi object thành dictionary
        """
        # TODO: Implement conversion logic
        pass

    @classmethod
    def from_dict(cls, data: Dict) -> 'Shop':
        """
        Tạo Shop object từ dictionary
        """
        # TODO: Implement creation logic
        pass

    def add_product(self, product: 'Product'):
        """
        Thêm sản phẩm vào cửa hàng
        """
        # TODO: Implement add product logic
        pass
