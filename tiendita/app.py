from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask.cli import with_appcontext
import click
import os

# Extensions (initialized here for imports)
db = SQLAlchemy()
login_manager = LoginManager()

# Models
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(120), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    image = db.Column(db.String(200))
    thumb = db.Column(db.String(200))
    inventory = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', backref='products')

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None


def create_app(config_object=None):
    """Factory to create a Flask app."""
    app = Flask(__name__, static_folder='static')

    # Load configuration
    if config_object:
        app.config.from_object(config_object)
    else:
        # Attempt to load config.py from project root (optional)
        app.config.from_pyfile('config.py', silent=True)

    # Ensure default upload folder
    app.config.setdefault('UPLOAD_FOLDER', os.path.join(app.root_path, 'static', 'uploads'))

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    # Simple routes used by templates
    @app.route('/')
    def index():
        q = request.args.get('q', '')
        products = Product.query.limit(48).all()
        categories = Category.query.all()
        return render_template('index.html', products=products, categories=categories, q=q)

    @app.route('/product/<int:product_id>')
    def product_detail(product_id):
        product = Product.query.get_or_404(product_id)
        categories = Category.query.all()
        return render_template('product.html', product=product, categories=categories)

    @app.route('/uploads/<path:filename>')
    def uploads(filename):
        upload_folder = app.config.get('UPLOAD_FOLDER')
        return send_from_directory(upload_folder, filename)

    @app.route('/add_to_cart/<int:product_id>', methods=['POST'])
    def add_to_cart(product_id):
        # Demo implementation: flash a message and redirect back
        flash('Added to cart (demo).', 'success')
        return redirect(request.referrer or url_for('index'))

    @app.route('/cart')
    def cart():
        categories = Category.query.all()
        # If you have a cart template, it will be used. Otherwise redirect to home.
        template = 'cart.html' if os.path.exists(os.path.join(app.root_path, 'templates', 'cart.html')) else 'index.html'
        return render_template(template, categories=categories)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash('Logged in.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password (demo).', 'danger')
        categories = Category.query.all()
        return render_template('login.html', categories=categories)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            if not username or not password:
                flash('Please provide username and password.', 'warning')
            elif User.query.filter_by(username=username).first():
                flash('Username already exists.', 'warning')
            else:
                user = User(username=username, password_hash=generate_password_hash(password))
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash('Account created (demo).', 'success')
                return redirect(url_for('index'))
        categories = Category.query.all()
        # Reuse login.html for the simple register view
        return render_template('login.html', categories=categories)

    # CLI helpers
    @app.cli.command('init-db')
    @with_appcontext
    def init_db_command():
        """Initialize the database (create tables)."""
        db.create_all()
        click.echo('Initialized the database.')

    @app.cli.command('seed-db')
    @with_appcontext
    def seed_db_command():
        """Seed the database with a small demo dataset."""
        if Category.query.count() == 0:
            c = Category(name='General', slug='general')
            db.session.add(c)
            db.session.commit()
            p = Product(
                name='Sample product',
                price=9.99,
                image='',
                thumb='',
                inventory=10,
                description='This is a demo product.',
                category_id=c.id,
            )
            db.session.add(p)
            db.session.commit()
            click.echo('Seeded demo data.')
        else:
            click.echo('Database already seeded.')

    return app
