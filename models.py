from sqlalchemy import Column, Integer, String, Text
from database import Base

class Newsletter(Base):
    __tablename__ = "newsletter"
    summary_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    picture = Column(String)
    content = Column(Text, nullable=False)
    description = Column(String(255))