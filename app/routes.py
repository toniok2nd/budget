from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app import db
from app.models import Category, Transaction
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Calculate total balance
    income = db.session.query(func.sum(Transaction.amount)).filter_by(type='income').scalar() or 0
    expenses = db.session.query(func.sum(Transaction.amount)).filter_by(type='expense').scalar() or 0
    balance = income - expenses
    
    recent_transactions = Transaction.query.order_by(Transaction.date.desc()).limit(5).all()
    
    return render_template('index.html', balance=balance, transactions=recent_transactions)

@bp.route('/add', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        type = request.form.get('type')
        category_id = request.form.get('category')
        
        # Simple validation
        if not category_id and type == 'expense':
            # Default to some category or handle error. For now, let's assume UI handles it or we allow nullable
            pass
            
        transaction = Transaction(
            amount=amount,
            description=description,
            type=type,
            category_id=category_id if category_id else None
        )
        db.session.add(transaction)
        db.session.commit()
        return redirect(url_for('main.index'))
        
    categories = Category.query.all()
    return render_template('add_expense.html', categories=categories)

@bp.route('/history')
def history():
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template('history.html', transactions=transactions)

@bp.route('/api/stats/<period>')
def stats(period):
    # For now, simple breakdown by category for expenses
    # In a real app, "period" would filter by month/year
    
    data = db.session.query(
        Category.name, 
        Category.color, 
        func.sum(Transaction.amount)
    ).join(Transaction).filter(Transaction.type == 'expense').group_by(Category.id).all()
    
    labels = [d[0] for d in data]
    colors = [d[1] for d in data]
    values = [d[2] for d in data]
    
    return jsonify({
        'labels': labels,
        'colors': colors,
        'data': values
    })

# Initialize some categories if empty (helper for first run)
@bp.before_app_request
def create_tables():
    db.create_all()
    if not Category.query.first():
        cats = [
            Category(name='Food', color='#FF6384'),
            Category(name='Transport', color='#36A2EB'),
            Category(name='Shopping', color='#FFCE56'),
            Category(name='Bills', color='#4BC0C0'),
            Category(name='Entertainment', color='#9966FF'),
            Category(name='Other', color='#C9CBCF')
        ]
        db.session.add_all(cats)
        db.session.commit()
