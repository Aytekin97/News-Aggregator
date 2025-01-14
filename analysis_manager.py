from typing import List
from schemas import (
    NewsAggregatorResultSchema, 
    SummaryOpenAiResponseSchema, 
    ArticleAnalysisResultSchema, 
    AnalysisResultOpenAiResponseSchema, 
    AgentAnalysisResultSchema,
    AgentModelOpenAiResponseSchema,
    AgentDescriptionListOpenAiResponseSchema
)
from agents import summary_agent, primary_analysis_agent, agent_creator_agent, Agent
from loguru import logger


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