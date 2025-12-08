from app import create_app, db
from app.models import Category, Transaction

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Category': Category, 'Transaction': Transaction}

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
