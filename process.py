import scrapy

class EttuSpider(scrapy.Spider):
    '''Parser for m.ettu.ru.'''
    FEED_STORAGES={'c': 'scrapy.contrib.feedexport.FileFeedStorage'} 
    name = "ettuspider"
    start_urls = ["http://m.ettu.ru"]
    
    def parse(self, response):
            first_level_as = response.css(".letter-link")
            for a in first_level_as:
                yield {"level": 1, "link": "http://m.ettu.ru" + a.css("a::attr(href)").extract_first(),
                        "name": a.css("a::text").extract_first()}
            for a in first_level_as:
                yield scrapy.Request("http://m.ettu.ru" + a.css("a::attr(href)").extract_first(), self.parse2)
    
    
    def parse2(self, response):
        second_level_as = response.xpath("//a[contains(@href,'station')]")
        for a in second_level_as:
            yield {"level": 2, "parent_url": response.url,"link": "http://m.ettu.ru" + a.xpath("@href").extract_first(), "name": a.xpath("text()").extract_first()}
        
        for a in second_level_as:
            yield scrapy.Request("http://m.ettu.ru" + a.xpath("@href").extract_first(), self.parse3)
    
    
    def parse3(self, response):
        marker_coords = ""
        try:
            marker_coords = response.xpath("//img/@src").extract_first().split("&markers=size:mid|")[1].split("&path")[0]
        except(AttributeError):
            yield {"level" : 3, "url": response.url, "marker_coords": "", "error": "True"}
        yield {"level" : 3, "url": response.url, "marker_coords": marker_coords, "error": "False"}