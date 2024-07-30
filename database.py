from sqlalchemy import BOOLEAN, Index, create_engine, Column, Integer, VARCHAR, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import dotenv_values

config = dotenv_values(".env")

DATABASE_USERNAME = config.get("DATABASE_USERNAME") if config else os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = config.get("DATABASE_PASSWORD") if config else os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = config.get("DATABASE_HOST") if config else os.getenv("DATABASE_HOST")
DATABASE_NAME = config.get("DATABASE_NAME") if config else os.getenv("DATABASE_NAME")
DATABASE_PORT = config.get("DATABASE_PORT") if config else os.getenv("DATABASE_PORT")

Base = declarative_base()


class Camp(Base):
    __tablename__ = "Camps"
    id = Column(Integer, primary_key=True, autoincrement=True)
    hashLink = Column(VARCHAR(255), nullable=False, unique=True)
    link = Column(VARCHAR(255), nullable=False)
    topic = Column(Text)
    imageUrl = Column(Text, nullable=False)
    deadline = Column(DateTime)
    createdAt = Column(DateTime, nullable=False, default=func.current_timestamp())
    updatedAt = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    isActive = Column(BOOLEAN, nullable=False, default=True)

    __table_args__ = (
        Index('idx_camps_hash_link', 'hashLink'),
        Index('idx_camps_updated_at', 'updatedAt'),
    )

class Competition(Base):
    __tablename__ = "Competitions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    hashLink = Column(VARCHAR(255), nullable=False, unique=True)
    link = Column(VARCHAR(255), nullable=False)
    topic = Column(Text)
    imageUrl = Column(Text, nullable=False)
    deadline = Column(DateTime)
    createdAt = Column(DateTime, nullable=False, default=func.current_timestamp())
    updatedAt = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    isActive = Column(BOOLEAN, nullable=False, default=True)

    __table_args__ = (
        Index('idx_competitions_hash_link', 'hashLink'),
        Index('idx_competitions_updated_at', 'updatedAt'),
    )

class Other(Base):
    __tablename__ = "Others"
    id = Column(Integer, primary_key=True, autoincrement=True)
    hashLink = Column(VARCHAR(255), nullable=False, unique=True)
    link = Column(VARCHAR(255), nullable=False)
    topic = Column(Text)
    imageUrl = Column(Text, nullable=False)
    deadline = Column(DateTime)
    createdAt = Column(DateTime, nullable=False, default=func.current_timestamp())
    updatedAt = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    isActive = Column(BOOLEAN, nullable=False, default=True)

    __table_args__ = (
        Index('idx_others_hash_link', 'hashLink'),
        Index('idx_others_updated_at', 'updatedAt'),
    )

engine = create_engine(f"mysql+mysqlconnector://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}")
factory = sessionmaker(bind=engine)
session = factory()
Base.metadata.create_all(engine)