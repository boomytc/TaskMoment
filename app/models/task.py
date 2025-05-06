from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.models.base import Base, task_tags

class Task(Base):
    """任务模型"""
    __tablename__ = "task"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    
    # 多对多标签关系
    tags = relationship("Tag", secondary=task_tags, backref="tasks")

    def display_title(self):
        """返回带有标签的任务标题（用于UI显示）"""
        if not self.tags:
            return self.title
            
        # 将所有标签添加到标题后面
        tags_str = " ".join([f"#{tag.tag}" for tag in self.tags])
        return f"{self.title} {tags_str}"
