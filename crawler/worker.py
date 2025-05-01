from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        unique_pages = set()
        subdomains = {}
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp, unique_pages, subdomains)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
        with open("pages.txt", 'a', encoding='UTF-8') as file:
            file.write("Number of Unique Pages Found:" + str(len(unique_pages)) + '\n')
            file.write("Number of Unique Pages Found for Each Subdomain:\n")
            for subdomain in subdomains:
                file.write(subdomain + " " + str(subdomains[subdomain]) + "\n")
            file.write("\n\nThe unique pages found were:\n")
            counter = 0
            for page_link in unique_pages:
                file.write("URL #" + str(counter) + ": " + page_link + "\n")
                counter += 1
