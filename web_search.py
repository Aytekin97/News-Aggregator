import requests
from datetime import datetime, timedelta
import time
from typing import List

from loguru import logger
from config import settings
from schemas import LinkTagsSchema


class GoogleSearchClient:
    def __init__(self):
        self.api_key = settings.google_search_api_key
        self.search_engine_id = settings.google_search_engine_id
        self.url = settings.google_search_engine_url
        self.news_range_in_days = settings.news_range_in_days
        self.number_of_retries = settings.google_search_number_of_retries

    def get_news_links(self) -> List[LinkTagsSchema]:
        link_tags_response = self.fetch_news()
        logger.info("Links fetched length: {length}.".format(length=len(link_tags_response)))
        return link_tags_response

    def fetch_news(self) -> List[LinkTagsSchema]:
        from_date = (datetime.now() - timedelta(days=self.news_range_in_days)).strftime("%Y%m%d")
        to_date = datetime.now().strftime("%Y%m%d")

        keyWords = {
            "Load Growth news New York": "Load Growth",
            "Demand Response news New York": "Demand Response",
            "Zero-emission news New York": "Zero-Emission",
            "Grid Reliability news New York": "Grid Reliability",
            "Peak demand news New York": "Peak Demand",
            "Grid Interconnection news New York": "Grid Interconnection",
            "Battery energy storage system (BESS) news New York": "BESS",
            "Energy Storage news New York": "Energy Storage",
        }

        # Values respresents links to exclude, if no value,
        # then there will be no links to exclude
        sites = {
            "utilitydive.com/news/": "",
            "powermag.com/": ["powermag.com/category/", "powermag.com/author/", "powermag.com/tag/"],
            "canarymedia.com/articles/": "",
            "latitudemedia.com/news/": "",
            "energy-storage.news/": [
                "energy-storage.news/category",
                "energy-storage.news/subjects",
                "energy-storage.news/tag/",
            ],
            "thehill.com/opinion/energy-environment/": "",
            "thehill.com/policy/energy-environment/": "",
            "thehill.com/homenews/": "",
            "heatmap.news/sparks/": "",
            "about.bnef.com/blog/": ["about.bnef.com/blog/category/"],
            "theconversation.com/": [
                "theconversation.com/uk",
                "theconversation.com/topics/",
                "theconversation.com/us/topics/",
                "theconversation.com/nz/topics/",
                "theconversation.com/us",
                "theconversation.com/au",
            ],
            "thecity.nyc/": ["thecity.nyc/author/"],
            "politico.com/news/": "politico.com/news/new-york",
            "prnewswire.com/news-releases/": "",
            "governor.ny.gov/news/": "governor.ny.gov/news?",
            "nyserda.ny.gov/About/Newsroom/": "",
            "renews.biz/": ["renews.biz/tags?", "renews.biz/remix"]
        }

        results = []
        request_count = 0
        seen_links = set()

        for keyWord, tag in keyWords.items():
            for site, exclusions in sites.items():
                if request_count >= 90:
                    time.sleep(60)
                    request_count = 0

                query = f"{keyWord} site:{site}"

                if exclusions:
                    exclusion_str = " ".join([f"-inurl:{url}" for url in exclusions])
                    query += f" {exclusion_str}"

                params = {
                    "q": query,
                    "key": self.api_key,
                    "cx": self.search_engine_id,
                    "sort": f"date:r:{from_date}:{to_date}",
                }

                response = requests.get(self.url, params=params)
                request_count += 1
                result = response.json()

                if "items" in result:
                    for item in result["items"]:
                        link = item.get("link")
                        if link and link not in seen_links:
                            seen_links.add(link)
                            results.append(LinkTagsSchema(link=link, tags=[tag]))
                        elif link and link in seen_links:
                            for result in results:
                                if result.link == link:
                                    result.tags.append(tag)

        return results
