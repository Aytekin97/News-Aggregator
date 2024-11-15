#!/usr/bin/env python

from typing import List

import html

import os
import json

from loguru import logger

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from agent import news_classification_agent, agent_creator_agent, primary_analysis_agent, summary_agent, Agent

from schemas import (
    ClassificationScoreOpenAiResponseSchema,
    AgentDescriptionListOpenAiResponseSchema,
    AgentModelOpenAiResponseSchema,
    AnalysisResultOpenAiResponseSchema,
    SummaryOpenAiResponseSchema,
    ArticleClassificationScoreSchema,
    NewsAggregatorResultSchema,
    ArticleAnalysisResultSchema,
    AgentAnalysisResultSchema,
    ArticleResponseSchema,
)

from article_fetcher import ArticleFetcher
from web_search import GoogleSearchClient
from openai_client import OpenAiClient
#from db import Sessions, NewsModel, TagModel
from config import settings

path = os.path.join(os.path.dirname(__file__), "web_search_results.json")


def main(company):
    google_search_client = GoogleSearchClient(company)
    logger.info("Google search client created.")
    openai_client = OpenAiClient()
    logger.info("OpenAI client created.")

    links_tags = google_search_client.get_news_links()

    article_fetcher = ArticleFetcher(links_tags, openai_client)
    logger.info("Article fetcher created.")
    articles = article_fetcher.get_all_articles()
    logger.info("Articles fetched")
    logger.info(f"Number of articles fetched: {len(articles)}")

    company_based_articles = filter_company_based_articles(articles, openai_client, company)

    with open(path, "w") as file:
        company_based_articles_data = [company_based_article.dict() for company_based_article in company_based_articles]
        json.dump(company_based_articles_data, file, indent=4, default=str)






def filter_company_based_articles(articles: List[ArticleResponseSchema], openai_client, company) -> List[ArticleClassificationScoreSchema]:
    all_articles = get_classification_score_of_company_based_news(articles, openai_client, company)
    filtered_articles = [result for result in all_articles if result.score >= settings.ny_classification_score_threshold]
    sorted_filtered_articles = sorted(filtered_articles, key=lambda x: x.score, reverse=True)
    logger.info("Number of articles before classification: {length}.".format(length=len(articles)))
    logger.info("Number of articles after classification: {}.".format(len(filtered_articles)))
    return sorted_filtered_articles

def get_classification_score_of_company_based_news(articles, openai_client, company) -> List[ArticleClassificationScoreSchema]:
    results = []
    for article in articles:
        result = get_classification_result(article, openai_client, company)
        results.append(result)
    return results

def get_classification_result(article, openai_client, company) -> ArticleClassificationScoreSchema:
    news_classification_agent.set_company(company)
    prompt = news_classification_agent.prompt(f"link: {article.link}, title: {article.title}, text: {article.text}")
    output = openai_client.query_gpt(prompt, ClassificationScoreOpenAiResponseSchema)
    if isinstance(output, ClassificationScoreOpenAiResponseSchema):
        return ArticleClassificationScoreSchema(
            link=article.link,
            title=article.title,
            score=output.score,
            tags=article.tags,
            text=article.text,
            published_date=article.published_date,
            html=article.html,
        )
    else:
        logger.error("Classification response schema is not valid.")



if __name__ == "__main__":
    main("AMAZON")
