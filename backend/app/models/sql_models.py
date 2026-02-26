from typing import List, Optional
from sqlalchemy import String, Float, Integer, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    reviewerID: Mapped[str] = mapped_column(String(50), primary_key=True)
    reviewerName: Mapped[Optional[str]] = mapped_column(String(100))
    meta: Mapped[Optional[dict]] = mapped_column(JSON)
    
    reviews: Mapped[List["Review"]] = relationship(back_populates="user")
    
class Item(Base):
    __tablename__ = "items"
    
    asin: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    price: Mapped[float] = mapped_column(Float, default=0.0)
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    feature: Mapped[Optional[List[str]]] = mapped_column(JSON)
    categories: Mapped[Optional[List[List[str]]]] = mapped_column(JSON)
    also_buy: Mapped[Optional[List[str]]] = mapped_column(JSON)
    also_viewed: Mapped[Optional[List[str]]] = mapped_column(JSON)
    imageURL: Mapped[Optional[str]] = mapped_column(String(500))
    imageURLHighRes: Mapped[Optional[str]] = mapped_column(String(500))
    
    reviews: Mapped[List["Review"]] = relationship(back_populates="item")

class Review(Base):
    __tablename__ = "reviews"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reviewerID: Mapped[str] = mapped_column(ForeignKey("users.reviewerID"))
    asin: Mapped[str] = mapped_column(ForeignKey("items.asin"))
    overall: Mapped[float] = mapped_column(Float)
    reviewText: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    unixReviewTime: Mapped[int] = mapped_column(Integer)
    reviewTime: Mapped[Optional[str]] = mapped_column(String(50))
    vote: Mapped[Optional[str]] = mapped_column(String(20))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    style: Mapped[Optional[dict]] = mapped_column(JSON)
    image: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    user: Mapped["User"] = relationship(back_populates="reviews")
    item: Mapped["Item"] = relationship(back_populates="reviews")

class SocialEdge(Base):
    __tablename__ = "social_edges"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(ForeignKey("users.reviewerID"))
    target: Mapped[str] = mapped_column(ForeignKey("users.reviewerID"))
    weight: Mapped[float] = mapped_column(Float, default=0.0)
    type: Mapped[Optional[str]] = mapped_column(String(20))
