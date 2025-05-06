from datetime import datetime
from enum import IntEnum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, SmallInteger
from sqlalchemy.orm import relationship

from app.models.base import Base, task_tags

class Priority(IntEnum):
    """任务优先级枚举"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class Task(Base):
    """任务模型"""
    __tablename__ = "task"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    priority = Column(SmallInteger, default=Priority.NONE, nullable=False)
    
    # 多对多标签关系
    tags = relationship("Tag", secondary=task_tags, backref="tasks")

    def display_title(self):
        """返回带有标签的任务标题（用于UI显示）"""
        if not self.tags:
            return self.title
            
        # 将所有标签添加到标题后面
        tags_str = " ".join([f"#{tag.tag}" for tag in self.tags])
        return f"{self.title} {tags_str}"
        
    def get_priority_color(self):
        """返回优先级对应的颜色
        
        Returns:
            str: 颜色代码
        """
        if self.priority == Priority.HIGH:
            return "#FF4D4D"  # 红色
        elif self.priority == Priority.MEDIUM:
            return "#FFD700"  # 黄色
        elif self.priority == Priority.LOW:
            return "#4D94FF"  # 蓝色
        else:
            return "#808080"  # 灰色
            
    def get_priority_name(self):
        """返回优先级名称
        
        Returns:
            str: 优先级名称
        """
        if self.priority == Priority.HIGH:
            return "高"
        elif self.priority == Priority.MEDIUM:
            return "中"
        elif self.priority == Priority.LOW:
            return "低"
        else:
            return "无"
