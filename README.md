# 注塑模具外贸CRM系统

一个轻量级的客户关系管理系统，专门为注塑模具外贸企业设计。

## 功能特性

- ✅ 客户信息管理（公司名称、国家、联系人、邮箱）
- ✅ 产品分类管理
- ✅ 跟进日期记录
- ✅ 报价状态追踪
- ✅ 成交记录统计
- ✅ 数据导出功能
- ✅ 响应式设计

## 技术栈

- **前端**: HTML5 + Bootstrap 5 + JavaScript
- **后端**: Python Flask
- **数据库**: SQLite
- **依赖**: Flask, Flask-CORS, python-dateutil

## 快速开始

### 1. 环境要求

- Python 3.7+
- pip

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 初始化数据库

```bash
python init_db.py
```

### 4. 运行服务器

```bash
python app.py
```

然后打开浏览器访问：`http://localhost:5000`

## 文件结构

```
injection-mold-crm/
├── app.py                 # Flask应用主文件
├── init_db.py            # 数据库初始化脚本
├── requirements.txt      # 项目依赖
├── README.md             # 项目说明
├── static/
│   ├── css/
│   │   └── style.css     # 样式文件
│   └── js/
│       └── main.js       # 前端脚本
├── templates/
│   └── index.html        # 主页面
└── crm.db               # SQLite数据库（自动生成）
```

## 使用说明

### 添加客户
1. 填写客户信息表单
2. 点击「添加客户」按钮

### 跟进管理
- 点击「详情」按钮查看客户信息
- 添加跟进日期和备注

### 报价管理
- 在客户列表中修改报价状态
- 支持：未报价 → 已报价 → 已成交

### 数据导出
- 点击「导出数据」按钮
- 下载CSV格式文件

## API 文档

### 获取所有客户
```
GET /api/customers
```

### 添加客户
```
POST /api/customers
Content-Type: application/json

{
  "company_name": "ABC公司",
  "country": "美国",
  "contact_person": "张三",
  "email": "zhang@example.com",
  "product_type": "精密塑料件",
  "follow_up_date": "2026-06-20",
  "quote_status": "未报价",
  "notes": "首次联系"
}
```

### 更新客户
```
PUT /api/customers/<id>
Content-Type: application/json
```

### 删除客户
```
DELETE /api/customers/<id>
```

### 添加成交记录
```
POST /api/customers/<id>/transactions
Content-Type: application/json

{
  "amount": 5000,
  "transaction_date": "2026-06-19",
  "notes": "订单号：2026001"
}
```

### 添加跟进记录
```
POST /api/customers/<id>/follow-ups
Content-Type: application/json

{
  "follow_up_date": "2026-06-25",
  "notes": "跟进内容"
}
```

## 注意事项

- 所有日期格式为 YYYY-MM-DD
- 报价状态：未报价、已报价、已成交
- 支持多种产品类型

## 许可证

MIT
