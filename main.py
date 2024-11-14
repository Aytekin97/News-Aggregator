#!/usr/bin/env python

from typing import List

from loguru import logger

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError



from article_fetcher import ArticleFetcher
from web_search import GoogleSearchClient
from openai_client import OpenAiClient
#from db import Sessions, NewsModel, TagModel
from config import settings


def main():
    google_search_client = GoogleSearchClient()
    logger.info("Google search client created.")
    openai_client = OpenAiClient()
    logger.info("OpenAI client created.")

    links_tags = google_search_client.get_news_links()

    article_fetcher = ArticleFetcher(links_tags, openai_client)
    logger.info("Article fetcher created.")


if __name__ == "__main__":
    main()
