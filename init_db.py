import sqlite3
import os

DATABASE = 'crm.db'

def init_database():
    if os.path.exists(DATABASE):
        print(f'数据库 {DATABASE} 已存在')
        return
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # 创建客户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            country TEXT NOT NULL,
            contact_person TEXT NOT NULL,
            email TEXT NOT NULL,
            product_type TEXT NOT NULL,
            follow_up_date TEXT,
            quote_status TEXT DEFAULT '未报价',
            created_date TEXT NOT NULL,
            updated_date TEXT NOT NULL,
            notes TEXT
        )
    ''')
    
    # 创建成交记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            transaction_date TEXT NOT NULL,
            created_date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    # 创建跟进记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS follow_ups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            follow_up_date TEXT NOT NULL,
            notes TEXT,
            created_date TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f'数据库 {DATABASE} 初始化成功！')

if __name__ == '__main__':
    init_database()
