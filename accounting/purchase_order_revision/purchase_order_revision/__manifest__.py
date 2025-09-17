# -*- coding: utf-8 -*-
# Copyright 2023 Basic Solution Co., Ltd. (<https://www.basic-solution.com/>)


{
    "name": "Purchasee order revisions",
    "summary": "Keep track of revised purchase order",
    "version": "14.0.0.0.0",
    "category": "Purchase orders",
    "author": "Basic Solution Co., Ltd.",
    "website": "https://www.basic-solution.com",
    "license": "AGPL-3",
    "depends": ["base_revision", "purchase"],
    "data": ["views/purchase_order.xml"],
    "installable": True,
    "post_init_hook": "populate_unrevisioned_name",
}

