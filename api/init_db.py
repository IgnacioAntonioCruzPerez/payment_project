from .models import Base
from sqlalchemy import create_engine

engine = create_engine("sqlite:///payments.db", echo=True)

Base.metadata.create_all(engine)
print("DB and tables created successfully!")