from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

Base = declarative_base()

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    amount = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    meta_info = Column(String, nullable=True) 