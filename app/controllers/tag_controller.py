from typing import List, Optional

from app.models.tag import Tag

class TagController:
    """标签控制器，处理标签相关的业务逻辑"""
    
    def __init__(self, session): 
        """初始化控制器
        
        Args:
            session: 数据库会话
        """
        self.session = session
        
    def get_all_tags(self) -> List[Tag]:
        """获取所有标签，按标签名称排序
        
        Returns:
            标签列表
        """
        return self.session.query(Tag).order_by(Tag.tag).all()
        
    def get_tag_by_id(self, tag_id: int) -> Optional[Tag]:
        """根据ID获取标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            标签对象，如果不存在则返回None
        """
        return self.session.query(Tag).get(tag_id)
        
    def get_tag_by_name(self, tag_name: str) -> Optional[Tag]:
        """根据名称获取标签
        
        Args:
            tag_name: 标签名称
            
        Returns:
            标签对象，如果不存在则返回None
        """
        return self.session.query(Tag).filter_by(tag=tag_name).first()
        
    def create_tag(self, tag_name: str) -> Optional[Tag]:
        """创建新标签
        
        Args:
            tag_name: 标签名称
            
        Returns:
            创建的标签对象，如果标签名已存在则返回None
        """
        # 检查标签是否已存在
        existing_tag = self.get_tag_by_name(tag_name)
        if existing_tag:
            return None
            
        # 创建新标签
        tag = Tag(tag=tag_name)
        self.session.add(tag)
        self.session.commit()
        return tag
        
    def update_tag(self, tag_id: int, new_name: str) -> Optional[Tag]:
        """更新标签名称
        
        Args:
            tag_id: 标签ID
            new_name: 新标签名称
            
        Returns:
            更新后的标签对象，如果标签不存在或新名称已存在则返回None
        """
        # 获取要更新的标签
        tag = self.get_tag_by_id(tag_id)
        if not tag:
            return None
            
        # 检查新名称是否已存在
        existing = self.session.query(Tag).filter(Tag.tag == new_name, Tag.id != tag_id).first()
        if existing:
            return None
            
        # 更新标签名称
        tag.tag = new_name
        self.session.commit()
        return tag
        
    def delete_tag(self, tag_id: int) -> bool:
        """删除标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            是否成功删除
        """
        tag = self.get_tag_by_id(tag_id)
        if not tag:
            return False
            
        self.session.delete(tag)
        self.session.commit()
        return True
        
    def get_or_create_tag(self, tag_name: str) -> Tag:
        """获取标签，如果不存在则创建
        
        Args:
            tag_name: 标签名称
            
        Returns:
            标签对象
        """
        tag = self.get_tag_by_name(tag_name)
        if not tag:
            tag = Tag(tag=tag_name)
            self.session.add(tag)
            self.session.commit()
        return tag
