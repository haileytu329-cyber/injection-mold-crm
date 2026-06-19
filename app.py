from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

DATABASE = 'crm.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
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

@app.route('/')
def index():
    return render_template('index.html')

# ==================== 客户管理接口 ====================

@app.route('/api/customers', methods=['GET'])
def get_customers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取筛选条件
        country = request.args.get('country')
        quote_status = request.args.get('quote_status')
        product_type = request.args.get('product_type')
        
        query = 'SELECT * FROM customers WHERE 1=1'
        params = []
        
        if country:
            query += ' AND country = ?'
            params.append(country)
        if quote_status:
            query += ' AND quote_status = ?'
            params.append(quote_status)
        if product_type:
            query += ' AND product_type = ?'
            params.append(product_type)
        
        query += ' ORDER BY updated_date DESC'
        
        cursor.execute(query, params)
        customers = cursor.fetchall()
        conn.close()
        
        result = []
        for customer in customers:
            # 获取成交记录
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(amount) FROM transactions WHERE customer_id = ?', (customer['id'],))
            total_amount = cursor.fetchone()[0] or 0
            conn.close()
            
            result.append({
                'id': customer['id'],
                'company_name': customer['company_name'],
                'country': customer['country'],
                'contact_person': customer['contact_person'],
                'email': customer['email'],
                'product_type': customer['product_type'],
                'follow_up_date': customer['follow_up_date'],
                'quote_status': customer['quote_status'],
                'created_date': customer['created_date'],
                'updated_date': customer['updated_date'],
                'notes': customer['notes'],
                'total_amount': total_amount
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers', methods=['POST'])
def add_customer():
    try:
        data = request.get_json()
        
        required_fields = ['company_name', 'country', 'contact_person', 'email', 'product_type']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO customers 
            (company_name, country, contact_person, email, product_type, follow_up_date, quote_status, created_date, updated_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['company_name'],
            data['country'],
            data['contact_person'],
            data['email'],
            data['product_type'],
            data.get('follow_up_date', ''),
            data.get('quote_status', '未报价'),
            now,
            now,
            data.get('notes', '')
        ))
        
        conn.commit()
        customer_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'id': customer_id, 'message': '客户添加成功'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            conn.close()
            return jsonify({'error': '客户不存在'}), 404
        
        # 获取成交记录
        cursor.execute('SELECT * FROM transactions WHERE customer_id = ? ORDER BY transaction_date DESC', (customer_id,))
        transactions = [dict(row) for row in cursor.fetchall()]
        
        # 获取跟进记录
        cursor.execute('SELECT * FROM follow_ups WHERE customer_id = ? ORDER BY follow_up_date DESC', (customer_id,))
        follow_ups = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'id': customer['id'],
            'company_name': customer['company_name'],
            'country': customer['country'],
            'contact_person': customer['contact_person'],
            'email': customer['email'],
            'product_type': customer['product_type'],
            'follow_up_date': customer['follow_up_date'],
            'quote_status': customer['quote_status'],
            'created_date': customer['created_date'],
            'updated_date': customer['updated_date'],
            'notes': customer['notes'],
            'transactions': transactions,
            'follow_ups': follow_ups
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查客户是否存在
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': '客户不存在'}), 404
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        updates = []
        params = []
        
        fields = ['company_name', 'country', 'contact_person', 'email', 'product_type', 'follow_up_date', 'quote_status', 'notes']
        for field in fields:
            if field in data:
                updates.append(f'{field} = ?')
                params.append(data[field])
        
        if updates:
            updates.append('updated_date = ?')
            params.append(now)
            params.append(customer_id)
            
            query = f'UPDATE customers SET {", ".join(updates)} WHERE id = ?'
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
        return jsonify({'message': '客户信息更新成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查客户是否存在
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': '客户不存在'}), 404
        
        # 删除相关记录
        cursor.execute('DELETE FROM transactions WHERE customer_id = ?', (customer_id,))
        cursor.execute('DELETE FROM follow_ups WHERE customer_id = ?', (customer_id,))
        cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': '客户删除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 成交记录接口 ====================

@app.route('/api/customers/<int:customer_id>/transactions', methods=['POST'])
def add_transaction(customer_id):
    try:
        data = request.get_json()
        
        if 'amount' not in data or 'transaction_date' not in data:
            return jsonify({'error': '缺少必填字段'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查客户是否存在
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': '客户不存在'}), 404
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO transactions (customer_id, amount, transaction_date, created_date, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            customer_id,
            data['amount'],
            data['transaction_date'],
            now,
            data.get('notes', '')
        ))
        
        # 更新客户的报价状态为已成交
        cursor.execute('UPDATE customers SET quote_status = ?, updated_date = ? WHERE id = ?', 
                      ('已成交', now, customer_id))
        
        conn.commit()
        transaction_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'id': transaction_id, 'message': '成交记录添加成功'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 跟进记录接口 ====================

@app.route('/api/customers/<int:customer_id>/follow-ups', methods=['POST'])
def add_follow_up(customer_id):
    try:
        data = request.get_json()
        
        if 'follow_up_date' not in data:
            return jsonify({'error': '缺少跟进日期'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查客户是否存在
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': '客户不存在'}), 404
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO follow_ups (customer_id, follow_up_date, notes, created_date)
            VALUES (?, ?, ?, ?)
        ''', (
            customer_id,
            data['follow_up_date'],
            data.get('notes', ''),
            now
        ))
        
        # 更新客户的跟进日期
        cursor.execute('UPDATE customers SET follow_up_date = ?, updated_date = ? WHERE id = ?',
                      (data['follow_up_date'], now, customer_id))
        
        conn.commit()
        follow_up_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'id': follow_up_id, 'message': '跟进记录添加成功'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 统计接口 ====================

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 总客户数
        cursor.execute('SELECT COUNT(*) FROM customers')
        total_customers = cursor.fetchone()[0]
        
        # 已成交客户数
        cursor.execute("SELECT COUNT(*) FROM customers WHERE quote_status = '已成交'")
        completed_customers = cursor.fetchone()[0]
        
        # 总成交金额
        cursor.execute('SELECT SUM(amount) FROM transactions')
        total_amount = cursor.fetchone()[0] or 0
        
        # 按国家统计
        cursor.execute('SELECT country, COUNT(*) as count FROM customers GROUP BY country')
        by_country = [{'country': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # 按报价状态统计
        cursor.execute('SELECT quote_status, COUNT(*) as count FROM customers GROUP BY quote_status')
        by_status = [{'status': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'total_customers': total_customers,
            'completed_customers': completed_customers,
            'total_amount': total_amount,
            'by_country': by_country,
            'by_status': by_status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 导出接口 ====================

@app.route('/api/export', methods=['GET'])
def export_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM customers ORDER BY updated_date DESC')
        customers = cursor.fetchall()
        conn.close()
        
        csv_data = 'ID,公司名称,国家,联系人,邮箱,产品类型,跟进日期,报价状态,创建日期,更新日期,备注\n'
        for customer in customers:
            row = f'{customer["id"]},"{customer["company_name"]}","{customer["country"]}","{customer["contact_person"]}","{customer["email"]}","{customer["product_type"]}","{customer["follow_up_date"]}","{customer["quote_status"]}","{customer["created_date"]}","{customer["updated_date"]}","{customer["notes"]}"\n'
            csv_data += row
        
        return csv_data, 200, {
            'Content-Type': 'text/csv; charset=utf-8',
            'Content-Disposition': 'attachment; filename=crm_customers.csv'
        }
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
