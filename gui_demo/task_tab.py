import sys
from datetime import datetime

from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QDateEdit, QComboBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QDialog, QLabel, QMessageBox, QGridLayout,
    QListWidget, QListWidgetItem, QAbstractItemView
)

from models import Task, Tag, Session


def parse_date(date: QDate) -> datetime | None:
    if not date.isValid():
        return None
    return datetime(date.year(), date.month(), date.day())


def extract_tag(title: str):
    """Extract #tag pattern from title. Returns (pure_title, tag_name | None)."""
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


class EditTaskDialog(QDialog):
    def __init__(self, session, task: Task | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑任务" if task else "新建任务")
        self.session = session
        self.task = task

        self.title_edit = QLineEdit()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate()) # <-- Set default to today initially
        
        # 替换单一标签下拉框为标签列表和添加标签控件
        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QAbstractItemView.MultiSelection)  # 允许多选
        self.tag_list.setMaximumHeight(100)  # 限制高度
        
        self.new_tag_edit = QLineEdit()
        self.new_tag_edit.setPlaceholderText("输入新标签")
        self.add_tag_btn = QPushButton("+")
        self.add_tag_btn.setMaximumWidth(30)
        
        # 初始化标签列表
        self._init_tag_list()

        # Layout
        layout = QGridLayout()
        layout.addWidget(QLabel("任务内容:"), 0, 0)
        layout.addWidget(self.title_edit, 0, 1)
        layout.addWidget(QLabel("截止日期:"), 1, 0)
        layout.addWidget(self.date_edit, 1, 1)
        layout.addWidget(QLabel("标签:"), 2, 0)
        
        # 标签选择区域
        tag_area = QVBoxLayout()
        tag_area.addWidget(self.tag_list)
        
        # 新标签输入区域
        new_tag_layout = QHBoxLayout()
        new_tag_layout.addWidget(self.new_tag_edit)
        new_tag_layout.addWidget(self.add_tag_btn)
        tag_area.addLayout(new_tag_layout)
        
        layout.addLayout(tag_area, 2, 1)

        btn_box = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        btn_box.addWidget(save_btn)
        btn_box.addWidget(cancel_btn)
        layout.addLayout(btn_box, 3, 0, 1, 2)

        self.setLayout(layout)

        # 连接信号
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        self.add_tag_btn.clicked.connect(self._add_new_tag)

        # 如果是编辑任务，填充表单
        if task:
            self.title_edit.setText(task.title)  # 只显示标题，不包含标签
            if task.due_date:  # 只在任务有截止日期时设置
                self.date_edit.setDate(QDate(task.due_date.year, task.due_date.month, task.due_date.day))
            else:
                self.date_edit.setDate(QDate())  # 清除日期
                
            # 选中任务已有的标签
            self._select_task_tags()

    def _init_tag_list(self):
        """初始化标签列表"""
        self.tag_list.clear()
        self.tag_map = {}  # 用于存储标签项和标签对象的映射
        
        # 加载所有标签
        for tag in self.session.query(Tag).order_by(Tag.tag).all():
            item = QListWidgetItem(tag.tag)
            item.setData(Qt.UserRole, tag.id)  # 存储标签 ID
            self.tag_list.addItem(item)
            self.tag_map[tag.id] = item
    
    def _select_task_tags(self):
        """选中任务已有的标签"""
        if not self.task or not self.task.tags:
            return
            
        # 选中任务已有的标签
        for tag in self.task.tags:
            if tag.id in self.tag_map:
                self.tag_map[tag.id].setSelected(True)
    
    def _add_new_tag(self):
        """添加新标签到列表"""
        tag_name = self.new_tag_edit.text().strip()
        if not tag_name:
            return
            
        # 检查标签是否已存在
        existing_tag = self.session.query(Tag).filter_by(tag=tag_name).first()
        
        if existing_tag:
            # 如果标签已存在，选中它
            if existing_tag.id in self.tag_map:
                self.tag_map[existing_tag.id].setSelected(True)
        else:
            # 创建新标签
            new_tag = Tag(tag=tag_name)
            self.session.add(new_tag)
            self.session.commit()
            
            # 添加到列表并选中
            item = QListWidgetItem(new_tag.tag)
            item.setData(Qt.UserRole, new_tag.id)
            item.setSelected(True)
            self.tag_list.addItem(item)
            self.tag_map[new_tag.id] = item
        
        # 清空输入框
        self.new_tag_edit.clear()
    
    def get_data(self):
        """返回任务数据字典"""
        title = self.title_edit.text().strip()
        if not title:
            return None

        # 从标题中提取标签
        title, tag_in_title = extract_tag(title)
        
        # 获取选中的标签
        selected_tags = []
        for item in self.tag_list.selectedItems():
            tag_id = item.data(Qt.UserRole)
            selected_tags.append(tag_id)
            
        # 如果标题中有标签，添加到选中的标签列表
        if tag_in_title:
            tag = self.session.query(Tag).filter_by(tag=tag_in_title).first()
            if not tag:
                tag = Tag(tag=tag_in_title)
                self.session.add(tag)
                self.session.commit()
            
            if tag.id not in selected_tags:
                selected_tags.append(tag.id)

        due_date = parse_date(self.date_edit.date())

        return {
            "title": title,
            "due_date": due_date,
            "tag_ids": selected_tags
        }


class TaskTab(QWidget):
    # 定义信号
    task_changed = Signal()
    
    def __init__(self, session):
        super().__init__()
        self.session = session
        self._setup_ui()
        self.load_tasks()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ----------- Input Row -------------
        input_row = QHBoxLayout()
        self.new_title_edit = QLineEdit()
        self.new_title_edit.setPlaceholderText("添加新任务…")
        self.new_date_edit = QDateEdit()
        self.new_date_edit.setCalendarPopup(True)
        self.new_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.new_date_edit.setDate(QDate.currentDate()) # <-- Set default to today
        
        # 使用按钮打开编辑对话框来选择标签，而不是下拉框
        self.tag_btn = QPushButton("选择标签")
        add_btn = QPushButton("添加")

        input_row.addWidget(self.new_title_edit, 3)
        input_row.addWidget(self.new_date_edit, 1)
        input_row.addWidget(self.tag_btn, 1)
        input_row.addWidget(add_btn, 1)

        layout.addLayout(input_row)

        # ----------- Task Table -------------
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["完成", "任务", "截止日期", "标签", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # <-- Resize first column
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter) # <-- Center header text
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.table)

        # ----------- Connections -------------
        add_btn.clicked.connect(self.add_task)
        self.tag_btn.clicked.connect(self.select_tags)
        self.table.cellChanged.connect(self.handle_cell_changed)
        
        # 初始化标签选择状态
        self.selected_tag_ids = []

    def select_tags(self):
        """打开标签选择对话框"""
        # 创建一个简化版的标签选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("选择标签")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        
        # 标签列表
        tag_list = QListWidget()
        tag_list.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(tag_list)
        
        # 添加新标签区域
        new_tag_layout = QHBoxLayout()
        new_tag_edit = QLineEdit()
        new_tag_edit.setPlaceholderText("输入新标签")
        add_tag_btn = QPushButton("+")
        add_tag_btn.setMaximumWidth(30)
        new_tag_layout.addWidget(new_tag_edit)
        new_tag_layout.addWidget(add_tag_btn)
        layout.addLayout(new_tag_layout)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        # 加载标签并选中已选标签
        tag_map = {}
        for tag in self.session.query(Tag).order_by(Tag.tag).all():
            item = QListWidgetItem(tag.tag)
            item.setData(Qt.UserRole, tag.id)
            tag_list.addItem(item)
            tag_map[tag.id] = item
            
            # 如果标签已经选中，则选中它
            if tag.id in self.selected_tag_ids:
                item.setSelected(True)
        
        # 添加新标签的函数
        def add_new_tag():
            tag_name = new_tag_edit.text().strip()
            if not tag_name:
                return
                
            # 检查标签是否已存在
            existing_tag = self.session.query(Tag).filter_by(tag=tag_name).first()
            
            if existing_tag:
                # 如果标签已存在，选中它
                if existing_tag.id in tag_map:
                    tag_map[existing_tag.id].setSelected(True)
            else:
                # 创建新标签
                new_tag = Tag(tag=tag_name)
                self.session.add(new_tag)
                self.session.commit()
                
                # 添加到列表并选中
                item = QListWidgetItem(new_tag.tag)
                item.setData(Qt.UserRole, new_tag.id)
                item.setSelected(True)
                tag_list.addItem(item)
                tag_map[new_tag.id] = item
            
            # 清空输入框
            new_tag_edit.clear()
        
        # 连接信号
        add_tag_btn.clicked.connect(add_new_tag)
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        # 执行对话框
        if dialog.exec() == QDialog.Accepted:
            # 获取选中的标签
            self.selected_tag_ids = []
            for item in tag_list.selectedItems():
                tag_id = item.data(Qt.UserRole)
                self.selected_tag_ids.append(tag_id)
            
            # 更新标签按钮文本
            self._update_tag_button_text()
    
    def _update_tag_button_text(self):
        """更新标签按钮文本"""
        if not self.selected_tag_ids:
            self.tag_btn.setText("选择标签")
            return
            
        # 获取所有选中标签的名称
        tag_names = []
        for tag_id in self.selected_tag_ids:
            tag = self.session.query(Tag).get(tag_id)
            if tag:
                tag_names.append(tag.tag)
        
        # 如果标签太多，只显示前几个
        if len(tag_names) <= 2:
            self.tag_btn.setText(", ".join(tag_names))
        else:
            self.tag_btn.setText(f"{tag_names[0]}, {tag_names[1]}... (+{len(tag_names)-2})")


    def load_tasks(self):
        self.table.setRowCount(0)
        for task in self.session.query(Task).order_by(Task.created_at.desc()).all():
            self._add_task_to_table(task)

    def _add_task_to_table(self, task: Task):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Completed checkbox
        chk_item = QTableWidgetItem()
        chk_item.setFlags(chk_item.flags() | Qt.ItemIsUserCheckable)
        chk_item.setCheckState(Qt.Checked if task.completed else Qt.Unchecked)
        chk_item.setData(Qt.UserRole, task.id)
        chk_item.setTextAlignment(Qt.AlignCenter) # <-- Center checkbox item
        self.table.setItem(row, 0, chk_item)

        # Title
        title_item = QTableWidgetItem(task.display_title())
        title_item.setTextAlignment(Qt.AlignCenter) # <-- Center text
        self.table.setItem(row, 1, title_item)

        # Due date
        due_text = task.due_date.strftime("%Y-%m-%d") if task.due_date else ""
        due_item = QTableWidgetItem(due_text)
        due_item.setTextAlignment(Qt.AlignCenter) # <-- Center text
        self.table.setItem(row, 2, due_item)

        # 标签
        tag_text = ", ".join([tag.tag for tag in task.tags]) if task.tags else ""
        tag_item = QTableWidgetItem(tag_text)
        tag_item.setTextAlignment(Qt.AlignCenter) # <-- Center text
        self.table.setItem(row, 3, tag_item)

        # Actions (Edit/Delete buttons)
        action_widget = QWidget()
        hl = QHBoxLayout(action_widget)
        hl.setContentsMargins(0, 0, 0, 0)
        edit_btn = QPushButton("编辑")
        delete_btn = QPushButton("删除")
        hl.addStretch(1)  # 添加前置拉伸以居中按钮
        hl.addWidget(edit_btn)
        hl.addWidget(delete_btn)
        hl.addStretch(1)  # 添加后置拉伸以居中按钮
        self.table.setCellWidget(row, 4, action_widget)

        # Connect signals
        edit_btn.clicked.connect(lambda _, tid=task.id: self.edit_task(tid))
        delete_btn.clicked.connect(lambda _, tid=task.id: self.delete_task(tid))

    # ---------------- Add task -----------------
    def add_task(self):
        raw_title = self.new_title_edit.text().strip()
        if not raw_title:
            return
        due_dt = parse_date(self.new_date_edit.date())
        
        # 从标题中提取标签
        title, tag_in_title = extract_tag(raw_title)
        
        # 创建新任务
        task = Task(title=title, due_date=due_dt)
        self.session.add(task)
        
        # 添加选中的标签
        for tag_id in self.selected_tag_ids:
            tag = self.session.query(Tag).get(tag_id)
            if tag:
                task.tags.append(tag)
        
        # 如果标题中有标签，添加到任务标签中
        if tag_in_title:
            tag = self.session.query(Tag).filter_by(tag=tag_in_title).first()
            if not tag:
                tag = Tag(tag=tag_in_title)
                self.session.add(tag)
                self.session.commit()
            
            # 检查标签是否已经添加
            if tag not in task.tags:
                task.tags.append(tag)
        
        # 保存任务
        self.session.commit()

        # 重置输入
        self.new_title_edit.clear()
        self.new_date_edit.setDate(QDate())
        self.selected_tag_ids = []
        self.tag_btn.setText("选择标签")

        # 更新UI
        self.load_tasks()
        
        # 发出任务变更信号
        self.task_changed.emit()

    # ---------------- Edit task -----------------
    def edit_task(self, task_id: int):
        task = self.session.query(Task).get(task_id)
        if not task:
            return
        dlg = EditTaskDialog(self.session, task, self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if not data:
                QMessageBox.warning(self, "错误", "任务标题不能为空")
                return
                
            # 更新任务基本信息
            task.title = data["title"]
            task.due_date = data["due_date"]
            
            # 更新任务标签
            # 首先清除所有现有标签
            task.tags.clear()
            
            # 添加选中的标签
            for tag_id in data["tag_ids"]:
                tag = self.session.query(Tag).get(tag_id)
                if tag:
                    task.tags.append(tag)
                    
            # 保存更改
            self.session.commit()
            self.load_tasks()
            
            # 发出任务变更信号
            self.task_changed.emit()

    # ---------------- Delete task -----------------
    def delete_task(self, task_id: int):
        if QMessageBox.question(self, "确认", "确定删除该任务吗？") != QMessageBox.Yes:
            return
        task = self.session.query(Task).get(task_id)
        if not task:
            return
        self.session.delete(task)
        self.session.commit()
        self.load_tasks()
        
        # 发出任务变更信号
        self.task_changed.emit()

    # ---------------- Toggle completed -----------------
    def handle_cell_changed(self, row: int, column: int):
        if column == 0:
            item = self.table.item(row, column)
            if not item:
                return
                
            task_id = item.data(Qt.UserRole)
            task = self.session.query(Task).get(task_id)
            if not task:
                return
                
            task.completed = item.checkState() == Qt.Checked
            self.session.commit()
            
            # 可选的删除线文本
            title_item = self.table.item(row, 1)
            if title_item:  # 添加空值检查
                font = title_item.font()
                font.setStrikeOut(task.completed)
                title_item.setFont(font)
                
            # 发出任务变更信号
            self.task_changed.emit()
