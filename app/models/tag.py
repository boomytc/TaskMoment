from sqlalchemy import Column, Integer, String

from app.models.base import Base

class Tag(Base):
    """标签模型"""
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True)
    tag = Column(String(50), nullable=False, unique=True)

    def __repr__(self):
        return f"<Tag {self.tag}>"
