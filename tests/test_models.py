from app.models import Category, Transaction
from app import db

def test_category_creation(app):
    cat = Category(name='TestCat', color='#000000')
    db.session.add(cat)
    db.session.commit()
    
    assert cat.id is not None
    assert cat.name == 'TestCat'

def test_transaction_creation(app):
    cat = Category(name='TestCat', color='#000000')
    db.session.add(cat)
    db.session.commit()

    t = Transaction(amount=100.0, description='Test', type='expense', category_id=cat.id)
    db.session.add(t)
    db.session.commit()
    
    assert t.id is not None
    assert t.amount == 100.0
    assert t.category.name == 'TestCat'
