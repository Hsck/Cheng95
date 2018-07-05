# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Cheng95Item(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    company = scrapy.Field()
    salary = scrapy.Field()
    need = scrapy.Field()
    education = scrapy.Field()
    come_from = scrapy.Field()
    release_time = scrapy.Field()
    address = scrapy.Field()
    detail_address = scrapy.Field()
    job_requirement = scrapy.Field()
    job_content = scrapy.Field()

