from datetime import datetime, date
from enum import IntEnum
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Boolean, DateTime, SmallInteger, Date, or_, and_, case, desc, asc
from sqlalchemy.orm import relationship, Query

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
    due_date = Column(Date, nullable=True)
    priority = Column(SmallInteger, default=Priority.NONE, nullable=False)
    
    # 多对多标签关系
    tags = relationship("Tag", secondary=task_tags, backref="tasks")
    
    @staticmethod
    def filter_tasks(session, keyword: Optional[str] = None, due_date_filter: Optional[str] = None, 
                    status: Optional[bool] = None, priority: Optional[int] = None, 
                    tag_ids: Optional[List[int]] = None) -> List["Task"]:
        """筛选和搜索任务
        
        Args:
            session: 数据库会话
            keyword: 搜索关键词（标题中包含）
            due_date_filter: 截止日期筛选，可选值：'today', 'tomorrow', 'week', 'none', 'overdue', 'future', 或具体日期字符串'yyyy-MM-dd'
            status: 完成状态，True表示已完成，False表示未完成，None表示不筛选
            priority: 优先级筛选，对应Priority枚举值，None表示不筛选
            tag_ids: 标签ID列表，筛选包含任一标签的任务，None表示不筛选
            
        Returns:
            筛选后的任务列表
        """
        query = session.query(Task)
        
        # 关键词搜索（标题中包含）
        if keyword and keyword.strip():
            query = query.filter(Task.title.ilike(f'%{keyword.strip()}%'))
        
        # 完成状态筛选
        if status is not None:
            query = query.filter(Task.completed == status)
        
        # 优先级筛选
        if priority is not None:
            query = query.filter(Task.priority == priority)
        
        # 标签筛选
        if tag_ids and len(tag_ids) > 0:
            from app.models.base import task_tags
            from app.models.tag import Tag
            query = query.join(task_tags).join(Tag).filter(Tag.id.in_(tag_ids)).distinct()
        
        # 截止日期筛选
        if due_date_filter:
            today = date.today()
            
            if due_date_filter == 'today':
                # 今天到期
                query = query.filter(Task.due_date == today)
            elif due_date_filter == 'tomorrow':
                # 明天到期
                tomorrow = date(today.year, today.month, today.day + 1)
                query = query.filter(Task.due_date == tomorrow)
            elif due_date_filter == 'week':
                # 一周内到期（包括今天）
                week_later = date(today.year, today.month, today.day + 7)
                query = query.filter(Task.due_date >= today, Task.due_date <= week_later)
            elif due_date_filter == 'none':
                # 无截止日期
                query = query.filter(Task.due_date == None)
            elif due_date_filter == 'overdue':
                # 已逾期（截止日期在今天之前且未完成）
                query = query.filter(Task.due_date < today, Task.completed == False)
            elif due_date_filter == 'future':
                # 未来到期（今天之后）
                query = query.filter(Task.due_date > today)
            else:
                # 尝试解析具体日期
                try:
                    specific_date = datetime.strptime(due_date_filter, "%Y-%m-%d").date()
                    query = query.filter(Task.due_date == specific_date)
                except ValueError:
                    # 日期格式不正确，忽略此筛选条件
                    pass
        
        # 排序规则：未完成的排在前面，按截止日期升序（无截止日期的排在最后），
        # 相同截止日期的按优先级降序，相同优先级的按创建时间降序
        due_date_case = case(
            (Task.due_date == None, 1),  # 无截止日期的排在后面
            else_=0
        )
        
        completed_case = case(
            (Task.completed == True, 1),  # 已完成的排在后面
            else_=0
        )
        
        return query.order_by(
            completed_case,  # 未完成的排在前面
            due_date_case,   # 有截止日期的排在前面
            asc(Task.due_date),  # 按截止日期升序
            desc(Task.priority),  # 按优先级降序
            desc(Task.created_at)  # 按创建时间降序
        ).all()

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
