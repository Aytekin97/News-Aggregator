#!/usr/bin/env python

from typing import List

from fastapi import FastAPI, HTTPException
import os

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
    CompanyRequest
)

from article_fetcher import ArticleFetcher
from web_search import GoogleSearchClient
from openai_client import OpenAiClient, OpenAiClientForDates
from db import Sessions, NewsModel, TagModel
from config import settings


app = FastAPI()

@app.post("/process-news")
def main(request: CompanyRequest):

    company = request.company
    try:
        google_search_client = GoogleSearchClient(company)
        logger.info("Google search client created.")
        openai_client = OpenAiClient()
        openai_client_for_dates = OpenAiClientForDates()
        logger.info("OpenAI client created.")

        links_tags = google_search_client.get_news_links()

        article_fetcher = ArticleFetcher(links_tags, openai_client_for_dates)
        logger.info("Article fetcher created.")
        articles = article_fetcher.get_all_articles()
        logger.info("Articles fetched")
        logger.info(f"Number of articles fetched: {len(articles)}")

        company_based_articles = filter_company_based_articles(articles, openai_client, company)

        company_based_articles_with_dates = article_fetcher.get_published_date(company_based_articles)

        dynamic_agents = create_dynamic_agents(company_based_articles_with_dates, openai_client)
        
        analysis = run_analysis(company_based_articles_with_dates, dynamic_agents, openai_client)

        summaries = summarize_analyses(analysis, openai_client)

        logger.info("Found {count} summaries.".format(count=len(summaries)))

        for s in Sessions:
            session: Session = s()
            for summary in summaries:
                try:
                    logger.info(
                        "Adding summary to database {engine} for {link}.".format(
                            engine=session.bind.url.database,
                            link=summary.link,
                        )
                    )
                    news_article = NewsModel(
                        classification_score=summary.classification_score,
                        title=summary.title,
                        summary=summary.summary,
                        link=str(summary.link),  # Convert URL to string
                        published_date=summary.published_date,
                    )
                    from sqlalchemy.sql import select
                    for tag_name in summary.tags:
                        tag_name_normalized = tag_name.strip().lower()
                        logger.debug(f"Processing tag: {tag_name_normalized}")
                        try:
                            tag = session.scalars(select(TagModel).where(TagModel.name == tag_name_normalized)).first()
                            if not tag:
                                tag = TagModel(name=tag_name_normalized)
                                session.add(tag)
                                session.flush()  # Ensure tag gets an ID
                                logger.debug(f"Added new tag with ID: {tag.id}")
                            else:
                                logger.debug(f"Tag already exists with ID: {tag.id}")
                            news_article.tags.append(tag)
                        except Exception as e:
                            logger.error(f"Error processing tag '{tag_name_normalized}': {e}")
                            session.rollback()

                    session.add(news_article)
                    session.commit()
                except IntegrityError as e:
                    logger.info("Link already exists in the database.")
                    logger.error("Integrity error: {error}.".format(error=str(e)))
                    session.rollback()
                except Exception as e:
                    session.rollback()
                    logger.error("Database error: {error}.".format(error=str(e)))

    except Exception as e:
        logger.error(f"Error processing news for {company}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the news.")



def summarize_analyses(analysis, openai_client) -> List[NewsAggregatorResultSchema]:
    def get_summary(analysis, openai_client) -> NewsAggregatorResultSchema:
        all_reports = [agent_analysis.analysis for agent_analysis in analysis.analysis]
        all_reports_string = "".join(all_reports)
        prompt = summary_agent.prompt(all_reports_string)
        summary = openai_client.query_gpt(prompt, SummaryOpenAiResponseSchema)
        return NewsAggregatorResultSchema(
            link=analysis.link,
            title=analysis.title,
            published_date=analysis.published_date,
            classification_score=analysis.score,
            summary=summary.summary,
            tags=analysis.tags,
        )

    articles_with_summaries = []
    for anl in analysis:
        all_agents_analysis = get_summary(anl, openai_client)
        articles_with_summaries.append(all_agents_analysis)
    logger.info("Summarization done.")
    return articles_with_summaries


def run_analysis(articles, dynamic_agents, openai_client) -> List[ArticleAnalysisResultSchema]:
    def analyze_article(article, dynamic_agents, openai_client) -> ArticleAnalysisResultSchema:
        analysis_per_article = []
        for agent in dynamic_agents:
            prompt = agent.prompt(f"article:{article.text}")
            analysis_result_per_agent = openai_client.query_gpt(prompt, AnalysisResultOpenAiResponseSchema)
            analysis_per_article.append(AgentAnalysisResultSchema(analysis=analysis_result_per_agent.analysis))
        return ArticleAnalysisResultSchema(
            link=article.link,
            title=article.title,
            score=article.score,
            analysis=analysis_per_article,
            published_date=article.published_date,
            tags=article.tags,
        )

    all_analysis = []
    for article in articles:
        article_analysis_result = analyze_article(article, dynamic_agents, openai_client)
        all_analysis.append(article_analysis_result)
    logger.info("Analysis done.")
    return all_analysis

def create_dynamic_agents(company_based_articles_with_dates, openai_client) -> List[Agent]:
    def make_dynamic_agents(agents_needed, openai_client):
        prompts = [agent_creator_agent.prompt(i) for i in agents_needed]
        agent_meta_data = [openai_client.query_gpt(i, AgentModelOpenAiResponseSchema) for i in prompts]
        dynamic_agents = [Agent(i.name, i.role, i.function) for i in agent_meta_data]
        return dynamic_agents

    news = "".join([i.text for i in company_based_articles_with_dates])
    prompt = primary_analysis_agent.prompt(f"News: {news}")
    dynamic_agents_descriptions = openai_client.query_gpt(prompt, AgentDescriptionListOpenAiResponseSchema)
    agents_needed = [f"name:{i.name} description:{i.description}" for i in dynamic_agents_descriptions.agents]

    n_try = 5
    for i in range(n_try):
        try:
            dynamic_agents = make_dynamic_agents(agents_needed, openai_client)
            break
        except Exception as e:
            logger.info("Failed to create agents, trying again.")
            if i == n_try - 1:
                raise e
    logger.info("Dynamic agents created.")
    return dynamic_agents

def filter_company_based_articles(articles: List[ArticleResponseSchema], openai_client, company) -> List[ArticleClassificationScoreSchema]:
    all_articles = get_classification_score_of_company_based_news(articles, openai_client, company)
    filtered_articles = [result for result in all_articles if result.score >= settings.classification_score_threshold]
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


@app.get("/")
def health_check():
    """
    Basic health check endpoint to verify the API is running.
    """
    return {"status": "API is running!"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Default to 8000 if Railway doesn't provide a PORT variable
    uvicorn.run(app, host="0.0.0.0", port=port)
