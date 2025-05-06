from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog
)

from app.controllers.tag_controller import TagController

class TagTab(QWidget):
    """标签管理标签页"""
    
    def __init__(self, session):
        """初始化标签页
        
        Args:
            session: 数据库会话
        """
        super().__init__()
        
        # 创建控制器
        self.tag_controller = TagController(session)
        
        # 初始化UI
        self._setup_ui()
        
        # 加载标签
        self.load_tags()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 输入行
        input_row = QHBoxLayout()
        self.new_tag_edit = QLineEdit()
        self.new_tag_edit.setPlaceholderText("添加新标签…")
        add_btn = QPushButton("添加")
        
        input_row.addWidget(self.new_tag_edit, 4)
        input_row.addWidget(add_btn, 1)
        
        layout.addLayout(input_row)
        
        # 标签表格
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["标签", "任务数量", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.table)
        
        # 连接信号
        add_btn.clicked.connect(self.add_tag)
        self.new_tag_edit.returnPressed.connect(self.add_tag)
    
    def load_tags(self):
        """加载所有标签"""
        self.table.setRowCount(0)
        
        for tag in self.tag_controller.get_all_tags():
            self._add_tag_to_table(tag)
    
    def _add_tag_to_table(self, tag):
        """将标签添加到表格
        
        Args:
            tag: 标签对象
        """
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # 标签名称
        tag_item = QTableWidgetItem(tag.tag)
        tag_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 0, tag_item)
        
        # 任务数量
        task_count = len(tag.tasks)
        count_item = QTableWidgetItem(str(task_count))
        count_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 1, count_item)
        
        # 操作按钮
        action_widget = QWidget()
        hl = QHBoxLayout(action_widget)
        hl.setContentsMargins(0, 0, 0, 0)
        edit_btn = QPushButton("重命名")
        delete_btn = QPushButton("删除")
        hl.addStretch(1)
        hl.addWidget(edit_btn)
        hl.addWidget(delete_btn)
        hl.addStretch(1)
        self.table.setCellWidget(row, 2, action_widget)
        
        # 连接信号
        edit_btn.clicked.connect(lambda _, tid=tag.id: self.edit_tag(tid))
        delete_btn.clicked.connect(lambda _, tid=tag.id: self.delete_tag(tid))
    
    def add_tag(self):
        """添加新标签"""
        tag_name = self.new_tag_edit.text().strip()
        if not tag_name:
            return
            
        # 创建标签
        tag = self.tag_controller.create_tag(tag_name)
        if not tag:
            QMessageBox.warning(self, "错误", f"标签 '{tag_name}' 已存在")
            return
            
        # 重置输入
        self.new_tag_edit.clear()
        
        # 更新UI
        self.load_tags()
    
    def edit_tag(self, tag_id):
        """编辑标签
        
        Args:
            tag_id: 标签ID
        """
        tag = self.tag_controller.get_tag_by_id(tag_id)
        if not tag:
            return
            
        # 获取新标签名称
        new_name, ok = QInputDialog.getText(
            self, "重命名标签", "输入新的标签名称:", 
            QLineEdit.Normal, tag.tag
        )
        
        if not ok or not new_name.strip():
            return
            
        # 更新标签
        new_name = new_name.strip()
        result = self.tag_controller.update_tag(tag_id, new_name)
        
        if not result:
            QMessageBox.warning(self, "错误", f"标签 '{new_name}' 已存在")
            return
            
        # 更新UI
        self.load_tags()
    
    def delete_tag(self, tag_id):
        """删除标签
        
        Args:
            tag_id: 标签ID
        """
        tag = self.tag_controller.get_tag_by_id(tag_id)
        if not tag:
            return
            
        # 确认删除
        task_count = len(tag.tasks)
        if task_count > 0:
            if QMessageBox.question(
                self, 
                "确认删除", 
                f"标签 '{tag.tag}' 已被 {task_count} 个任务使用，确定删除吗？"
            ) != QMessageBox.Yes:
                return
        else:
            if QMessageBox.question(
                self, 
                "确认删除", 
                f"确定删除标签 '{tag.tag}' 吗？"
            ) != QMessageBox.Yes:
                return
                
        # 删除标签
        self.tag_controller.delete_tag(tag_id)
        
        # 更新UI
        self.load_tags()
