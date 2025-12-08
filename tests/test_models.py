from app.models import Category, Transaction, Budget, User
from app import db

def test_user_creation(app):
    user = User(username='testuser')
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    
    assert user.id is not None
    assert user.check_password('password')
    assert not user.check_password('wrong')

def test_category_creation(app):
    user = User(username='testuser_cat')
    db.session.add(user)
    db.session.commit()
    
    cat = Category(name='TestCat', color='#000000', user=user)
    db.session.add(cat)
    db.session.commit()
    
    assert cat.id is not None
    assert cat.name == 'TestCat'
    assert cat.user_id == user.id

def test_transaction_creation(app):
    user = User(username='testuser_trans')
    db.session.add(user)
    db.session.commit()

    cat = Category(name='TestCat', color='#000000', user=user)
    db.session.add(cat)
    db.session.commit()

    t = Transaction(amount=100.0, description='Test', type='expense', category_id=cat.id, user=user)
    db.session.add(t)
    db.session.commit()
    
    assert t.id is not None
    assert t.amount == 100.0
    assert t.user_id == user.id

def test_budget_creation(app):
    user = User(username='testuser_budget')
    db.session.add(user)
    db.session.commit()

    cat = Category(name='TestCat', color='#000000', user=user)
    db.session.add(cat)
    db.session.commit()
    
    b = Budget(amount=500.0, month=12, year=2025, category_id=cat.id)
    db.session.add(b)
    db.session.commit()
    
    assert b.id is not None
    assert b.amount == 500.0
    assert b.year == 2025
