from datetime import datetime, date
from typing import List, Dict, Optional, Any

from sqlalchemy import case, desc, asc

from app.models.task import Task, Priority
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
        """获取所有任务，按截止日期、优先级和创建时间排序
        
        排序规则：
        1. 未完成的任务排在已完成的任务前面
        2. 按截止日期升序（无截止日期的排在最后）
        3. 相同截止日期的按优先级降序（高>中>低>无）
        4. 相同优先级的按创建时间降序
        
        Returns:
            任务列表
        """
        # 使用case when语句处理截止日期为空的情况
        due_date_case = case(
            (Task.due_date == None, 1),  # 无截止日期的排在后面
            else_=0
        )
        
        # 使用case when语句处理已完成任务
        completed_case = case(
            (Task.completed == True, 1),  # 已完成的排在后面
            else_=0
        )
        
        return self.session.query(Task).order_by(
            completed_case,  # 未完成的排在前面
            due_date_case,   # 有截止日期的排在前面
            asc(Task.due_date),  # 按截止日期升序
            desc(Task.priority),  # 按优先级降序
            desc(Task.created_at)  # 按创建时间降序
        ).all()
        
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """根据ID获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在则返回None
        """
        return self.session.query(Task).get(task_id)
        
    def create_task(self, title: str, due_date: Optional[str] = None, tag_ids: List[int] = None, priority: int = Priority.NONE) -> Task:
        """创建新任务
        
        Args:
            title: 任务标题
            due_date: 截止日期 (yyyy-MM-dd 格式字符串或 None)
            tag_ids: 标签ID列表
            priority: 优先级，默认为无
        
        Returns:
            创建的任务对象
        """
        parsed_due_date: Optional[date] = None
        if due_date:
            try:
                parsed_due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
            except ValueError:
                # 如果格式不正确，可以记录日志或按 None 处理
                parsed_due_date = None

        task = Task(title=title, due_date=parsed_due_date, priority=priority)
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
            data: 要更新的数据字典，可包含title, due_date (yyyy-MM-dd str or None), tag_ids, priority, completed
        
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
            due_date_str = data['due_date']
            if due_date_str:
                try:
                    task.due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                except ValueError:
                    # 如果格式不正确，可以记录日志或保持原样/设为None
                    task.due_date = None # 或者选择不修改: pass
            else:
                task.due_date = None # 如果传入 None，则设为 None

        if 'completed' in data:
            task.completed = data['completed']
        if 'priority' in data:
            task.priority = data['priority']
            
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
        
    def get_tasks_by_priority(self, priority: int) -> List[Task]:
        """获取指定优先级的任务
        
        Args:
            priority: 优先级值
            
        Returns:
            任务列表
        """
        return self.session.query(Task).filter(Task.priority == priority).all()
    
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
