from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from app import db
from app.models import Category, Transaction, Budget, User
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta, date
from sqlalchemy import func
from functools import wraps
from flask import abort

bp = Blueprint('main', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            error = 'Invalid username or password'
        elif not user.is_approved:
            error = 'Account pending approval. Please contact the administrator.'
        else:
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            return redirect(url_for('main.index'))
            
    return render_template('login.html', error=error)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            error = 'Username already exists'
        else:
            # Check if this is the first user
            user_count = User.query.count()
            is_first_user = (user_count == 0)
            
            user = User(username=username, is_admin=is_first_user, is_approved=is_first_user)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Create default categories for new user
            default_cats = [
                Category(name='Food', color='#FF6384', icon='🍔', user=user),
                Category(name='Transport', color='#36A2EB', icon='🚗', user=user),
                Category(name='Shopping', color='#FFCE56', icon='🛍️', user=user),
                Category(name='Bills', color='#4BC0C0', icon='📄', user=user),
                Category(name='Entertainment', color='#9966FF', icon='🎬', user=user),
                Category(name='Other', color='#C9CBCF', icon='📦', user=user)
            ]
            db.session.add_all(default_cats)
            db.session.commit()
            
            if is_first_user:
                login_user(user)
                return redirect(url_for('main.index'))
            else:
                flash('Registration successful. Please wait for admin approval.', 'info')
                return redirect(url_for('main.login'))
            
    return render_template('register.html', error=error)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.login'))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    return render_template('admin_dashboard.html', users=users)

@bp.route('/admin/approve/<int:user_id>')
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'User {user.username} approved.', 'success')
    return redirect(url_for('main.admin_dashboard'))

@bp.route('/admin/revoke/<int:user_id>')
@login_required
@admin_required
def revoke_user(user_id):
    if user_id == current_user.id:
        flash('Cannot revoke your own admin rights/approval.', 'error')
        return redirect(url_for('main.admin_dashboard'))
        
    user = User.query.get_or_404(user_id)
    user.is_approved = False
    db.session.commit()
    flash(f'User {user.username} revoked.', 'warning')
    return redirect(url_for('main.admin_dashboard'))

@bp.route('/admin/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('Cannot delete yourself.', 'error')
        return redirect(url_for('main.admin_dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Delete related data first
    Category.query.filter_by(user_id=user.id).delete()
    Transaction.query.filter_by(user_id=user.id).delete()
    Budget.query.filter_by(user_id=user.id).delete() # If budget has user_id, or join?
    # Budget doesn't have user_id directly, it links to Category.
    # But since we deleted Categories, Budgets might violate foreign key if not cascade?
    # Budget links to Category. If we delete Category, what happens to Budget?
    # Let's check model. Models usually cascade or we delete manual.
    # Category model: categories = db.relationship('Category', backref='user', lazy=True)
    # Budget model: category_id. 
    # Let's clean up properly.
    # Find all categories for user
    cats = Category.query.filter_by(user_id=user.id).all()
    for c in cats:
        Budget.query.filter_by(category_id=c.id).delete()
        
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} deleted.', 'success')
    return redirect(url_for('main.admin_dashboard'))

@bp.route('/admin/toggle_admin/<int:user_id>')
@login_required
@admin_required
def toggle_admin(user_id):
    if user_id == current_user.id:
        flash('Cannot change your own admin status.', 'error')
        return redirect(url_for('main.admin_dashboard'))
        
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    status = "promoted to Admin" if user.is_admin else "demoted to User"
    flash(f'User {user.username} {status}.', 'success')
    return redirect(url_for('main.admin_dashboard'))

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_user.check_password(current_password):
            flash('Invalid current password', 'error')
        elif new_password != confirm_password:
            flash('New passwords do not match', 'error')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password updated successfully', 'success')
            return redirect(url_for('main.index'))
    
    return render_template('change_password.html')

@bp.route('/')
@login_required

def index():
    # Helper to get period from query params or default to today
    today = date.today()
    try:
        selected_month = int(request.args.get('month', today.month))
        selected_year = int(request.args.get('year', today.year))
    except ValueError:
        selected_month = today.month
        selected_year = today.year
        
    # Budget Progress Logic for SELECTED PERIOD
    categories = Category.query.filter_by(user_id=current_user.id).all()
    budget_data = []
    
    for cat in categories:
        # Get budget for this category for selected month
        budget = Budget.query.filter_by(
            category_id=cat.id, 
            month=selected_month, 
            year=selected_year
        ).first()
        
        limit = budget.amount if budget else 0
        
        # Calculate spent for this category this month
        spent = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.category_id == cat.id,
            Transaction.type == 'expense',
            Transaction.user_id == current_user.id,
            func.extract('month', Transaction.date) == selected_month,
            func.extract('year', Transaction.date) == selected_year
        ).scalar() or 0
        
        available = limit - spent
        
        budget_data.append({
            'name': cat.name,
            'color': cat.color,
            'icon': cat.icon,
            'limit': limit,
            'spent': spent,
            'available': available,
            'percent': (spent / limit * 100) if limit > 0 else 0
        })

    # Recent transactions should arguably filtered or just last 5 global? 
    # Usually "Recent" means global recent. Let's keep it global recent for now or filter?
    # User might want to see transactions for that month. Let's show recent for that month if filtered, else global?
    # Simple approach: "Recent Activity" is usually timeline. Let's keep it global for now to avoid confusion.
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).limit(5).all()
    
    # Calculate Monthly Overview (Total Limit vs Total Spent for selected period)
    total_monthly_limit = sum(item['limit'] for item in budget_data)
    total_monthly_spent = sum(item['spent'] for item in budget_data)
    monthly_available = total_monthly_limit - total_monthly_spent
    
    return render_template(
        'index.html', 
        transactions=recent_transactions, 
        budget_data=budget_data, 
        user=current_user,
        selected_month=selected_month,
        selected_year=selected_year,
        today=today,
        date=date,
        monthly_available=monthly_available,
        total_monthly_limit=total_monthly_limit
    )

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        type = request.form.get('type')
        category_id = request.form.get('category')
        
        transaction = Transaction(
            amount=amount,
            description=description,
            type=type,
            category_id=category_id if category_id else None,
            user_id=current_user.id
        )
        db.session.add(transaction)
        db.session.commit()
        return redirect(url_for('main.index'))
        
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('add_expense.html', categories=categories)

@bp.route('/history')
@login_required
def history():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    return render_template('history.html', transactions=transactions)

@bp.route('/api/stats/<period>')
@login_required
def stats(period):
    data = db.session.query(
        Category.name, 
        Category.color, 
        func.sum(Transaction.amount)
    ).join(Transaction).filter(
        Transaction.type == 'expense',
        Transaction.user_id == current_user.id
    ).group_by(Category.id).all()
    
    labels = [d[0] for d in data]
    colors = [d[1] for d in data]
    values = [d[2] for d in data]
    
    return jsonify({
        'labels': labels,
        'colors': colors,
        'data': values
    })

@bp.route('/budgets/copy', methods=['POST'])
@login_required
def copy_budgets():
    # Helper to calculate previous month from today
    today = date.today()
    
    # Get target month/year from form data
    try:
        target_month = int(request.form.get('month', today.month))
        target_year = int(request.form.get('year', today.year))
    except ValueError:
        target_month = today.month
        target_year = today.year

    # Calculate previous month relative to TARGET month
    prev_month = target_month - 1
    prev_year = target_year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
        
    # Get previous budgets
    prev_budgets = Budget.query.filter_by(
        month=prev_month,
        year=prev_year
    ).join(Category).filter(Category.user_id == current_user.id).all()
    
    if not prev_budgets:
        flash('No budgets found in previous month to copy.')
        return redirect(url_for('main.manage_budgets', month=target_month, year=target_year))
        
    # Apply to current (target) month
    for pb in prev_budgets:
        # Check if budget already exists for target month
        cb = Budget.query.filter_by(
            category_id=pb.category_id,
            month=target_month,
            year=target_year
        ).first()
        
        if not cb:
            new_budget = Budget(
                category_id=pb.category_id,
                amount=pb.amount,
                month=target_month,
                year=target_year
            )
            db.session.add(new_budget)
        else:
            # Overwrite logic
            cb.amount = pb.amount
            
    db.session.commit()
    return redirect(url_for('main.manage_budgets', month=target_month, year=target_year))

@bp.route('/budgets', methods=['GET', 'POST'])
@login_required
def manage_budgets():
    today = date.today()
    
    # Get target month/year from query params or form data (default to current)
    try:
        if request.method == 'POST':
            selected_month = int(request.form.get('month', today.month))
            selected_year = int(request.form.get('year', today.year))
        else:
            selected_month = int(request.args.get('month', today.month))
            selected_year = int(request.args.get('year', today.year))
    except ValueError:
        selected_month = today.month
        selected_year = today.year

    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('budget_'):
                cat_id = int(key.split('_')[1])
                # Ensure category belongs to user
                cat = Category.query.get(cat_id)
                if not cat or cat.user_id != current_user.id:
                    continue
                    
                amount = float(value) if value else 0.0
                
                budget = Budget.query.filter_by(
                    category_id=cat_id,
                    month=selected_month,
                    year=selected_year
                ).first()
                
                if budget:
                    budget.amount = amount
                else:
                    budget = Budget(
                        category_id=cat_id,
                        amount=amount,
                        month=selected_month,
                        year=selected_year
                    )
                    db.session.add(budget)
        
        db.session.commit()
        # Redirect back to manage budgets for same period, or index? 
        return redirect(url_for('main.manage_budgets', month=selected_month, year=selected_year))

    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    # Logic to pre-fill from previous month if currently selected month is empty
    current_month_budgets = Budget.query.filter_by(
        month=selected_month, 
        year=selected_year
    ).join(Category).filter(Category.user_id==current_user.id).first()
    
    use_previous_month = False
    
    # Calculate previous month explicitly
    prev_month = selected_month - 1
    prev_year = selected_year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
        
    if not current_month_budgets:
        use_previous_month = True
        
    categories_with_budgets = []
    for cat in categories:
        # Try to find budget for current month first
        budget = Budget.query.filter_by(category_id=cat.id, month=selected_month, year=selected_year).first()
        
        # If no budget for current month and we decided to copy, try previous month
        if not budget and use_previous_month:
             budget = Budget.query.filter_by(category_id=cat.id, month=prev_month, year=prev_year).first()
        
        categories_with_budgets.append({
            'category': cat,
            'amount': budget.amount if budget else ''
        })
        
    return render_template('budgets.html', 
                           items=categories_with_budgets, 
                           today=today, 
                           date=date, 
                           selected_month=selected_month, 
                           selected_year=selected_year)

@bp.route('/categories')
@login_required
def categories():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('categories.html', categories=categories)

@bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        name = request.form.get('name')
        color = request.form.get('color')
        icon = request.form.get('icon')
        
        if name:
            cat = Category(name=name, color=color, icon=icon, user_id=current_user.id)
            db.session.add(cat)
            db.session.commit()
            return redirect(url_for('main.categories'))
            
    return render_template('category_form.html')

@bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    cat = Category.query.get_or_404(id)
    if cat.user_id != current_user.id:
        return redirect(url_for('main.categories'))
        
    if request.method == 'POST':
        cat.name = request.form.get('name')
        cat.color = request.form.get('color')
        cat.icon = request.form.get('icon')
        db.session.commit()
        return redirect(url_for('main.categories'))
        
    return render_template('category_form.html', category=cat)

@bp.route('/categories/<int:id>/delete')
@login_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    if cat.user_id != current_user.id:
        return redirect(url_for('main.categories'))
    
    # Manually delete related budgets
    Budget.query.filter_by(category_id=cat.id).delete()
    
    # Set transactions to null category (Uncategorized)
    Transaction.query.filter_by(category_id=cat.id).update({Transaction.category_id: None})
    
    db.session.delete(cat)
    db.session.commit()
    return redirect(url_for('main.categories'))



