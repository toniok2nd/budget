from datetime import date
from app.models import Budget, User, Category, Transaction
from app import db
from datetime import date

def test_manage_budgets_page(client):
    # Needs login
    client.post('/register', data={'username': 'user', 'password': 'pw'}, follow_redirects=True)
    client.post('/login', data={'username': 'user', 'password': 'pw'}, follow_redirects=True)
    
    response = client.get('/budgets', follow_redirects=True)
    assert response.status_code == 200
    assert b'Manage Budgets' in response.data
    
    # Check for current month display (e.g., "January 2025")
    today = date.today()
    month_str = today.strftime('%B %Y')
    assert month_str.encode() in response.data

def test_budget_copy_logic(client, app):
    # Setup user and previous month budget
    client.post('/register', data={'username': 'user_copy', 'password': 'pass'}, follow_redirects=True)
    client.post('/login', data={'username': 'user_copy', 'password': 'pass'}, follow_redirects=True)
    
    with app.app_context():
        user = User.query.filter_by(username='user_copy').first()
        cat = Category.query.filter_by(user_id=user.id).first()
        
        # Set budget for previous month (e.g. today.month - 1)
        # Handle Jan case
        today = date.today()
        prev_month = today.month - 1
        prev_year = today.year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1
            
        b = Budget(amount=888, month=prev_month, year=prev_year, category_id=cat.id)
        db.session.add(b)
        db.session.commit()
        
    # Now visit manage_budgets (which defaults to current month)
    # Since current month has no budgets, it should pre-fill with 888
    response = client.get('/budgets', follow_redirects=True)
    assert response.status_code == 200
    # Look for the value 888 in the input field
    # <input ... value="888.0"> or similar
    assert b'888' in response.data

def test_explicit_copy_budget(client, app):
    # Setup user and previous month budget
    client.post('/register', data={'username': 'user_ex_copy', 'password': 'pass'}, follow_redirects=True)
    client.post('/login', data={'username': 'user_ex_copy', 'password': 'pass'}, follow_redirects=True)
    
    with app.app_context():
        user = User.query.filter_by(username='user_ex_copy').first()
        cat = Category.query.filter_by(user_id=user.id).first()
        
        today = date.today()
        prev_month = today.month - 1
        prev_year = today.year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1
            
        b = Budget(amount=999, month=prev_month, year=prev_year, category_id=cat.id)
        db.session.add(b)
        db.session.commit()
        
    # Trigger explicit copy
    response = client.post('/budgets/copy', follow_redirects=True)
    assert response.status_code == 200
    
    # Should now see 999
    assert b'999' in response.data

def test_set_budget(client, app):
    client.post('/register', data={'username': 'user', 'password': 'pw'}, follow_redirects=True)
    client.post('/login', data={'username': 'user', 'password': 'pw'}, follow_redirects=True)
    
    # Register creates default categories. Let's pick one.
    with app.app_context():
        user = User.query.filter_by(username='user').first()
        cat = Category.query.filter_by(user_id=user.id).first()
        cat_id = cat.id

    response = client.post('/budgets', data={
        f'budget_{cat_id}': '1000.00'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    with app.app_context():
        today = date.today()
        b = Budget.query.filter_by(category_id=cat_id, month=today.month, year=today.year).first()
        assert b is not None
        assert b.amount == 1000.00
