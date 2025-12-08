from datetime import datetime
from app.models import User, Category, Transaction, Budget
from app import db

def login(client, username, password):
    return client.post('/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

def logout(client):
    return client.get('/logout', follow_redirects=True)

def register(client, username, password):
    return client.post('/register', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

def test_login_logout(client, app):
    # Register first
    register(client, 'testuser', 'password')
    response = logout(client)
    assert response.status_code == 200
    
    response = login(client, 'testuser', 'password')
    assert response.status_code == 200
    assert b'My Budget' in response.data
    
    logout(client)
    response = login(client, 'testuser', 'wrong')
    assert b'Invalid username or password' in response.data

def test_home_page_requires_login(client):
    response = client.get('/', follow_redirects=True)
    assert b'Login' in response.data

def test_add_transaction(client, app):
    register(client, 'testuser', 'password')
    login(client, 'testuser', 'password')
    
    # Needs category first (created separately or use defaults if implemented)
    # Register creates defaults now
    
    response = client.post('/add', data={
        'amount': '50',
        'description': 'Test Expense',
        'type': 'expense',
        'category': '1' # Assuming id 1 exists from defaults
    }, follow_redirects=True)
    
    assert response.status_code == 200

def test_stats_api(client):
    register(client, 'testuser', 'password')
    login(client, 'testuser', 'password')
    response = client.get('/api/stats/month')
    assert response.status_code == 200
    assert response.is_json

def test_delete_category_with_data(client, app):
    # Setup user and data
    register(client, 'user_del', 'pass')
    login(client, 'user_del', 'pass')
    
    with app.app_context():
        user = User.query.filter_by(username='user_del').first()
        cat = Category.query.filter_by(user_id=user.id).first() # Use default cat
        # Create transaction and budget
        t = Transaction(amount=10, description='t', type='expense', category_id=cat.id, user_id=user.id)
        b = Budget(amount=100, month=1, year=2025, category_id=cat.id)
        db.session.add(t)
        db.session.add(b)
        db.session.commit()
        cat_id = cat.id

    # Try delete
    response = client.get(f'/categories/{cat_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    
    with app.app_context():
        # Cat should be gone
        assert Category.query.get(cat_id) is None
        # Budget should be gone
        assert Budget.query.filter_by(category_id=cat_id).first() is None
        # Transaction should exist but have no category
        t_check = Transaction.query.filter_by(description='t').first()
        assert t_check is not None
        assert t_check.category_id is None

def test_dashboard_period_filtering(client, app):
    # Setup user and data for specific date
    username = 'user_period'
    register(client, username, 'pass')
    login(client, username, 'pass')
    
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        cat = Category.query.filter_by(user_id=user.id).first()
        
        # Add transaction for Jan 2025
        t1 = Transaction(amount=50, description='Jan', type='expense', category_id=cat.id, user_id=user.id)
        t1.date = datetime(2025, 1, 15)
        
        # Add transaction for Feb 2025
        t2 = Transaction(amount=100, description='Feb', type='expense', category_id=cat.id, user_id=user.id)
        t2.date = datetime(2025, 2, 15)
        
        # Add budget for Jan 2025
        b1 = Budget(amount=200, month=1, year=2025, category_id=cat.id)
        
        db.session.add_all([t1, t2, b1])
        db.session.commit()
        
    # Test Default (Today) - Assuming today is not 2025 or we just check specific query param functionality
    # Let's request Jan 2025 explicitly
    response = client.get('/?month=1&year=2025', follow_redirects=True)
    assert response.status_code == 200
    # Available should be 200 - 50 = 150
    # Search for "Available: $150.00" or check budget data if possible
    assert b"Available: $150.00" in response.data
    
    # Check Feb 2025
    response = client.get('/?month=2&year=2025', follow_redirects=True)
    assert response.status_code == 200
    # No budget set for Feb, so available should be shown? logic handles budget=None as limit=0.
    # Limit 0, Spent 100. Available -100.
    # Spent: $100.00
    assert b"Spent: $100.00" in response.data

