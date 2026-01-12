
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from datetime import datetime
import re
app = Flask(__name__)
app.secret_key = 'your_secret_key_here_12345'
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'finance_tracker'
}
def get_db_connection():
    return mysql.connector.connect(**db_config)
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            category VARCHAR(50) NOT NULL,
            description TEXT,
            expense_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            source VARCHAR(100) NOT NULL,
            frequency VARCHAR(20) NOT NULL,
            income_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budget (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            category VARCHAR(50) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            month VARCHAR(7) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE KEY unique_user_category_month (user_id, category, month)
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            flash('Invalid email format!', 'error')
            return redirect(url_for('register'))
        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return redirect(url_for('register'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
        if cursor.fetchone():
            flash('Email already registered!', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        cursor.execute('INSERT INTO users (name, email, password) VALUES (%s, %s, %s)',
                      (name, email, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password') 
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        return redirect(url_for('dashboard'))
    flash('Invalid email or password!', 'error')
    return redirect(url_for('index'))
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT SUM(amount) as total FROM income WHERE user_id = %s', (user_id,))
    total_income = cursor.fetchone()['total'] or 0
    cursor.execute('SELECT SUM(amount) as total FROM expenses WHERE user_id = %s', (user_id,))
    total_expenses = cursor.fetchone()['total'] or 0
    current_month = datetime.now().strftime('%Y-%m')
    cursor.execute('''
        SELECT b.category, b.amount as budget_amount,
               COALESCE(SUM(e.amount), 0) as spent_amount
        FROM budget b
        LEFT JOIN expenses e ON b.category = e.category 
            AND e.user_id = b.user_id 
            AND DATE_FORMAT(e.expense_date, '%Y-%m') = b.month
        WHERE b.user_id = %s AND b.month = %s
        GROUP BY b.id, b.category, b.amount
    ''', (user_id, current_month))
    budget_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', 
                         total_income=total_income,
                         total_expenses=total_expenses,
                         balance=total_income - total_expenses,
                         budget_data=budget_data)

@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        amount = request.form.get('amount')
        category = request.form.get('category')
        description = request.form.get('description')
        expense_date = request.form.get('expense_date')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO expenses (user_id, amount, category, description, expense_date)
            VALUES (%s, %s, %s, %s, %s)
        ''', (user_id, amount, category, description, expense_date))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses'))
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT * FROM expenses WHERE user_id = %s ORDER BY expense_date DESC
    ''', (user_id,))
    expenses_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('expenses.html', expenses=expenses_list)
@app.route('/income', methods=['GET', 'POST'])
def income():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        amount = request.form.get('amount')
        source = request.form.get('source')
        frequency = request.form.get('frequency')
        income_date = request.form.get('income_date')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO income (user_id, amount, source, frequency, income_date)
            VALUES (%s, %s, %s, %s, %s)
        ''', (user_id, amount, source, frequency, income_date))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Income added successfully!', 'success')
        return redirect(url_for('income'))
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT * FROM income WHERE user_id = %s ORDER BY income_date DESC
    ''', (user_id,))
    income_list = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('income.html', incomes=income_list)

@app.route('/budget', methods=['GET', 'POST'])
def budget():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        category = request.form.get('category')
        amount = request.form.get('amount')
        month = request.form.get('month')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO budget (user_id, category, amount, month)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE amount = %s
        ''', (user_id, category, amount, month, amount))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Budget set successfully!', 'success')
        return redirect(url_for('budget'))
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT * FROM budget WHERE user_id = %s ORDER BY month DESC, category
    ''', (user_id,))
    budget_list = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('budget.html', budgets=budget_list)

@app.route('/transactions')
def transactions():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = '''
        SELECT 'expense' as type, id, amount, category, description as details, expense_date as date
        FROM expenses WHERE user_id = %s
        UNION ALL
        SELECT 'income' as type, id, amount, 'Income' as category, source as details, income_date as date
        FROM income WHERE user_id = %s
        ORDER BY date DESC
    '''
    
    cursor.execute(query, (user_id, user_id))
    all_transactions = cursor.fetchall()
    cursor.close()
    conn.close()
    filtered = all_transactions
    if search:
        filtered = [t for t in filtered if search.lower() in str(t['details']).lower()]
    if category and category != 'all':
        filtered = [t for t in filtered if t['category'] == category]
    
    return render_template('transactions.html', transactions=filtered)

@app.route('/delete_expense/<int:expense_id>')
def delete_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = %s AND user_id = %s', 
                  (expense_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Expense deleted!', 'success')
    return redirect(url_for('expenses'))

@app.route('/delete_income/<int:income_id>')
def delete_income(income_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM income WHERE id = %s AND user_id = %s', 
                  (income_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Income deleted!', 'success')
    return redirect(url_for('income'))

@app.route('/admin/dashboard')
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT COUNT(*) as count FROM users')
    user_count = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM expenses')
    expense_count = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM income')
    income_count = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM budget')
    budget_count = cursor.fetchone()['count']
    cursor.close()
    conn.close()
    return render_template('admin_dashboard.html', 
                         user_count=user_count,
                         expense_count=expense_count,
                         income_count=income_count,
                         budget_count=budget_count)

@app.route('/admin/users')
def admin_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
    all_users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_users.html', users=all_users)
@app.route('/admin/all_expenses')
def admin_expenses():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT e.*, u.name as user_name, u.email 
        FROM expenses e 
        JOIN users u ON e.user_id = u.id 
        ORDER BY e.expense_date DESC
    ''')
    all_expenses = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_expenses.html', expenses=all_expenses)
if __name__ == '__main__':
    init_db()

    app.run(debug=True)
