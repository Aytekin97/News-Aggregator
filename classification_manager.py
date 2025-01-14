from loguru import logger
from config import settings
from schemas import ArticleClassificationScoreSchema, ArticleResponseSchema, ClassificationScoreOpenAiResponseSchema
from agents import news_classification_agent
from typing import List


def filter_company_based_articles(articles: List[ArticleResponseSchema], openai_client, company, questions_and_threshold) -> List[ArticleClassificationScoreSchema]:
    all_articles = get_classification_score_of_company_based_news(articles, openai_client, company, questions_and_threshold)
    filtered_articles = [result for result in all_articles if result.score >= questions_and_threshold.threshold]
    sorted_filtered_articles = sorted(filtered_articles, key=lambda x: x.score, reverse=True)
    logger.info("Number of articles before classification: {length}.".format(length=len(articles)))
    logger.info("Number of articles after classification: {}.".format(len(filtered_articles)))
    return sorted_filtered_articles

def get_classification_score_of_company_based_news(articles, openai_client, company, questions_and_threshold) -> List[ArticleClassificationScoreSchema]:
    results = []
    for article in articles:
        result = get_classification_result(article, openai_client, company, questions_and_threshold)
        results.append(result)
    return results

def get_classification_result(article, openai_client, company, questions_and_threshold) -> ArticleClassificationScoreSchema:
    combined_questions = "\n".join(questions_and_threshold.questions)
    news_classification_agent.function = combined_questions
    prompt = news_classification_agent.prompt(f"link: {article.link}, company name: {company} title: {article.title}, text: {article.text}")
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