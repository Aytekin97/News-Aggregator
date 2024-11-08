from typing import Annotated, List
from datetime import datetime, date
from pydantic import BaseModel, HttpUrl, PlainSerializer


class LinkTagsSchema(BaseModel):
        link: str
        tags: list[str]