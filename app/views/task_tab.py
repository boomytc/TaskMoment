from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView, 
    QDialog, QLabel, QMessageBox, QGridLayout, QListWidget, 
    QListWidgetItem, QAbstractItemView
)

from app.controllers.task_controller import TaskController
from app.controllers.tag_controller import TagController
from app.models.task import Task
from app.models.tag import Tag

class TaskEditDialog(QDialog):
    """任务编辑对话框"""
    
    def __init__(self, task_controller, tag_controller, task=None, parent=None):
        """初始化对话框
        
        Args:
            task_controller: 任务控制器
            tag_controller: 标签控制器
            task: 要编辑的任务，如果为None则为新建任务
            parent: 父窗口
        """
        super().__init__(parent)
        self.task_controller = task_controller
        self.tag_controller = tag_controller
        self.task = task
        self.setWindowTitle("编辑任务" if task else "新建任务")
        
        self._init_ui()
        
        # 如果是编辑任务，填充表单
        if task:
            self._populate_form()
    
    def _init_ui(self):
        """初始化UI"""
        # 创建控件
        self.title_edit = QLineEdit()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        
        # 标签列表和添加标签控件
        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.tag_list.setMaximumHeight(100)
        
        self.new_tag_edit = QLineEdit()
        self.new_tag_edit.setPlaceholderText("输入新标签")
        self.add_tag_btn = QPushButton("+")
        self.add_tag_btn.setMaximumWidth(30)
        
        # 初始化标签列表
        self._init_tag_list()
        
        # 布局
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
        
        # 按钮区域
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
    
    def _init_tag_list(self):
        """初始化标签列表"""
        self.tag_list.clear()
        self.tag_map = {}  # 用于存储标签项和标签对象的映射
        
        # 加载所有标签
        for tag in self.tag_controller.get_all_tags():
            item = QListWidgetItem(tag.tag)
            item.setData(Qt.UserRole, tag.id)
            self.tag_list.addItem(item)
            self.tag_map[tag.id] = item
    
    def _populate_form(self):
        """填充表单数据"""
        if not self.task:
            return
            
        self.title_edit.setText(self.task.title)
        
        if self.task.due_date:
            self.date_edit.setDate(QDate(
                self.task.due_date.year,
                self.task.due_date.month,
                self.task.due_date.day
            ))
        else:
            self.date_edit.setDate(QDate())
            
        # 选中任务已有的标签
        for tag in self.task.tags:
            if tag.id in self.tag_map:
                self.tag_map[tag.id].setSelected(True)
    
    def _add_new_tag(self):
        """添加新标签"""
        tag_name = self.new_tag_edit.text().strip()
        if not tag_name:
            return
            
        # 获取或创建标签
        tag = self.tag_controller.get_or_create_tag(tag_name)
        
        # 如果标签已在列表中，选中它
        if tag.id in self.tag_map:
            self.tag_map[tag.id].setSelected(True)
        else:
            # 添加到列表并选中
            item = QListWidgetItem(tag.tag)
            item.setData(Qt.UserRole, tag.id)
            item.setSelected(True)
            self.tag_list.addItem(item)
            self.tag_map[tag.id] = item
        
        # 清空输入框
        self.new_tag_edit.clear()
    
    def get_data(self):
        """获取表单数据
        
        Returns:
            包含任务数据的字典，如果标题为空则返回None
        """
        title = self.title_edit.text().strip()
        if not title:
            return None
            
        # 从标题中提取标签
        title, tag_in_title = self.task_controller.extract_tag(title)
        
        # 获取选中的标签ID
        selected_tags = []
        for item in self.tag_list.selectedItems():
            tag_id = item.data(Qt.UserRole)
            selected_tags.append(tag_id)
            
        # 如果标题中有标签，添加到选中的标签列表
        if tag_in_title:
            tag = self.tag_controller.get_or_create_tag(tag_in_title)
            if tag.id not in selected_tags:
                selected_tags.append(tag.id)
                
        # 获取截止日期
        due_date = self.task_controller.parse_date(self.date_edit.date())
        
        return {
            "title": title,
            "due_date": due_date,
            "tag_ids": selected_tags
        }


class TagSelectionDialog(QDialog):
    """标签选择对话框"""
    
    def __init__(self, tag_controller, selected_tag_ids=None, parent=None):
        """初始化对话框
        
        Args:
            tag_controller: 标签控制器
            selected_tag_ids: 已选中的标签ID列表
            parent: 父窗口
        """
        super().__init__(parent)
        self.tag_controller = tag_controller
        self.selected_tag_ids = selected_tag_ids or []
        self.setWindowTitle("选择标签")
        self.setMinimumWidth(300)
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标签列表
        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.tag_list)
        
        # 添加新标签区域
        new_tag_layout = QHBoxLayout()
        self.new_tag_edit = QLineEdit()
        self.new_tag_edit.setPlaceholderText("输入新标签")
        self.add_tag_btn = QPushButton("+")
        self.add_tag_btn.setMaximumWidth(30)
        new_tag_layout.addWidget(self.new_tag_edit)
        new_tag_layout.addWidget(self.add_tag_btn)
        layout.addLayout(new_tag_layout)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        # 加载标签并选中已选标签
        self.tag_map = {}
        for tag in self.tag_controller.get_all_tags():
            item = QListWidgetItem(tag.tag)
            item.setData(Qt.UserRole, tag.id)
            self.tag_list.addItem(item)
            self.tag_map[tag.id] = item
            
            # 如果标签已经选中，则选中它
            if tag.id in self.selected_tag_ids:
                item.setSelected(True)
        
        # 连接信号
        self.add_tag_btn.clicked.connect(self._add_new_tag)
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
    
    def _add_new_tag(self):
        """添加新标签"""
        tag_name = self.new_tag_edit.text().strip()
        if not tag_name:
            return
            
        # 获取或创建标签
        tag = self.tag_controller.get_or_create_tag(tag_name)
        
        # 如果标签已在列表中，选中它
        if tag.id in self.tag_map:
            self.tag_map[tag.id].setSelected(True)
        else:
            # 添加到列表并选中
            item = QListWidgetItem(tag.tag)
            item.setData(Qt.UserRole, tag.id)
            item.setSelected(True)
            self.tag_list.addItem(item)
            self.tag_map[tag.id] = item
        
        # 清空输入框
        self.new_tag_edit.clear()
    
    def get_selected_tag_ids(self):
        """获取选中的标签ID列表
        
        Returns:
            标签ID列表
        """
        selected_tags = []
        for item in self.tag_list.selectedItems():
            tag_id = item.data(Qt.UserRole)
            selected_tags.append(tag_id)
        return selected_tags


class TaskTab(QWidget):
    """任务标签页"""
    
    # 定义信号
    task_changed = Signal()
    
    def __init__(self, session):
        """初始化标签页
        
        Args:
            session: 数据库会话
        """
        super().__init__()
        
        # 创建控制器
        self.task_controller = TaskController(session)
        self.tag_controller = TagController(session)
        
        # 初始化UI
        self._setup_ui()
        
        # 加载任务
        self.load_tasks()
        
        # 初始化标签选择状态
        self.selected_tag_ids = []
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 输入行
        input_row = QHBoxLayout()
        self.new_title_edit = QLineEdit()
        self.new_title_edit.setPlaceholderText("添加新任务…")
        self.new_date_edit = QDateEdit()
        self.new_date_edit.setCalendarPopup(True)
        self.new_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.new_date_edit.setDate(QDate.currentDate())
        
        # 标签选择按钮
        self.tag_btn = QPushButton("选择标签")
        add_btn = QPushButton("添加")
        
        input_row.addWidget(self.new_title_edit, 3)
        input_row.addWidget(self.new_date_edit, 1)
        input_row.addWidget(self.tag_btn, 1)
        input_row.addWidget(add_btn, 1)
        
        layout.addLayout(input_row)
        
        # 任务表格
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["完成", "任务", "截止日期", "标签", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.table)
        
        # 连接信号
        add_btn.clicked.connect(self.add_task)
        self.tag_btn.clicked.connect(self.select_tags)
        self.table.cellChanged.connect(self.handle_cell_changed)
    
    def select_tags(self):
        """打开标签选择对话框"""
        dialog = TagSelectionDialog(
            self.tag_controller,
            self.selected_tag_ids,
            self
        )
        
        if dialog.exec() == QDialog.Accepted:
            # 获取选中的标签
            self.selected_tag_ids = dialog.get_selected_tag_ids()
            
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
            tag = self.tag_controller.get_tag_by_id(tag_id)
            if tag:
                tag_names.append(tag.tag)
        
        # 如果标签太多，只显示前几个
        if len(tag_names) <= 2:
            self.tag_btn.setText(", ".join(tag_names))
        else:
            self.tag_btn.setText(f"{tag_names[0]}, {tag_names[1]}... (+{len(tag_names)-2})")
    
    def load_tasks(self):
        """加载所有任务"""
        self.table.setRowCount(0)
        
        for task in self.task_controller.get_all_tasks():
            self._add_task_to_table(task)
    
    def _add_task_to_table(self, task):
        """将任务添加到表格
        
        Args:
            task: 任务对象
        """
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # 完成复选框
        chk_item = QTableWidgetItem()
        chk_item.setFlags(chk_item.flags() | Qt.ItemIsUserCheckable)
        chk_item.setCheckState(Qt.Checked if task.completed else Qt.Unchecked)
        chk_item.setData(Qt.UserRole, task.id)
        chk_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 0, chk_item)
        
        # 标题
        title_item = QTableWidgetItem(task.title)
        title_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 1, title_item)
        
        # 截止日期
        due_text = task.due_date.strftime("%Y-%m-%d") if task.due_date else ""
        due_item = QTableWidgetItem(due_text)
        due_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 2, due_item)
        
        # 标签
        tag_text = ", ".join([tag.tag for tag in task.tags]) if task.tags else ""
        tag_item = QTableWidgetItem(tag_text)
        tag_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 3, tag_item)
        
        # 操作按钮
        action_widget = QWidget()
        hl = QHBoxLayout(action_widget)
        hl.setContentsMargins(0, 0, 0, 0)
        edit_btn = QPushButton("编辑")
        delete_btn = QPushButton("删除")
        hl.addStretch(1)
        hl.addWidget(edit_btn)
        hl.addWidget(delete_btn)
        hl.addStretch(1)
        self.table.setCellWidget(row, 4, action_widget)
        
        # 连接信号
        edit_btn.clicked.connect(lambda _, tid=task.id: self.edit_task(tid))
        delete_btn.clicked.connect(lambda _, tid=task.id: self.delete_task(tid))
        
        # 如果任务已完成，添加删除线
        if task.completed:
            font = title_item.font()
            font.setStrikeOut(True)
            title_item.setFont(font)
    
    def add_task(self):
        """添加新任务"""
        raw_title = self.new_title_edit.text().strip()
        if not raw_title:
            return
            
        # 从标题中提取标签
        title, tag_in_title = self.task_controller.extract_tag(raw_title)
        
        # 获取截止日期
        due_dt = self.task_controller.parse_date(self.new_date_edit.date())
        
        # 准备标签ID列表
        tag_ids = list(self.selected_tag_ids)
        
        # 如果标题中有标签，添加到标签列表
        if tag_in_title:
            tag = self.tag_controller.get_or_create_tag(tag_in_title)
            if tag.id not in tag_ids:
                tag_ids.append(tag.id)
        
        # 创建任务
        self.task_controller.create_task(title, due_dt, tag_ids)
        
        # 重置输入
        self.new_title_edit.clear()
        self.new_date_edit.setDate(QDate())
        self.selected_tag_ids = []
        self.tag_btn.setText("选择标签")
        
        # 更新UI
        self.load_tasks()
        
        # 发出任务变更信号
        self.task_changed.emit()
    
    def edit_task(self, task_id):
        """编辑任务
        
        Args:
            task_id: 任务ID
        """
        task = self.task_controller.get_task_by_id(task_id)
        if not task:
            return
            
        # 打开编辑对话框
        dlg = TaskEditDialog(self.task_controller, self.tag_controller, task, self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if not data:
                QMessageBox.warning(self, "错误", "任务标题不能为空")
                return
                
            # 更新任务
            self.task_controller.update_task(task_id, data)
            
            # 更新UI
            self.load_tasks()
            
            # 发出任务变更信号
            self.task_changed.emit()
    
    def delete_task(self, task_id):
        """删除任务
        
        Args:
            task_id: 任务ID
        """
        if QMessageBox.question(self, "确认", "确定删除该任务吗？") != QMessageBox.Yes:
            return
            
        # 删除任务
        if self.task_controller.delete_task(task_id):
            # 更新UI
            self.load_tasks()
            
            # 发出任务变更信号
            self.task_changed.emit()
    
    def handle_cell_changed(self, row, column):
        """处理单元格变更
        
        Args:
            row: 行索引
            column: 列索引
        """
        if column == 0:
            item = self.table.item(row, column)
            if not item:
                return
                
            task_id = item.data(Qt.UserRole)
            task = self.task_controller.get_task_by_id(task_id)
            if not task:
                return
                
            # 更新任务完成状态
            self.task_controller.update_task(task_id, {
                "completed": item.checkState() == Qt.Checked
            })
            
            # 更新UI - 添加或移除删除线
            title_item = self.table.item(row, 1)
            if title_item:
                font = title_item.font()
                font.setStrikeOut(item.checkState() == Qt.Checked)
                title_item.setFont(font)
            
            # 发出任务变更信号
            self.task_changed.emit()
