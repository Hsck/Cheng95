import time
from scrapy import Request
from scrapy.contrib.linkextractors import LinkExtractor
import scrapy
import re
from cheng95.items import Cheng95Item


class cheng95Spider(scrapy.Spider):
    name = 'cheng95'
    start_urls = [
        'http://www.cheng95.com/positions/detail?id=29612904',
        'http://www.cheng95.com/positions/search?keyword=%E8%AE%A1%E7%AE%97%E6%9C%BA',  # 计算机
        'http://www.cheng95.com/positions/search?keyword=%E6%88%BF%E5%9C%B0%E4%BA%A7',  # 房地产
        'http://www.cheng95.com/positions/search?keyword=%E5%88%B6%E9%80%A0',  # 制造
        'http://www.cheng95.com/positions/search?keyword=%E5%8C%BB%E7%96%97',  # 医疗
        'http://www.cheng95.com/positions/search?keyword=%E9%87%91%E8%9E%8D',  # 金融
        'http://www.cheng95.com/positions/search?keyword=%E6%9C%8D%E5%8A%A1',  # 服务
        'http://www.cheng95.com/positions/search?keyword=%E8%B4%A2%E5%8A%A1',  # 财务
        'http://www.cheng95.com/positions/search?keyword=%E9%94%80%E5%94%AE',  # 销售
        'http://www.cheng95.com/positions/search?keyword=%E6%95%99%E8%82%B2',  # 教育
        'http://www.cheng95.com/positions/search?keyword=%E7%89%A9%E6%B5%81',  # 物流
        'http://www.cheng95.com/positions/search?keyword=%E8%83%BD%E6%BA%90',  # 能源
        'http://www.cheng95.com/positions/search?keyword=%E6%94%BF%E5%BA%9C',  # 政府
        'http://www.cheng95.com/positions/search?keyword=%E5%B9%BF%E5%91%8A',  # 广告
    ]

    def parse(self, response):
        # item2： 提取此页面所有的详情页，加入请求队列
        item2 = LinkExtractor(allow='\/detail', allow_domains='cheng95.com')
        for link in item2.extract_links(response):
            yield Request(url=link.url, priority=2, callback=self.parse, meta={'dont_redirect': True})
        # item1：提取此页面所有的索引页，加入请求队列
        item1 = LinkExtractor(allow='\/positions', allow_domains='cheng95.com', deny=('\/detail', '\/analyze'))
        for link in item1.extract_links(response):
            yield Request(url=link.url, priority=1, callback=self.parse, meta={'dont_redirect': True})
        # 如果当前请求的页面是索引页，从页面里解析出它的Total_count(总页面数)，并加入请求队列
        if 'search' in response.url:
            self.logger.debug('索引页')
            pattern = re.compile('totalpage: (\d*),', re.S)
            total_count = re.findall(pattern, response.text)
            if total_count:
                if 'page' not in response.request.url:
                    count = int(total_count[0])
                    if count > 500:
                        count = 500
                    # print('count数量:', count)
                    for page in range(2, count + 1):
                        next_url = response.request.url + '&page=' + str(page)
                        yield Request(url=next_url, priority=1, callback=self.parse, meta={'dont_redirect': True})
            else:
                self.logger.debug('索引页IP被禁')
        # 当目前的页面是详情页时，Xpath方式解析字段
        elif 'detail' in response.url:
            self.logger.debug('详情页')
            item = Cheng95Item()
            if response.xpath('//div[@class="basic-inner"]/h1/span[1]/text()').extract_first() != None:
                item['url'] = response.request.url
                item['title'] = response.xpath('//div[@class="basic-inner"]/h1/span[1]/text()').extract_first()
                item['company'] = response.xpath('//h2[@class="company-name"]/text()').extract_first('')
                item['salary'] = response.xpath('//div[@class="basic-inner"]/h1/span[2]/text()').extract_first('')
                others = response.xpath('//p[@class="extra-info clearfix"]/span/text()').extract()
                if others:
                    pattern1 = re.compile('招聘\d+人', re.S)
                    pattern2 = re.compile('中专|高中|本科|专科|硕士|博士', re.S)
                    if re.findall(pattern1, str(others)):
                        item['need'] = re.findall(pattern1, str(others))[0]
                    else:
                        item['need'] = None
                    if re.findall(pattern2, str(others)):
                        item['education'] = re.findall(pattern2, str(others))[0]
                    else:
                        item['education'] = None
                    item['come_from'] = others[-3]
                    item['release_time'] = others[-1]
                    item['address'] = others[-5]
                head = response.xpath('//div[@class="position-module position-detail"]/div[@class="module-hd"]/h3/text()').extract()
                content = response.xpath('//div[@class="position-module position-detail"]/div[@class="module-bd"]')
                for i in range(len(head)):
                    word = head.pop(0)
                    if word == '工作内容':
                        q = content.pop(0).xpath('text()').extract()
                        item['job_content'] = "".join([i.strip() for i in q])
                    elif word == '职位要求':
                        q = content.pop(0).xpath('text()').extract()
                        item['job_requirement'] = "".join([i.strip() for i in q])
                    elif word == '工作地点':
                        item['detail_address'] = content.pop(0).xpath('text()').extract_first('')
                    else:
                        pass
                yield item
            else:
                self.logger.debug('详情页IP被禁')
        else:
            pass
