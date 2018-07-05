# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import redis
import requests
import time
from itertools import cycle
from scrapy import signals
from scrapy.exceptions import IgnoreRequest
import pymongo
from scrapy.core.downloader.handlers.http11 import TunnelError
from twisted.web.client import ResponseFailed
from twisted.internet import defer
from twisted.internet.error import TimeoutError, DNSLookupError, \
    ConnectionRefusedError, ConnectionDone, ConnectError, \
    ConnectionLost, TCPTimedOutError


class Cheng95SpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class Cheng95DownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class RandomProxyMiddleware(object):
    set_name = 'jd:proxy_pool'

    EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed,
                           IOError, TunnelError)

    def __init__(self):
        self.proxy = set()

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(
        )
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.
        if len(self.proxy) < 200:
            spider.logger.info('请求代理页面')
            url = ''   # 自己代理页面的URL
            response = requests.get(url)
            self.proxy.update('http://' + x for x in response.text.split())

        if not request.meta.get('proxy'):
            request.meta['proxy'] = self.proxy.pop()
            self.proxy.add(request.meta['proxy'])
        #
            # return self._change_proxy(request, None, spider)
        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
        # print(response.status, response.url)

        if response.status in [302, 400, 404, 403, 405, 500, 503, 502, 504, 429, 408, 407, 307, 401]:
            spider.logger.debug('出现异常状态码')
            # print(f'异常状态码：{response.status}')
            return self._change_proxy(request, None, spider)
        if '请输入验证码' in response.text:
            spider.logger.debug('出现请输入验证码:', response.url)
            return self._change_proxy(request, None, spider)
        if '您访问的页面不存在' in response.text:
            spider.logger.debug('访问的页面不存在')
            raise IgnoreRequest
        if '该职位已暂停招聘' in response.text:
            spider.logger.debug('该职位已暂停招聘')
            raise IgnoreRequest
        if 'detail' in response.url:
            if response.xpath('//div[@class="basic-inner"]/h1/span[1]/text()').extract_first() == None:
                spider.logger.debug('详情页出现异常', response.url)
                return self._change_proxy(request, None, spider)
        if 'search' in response.url:
            if response.xpath('//div[@class="layout-main main"]') == []:
                spider.logger.debug('索引页出现异常', response.url)
                return self._change_proxy(request, None, spider)


        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.
        # print(exception)
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY):
            spider.logger.debug(exception)
            return self._change_proxy(request, None, spider)
        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain

    def _change_proxy(self, request, exception, spider):
        proxy = request.meta.get('proxy')
        if proxy:
            spider.logger.debug(f'移除无用代理 {proxy}')
            self.proxy.discard(proxy)
        proxy = self.proxy.pop()
        self.proxy.add(proxy)
        if proxy:
            request.meta['proxy'] = proxy
            spider.logger.debug(f'使用代理 {proxy}')
        return request

    def spider_opened(self, spider):
        spider.logger.info('Proxy_Pool: %s' % spider.name)


class DereplicationMiddleware(object):

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(
            mongo_uri=crawler.settings.get('MONGO_URL'),
            mongo_db=crawler.settings.get('MONGO_DATABASE'),
        )
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def spider_opened(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def process_request(self, request, spider):
        # Called with the response returned from the downloader.
        # print(

        if self.db.cheng59.find_one({'url': request.url}, {'_id': 1}):
            spider.logger.debug("去重")
            raise IgnoreRequest()
        # Must either;
        # - return a Res
        # ponse object
        # - return a Request object
        # - or raise IgnoreRequest
        return None