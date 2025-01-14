#!/usr/bin/env python
from fastapi import FastAPI, HTTPException
import os
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from agents import news_question_generator_agent
from schemas import CompanyRequest, QuestionsThresholdSchema
from article_fetcher import ArticleFetcher
from web_search import GoogleSearchClient
from openai_client import OpenAiClient, OpenAiClientForDates
from db import Sessions, NewsModel, TagModel
from classification_manager import filter_company_based_articles
from analysis_manager import create_dynamic_agents, run_analysis, summarize_analyses


app = FastAPI()

@app.post("/process-news")
def main(request: CompanyRequest):

    companies = request.companies
    for company in companies:
        logger.info(f"Getting news for: {company}")
        try: 
            openai_client = OpenAiClient()
            openai_client_for_dates = OpenAiClientForDates()
            logger.info("OpenAI client created.")

            logger.info(f"Getting search terms and threshold")
            news_question_generator_agent.set_company(company)
            prompt = news_question_generator_agent.prompt(company)
            output = openai_client.query_gpt(prompt, QuestionsThresholdSchema)
            logger.success(f"Number of questions: {len(output.questions)}, Threshold: {output.threshold}")

            google_search_client = GoogleSearchClient(company, request.number_of_days, openai_client)
            logger.info("Google search client created.")

            links_tags = google_search_client.get_news_links()

            article_fetcher = ArticleFetcher(links_tags, openai_client_for_dates)
            logger.info("Article fetcher created.")
            articles = article_fetcher.get_all_articles()
            logger.info("Articles fetched")
            logger.info(f"Number of articles fetched: {len(articles)}")

            company_based_articles = filter_company_based_articles(articles, openai_client, company, output)

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
                            company_name=company
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
