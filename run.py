from app import create_app, db
from app.models import Category, Transaction
from config import Config, DevelopmentConfig, ProductionConfig
import os

config_class = DevelopmentConfig if os.environ.get('FLASK_DEBUG') == '1' else ProductionConfig
app = create_app(config_class)

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Category': Category, 'Transaction': Transaction}

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
