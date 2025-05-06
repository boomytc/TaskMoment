#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库迁移工具
用于更新数据库结构，添加新字段等
"""

import sqlite3
from pathlib import Path

# 获取数据库路径
CURRENT_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = CURRENT_DIR / "data" / "tasks.db"

def migrate_database():
    """执行数据库迁移"""
    print(f"正在迁移数据库: {DB_PATH}")
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查task表是否存在priority列
    cursor.execute("PRAGMA table_info(task)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    # 如果不存在priority列，添加它
    if "priority" not in column_names:
        print("添加优先级字段...")
        cursor.execute("ALTER TABLE task ADD COLUMN priority SMALLINT DEFAULT 0 NOT NULL")
        conn.commit()
        print("优先级字段添加成功！")
    else:
        print("优先级字段已存在，无需迁移")
    
    # 关闭连接
    conn.close()
    print("数据库迁移完成！")

if __name__ == "__main__":
    migrate_database()
