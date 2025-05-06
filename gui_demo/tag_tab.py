from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog
)

from models import Tag, Task


class TagTab(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self._setup_ui()
        self.load_tags()
        
    def _setup_ui(self):
        """设置标签管理标签页的界面和功能"""
        tag_layout = QVBoxLayout(self)
        
        # 添加标签区域
        input_group = QHBoxLayout()
        self.new_tag_edit = QLineEdit()
        self.new_tag_edit.setPlaceholderText("输入新标签名称")
        add_tag_btn = QPushButton("添加标签")
        input_group.addWidget(self.new_tag_edit, 3)
        input_group.addWidget(add_tag_btn, 1)
        
        tag_layout.addLayout(input_group)
        
        # 标签列表
        self.tag_table = QTableWidget(0, 3)
        self.tag_table.setHorizontalHeaderLabels(["标签名称", "任务数量", "操作"])
        self.tag_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tag_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.tag_table.verticalHeader().setVisible(False)
        self.tag_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        tag_layout.addWidget(self.tag_table)
        
        # 连接信号
        add_tag_btn.clicked.connect(self.add_tag)
    
    def add_tag(self):
        """添加新标签"""
        tag_name = self.new_tag_edit.text().strip()
        if not tag_name:
            return
            
        # 检查标签是否已存在
        existing_tag = self.session.query(Tag).filter_by(tag=tag_name).first()
        if existing_tag:
            QMessageBox.warning(self, "错误", f"标签 '{tag_name}' 已存在")
            return
            
        # 创建新标签
        new_tag = Tag(tag=tag_name)
        self.session.add(new_tag)
        self.session.commit()
        
        # 清空输入框
        self.new_tag_edit.clear()
        
        # 刷新标签列表
        self.load_tags()
        
        # 发出标签变更信号
        if hasattr(self, 'tag_changed') and self.tag_changed is not None:
            self.tag_changed.emit()
        
    def load_tags(self):
        """加载所有标签到标签表格中"""
        self.tag_table.setRowCount(0)
        
        # 查询所有标签
        tags = self.session.query(Tag).all()
        
        for tag in tags:
            row = self.tag_table.rowCount()
            self.tag_table.insertRow(row)
            
            # 标签名称
            name_item = QTableWidgetItem(tag.tag)
            name_item.setTextAlignment(Qt.AlignCenter)
            self.tag_table.setItem(row, 0, name_item)
            
            # 任务数量 - 使用多对多关系查询
            task_count = len(tag.tasks)
            count_item = QTableWidgetItem(str(task_count))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.tag_table.setItem(row, 1, count_item)
            
            # 操作按钮
            action_widget = QWidget()
            hl = QHBoxLayout(action_widget)
            hl.setContentsMargins(0, 0, 0, 0)
            
            edit_btn = QPushButton("编辑")
            delete_btn = QPushButton("删除")
            
            hl.addStretch(1)  # 添加前置拉伸以居中按钮
            hl.addWidget(edit_btn)
            hl.addWidget(delete_btn)
            hl.addStretch(1)  # 添加后置拉伸以居中按钮
            
            self.tag_table.setCellWidget(row, 2, action_widget)
            
            # 连接信号
            edit_btn.clicked.connect(lambda _, tid=tag.id: self.edit_tag(tid))
            delete_btn.clicked.connect(lambda _, tid=tag.id: self.delete_tag(tid))
    
    def edit_tag(self, tag_id):
        """编辑标签"""
        tag = self.session.query(Tag).get(tag_id)
        if not tag:
            return
            
        # 弹出输入对话框
        new_name, ok = QInputDialog.getText(self, "编辑标签", "新标签名称:", QLineEdit.Normal, tag.tag)
        
        if ok and new_name.strip():
            # 检查名称是否已存在
            existing = self.session.query(Tag).filter(Tag.tag == new_name.strip(), Tag.id != tag_id).first()
            if existing:
                QMessageBox.warning(self, "错误", f"标签 '{new_name}' 已存在")
                return
                
            # 更新标签名称
            tag.tag = new_name.strip()
            self.session.commit()
            
            # 刷新标签列表
            self.load_tags()
            
            # 发出标签变更信号
            if hasattr(self, 'tag_changed') and self.tag_changed is not None:
                self.tag_changed.emit()
    
    def delete_tag(self, tag_id):
        """删除标签"""
        tag = self.session.query(Tag).get(tag_id)
        if not tag:
            return
            
        # 检查是否有任务使用该标签
        task_count = len(tag.tasks)
        
        message = f"确定要删除标签 '{tag.tag}' 吗?"
        if task_count > 0:
            message += f"\n该标签当前被 {task_count} 个任务使用。删除后，这些任务将不再有标签。"
            
        if QMessageBox.question(self, "确认删除", message) != QMessageBox.Yes:
            return
            
        # 删除标签
        self.session.delete(tag)
        self.session.commit()
        
        # 刷新标签列表
        self.load_tags()
        
        # 发出标签变更信号
        if hasattr(self, 'tag_changed') and self.tag_changed is not None:
            self.tag_changed.emit()
