from datetime import date
from app.models import Budget, Category, User, db

def test_manage_budgets_selection(client, app):
    # Setup
    client.post('/register', data={'username': 'test_select', 'password': 'pw'}, follow_redirects=True)
    client.post('/login', data={'username': 'test_select', 'password': 'pw'}, follow_redirects=True)
    
    # 1. Test default load (Current Month)
    today = date.today()
    response = client.get('/budgets', follow_redirects=True)
    assert response.status_code == 200
    # Verify current month (or default) is selected
    # Look for 'selected' on the correct option interaction
    # e.g. <option value="12" selected>December</option>
    expected_month_val = f'value="{today.month}" selected'.encode()
    expected_year_val = f'value="{today.year}" selected'.encode()
    assert expected_month_val in response.data
    assert expected_year_val in response.data
    
    # 2. Test selecting a future month (e.g., January 2035)
    future_month = 1
    future_year = 2035
    response = client.get(f'/budgets?month={future_month}&year={future_year}', follow_redirects=True)
    assert response.status_code == 200
    
    expected_month_val = f'value="{future_month}" selected'.encode()
    expected_year_val = f'value="{future_year}" selected'.encode()
    assert expected_month_val in response.data
    assert expected_year_val in response.data
    
    # 3. Test saving a budget for that future month
    # Get a category id first
    with app.app_context():
        u = User.query.filter_by(username='test_select').first()
        cat = Category.query.filter_by(user_id=u.id).first()
        cat_id = cat.id

    response = client.post('/budgets', data={
        f'budget_{cat_id}': '500.00',
        'month': future_month,
        'year': future_year
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Should redirect and still have 2035 selected
    assert expected_month_val in response.data
    assert expected_year_val in response.data
    
    with app.app_context():
        # Verify db
        b = Budget.query.filter_by(category_id=cat_id, month=future_month, year=future_year).first()
        assert b is not None
        assert b.amount == 500.00

def test_copy_budget_target_logic(client, app):
    # Setup
    client.post('/register', data={'username': 'test_copy_target', 'password': 'pw'}, follow_redirects=True)
    client.post('/login', data={'username': 'test_copy_target', 'password': 'pw'}, follow_redirects=True)
    
    # Create a budget for Month 1, Year 2030
    with app.app_context():
        u = User.query.filter_by(username='test_copy_target').first()
        cat = Category.query.filter_by(user_id=u.id).first()
        cat_id = cat.id
        
        b = Budget(amount=300, month=1, year=2030, category_id=cat_id)
        db.session.add(b)
        db.session.commit()
    
    # Now, try to "Copy Previous" into Month 2, Year 2030
    # The previous month for 2/2030 is 1/2030, which has budget 300.
    
    response = client.post('/budgets/copy', data={
        'month': '2',
        'year': '2030'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Should redirect to Manage Budgets for Feb 2030
    # Check that selector preserved Month 2, Year 2030
    assert b'value="2" selected' in response.data
    assert b'value="2030" selected' in response.data

def test_manage_budgets_defaults_to_prev_month(client, app):
    # Test that opening a NEW month defaults to showing values from PREV month (logic in GET)
    # Setup
    client.post('/register', data={'username': 'test_default', 'password': 'pw'}, follow_redirects=True)
    client.post('/login', data={'username': 'test_default', 'password': 'pw'}, follow_redirects=True)
    
    with app.app_context():
        u = User.query.filter_by(username='test_default').first()
        cat = Category.query.filter_by(user_id=u.id).first()
        # Set Budget for Dec 2029
        b = Budget(amount=999, month=12, year=2029, category_id=cat.id)
        db.session.add(b)
        db.session.commit()
        
    # User GETs Jan 2030 (which is empty in DB)
    # Should pre-fill 999 from Dec 2029
    response = client.get('/budgets?month=1&year=2030', follow_redirects=True)
    
    # We inspect the input value in HTML, it should contain "999.0"
    assert b'value="999.0"' in response.data
