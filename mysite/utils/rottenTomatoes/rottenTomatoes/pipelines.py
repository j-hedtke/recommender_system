# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json
from scrapy.exceptions import DropItem
import re

YEAR_CUTOFF = 2000

class RottentomatoesPipeline(object):
    def process_item(self, item, spider):
        if item is not None:
            if item.get('title') and item.get('reviewer') and item.get('rating'):
                year = item.get('year')
                if year:
                    if re.search('TV', year) is None and int(year) >= YEAR_CUTOFF:
                        return item
        raise DropItem("Missing field in %s" % item) 
