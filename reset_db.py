import os
import shutil
from app import create_app, db

def reset_database():
    print("开始重置数据库...")
    
    # 数据库文件路径
    instance_path = 'instance'
    db_file = os.path.join(instance_path, 'health_tracker.sqlite')
    
    # 1. 删除旧的数据库文件
    if os.path.exists(db_file):
        print(f"删除旧数据库文件: {db_file}")
        try:
            os.remove(db_file)
        except Exception as e:
            print(f"警告: 删除数据库文件时出错: {e}")
    
    # 2. 创建新的数据库
    app = create_app()
    with app.app_context():
        print("创建新数据库...")
        db.create_all()
        print("数据库创建成功!")

if __name__ == "__main__":
    reset_database()
    print("数据库重置完成!")

# Generated by Copilot
