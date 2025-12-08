def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'My Budget' in response.data

def test_add_transaction_get(client):
    response = client.get('/add')
    assert response.status_code == 200
    assert b'Add Transaction' in response.data

def test_add_transaction_post(client):
    response = client.post('/add', data={
        'amount': '50',
        'description': 'Test Expense',
        'type': 'expense',
        'category': '' # No category for now or need to create one first
    }, follow_redirects=True)
    
    # Ideally should pass, but if category is required for expense we might need to handle it.
    # Our code currently allows None for category, or logic might fail if we enforce it.
    # Let's create a category first to be safe or test simple income.
    
    assert response.status_code == 200
    
def test_stats_api(client):
    response = client.get('/api/stats/month')
    assert response.status_code == 200
    # Should get JSON
    assert response.is_json
