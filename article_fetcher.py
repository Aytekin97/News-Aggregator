from newspaper import Article
from newspaper import Config
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from datetime import date
from bs4 import BeautifulSoup
import json
from dateutil import parser

from loguru import logger
from schemas import ArticlePublishedDateOpenAiResponseSchema, ArticleResponseSchema, ArticleWithPublishedDateResponseSchema
from agent import published_date_agent


class ArticleFetcher:
    def __init__(self, links_tags, openai_client):
        self.links_tags = links_tags
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )
        self.openai_client = openai_client
        self.config = Config()
        self.config.browser_user_agent = self.user_agent
        self.config.request_timeout = 20

    def __fetch_article(self, link_tags):
        article = Article(link_tags.link, config=self.config)
        try:
            article.download()
            article.parse()
            if not article.title:
                logger.info(f"No title found. URL: {link_tags.link}")
                return None
            if not article.text:
                logger.info(f"No article text found. URL: {link_tags.link}")
                return None
            
            # Truncate the HTML string to half its length
            html_content = article.html
            if html_content:
                html_content = html_content[len(html_content) // 2:]

            return ArticleResponseSchema(
                link=link_tags.link,
                tags=link_tags.tags,
                title=article.title,
                text=article.text,
                html=html_content,
                published_date=article.publish_date
            )
        except Exception as e:
            logger.error(f"Error fetching article: {str(e)}. URL: {link_tags.link}")
            return None
        

    def get_all_articles(self, max_workers=20) -> List[ArticleResponseSchema]:
        articles = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.__fetch_article, link_tags) for link_tags in self.links_tags]
            for future in as_completed(futures):
                try:
                    fetched_article_with_link = future.result()
                    if fetched_article_with_link:
                        articles.append(fetched_article_with_link)
                except Exception as e:
                    logger.error(f"Error fetching article: {str(e)}")
        return articles
    
    
    def get_published_date(self, articles) -> List[ArticleWithPublishedDateResponseSchema]:
        articles_with_published_date = []
        for article in articles:
            published_date = self.__get_published_date(article)
            if not published_date or published_date == date(1970, 1, 1):
                logger.info(f"Published date not found. URL: {article.link}")
                continue
            articles_with_published_date.append(ArticleWithPublishedDateResponseSchema(
                link=article.link, title=article.title, score=article.score, tags=article.tags, published_date=published_date, text=article.text))
        return articles_with_published_date
    
    
    def __get_published_date(self, article) -> date:
        if article.published_date:
            return article.published_date.date()
        else:
            soup = BeautifulSoup(article.html, "html.parser")
            script_tag = soup.find("script", {"type":"application/ld+json"})
            if not script_tag:
                logger.info(f"No script tag found. Trying to get published date via llm. URL: {article.link}")
                return self.__get_published_date_via_llm(article)
            try:
                json_content = json.loads(script_tag.string.strip().replace("\n", "").replace("    ", ""))
                if "@graph" in json_content:
                    for item in json_content["@graph"]:
                        if "datePublished" in item:
                            datetime_str = item["datePublished"]
                elif "datePublished" in json_content:
                    datetime_str = json_content['datePublished']
                else:
                    logger.info(f"No datePublished found in json+ld. Trying to get published date via llm. URL: {article.link}")
                    return self.__get_published_date_via_llm(article)
                try:
                    parsed_date = parser.parse(datetime_str)
                    return parsed_date.date()
                except (ValueError, TypeError) as e:
                    logger.info(f"Error parsing published date: {e}, URL: {article.link}")
                    return self.__get_published_date_via_llm(article)
            except json.JSONDecodeError as e:
                logger.info(f"Error decoding json+ld: {e} URL: {article.link}")
                return self.__get_published_date_via_llm(article)
            
            
    def __get_published_date_via_llm(self, article) -> date:
        prompt = published_date_agent.prompt(article.html)
        response = self.openai_client.query_gpt(prompt, ArticlePublishedDateOpenAiResponseSchema)
        if isinstance(response, ArticlePublishedDateOpenAiResponseSchema):
            parsed_date = parser.parse(response.published_date)
            logger.info(f"Published date fetched via LLM. URL: {parsed_date.date()}")
            return parsed_date.date()
        else:
            logger.error(f"Error fetching published date via LLM. Bad LLM response URL: {article.link}, response: {response}")

