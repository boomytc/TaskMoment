import os
import pymysql
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional

# 加载 .env 文件
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# 数据库连接配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4'
}

class UserDatabase:
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

    def add_user(self, username: str, password: str, email: str) -> bool:
        """
        添加新用户到数据库
        
        参数:
            username: 用户名
            password: 密码
            email: 电子邮件
            
        返回:
            bool: 添加成功返回True，失败返回False
        """
        if not self.connection:
            print("未连接到数据库")
            return False

        try:
            with self.connection.cursor() as cursor:
                sql = """
                INSERT INTO Users (username, password, email, created_time)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (username, password, email, datetime.now()))
            
            self.connection.commit()
            print("用户添加成功")
            return True
            
        except Exception as e:
            self.connection.rollback()
            print(f"添加用户失败: {e}")
            return False

    def get_users(self) -> Optional[list]:
        """获取所有用户信息"""
        if not self.connection:
            print("未连接到数据库")
            return None

        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT user_id, username, email, created_time FROM Users"
                cursor.execute(sql)
                users = cursor.fetchall()
                print("\n当前用户列表:")
                print("ID\t用户名\t\t邮箱\t\t\t创建时间")
                print("-" * 70)
                for user in users:
                    print(f"{user[0]}\t{user[1]:<12}\t{user[2]:<24}\t{user[3]}")
                return users
        except Exception as e:
            print(f"获取用户列表失败: {e}")
            return None

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("数据库连接已关闭")

def main():
    # 使用示例
    db = UserDatabase()
    if db.connect():
        # 添加测试用户
        if db.add_user(
            username="test_user",
            password="test_password",
            email="test@example.com"
        ):
            # 显示用户列表
            db.get_users()
        db.close()

if __name__ == '__main__':
    main()