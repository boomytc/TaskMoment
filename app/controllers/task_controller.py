from datetime import datetime
from typing import List, Dict, Optional, Any

from PySide6.QtCore import QDate

from app.models.task import Task
from app.models.tag import Tag

class TaskController:
    """任务控制器，处理任务相关的业务逻辑"""
    
    def __init__(self, session):
        """初始化控制器
        
        Args:
            session: 数据库会话
        """
        self.session = session
        
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务，按创建时间降序排序
        
        Returns:
            任务列表
        """
        return self.session.query(Task).order_by(Task.created_at.desc()).all()
        
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """根据ID获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在则返回None
        """
        return self.session.query(Task).get(task_id)
        
    def create_task(self, title: str, due_date: Optional[datetime] = None, tag_ids: List[int] = None) -> Task:
        """创建新任务
        
        Args:
            title: 任务标题
            due_date: 截止日期
            tag_ids: 标签ID列表
            
        Returns:
            创建的任务对象
        """
        task = Task(title=title, due_date=due_date)
        self.session.add(task)
        
        # 添加标签
        if tag_ids:
            for tag_id in tag_ids:
                tag = self.session.query(Tag).get(tag_id)
                if tag:
                    task.tags.append(tag)
        
        self.session.commit()
        return task
        
    def update_task(self, task_id: int, data: Dict[str, Any]) -> Optional[Task]:
        """更新任务
        
        Args:
            task_id: 任务ID
            data: 要更新的数据字典，可包含title, due_date, tag_ids
            
        Returns:
            更新后的任务对象，如果任务不存在则返回None
        """
        task = self.get_task_by_id(task_id)
        if not task:
            return None
            
        # 更新任务基本信息
        if 'title' in data:
            task.title = data['title']
        if 'due_date' in data:
            task.due_date = data['due_date']
        if 'completed' in data:
            task.completed = data['completed']
            
        # 更新任务标签
        if 'tag_ids' in data:
            # 清除所有现有标签
            task.tags.clear()
            
            # 添加新标签
            for tag_id in data['tag_ids']:
                tag = self.session.query(Tag).get(tag_id)
                if tag:
                    task.tags.append(tag)
        
        self.session.commit()
        return task
        
    def delete_task(self, task_id: int) -> bool:
        """删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功删除
        """
        task = self.get_task_by_id(task_id)
        if not task:
            return False
            
        self.session.delete(task)
        self.session.commit()
        return True
        
    def toggle_task_completed(self, task_id: int) -> Optional[Task]:
        """切换任务完成状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            更新后的任务对象，如果任务不存在则返回None
        """
        task = self.get_task_by_id(task_id)
        if not task:
            return None
            
        task.completed = not task.completed
        self.session.commit()
        return task
        
    @staticmethod
    def parse_date(date: QDate) -> Optional[datetime]:
        """将QDate转换为datetime
        
        Args:
            date: QDate对象
            
        Returns:
            datetime对象，如果日期无效则返回None
        """
        if not date.isValid():
            return None
        return datetime(date.year(), date.month(), date.day())
        
    @staticmethod
    def extract_tag(title: str) -> tuple:
        """从标题中提取标签
        
        Args:
            title: 任务标题
            
        Returns:
            (纯标题, 标签名称)元组，如果没有标签则标签名称为None
        """
        words = title.split()
        tag_name = None
        new_title_parts = []
        for w in words:
            if w.startswith("#") and len(w) > 1:
                tag_name = w[1:]
            else:
                new_title_parts.append(w)
        pure_title = " ".join(new_title_parts).strip()
        return pure_title, tag_name
