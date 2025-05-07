from PySide6.QtCore import Qt, QDate, Signal, QThreadPool, Slot
from PySide6.QtGui import QColor, QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QCalendarWidget, QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QDialog, QLabel, QMessageBox, QGridLayout, QListWidget, 
    QListWidgetItem, QAbstractItemView, QComboBox, QCheckBox, QMenu, QDateEdit
)
from datetime import date

from app.controllers.task_controller import TaskController
from app.controllers.tag_controller import TagController
from app.models.task import Task, Priority
from app.workers import GetAllTasksWorker

class TaskEditDialog(QDialog):
    """任务编辑对话框"""
    
    def __init__(self, tag_controller: TagController, task_controller: TaskController, task=None, parent=None):
        """初始化对话框
        
        Args:
            tag_controller: 标签控制器
            task_controller: 任务控制器
            task: 要编辑的任务，如果为None则为新建任务
            parent: 父窗口
        """
        super().__init__(parent)
        self.tag_controller = tag_controller
        self.task_controller = task_controller
        self.task = task
        self.setWindowTitle("编辑任务" if task else "新建任务")
        
        self._init_ui()
        
        # 如果是编辑任务，填充表单
        if task:
            self._load_task_data()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("任务标题")
        layout.addWidget(QLabel("标题:"))
        layout.addWidget(self.title_edit)

        self.due_date_edit = QDateEdit(self)
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDate(QDate.currentDate())
        self.due_date_edit.setSpecialValueText("无截止日期")
        layout.addWidget(QLabel("截止日期:"))
        layout.addWidget(self.due_date_edit)

        self.priority_combo = QComboBox()
        self.priority_combo.addItem("无", Priority.NONE)
        self.priority_combo.addItem("低", Priority.LOW)
        self.priority_combo.addItem("中", Priority.MEDIUM)
        self.priority_combo.addItem("高", Priority.HIGH)
        layout.addWidget(QLabel("优先级:"))
        layout.addWidget(self.priority_combo)

        self.tags_list_widget = QListWidget()
        self.tags_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        all_tags = self.tag_controller.get_all_tags()
        self.tag_map = {}
        for tag_obj in all_tags:
            item = QListWidgetItem(tag_obj.tag)
            item.setData(Qt.UserRole, tag_obj.id)
            self.tags_list_widget.addItem(item)
            self.tag_map[tag_obj.id] = item
        layout.addWidget(QLabel("标签:"))
        layout.addWidget(self.tags_list_widget)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _load_task_data(self):
        """加载任务数据到UI"""
        self.title_edit.setText(self.task.title)
        if self.task.due_date and self.task.due_date != date(1752, 9, 14):
            self.due_date_edit.setDate(QDate(self.task.due_date.year, self.task.due_date.month, self.task.due_date.day))
        else:
            self.due_date_edit.setDate(self.due_date_edit.minimumDate()) 

        priority_value = self.task.priority if isinstance(self.task.priority, int) else Priority.NONE
        self.priority_combo.setCurrentIndex(self.priority_combo.findData(priority_value))
        
        for tag_obj in self.task.tags:
            if tag_obj.id in self.tag_map:
                self.tag_map[tag_obj.id].setSelected(True)

    def get_task_data(self):
        """获取表单数据
        
        Returns:
            包含任务数据的字典，如果标题为空则返回None
        """
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "输入错误", "标题不能为空。")
            return None

        due_date_qdate = self.due_date_edit.date()
        due_date_str = None
        if due_date_qdate != self.due_date_edit.minimumDate():
            due_date_str = due_date_qdate.toString("yyyy-MM-dd")

        priority = self.priority_combo.currentData()
        
        selected_tag_ids = []
        for item in self.tags_list_widget.selectedItems():
            selected_tag_ids.append(item.data(Qt.UserRole))

        data = {
            'title': title,
            'due_date': due_date_str,
            'priority': priority,
            'tag_ids': selected_tag_ids
        }
        if self.task: 
            data['completed'] = self.task.completed # 保留现有完成状态
        return data


class TaskTab(QWidget):
    """任务管理标签页"""
    
    # 定义信号
    task_changed = Signal()
    
    def __init__(self, task_controller: TaskController, tag_controller: TagController, SessionMaker, parent=None):
        """初始化任务管理标签页
        
        Args:
            task_controller: 任务控制器
            tag_controller: 标签控制器
            SessionMaker: 数据库会话生成器
            parent: 父窗口
        """
        super().__init__(parent)
        self.task_controller = task_controller
        self.tag_controller = tag_controller
        self.SessionMaker = SessionMaker
        self.thread_pool = QThreadPool()
        self._init_ui()
        self.load_tasks()

    def _init_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        self.add_task_button = QPushButton("添加任务")
        self.add_task_button.clicked.connect(self.open_add_task_dialog)
        toolbar_layout.addWidget(self.add_task_button)
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # 任务列表
        self.table = QTableWidget()
        self.table.setColumnCount(6) # ID, 标题, 截止日期, 优先级, 标签, 完成
        self.table.setHorizontalHeaderLabels(["ID", "标题", "截止日期", "优先级", "标签", "完成"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # 标题列拉伸
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # 完成列自适应内容
        self.table.setEditTriggers(QTableWidget.NoEditTriggers) # 禁止直接编辑
        self.table.setSelectionBehavior(QTableWidget.SelectRows) # 整行选择
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.doubleClicked.connect(self.open_edit_task_dialog_on_double_click)
        layout.addWidget(self.table)

    def load_tasks(self):
        """异步加载任务列表"""
        self.add_task_button.setEnabled(False)
        worker = GetAllTasksWorker(self.SessionMaker)
        worker.signals.finished.connect(self._on_load_tasks_finished)
        worker.signals.error.connect(self._on_load_tasks_error)
        self.thread_pool.start(worker)

    @Slot(object)
    def _on_load_tasks_finished(self, tasks):
        """任务加载完成后的处理"""
        self.table.setRowCount(0)
        for task in tasks:
            self._add_task_to_table(task)
        self.add_task_button.setEnabled(True)

    @Slot(str)
    def _on_load_tasks_error(self, error_message):
        """任务加载错误处理"""
        QMessageBox.critical(self, "加载任务失败", error_message)
        self.add_task_button.setEnabled(True)

    def _add_task_to_table(self, task):
        """将任务添加到表格"""
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        # ID (隐藏)
        id_item = QTableWidgetItem(str(task.id))
        self.table.setItem(row_position, 0, id_item)
        self.table.setColumnHidden(0, True)

        # 标题
        title_item = QTableWidgetItem(task.title)
        if task.completed:
            font = title_item.font()
            font.setStrikeOut(True)
            title_item.setFont(font)
            title_item.setForeground(QColor("gray"))
        title_item.setTextAlignment(Qt.AlignCenter) # 居中对齐
        self.table.setItem(row_position, 1, title_item)

        # 截止日期
        due_date_str = "无截止日期"
        if task.due_date:
            if task.due_date == date(1752, 9, 14):
                due_date_str = "无截止日期"
            else:
                due_date_str = task.due_date.strftime("%Y-%m-%d")
        due_date_item = QTableWidgetItem(due_date_str)
        due_date_item.setTextAlignment(Qt.AlignCenter) # 居中对齐
        self.table.setItem(row_position, 2, due_date_item)

        # 优先级
        priority_item = QTableWidgetItem(task.get_priority_name())
        priority_item.setForeground(QColor(task.get_priority_color()))
        priority_item.setTextAlignment(Qt.AlignCenter) # 居中对齐
        self.table.setItem(row_position, 3, priority_item)

        # 标签
        tags_str = ", ".join([tag.tag for tag in task.tags])
        tags_item = QTableWidgetItem(tags_str)
        tags_item.setTextAlignment(Qt.AlignCenter) # 居中对齐
        self.table.setItem(row_position, 4, tags_item)

        # 完成状态 (复选框)
        completed_checkbox = QCheckBox()
        completed_checkbox.setChecked(task.completed)
        completed_checkbox.clicked.connect(lambda checked, task_id=task.id: self.toggle_task_completed_status(task_id, checked))
        
        # 创建一个容器 QWidget 用于居中复选框
        cell_widget = QWidget()
        layout_checkbox = QHBoxLayout(cell_widget)
        layout_checkbox.addWidget(completed_checkbox)
        layout_checkbox.setAlignment(Qt.AlignCenter) # 布局居中
        layout_checkbox.setContentsMargins(0,0,0,0) # 移除边距
        cell_widget.setLayout(layout_checkbox) # 设置布局到容器

        self.table.setCellWidget(row_position, 5, cell_widget) # 将容器 QWidget 设置为单元格小部件

    def open_add_task_dialog(self):
        """打开添加任务对话框"""
        dialog = TaskEditDialog(self.tag_controller, self.task_controller, parent=self)
        if dialog.exec():
            data = dialog.get_task_data()
            if data:
                self.task_controller.create_task(**data)
                self.load_tasks()
                self.task_changed.emit()

    def open_edit_task_dialog_on_double_click(self, item):
        """双击打开编辑任务对话框"""
        row = item.row()
        self.open_edit_task_dialog(row)

    def open_edit_task_dialog(self, row):
        """打开编辑任务对话框"""
        task_id = int(self.table.item(row, 0).text())
        task = self.task_controller.get_task_by_id(task_id)
        if not task:
            QMessageBox.warning(self, "错误", "找不到任务")
            return

        dialog = TaskEditDialog(self.tag_controller, self.task_controller, task=task, parent=self)
        if dialog.exec():
            data = dialog.get_task_data()
            if data:
                self.task_controller.update_task(task_id, data)
                self.load_tasks()
                self.task_changed.emit()

    def delete_task(self, row):
        """删除任务"""
        task_id = int(self.table.item(row, 0).text())
        reply = QMessageBox.question(self, "确认删除", "确定要删除此任务吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.task_controller.delete_task(task_id)
            self.load_tasks()
            self.task_changed.emit()

    def toggle_task_completed_status(self, task_id, checked):
        """切换任务完成状态"""
        self.task_controller.toggle_task_completed(task_id)
        self.load_tasks()
        self.task_changed.emit()

    def show_context_menu(self, pos):
        """显示右键菜单"""
        context_menu = QMenu(self)
        edit_action = QAction("编辑任务", self)
        delete_action = QAction("删除任务", self)
        
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
            
        row = selected_items[0].row()
        
        edit_action.triggered.connect(lambda: self.open_edit_task_dialog(row))
        delete_action.triggered.connect(lambda: self.delete_task(row))
        
        context_menu.addAction(edit_action)
        context_menu.addAction(delete_action)
        context_menu.exec(self.table.mapToGlobal(pos))
