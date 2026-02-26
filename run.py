import os
from app import create_app, db
from app.cli import register_cli

app = create_app(os.environ.get('FLASK_ENV', 'development'))

# Register CLI commands
register_cli(app)

@app.shell_context_processor
def make_shell_context():
    return {'db': db}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
