import sys
import os
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QDateEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QLabel, QMessageBox, QGridLayout
)

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# --------------------------- Database --------------------------------------

Base = declarative_base()


class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True)
    tag = Column(String(50), nullable=False, unique=True)

    def __repr__(self):
        return f"<Tag {self.tag}>"


class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)

    tag_id = Column(Integer, ForeignKey("tag.id"), nullable=True)
    tag = relationship("Tag", backref="tasks")

    def display_title(self):
        """Return title with #tag appended (for UI display)."""
        if self.tag:
            return f"{self.title} #{self.tag.tag}"
        return self.title


# Resolve the path to the SQLite DB used by the web version to ensure data is shared.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "webui_demo" / "tasks.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

# Create tables if they do not exist
Base.metadata.create_all(engine)


# --------------------------- Helpers ---------------------------------------

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


# --------------------------- UI Components ---------------------------------

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
        self.tag_combo = QComboBox()

        self._init_tag_combo()

        # Layout
        layout = QGridLayout()
        layout.addWidget(QLabel("任务内容:"), 0, 0)
        layout.addWidget(self.title_edit, 0, 1)
        layout.addWidget(QLabel("截止日期:"), 1, 0)
        layout.addWidget(self.date_edit, 1, 1)
        layout.addWidget(QLabel("标签:"), 2, 0)
        layout.addWidget(self.tag_combo, 2, 1)

        btn_box = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        btn_box.addWidget(save_btn)
        btn_box.addWidget(cancel_btn)
        layout.addLayout(btn_box, 3, 0, 1, 2)

        self.setLayout(layout)

        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        # Populate fields if editing
        if task:
            self.title_edit.setText(task.display_title())
            if task.due_date: # <-- Only set if task has a due date
                self.date_edit.setDate(QDate(task.due_date.year, task.due_date.month, task.due_date.day))
            if task.tag:
                index = self.tag_combo.findData(task.tag.id)
                if index >= 0:
                    self.tag_combo.setCurrentIndex(index)

    # ------------------- Tag helpers -------------------
    def _init_tag_combo(self):
        self.tag_combo.clear()
        self.tag_combo.addItem("无标签", None)
        tags = self.session.query(Tag).order_by(Tag.tag).all()
        for tag in tags:
            self.tag_combo.addItem(tag.tag, tag.id)

    # ------------------- Results -------------------
    def get_data(self):
        """Return dict with title, due_date, tag_id"""
        title_raw = self.title_edit.text().strip()
        if not title_raw:
            return None
        # Parse for #tag in text
        title, tag_name_in_title = extract_tag(title_raw)

        tag_id = self.tag_combo.currentData()
        # If user typed #tag in title, override combobox selection
        if tag_name_in_title:
            tag = self.session.query(Tag).filter_by(tag=tag_name_in_title).first()
            if not tag:
                tag = Tag(tag=tag_name_in_title)
                self.session.add(tag)
                self.session.commit()
            tag_id = tag.id

        due_dt = parse_date(self.date_edit.date())

        return {"title": title, "tag_id": tag_id, "due_date": due_dt}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("任务清单")
        self.resize(800, 600)

        self.session = Session()

        central = QWidget()
        self.setCentralWidget(central)

        vbox = QVBoxLayout(central)

        # ----------- Input Row -------------
        input_row = QHBoxLayout()
        self.new_title_edit = QLineEdit()
        self.new_title_edit.setPlaceholderText("添加新任务…")
        self.new_date_edit = QDateEdit()
        self.new_date_edit.setCalendarPopup(True)
        self.new_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.new_date_edit.setDate(QDate.currentDate()) # <-- Set default to today
        self.new_tag_combo = QComboBox()
        self._refresh_tag_combo()
        add_btn = QPushButton("添加")

        input_row.addWidget(self.new_title_edit, 2)
        input_row.addWidget(self.new_date_edit, 1)
        input_row.addWidget(self.new_tag_combo, 1)
        input_row.addWidget(add_btn)

        vbox.addLayout(input_row)

        # ----------- Task Table -------------
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["完成", "任务", "截止日期", "标签", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # <-- Resize first column
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter) # <-- Center header text
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        vbox.addWidget(self.table)

        # ----------- Connections -------------
        add_btn.clicked.connect(self.add_task)
        self.table.cellChanged.connect(self.handle_cell_changed)

        # Load tasks
        self.load_tasks()

    # ---------------- Tag Combo -----------------
    def _refresh_tag_combo(self):
        self.new_tag_combo.clear()
        self.new_tag_combo.addItem("无标签", None)
        tags = self.session.query(Tag).order_by(Tag.tag).all()
        for t in tags:
            self.new_tag_combo.addItem(t.tag, t.id)

    # ---------------- Load tasks ---------------
    def load_tasks(self):
        tasks = self.session.query(Task).order_by(Task.created_at.desc()).all()
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for task in tasks:
            self._add_task_to_table(task)
        self.table.blockSignals(False)

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

        # Tag
        tag_text = task.tag.tag if task.tag else ""
        tag_item = QTableWidgetItem(tag_text)
        tag_item.setTextAlignment(Qt.AlignCenter) # <-- Center text
        self.table.setItem(row, 3, tag_item)

        # Actions (Edit/Delete buttons)
        action_widget = QWidget()
        hl = QHBoxLayout(action_widget)
        hl.setContentsMargins(0, 0, 0, 0)
        edit_btn = QPushButton("编辑")
        delete_btn = QPushButton("删除")
        hl.addWidget(edit_btn)
        hl.addWidget(delete_btn)
        hl.addStretch()
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
        # Determine tag id
        tag_id = self.new_tag_combo.currentData()

        title, tag_in_title = extract_tag(raw_title)
        if tag_in_title:
            tag = self.session.query(Tag).filter_by(tag=tag_in_title).first()
            if not tag:
                tag = Tag(tag=tag_in_title)
                self.session.add(tag)
                self.session.commit()
            tag_id = tag.id

        task = Task(title=title, due_date=due_dt, tag_id=tag_id)
        self.session.add(task)
        self.session.commit()

        # Reset inputs
        self.new_title_edit.clear()
        self.new_date_edit.setDate(QDate())
        self.new_tag_combo.setCurrentIndex(0)
        self._refresh_tag_combo()

        # Update UI
        self.load_tasks()

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
            task.title = data["title"]
            task.due_date = data["due_date"]
            task.tag_id = data["tag_id"]
            self.session.commit()
            self._refresh_tag_combo()
            self.load_tasks()

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

    # ---------------- Toggle completed -----------------
    def handle_cell_changed(self, row: int, column: int):
        if column == 0:
            item = self.table.item(row, column)
            task_id = item.data(Qt.UserRole)
            task = self.session.query(Task).get(task_id)
            if task:
                task.completed = item.checkState() == Qt.Checked
                self.session.commit()
                # Optionally strike-through text
                font = self.table.item(row, 1).font()
                font.setStrikeOut(task.completed)
                self.table.item(row, 1).setFont(font)


# --------------------------- Entry Point -----------------------------------

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
