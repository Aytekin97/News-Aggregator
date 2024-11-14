from datetime import datetime, date
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import Session, sessionmaker, Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import as_declarative, DeclarativeMeta
from sqlalchemy.types import Integer, BigInteger, String, Text, DateTime, Date

from config import settings


engines = [create_engine(url) for url in settings.db_url]


class BaseMetaClass(DeclarativeMeta):

    def __init__(cls, name, bases, dict_):
        return super().__init__(name, bases, dict_)


@as_declarative(metaclass=BaseMetaClass)
class BaseModel:
    """Base model."""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, sort_order=-1)

    def __iter__(self):
        """
        Iterates over the columns of the model and yields their names and values.
        """
        for column in self.__table__.columns:
            yield column.name, getattr(self, column.name, None)


class NewsModel(BaseModel):
    __tablename__ = "news"

    classification_score: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String, nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    link: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    published_date: Mapped[date] = mapped_column(Date, nullable=True)

    tags: Mapped[list["TagModel"]] = relationship("TagModel", secondary="news_tags", back_populates="news")


class TagModel(BaseModel):
    __tablename__ = "tag"

    name: Mapped[str] = mapped_column(String, unique=True)
    news: Mapped[list["NewsModel"]] = relationship("NewsModel", secondary="news_tags", back_populates="tags")


class NewsTagsModel(BaseModel):
    __tablename__ = "news_tags"

    news_id: Mapped[int] = mapped_column(Integer, ForeignKey("news.id"))
    tag_id: Mapped[int] = mapped_column(Integer, ForeignKey("tag.id"))


for engine in engines:
    BaseModel.metadata.create_all(engine)


Sessions: list[Session] = [sessionmaker(engine) for engine in engines]
