// 全局变量
let currentCustomerId = null;
const API_BASE = '/api';

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    loadStatistics();
    loadCustomers();
    setupEventListeners();
    setInterval(loadStatistics, 60000); // 每分钟刷新一次
});

// 事件监听
function setupEventListeners() {
    // 添加客户
    document.getElementById('addCustomerForm').addEventListener('submit', handleAddCustomer);

    // 筛选
    document.getElementById('filterCountry').addEventListener('input', debounce(filterCustomers, 300));
    document.getElementById('filterStatus').addEventListener('change', filterCustomers);
    document.getElementById('filterProductType').addEventListener('input', debounce(filterCustomers, 300));
    document.getElementById('resetFilterBtn').addEventListener('click', resetFilters);

    // 导出
    document.getElementById('exportBtn').addEventListener('click', exportData);

    // 模态框事件
    document.getElementById('editCustomerForm').addEventListener('submit', handleEditCustomer);
    document.getElementById('addTransactionForm').addEventListener('submit', handleAddTransaction);
    document.getElementById('addFollowUpForm').addEventListener('submit', handleAddFollowUp);
    document.getElementById('deleteCustomerBtn').addEventListener('click', handleDeleteCustomer);
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 加载统计信息
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE}/statistics`);
        const data = await response.json();

        document.getElementById('totalCustomers').textContent = data.total_customers;
        document.getElementById('completedCustomers').textContent = data.completed_customers;
        document.getElementById('totalAmount').textContent = `¥${formatNumber(data.total_amount)}`;
        document.getElementById('pendingCustomers').textContent = 
            data.total_customers - data.completed_customers;

        // 按国家统计
        let countryHtml = '<ul class="list-group list-group-flush">';
        data.by_country.forEach(item => {
            countryHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">
                ${item.country}
                <span class="badge bg-primary rounded-pill">${item.count}</span>
            </li>`;
        });
        countryHtml += '</ul>';
        document.getElementById('countryStats').innerHTML = countryHtml;

        // 按状态统计
        let statusHtml = '<ul class="list-group list-group-flush">';
        data.by_status.forEach(item => {
            const badgeClass = {
                '未报价': 'bg-warning',
                '已报价': 'bg-info',
                '已成交': 'bg-success'
            }[item.status] || 'bg-secondary';
            
            statusHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">
                ${item.status}
                <span class="badge ${badgeClass} rounded-pill">${item.count}</span>
            </li>`;
        });
        statusHtml += '</ul>';
        document.getElementById('statusStats').innerHTML = statusHtml;
    } catch (error) {
        console.error('加载统计信息失败:', error);
    }
}

// 加载客户列表
async function loadCustomers() {
    try {
        const response = await fetch(`${API_BASE}/customers`);
        const customers = await response.json();

        if (customers.length === 0) {
            document.getElementById('noDataMessage').style.display = 'block';
            document.getElementById('customersTable').style.display = 'none';
            return;
        }

        document.getElementById('noDataMessage').style.display = 'none';
        document.getElementById('customersTable').style.display = 'table';

        const tbody = document.getElementById('customersBody');
        tbody.innerHTML = '';

        customers.forEach(customer => {
            const row = createCustomerRow(customer);
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('加载客户列表失败:', error);
    }
}

// 创建客户行
function createCustomerRow(customer) {
    const row = document.createElement('tr');
    
    const statusBadgeClass = {
        '未报价': 'badge-未报价',
        '已报价': 'badge-已报价',
        '已成交': 'badge-已成交'
    }[customer.quote_status] || 'bg-secondary';

    row.innerHTML = `
        <td>${customer.id}</td>
        <td>
            <strong>${customer.company_name}</strong>
            <br>
            <small class="text-muted">${customer.notes || '-'}</small>
        </td>
        <td>${customer.country}</td>
        <td>${customer.contact_person}</td>
        <td><small>${customer.email}</small></td>
        <td>${customer.product_type}</td>
        <td>${customer.follow_up_date || '-'}</td>
        <td><span class="badge ${statusBadgeClass}">${customer.quote_status}</span></td>
        <td>¥${formatNumber(customer.total_amount)}</td>
        <td>
            <button class="btn btn-sm btn-primary" onclick="viewCustomer(${customer.id})">
                <i class="bi bi-eye"></i> 详情
            </button>
        </td>
    `;
    
    return row;
}

// 查看客户详情
async function viewCustomer(customerId) {
    try {
        const response = await fetch(`${API_BASE}/customers/${customerId}`);
        const customer = await response.json();
        
        currentCustomerId = customerId;

        // 填充基本信息
        document.getElementById('modalTitle').textContent = `${customer.company_name} - 详情`;
        document.getElementById('detailCompanyName').textContent = customer.company_name;
        document.getElementById('detailCountry').textContent = customer.country;
        document.getElementById('detailContactPerson').textContent = customer.contact_person;
        document.getElementById('detailEmail').textContent = customer.email;
        document.getElementById('detailProductType').textContent = customer.product_type;
        document.getElementById('detailQuoteStatus').textContent = customer.quote_status;
        document.getElementById('detailFollowUpDate').textContent = customer.follow_up_date || '-';
        document.getElementById('detailCreatedDate').textContent = customer.created_date;
        document.getElementById('detailUpdatedDate').textContent = customer.updated_date;
        document.getElementById('detailNotes').textContent = customer.notes || '-';

        // 填充编辑表单
        document.getElementById('editQuoteStatus').value = customer.quote_status;
        document.getElementById('editFollowUpDate').value = customer.follow_up_date || '';
        document.getElementById('editNotes').value = customer.notes || '';

        // 显示成交记录
        displayTransactions(customer.transactions);

        // 显示跟进记录
        displayFollowUps(customer.follow_ups);

        // 显示模态框
        new bootstrap.Modal(document.getElementById('customerDetailModal')).show();
    } catch (error) {
        console.error('加载客户详情失败:', error);
        alert('加载客户详情失败');
    }
}

// 显示成交记录
function displayTransactions(transactions) {
    let html = '';
    if (transactions && transactions.length > 0) {
        html = '<div class="list-group">';
        transactions.forEach(trans => {
            html += `
                <div class="list-group-item">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">¥${formatNumber(trans.amount)}</h6>
                        <small>${trans.transaction_date}</small>
                    </div>
                    <p class="mb-1"><small>${trans.notes || '-'}</small></p>
                </div>
            `;
        });
        html += '</div>';
    } else {
        html = '<div class="alert alert-info">暂无成交记录</div>';
    }
    document.getElementById('transactionsList').innerHTML = html;
}

// 显示跟进记录
function displayFollowUps(followUps) {
    let html = '';
    if (followUps && followUps.length > 0) {
        html = '<div class="list-group">';
        followUps.forEach(followUp => {
            html += `
                <div class="list-group-item">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${followUp.follow_up_date}</h6>
                        <small class="text-muted">创建于 ${followUp.created_date}</small>
                    </div>
                    <p class="mb-0"><small>${followUp.notes || '-'}</small></p>
                </div>
            `;
        });
        html += '</div>';
    } else {
        html = '<div class="alert alert-info">暂无跟进记录</div>';
    }
    document.getElementById('followUpList').innerHTML = html;
}

// 添加客户
async function handleAddCustomer(e) {
    e.preventDefault();

    const formData = {
        company_name: document.getElementById('companyName').value,
        country: document.getElementById('country').value,
        contact_person: document.getElementById('contactPerson').value,
        email: document.getElementById('email').value,
        product_type: document.getElementById('productType').value,
        follow_up_date: document.getElementById('followUpDate').value,
        quote_status: document.getElementById('quoteStatus').value,
        notes: document.getElementById('notes').value
    };

    try {
        const response = await fetch(`${API_BASE}/customers`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            alert('客户添加成功！');
            document.getElementById('addCustomerForm').reset();
            loadCustomers();
            loadStatistics();
        } else {
            const error = await response.json();
            alert(`添加失败: ${error.error}`);
        }
    } catch (error) {
        console.error('添加客户失败:', error);
        alert('添加客户失败');
    }
}

// 编辑客户
async function handleEditCustomer(e) {
    e.preventDefault();

    const formData = {
        quote_status: document.getElementById('editQuoteStatus').value,
        follow_up_date: document.getElementById('editFollowUpDate').value,
        notes: document.getElementById('editNotes').value
    };

    try {
        const response = await fetch(`${API_BASE}/customers/${currentCustomerId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            alert('客户信息更新成功！');
            loadCustomers();
            loadStatistics();
            bootstrap.Modal.getInstance(document.getElementById('customerDetailModal')).hide();
        } else {
            const error = await response.json();
            alert(`更新失败: ${error.error}`);
        }
    } catch (error) {
        console.error('更新客户失败:', error);
        alert('更新客户失败');
    }
}

// 添加成交记录
async function handleAddTransaction(e) {
    e.preventDefault();

    const formData = {
        amount: parseFloat(document.getElementById('transactionAmount').value),
        transaction_date: document.getElementById('transactionDate').value,
        notes: document.getElementById('transactionNotes').value
    };

    try {
        const response = await fetch(`${API_BASE}/customers/${currentCustomerId}/transactions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            alert('成交记录添加成功！');
            document.getElementById('addTransactionForm').reset();
            viewCustomer(currentCustomerId);
            loadCustomers();
            loadStatistics();
        } else {
            const error = await response.json();
            alert(`添加失败: ${error.error}`);
        }
    } catch (error) {
        console.error('添加成交记录失败:', error);
        alert('添加成交记录失败');
    }
}

// 添加跟进记录
async function handleAddFollowUp(e) {
    e.preventDefault();

    const formData = {
        follow_up_date: document.getElementById('followUpDate').value,
        notes: document.getElementById('followUpNotes').value
    };

    try {
        const response = await fetch(`${API_BASE}/customers/${currentCustomerId}/follow-ups`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            alert('跟进记录添加成功！');
            document.getElementById('addFollowUpForm').reset();
            viewCustomer(currentCustomerId);
            loadCustomers();
        } else {
            const error = await response.json();
            alert(`添加失败: ${error.error}`);
        }
    } catch (error) {
        console.error('添加跟进记录失败:', error);
        alert('添加跟进记录失败');
    }
}

// 删除客户
async function handleDeleteCustomer() {
    if (!confirm('确定要删除该客户吗？此操作不可撤销。')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/customers/${currentCustomerId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            alert('客户删除成功！');
            loadCustomers();
            loadStatistics();
            bootstrap.Modal.getInstance(document.getElementById('customerDetailModal')).hide();
        } else {
            const error = await response.json();
            alert(`删除失败: ${error.error}`);
        }
    } catch (error) {
        console.error('删除客户失败:', error);
        alert('删除客户失败');
    }
}

// 筛选客户
async function filterCustomers() {
    const country = document.getElementById('filterCountry').value.trim();
    const status = document.getElementById('filterStatus').value;
    const productType = document.getElementById('filterProductType').value.trim();

    let url = `${API_BASE}/customers?`;
    const params = [];
    
    if (country) params.push(`country=${encodeURIComponent(country)}`);
    if (status) params.push(`quote_status=${encodeURIComponent(status)}`);
    if (productType) params.push(`product_type=${encodeURIComponent(productType)}`);
    
    url += params.join('&');

    try {
        const response = await fetch(url);
        const customers = await response.json();

        if (customers.length === 0) {
            document.getElementById('noDataMessage').style.display = 'block';
            document.getElementById('customersTable').style.display = 'none';
            return;
        }

        document.getElementById('noDataMessage').style.display = 'none';
        document.getElementById('customersTable').style.display = 'table';

        const tbody = document.getElementById('customersBody');
        tbody.innerHTML = '';

        customers.forEach(customer => {
            const row = createCustomerRow(customer);
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('筛选客户失败:', error);
    }
}

// 重置筛选
function resetFilters() {
    document.getElementById('filterCountry').value = '';
    document.getElementById('filterStatus').value = '';
    document.getElementById('filterProductType').value = '';
    loadCustomers();
}

// 导出数据
async function exportData() {
    try {
        const response = await fetch(`${API_BASE}/export`);
        const blob = await response.blob();
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `crm_customers_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('导出数据失败:', error);
        alert('导出数据失败');
    }
}

// 格式化数字
function formatNumber(num) {
    if (num === null || num === undefined) return '0';
    return Number(num).toLocaleString('zh-CN', { 
        maximumFractionDigits: 2, 
        minimumFractionDigits: 0 
    });
}
