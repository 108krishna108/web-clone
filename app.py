from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Get current date and time
current_datetime = datetime.now()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    products = Product.query.all()
    return render_template('home.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            # flash('Login successful!', 'success')
            return redirect(url_for('home'))

        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin='is_admin' in request.form


        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'warning')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password, is_admin=is_admin)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    products = Product.query.all()
    return render_template('admin.html', products=products)

# Route to display and edit products
@app.route('/edit_product', methods=['GET'])
def edit_product():
    # Fetch all products from the database
    products = Product.query.all()
    return render_template('edit_product.html', products=products)

# Route to handle the save functionality when editing a product
@app.route('/update_product/<int:product_id>', methods=['POST'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Get the updated values from the form
    product.name = request.form['name']
    product.description = request.form['description']
    product.price = request.form['price']
    
    # Save the updated product to the database
    db.session.commit()
    
    return redirect(url_for('edit_product'))

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        # Get the data from the form
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']

        last_product = Product.query.order_by(Product.id.desc()).first().id if Product.query.first() else None
        last_product_id = last_product + 1

        date_added = current_datetime
        # Create a new Product object
        new_product = Product(id=last_product_id, name=name, description=description, price=price, date_added=date_added)

        # Add the new product to the database
        db.session.add(new_product)
        db.session.commit()

        # Redirect to a different page (e.g., products list or home page)
        return redirect(url_for('home'))  # Redirect to home or wherever you want

    # If GET request, render the form to add a product
    return render_template('edit_product.html')

@app.route('/shipping_details/<int:product_id>', methods=['GET', 'POST'])
def shipping_details(product_id):
    product = Product.query.get_or_404(product_id)  # Fetch the product by ID
    
    if request.method == 'POST':
        quantity = int(request.form['quantity'])  # Get quantity from the form
        address = request.form['address']  # Get the shipping address from the form
        
        total_price = product.price * quantity  # Calculate total price

        # Redirect to an order confirmation page or show a success message
        return redirect(url_for('order_confirmation', product_id=product.id, quantity=quantity, total_price=total_price, address=address))

    return render_template('shipping_page.html', product=product)

@app.route('/order_confirmation')
def order_confirmation():
    product_id = request.args.get('product_id')
    quantity = request.args.get('quantity')
    total_price = float(request.args.get('total_price'))  # Convert total_price to float
    address = request.args.get('address')

    # You can save this order to the database or send confirmation here

    return render_template('order.html', product_id=product_id, quantity=quantity, total_price=total_price, address=address)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure all tables are created
    app.run(debug=True)
