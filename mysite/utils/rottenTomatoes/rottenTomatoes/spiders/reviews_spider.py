import scrapy
from scrapy_splash import SplashRequest
import re
import string
from rottenTomatoes.items import Review

#lua script for splash requests
script = """
function main(splash)
  splash:init_cookies(splash.args.cookies)
  assert(splash:go{
    splash.args.url,
    headers=splash.args.headers,
    http_method=splash.args.http_method,
    body=splash.args.body,
    })
  assert(splash:wait(0.5))

  local entries = splash:history()
  local last_response = entries[#entries].response
  return {
    url = splash:url(),
    headers = last_response.headers,
    http_status = last_response.status,
    cookies = splash:get_cookies(),
    html = splash:html(),
  }
end
"""

nREVIEWER_PAGES = 10

class ReviewsSpider(scrapy.Spider):
    name = "reviews"

    def start_requests(self):
        urls = [
            #'https://www.rottentomatoes.com/browse/dvd-streaming-all/'
            #'https://www.rottentomatoes.com/m/the_man_who_killed_don_quixote/reviews/',
            'https://www.rottentomatoes.com/critics/authors'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
            
            #for splash requests to render javascript
            """
            yield SplashRequest(url, self.parse,
                #without lua
                

                #with lua
                endpoint='execute',
                cache_args = ['lua_source'],
                args={'lua_source': script},
                headers={'X-My-Header': 'value'},
            )
            """

    #for starting at https://www.rottentomatoes.com/critics/authors, iterating through links to letters of alphabet
    def parse(self, response):
        for a in response.xpath('//div[has-class("container")][@id="main_container"]/div[1]/section[1]/div[1]/div[1]/div[1]/div[1]/div[2]/ul[1]/li'):
            href = a.css('a').attrib['href']
            yield response.follow(href, callback=self.parse_each_letter)
        
        #test for just letter 'a': passed
        """
        href = response.xpath('//div[has-class("container")][@id="main_container"]/div[1]/section[1]/div[1]/div[1]/div[1]/div[1]/div[2]/ul[1]/li').css('a').attrib['href']
        yield response.follow(href, callback=self.parse_each_letter)
        """
    #for each page of critics with last name starting with letter, follow link to each reviewer's page
    def parse_each_letter(self, response):
        for a in response.xpath('//div[has-class("container")][@id="main_container"]/div[1]/section[1]/div[1]/div[1]/div[1]/div[1]/table[1]/tbody[1]/tr/td/p/a[1]'):
            href = a.css('a').attrib['href']
            yield response.follow(href, callback = self.parse_reviewer)

    #follow link to next page of reviews (up to 10 pages) if not none
    def parse_reviewer(self, response):
        for i in range(1, nREVIEWER_PAGES):
            next_page = '?page=' + str(i)
            yield response.follow(next_page, self.parse_reviews)

    #parse reviews on each page of reviews for each reviewer
    def parse_reviews(self, response):
        #get reviewer name and org
        if response.status == 200:
            name = response.xpath('//div[@class="col-full-xs col-sm-19 col-critic-name"]/h1[1]/text()').get()
            orgName = response.xpath('//span[@class="col-sm-19 col-xs-14"]/a[1]/text()').get()
            #get each movie review
            for tr in response.xpath('//tbody[@id ="review-table-body"]/tr'):
                review = Review(reviewer = name, org = orgName)
                review['title'] = tr.xpath('./td[3]/a/text()').get().strip(' \n')
                review['year'] = tr.xpath('./td[3]').css('td::text').getall()[1].strip(' \n()')
                review['rating'] = tr.xpath('./td[1]/span[@class]').re_first(r'(fresh|rotten)')
                yield review

