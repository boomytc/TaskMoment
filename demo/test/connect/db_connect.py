import os
import pymysql
from typing import Optional, List, Dict
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 数据库连接配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST'), 
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),  
    'password': os.getenv('DB_PASSWORD'),  
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4'
}

class DatabaseConnection:
    def __init__(self):
        self.connection = None

    def connect(self) -> bool:
        """连接数据库"""
        try:
            self.connection = pymysql.connect(**DB_CONFIG)
            print(f"成功连接到数据库 {DB_CONFIG['database']}")
            return True
        except pymysql.Error as e:
            print(f"数据库连接失败: {e}")
            return False

    def get_tables(self) -> Optional[List[str]]:
        """获取所有表名"""
        if not self.connection:
            print("未连接到数据库")
            return None

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [table[0] for table in cursor.fetchall()]
                return tables
        except pymysql.Error as e:
            print(f"获取表信息失败: {e}")
            return None

    def get_table_schema(self, table_name: str) -> Optional[List[Dict]]:
        """获取指定表的结构信息"""
        if not self.connection:
            print("未连接到数据库")
            return None

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                schema = [
                    {
                        'Field': col[0],
                        'Type': col[1],
                        'Null': col[2],
                        'Key': col[3],
                        'Default': col[4],
                        'Extra': col[5]
                    }
                    for col in columns
                ]
                return schema
        except pymysql.Error as e:
            print(f"获取表结构失败: {e}")
            return None

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("数据库连接已关闭")

def main():
    # 使用示例
    db = DatabaseConnection()
    if db.connect():
        # 获取所有表名
        tables = db.get_tables()
        if tables:
            print("\n数据库中的表:")
            for table in tables:
                print(f"\n表名: {table}")
                # 获取表结构
                schema = db.get_table_schema(table)
                if schema:
                    print("表结构:")
                    for column in schema:
                        print(f"  {column['Field']}: {column['Type']} "
                              f"({column['Null']}, {column['Key']}, {column['Default']}, {column['Extra']})")

        db.close()

if __name__ == '__main__':
    main()