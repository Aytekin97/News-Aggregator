import requests
from datetime import datetime, timedelta
import time
from typing import List
from agents import search_terms_agent
from loguru import logger
from config import settings
from schemas import LinkTagsSchema, SearchTermsSchema


class GoogleSearchClient:
    def __init__(self, company, number_of_days, openai_client):
        self.api_key = settings.google_search_api_key
        self.search_engine_id = settings.google_search_engine_id
        self.url = settings.google_search_engine_url
        self.news_range_in_days = number_of_days
        self.number_of_retries = settings.google_search_number_of_retries
        self.company = company
        self.openai_client = openai_client

    def get_news_links(self) -> List[LinkTagsSchema]:
        link_tags_response = self.fetch_news()
        logger.info("Links fetched. Length: {length}.".format(length=len(link_tags_response)))
        return link_tags_response

    def fetch_news(self) -> List[LinkTagsSchema]:
        from_date = (datetime.now() - timedelta(days=self.news_range_in_days)).strftime("%Y%m%d")
        to_date = datetime.now().strftime("%Y%m%d")

        search_terms_agent.set_company(self.company)
        prompt = search_terms_agent.prompt(self.company)
        logger.info(f"Querying ChatGPT to get search terms and tags")
        pairs = self.openai_client.query_gpt(prompt, SearchTermsSchema)
        logger.success(f"Pairs received. Number of pairs: {len(pairs)}")

        # Values respresents links to exclude, if no value,
        # then there will be no links to exclude
        sites = {
            "investopedia.com": "",
            "fool.com": "",
            "finance.yahoo.com/news": ""
        }        

        results = []
        request_count = 0
        seen_links = set()

        for pair in pairs:
            for site, exclusions in sites.items():
                if request_count >= 90:
                    time.sleep(60)
                    request_count = 0

                query = f"{pair.search_term} site:{site}"

                if exclusions:
                    exclusion_str = " ".join([f"-inurl:{url}" for url in exclusions])
                    query += f" {exclusion_str}"

                params = {
                    "q": query,
                    "key": self.api_key,
                    "cx": self.search_engine_id,
                    "sort": f"date:r:{from_date}:{to_date}",
                }

                logger.info(f"Searching: {query}")

                response = requests.get(self.url, params=params)
                request_count += 1
                result = response.json()

                if "items" in result:
                    for item in result["items"]:
                        link = item.get("link")
                        if link and link not in seen_links:
                            seen_links.add(link)
                            results.append(LinkTagsSchema(link=link, tags=[pair.tag]))
                        elif link and link in seen_links:
                            for result in results:
                                if result.link == link:
                                    result.tags.append(pair.tag)

        return results
    