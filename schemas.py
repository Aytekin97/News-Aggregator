from typing import Annotated, List
from datetime import datetime, date
from pydantic import BaseModel, HttpUrl, PlainSerializer


class ClassificationScoreOpenAiResponseSchema(BaseModel):
    score: int

class ArticlePublishedDateOpenAiResponseSchema(BaseModel):
    published_date: str

class AgentModelDescriptionOpenAiResponseSchema(BaseModel):
    name: str
    description: str


class AgentDescriptionListOpenAiResponseSchema(BaseModel):
    agents: List[AgentModelDescriptionOpenAiResponseSchema]


class AgentModelOpenAiResponseSchema(BaseModel):
    name: str
    role: str
    function: str


class AnalysisResultOpenAiResponseSchema(BaseModel):
    analysis: str


class SummaryOpenAiResponseSchema(BaseModel):
    summary: str


class ArticleResponseSchema(BaseModel):
    link: HttpUrl
    tags: list[str]
    title: str
    text: str
    html: str | None = None
    published_date: datetime | None = None


class ArticleClassificationScoreSchema(BaseModel):
    link: HttpUrl
    tags: list[str]
    title: str
    score: int
    text: str
    published_date: datetime | None = None
    html: str | None = None

class ArticleWithPublishedDateResponseSchema(BaseModel):
    link: HttpUrl
    tags: list[str]
    title: str
    score: int
    published_date: date
    text: str

class AgentAnalysisResultSchema(BaseModel):
    analysis: str


class ArticleAnalysisResultSchema(BaseModel):
    link: HttpUrl
    title: str
    score: int
    analysis: List[AgentAnalysisResultSchema]
    published_date: date
    tags: list[str]


class NewsAggregatorResultSchema(BaseModel):
    link: Annotated[
        HttpUrl,
        PlainSerializer(
            lambda x: str(x),
        ),
    ]
    title: str
    published_date: date
    classification_score: int
    summary: str
    tags: list[str]


class LinkTagsSchema(BaseModel):
        link: str
        tags: list[str]


class CompanyRequest(BaseModel):
    companies: list[str]
    number_of_days: int
