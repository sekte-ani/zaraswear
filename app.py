from flask import Flask,redirect,url_for,render_template,request,jsonify,session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson import ObjectId
import re
import json
import os
from os.path import join, dirname
from werkzeug.utils import secure_filename 
from datetime import datetime
from collections import defaultdict
import random
import string

import os
from os.path import join, dirname
from dotenv import load_dotenv

load_dotenv()
client = MongoClient("mongodb+srv://zaraswear08:zaraswear2024@cluster0.4u1zfms.mongodb.net/dbzaraswear?retryWrites=true&w=majority")
db = client['dbzaraswear']
admin_collection = db['admin_']
import midtransclient

snap = midtransclient.Snap(
    is_production=False,  # tetap False karena kamu pakai Sandbox
    server_key=''  # ganti dengan server key dari akun Zaras.wear
)

# password = os.getenv('MONGO_PASSWORD')
# cxn_str = os.getenv('MONGODB_URI')
# client = MongoClient(cxn_str)
# dbname = os.getenv('DB_NAME')
# db = client[dbname]

app=Flask(__name__)
app.jinja_env.globals.update(enumerate=enumerate)
# app.secret_key = 'sparta'
app.secret_key = 'zaraswear2024'  # ganti dengan string random agar aman


UPLOAD_FOLDER = os.path.join('static', 'assets', 'img')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
produk = []

# Fungsi untuk mendapatkan keranjang belanja dari session
def get_cart():
    if 'email' in session:
        email = session['email']
        cart_data = session.get(email, '[]')
        try:
            cart = json.loads(cart_data)
        except json.JSONDecodeError:
            cart = []
    else:
        cart = []
    return cart

def save_cart(cart):
    if 'email' in session:
        email = session['email']
        # Simpan keranjang ke session berdasarkan email
        session['cart'] = cart

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_logged_in():
  return 'logged_in' in session and session['logged_in']

@app.context_processor
def utility_processor():
    def is_logged_in():
        return 'logged_in' in session and session['logged_in']
    return dict(is_logged_in=is_logged_in)

@app.route('/',methods=['GET','POST'])
def home():
  return render_template('index.html')

@app.route('/daftar',methods=['GET','POST'])
def daftar():
  if request.method == 'POST':
        nama = request.form['nama']
        noHp = request.form['noHp'] 
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        email_regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.match(email_regex, email):
            return jsonify({'result': 'failure', 'msg': 'Format email tidak valid'})
        if password != confirm_password:
            return jsonify({'result': 'failure', 'msg': 'Password belum sesuai'})
        hashed_password = generate_password_hash(password)
        if db.users.find_one({'email': email}):
            return jsonify({'result': 'failure', 'msg': 'Email sudah terdaftar'})
        
        registration_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.users.insert_one({
            'nama': nama,
            'noHp': noHp,
            'email': email,
            'password': hashed_password,
            'registration_date': registration_date,
        })
        return jsonify({'result': 'success'})
  return render_template('daftar.html')

@app.route('/beranda')
def beranda():
    if 'email' not in session:
        return redirect('/login')
    return render_template('beranda.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # ✅ sekarang sudah sesuai dengan form login.html
        email = request.form.get('email')
        password = request.form.get('password')

        user = db.users.find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['cart'] = []
            session['email'] = email
            return jsonify({'result': 'success', 'msg': 'success'})
        return jsonify({'result': 'failure', 'msg': 'Email atau password salah'})
    return render_template('login.html')

@app.route('/check_login_status', methods=['GET'])
def check_login_status():
    logged_in = session.get('logged_in', False)
    if logged_in:
        email = session.get('email', 'User')
        return jsonify({'logged_in': True, 'email': email})
    return jsonify({'logged_in': False})

@app.route('/profile',methods=['GET','POST'])
def profile():
  if 'logged_in' not in session or not session['logged_in']:
    return redirect(url_for('login'))
  email = session['email']
  user = db.users.find_one({'email': email})
  if not user:
    return jsonify({'result': 'failure', 'msg': 'Email tidak ditemukan'})
  return render_template('profile.html', user=user)

@app.route('/get_user_data', methods=['GET'])
def get_user_data():
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'result': 'failure', 'msg': 'User belum login'}), 401
    email = session['email']
    user = db.users.find_one({'email': email}, {'_id': 0, 'nama': 1, 'email': 1, 'noHp': 1,})
    if user:
        return jsonify(user), 200
    return jsonify({'result': 'failure', 'msg': 'User tidak ditemukan'}), 404

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'result': 'failure', 'msg': 'User belum login'}), 401
    data = request.json
    email = session['email']
    update_data = {
        'nama': data.get('nama'),
        'noHp': data.get('noHp'),
    }
    db.users.update_one({'email': email}, {'$set': update_data})
    return jsonify({'result': 'success'}), 200

@app.route('/logout', methods=['GET'])
def logout():
    # Clear the entire session
    session.clear()

    # Redirect to the home page or another safe page
    return redirect(url_for('home'))

@app.route('/tentangKami',methods=['GET','POST'])
def tentangKami():
  return render_template('tentangKami.html')

@app.route('/tambah_ke_keranjang',methods=['POST'])
def tambah_ke_keranjang():
    if not 'email' in session:
        return redirect(url_for('login'))
    print(session['email'])
    
    product_id = request.form.get('productId')
    product_name = request.form.get('name')
    product_price = request.form.get('price', type=float)
    quantity = request.form.get('quantity', type=int, default=1)
    
    print(f"Received product_id: {product_id}, quantity: {quantity}, price: {product_price}, name: {product_name}")
    
    if not product_id or quantity is None:
        return jsonify({'status': 'error', 'message': 'Product ID or quantity missing'}), 400
    try:
        product_id = str(product_id)
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid product ID'}), 400

    cart = session['cart']
    product_in_cart = next((item for item in cart if item['product_id'] == product_id), None)
    
    if product_in_cart:
        product_in_cart['quantity'] += quantity
    else:
        cart.append({'product_id': product_id, 'quantity': quantity, 'price': product_price, 'name': product_name})

    save_cart(cart)

    return jsonify({'status': 'success', 'message': 'Product added to cart successfully'})

@app.route('/keranjang', methods=['GET'])
def show_keranjang():
    if 'email' not in session:
        return redirect(url_for('login'))

    cart = session.get('cart', [])
    
    email = session['email']
    
    if not cart:
        print('Cart is empty or not retrieved correctly.')
    
    for item in cart:
        if 'price' not in item:
            item['price'] = 0

    total_price = sum(item['price'] * item['quantity'] for item in cart)
    # print("Total Price:", total_price)
    
    user = db.users.find_one({'email': email}, {'_id': 0, 'nama': 1, 'email': 1, 'noHp': 1})
    # print("User Data:", user)
    
    if not user:
        return "User data not found", 404
    
    return render_template('keranjang.html', user=user, keranjang=cart, total_price=total_price)

import midtransclient

snap = midtransclient.Snap(
    is_production=False,  # True kalau sudah Production
    server_key=''
)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        email = request.form['email']
        address = request.form['address']
        cart = session.get('cart', [])

        if not cart:
            return "Cart is empty or not retrieved correctly.", 400

        # ✅ hitung total_price dulu
        for item in cart:
            if 'price' not in item:
                item['price'] = 0
        total_price = sum(item['price'] * item['quantity'] for item in cart)

        order = {
            "email": email,
            "address": address,
            "cart": cart,
            "total_price": total_price,  # ✅ sudah ada
            "status": "pending",
            "created_at": datetime.now()
        }
        db.orders.insert_one(order)

        user = db.users.find_one({'email': email}, {'_id': 0, 'nama': 1, 'email': 1, 'noHp': 1})
        if not user:
            return "User not found.", 404

        param = {
    "transaction_details": {
        "order_id": ''.join(random.choices(string.ascii_letters, k=8)),
        "gross_amount": total_price,
    },
    "item_details": [
        {
            "id": item.get("product_id", ""),
            "price": int(item["price"]),
            "quantity": int(item["quantity"]),
            "name": item["name"]
        } for item in cart
    ],
    "customer_details": {
        "first_name": user['nama'],
        "last_name": "",
        "email": email,
        "phone": user['noHp'],
        "billing_address": {
            "first_name": user['nama'],
            "email": email,
            "phone": user['noHp'],
            "address": address
        },
        "shipping_address": {
            "first_name": user['nama'],
            "email": email,
            "phone": user['noHp'],
            "address": address
        }
    }
}

        try:
            transaction = snap.create_transaction(param)
            transaction_token = transaction['token']
            session['transaction_token'] = transaction_token
        except Exception as e:
            return f"Transaction creation failed: {str(e)}", 500

        return redirect(url_for('checkout'))

    elif request.method == 'GET':
        transaction_token = session.get('transaction_token')
        cart = session.get('cart', [])

        for item in cart:
            if 'price' not in item:
                item['price'] = 0
        total_price = sum(item['price'] * item['quantity'] for item in cart)

        if not transaction_token:
            return "Transaction token is missing.", 400

        return render_template(
            'checkout.html',
            transaction_token=transaction_token,
            keranjang=cart,
            total_price=total_price
        )

@app.route('/adminOrders')
def admin_orders():
    orders = list(db.orders.find({}, {'_id': 0}))
    return render_template('adminOrders.html', orders=orders)

@app.route('/hapusPesanan', methods=['POST'])
def hapus_pesanan():
    ids = request.form.getlist('selected_orders')  # Ambil id pesanan dari checkbox
    
    if ids:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        for order_id in ids:
            cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()

    return redirect(url_for('admin_orders'))


  
@app.route('/atasan',methods=['GET','POST'])
def atasan():
  atasan = list(db.atasan.find({}))  
  return render_template('atasan.html', atasan=atasan)

@app.route('/dress',methods=['GET','POST'])
def dress():
  dress = list(db.dress.find({}))  
  return render_template('dress.html', dress=dress)

@app.route('/hijab',methods=['GET','POST'])
def hijab():
  hijab = list(db.hijab.find({}))  
  return render_template('hijab.html', hijab=hijab)

@app.route('/outwear',methods=['GET','POST'])
def outwear():
  outwear = list(db.outwear.find({}))  
  return render_template('outwear.html', outwear=outwear)

@app.route('/dashboard',methods=['GET','POST'])
def dashboard():
  users = list(db.users.find({}, {'_id': 0, 'email': 1, 'nama': 1, 'registration_date': 1}))
    
  atasan = list(db.atasan.find({}))
  atasan_counts = defaultdict(int)
  for atasan in atasan:
      atasan_counts[atasan['name']] += 1
        
  dress = list(db.dress.find({}))
  dress_counts = defaultdict(int)
  for dress in dress:
      dress_counts[dress['name']] += 1

  hijab = list(db.hijab.find({}))
  hijab_counts = defaultdict(int)
  for hijab in hijab:
      hijab_counts[hijab['name']] += 1
        
  outwear = list(db.outwear.find({}))
  outwear_counts = defaultdict(int)
  for outwear in outwear:
      outwear_counts[outwear['name']] += 1
      return render_template('dashboard.html', users=users, outwear=outwear, outwear_counts=outwear_counts, hijab=hijab, hijab_counts=hijab_counts, dress=dress, dress_counts=dress_counts, atasan=atasan, 
                          atasan_counts=atasan_counts)

@app.route('/kelolaUser',methods=['GET','POST'])
def kelolaUser():
  users = list(db.users.find({}, {'_id':0, 'email':1, 'nama':1, 'noHp':1, 'registration_date':1,}))
  return render_template('kelolauser.html', users=users)

@app.route('/hapus_dari_keranjang/<product_id>', methods=['POST'])
def hapusProduk(product_id):
    if 'cart' not in session:
        return redirect(url_for('show_keranjang'))

    print("my sessions", session)
    print("Product ID to remove:", product_id)

    cart = session['cart']
    updated_cart = [item for item in cart if item['product_id'] != product_id]

    session['cart'] = updated_cart
    return redirect(url_for('show_keranjang'))

@app.route('/hapusUser', methods=['POST'])
def hapusUser():
    email = request.json.get('email')
    if email:
        result = db.users.delete_one({'email': email})
        if result.deleted_count == 1:
            return jsonify({'success': True, 'message': 'User berhasil terhapus'}), 200
        else:
            return jsonify({'success': False, 'message': 'Penghapusan user gagal'}), 404
    else:
        return jsonify({'success': False, 'message': 'Email parameter tidak ada'}), 400

@app.route('/upload/<filename>', methods=['GET'])
def upload_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/adminStatus',methods=['GET','POST'])
def adminStatus():
  return render_template('adminStatus.html')

@app.route('/adminAtasan',methods=['GET'])
def adminatasan():
  atasan = list(db.atasan.find({}))
  return render_template('adminAtasan.html', atasan=atasan)

@app.route('/tambah-atasan', methods=['POST'])
def tambah_atasan():
    if request.method == 'POST':
        try:
            name = request.form['productName']
            category = request.form['productCategory']
            quantity = int(request.form['productQuantity'])
            price = float(request.form['productPrice'])

            # Handling file upload
            if 'atasanImage' in request.files:
                file = request.files['atasanImage']
                if file.filename == '':
                    filename = None
                elif file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                else:
                    raise Exception('Invalid file type')
            else:
                filename = None

            # Add new accessory to the database
            new_accessory = {
                "name": name,
                "category": category,
                "quantity": quantity,
                "price": price,
                "image": filename
            }
            # Assuming db is your MongoDB client and accessories is your collection
            db.atasan.insert_one(new_accessory)

            # Optionally, refresh accessories list from database
            # global accessories  # Remove global variable usage if not needed
            # accessories = list(db.accessories.find({}))

            return jsonify({"result": "success"})
        
        except Exception as e:
            return jsonify({"result": "error", "message": str(e)}), 400  # Return error message and HTTP status 400 (Bad Request) for client-side debugging

@app.route('/edit-atasan/<atasan_id>', methods=['GET', 'POST'])
def edit_atasan(atasan_id):
    if request.method == 'GET':
        atasan = db.atasan.find_one({'_id': ObjectId(atasan_id)})
        if not atasan:
          return 'Product not found', 404
        return render_template('editAtasan.html', atasan=atasan)
    elif request.method == 'POST':
        try:
            product_name = request.form['productName']
            product_category = request.form['productCategory']
            product_quantity = int(request.form['productQuantity'])
            product_price = float(request.form['productPrice'])

            update_data = {
                'name': product_name,
                'category': product_category,
                'quantity': product_quantity,
                'price': product_price
            }

            if 'atasanImage' in request.files:
                file = request.files['atasanImage']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    update_data['image'] = filename
            result = db.atasan.update_one({'_id': ObjectId(atasan_id)}, {'$set': update_data})

            if result.modified_count == 1:
                return jsonify({'result': 'success', 'msg': 'Produk Atasan berhasil diupdate'})
            return jsonify({'result': 'failure', 'msg': 'Produk Atasan tidak ditemukan atau update tidak berhasil'})
        except Exception as e:
            return jsonify({'result': 'failure', 'msg': str(e)})
        
@app.route('/delete-atasan/<atasan_id>', methods=['DELETE'])
def delete_atasan(atasan_id):
    try:
        result = db.atasan.delete_one({'_id': ObjectId(atasan_id)})
        if result.deleted_count == 0:
            return jsonify({'result': 'failure', 'msg': 'Produk atasan tidak ditemukan'})
        return jsonify({'result': 'success', 'msg': 'Produk atasan berhasil terhapus'})
    except Exception as e:
        return jsonify({'result': 'failure', 'msg': str(e)})

@app.route('/adminDress',methods=['GET'])
def admindress():
  dress = list(db.dress.find({}))
  return render_template('adminDress.html', dress=dress)

@app.route('/tambah-dress', methods=['POST'])
def tambah_dress():
    if request.method == 'POST':
        try:
            name = request.form['productName']
            category = request.form['productCategory']
            quantity = int(request.form['productQuantity'])
            price = float(request.form['productPrice'])

            # Handling file upload
            if 'dressImage' in request.files:
                file = request.files['dressImage']
                if file.filename == '':
                    filename = None
                elif file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                else:
                    raise Exception('Invalid file type')
            else:
                filename = None

            # Add new accessory to the database
            new_accessory = {
                "name": name,
                "category": category,
                "quantity": quantity,
                "price": price,
                "image": filename
            }
            # Assuming db is your MongoDB client and accessories is your collection
            db.dress.insert_one(new_accessory)

            # Optionally, refresh accessories list from database
            # global accessories  # Remove global variable usage if not needed
            # accessories = list(db.accessories.find({}))

            return jsonify({"result": "success"})
        
        except Exception as e:
            return jsonify({"result": "error", "message": str(e)}), 400  # Return error message and HTTP status 400 (Bad Request) for client-side debugging

@app.route('/edit-dress/<dress_id>', methods=['GET', 'POST'])
def edit_dress(dress_id):
    if request.method == 'GET':
        dress = db.dress.find_one({'_id': ObjectId(dress_id)})
        if not dress:
          return 'Product not found', 404
        return render_template('editDress.html', dress=dress)
    elif request.method == 'POST':
        try:
            product_name = request.form['productName']
            product_category = request.form['productCategory']
            product_quantity = int(request.form['productQuantity'])
            product_price = float(request.form['productPrice'])

            update_data = {
                'name': product_name,
                'category': product_category,
                'quantity': product_quantity,
                'price': product_price
            }

            if 'dressImage' in request.files:
                file = request.files['dressImage']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    update_data['image'] = filename
            result = db.dress.update_one({'_id': ObjectId(dress_id)}, {'$set': update_data})

            if result.modified_count == 1:
                return jsonify({'result': 'success', 'msg': 'Produk Dress berhasil diupdate'})
            return jsonify({'result': 'failure', 'msg': 'Produk Dress tidak ditemukan atau update tidak berhasil'})
        except Exception as e:
            return jsonify({'result': 'failure', 'msg': str(e)})
        
@app.route('/delete-dress/<dress_id>', methods=['DELETE'])
def delete_dress(dress_id):
    try:
        result = db.dress.delete_one({'_id': ObjectId(dress_id)})
        if result.deleted_count == 0:
            return jsonify({'result': 'failure', 'msg': 'Produk dress tidak ditemukan'})
        return jsonify({'result': 'success', 'msg': 'Produk dress berhasil terhapus'})
    except Exception as e:
        return jsonify({'result': 'failure', 'msg': str(e)})
    
@app.route('/adminHijab',methods=['GET'])
def adminhijab():
  hijab = list(db.hijab.find({}))
  return render_template('adminHijab.html', hijab=hijab)

@app.route('/tambah-hijab', methods=['POST'])
def tambah_hijab():
    if request.method == 'POST':
        try:
            name = request.form['productName']
            category = request.form['productCategory']
            quantity = int(request.form['productQuantity'])
            price = float(request.form['productPrice'])

            # Handling file upload
            if 'hijabImage' in request.files:
                file = request.files['hijabImage']
                if file.filename == '':
                    filename = None
                elif file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                else:
                    raise Exception('Invalid file type')
            else:
                filename = None

            # Add new accessory to the database
            new_accessory = {
                "name": name,
                "category": category,
                "quantity": quantity,
                "price": price,
                "image": filename
            }
            # Assuming db is your MongoDB client and accessories is your collection
            db.hijab.insert_one(new_accessory)

            # Optionally, refresh accessories list from database
            # global accessories  # Remove global variable usage if not needed
            # accessories = list(db.accessories.find({}))

            return jsonify({"result": "success"})
        
        except Exception as e:
            return jsonify({"result": "error", "message": str(e)}), 400  # Return error message and HTTP status 400 (Bad Request) for client-side debugging

@app.route('/edit-hijab/<hijab_id>', methods=['GET', 'POST'])
def edit_hijab(hijab_id):
    if request.method == 'GET':
        hijab = db.hijab.find_one({'_id': ObjectId(hijab_id)})
        if not hijab:
          return 'Product not found', 404
        return render_template('editHijab.html', hijab=hijab)
    elif request.method == 'POST':
        try:
            product_name = request.form['productName']
            product_category = request.form['productCategory']
            product_quantity = int(request.form['productQuantity'])
            product_price = float(request.form['productPrice'])

            update_data = {
                'name': product_name,
                'category': product_category,
                'quantity': product_quantity,
                'price': product_price
            }

            if 'hijabImage' in request.files:
                file = request.files['hijabImage']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    update_data['image'] = filename
            result = db.hijab.update_one({'_id': ObjectId(hijab_id)}, {'$set': update_data})

            if result.modified_count == 1:
                return jsonify({'result': 'success', 'msg': 'Produk Hijab berhasil diupdate'})
            return jsonify({'result': 'failure', 'msg': 'Produk Hijab tidak ditemukan atau update tidak berhasil'})
        except Exception as e:
            return jsonify({'result': 'failure', 'msg': str(e)})
        
@app.route('/delete-hijab/<hijab_id>', methods=['DELETE'])
def delete_hijab(hijab_id):
    try:
        result = db.hijab.delete_one({'_id': ObjectId(hijab_id)})
        if result.deleted_count == 0:
            return jsonify({'result': 'failure', 'msg': 'Produk hijab tidak ditemukan'})
        return jsonify({'result': 'success', 'msg': 'Produk hijab berhasil terhapus'})
    except Exception as e:
        return jsonify({'result': 'failure', 'msg': str(e)})

@app.route('/adminOutwear',methods=['GET'])
def adminoutwear():
  outwear = list(db.outwear.find({}))
  return render_template('adminOutwear.html', outwear=outwear)

@app.route('/tambah-outwear', methods=['POST'])
def tambah_outwear():
    if request.method == 'POST':
        try:
            name = request.form['productName']
            category = request.form['productCategory']
            quantity = int(request.form['productQuantity'])
            price = float(request.form['productPrice'])

            # Handling file upload
            if 'outwearImage' in request.files:
                file = request.files['outwearImage']
                if file.filename == '':
                    filename = None
                elif file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                else:
                    raise Exception('Invalid file type')
            else:
                filename = None

            # Add new accessory to the database
            new_accessory = {
                "name": name,
                "category": category,
                "quantity": quantity,
                "price": price,
                "image": filename
            }
            # Assuming db is your MongoDB client and accessories is your collection
            db.outwear.insert_one(new_accessory)

            # Optionally, refresh accessories list from database
            # global accessories  # Remove global variable usage if not needed
            # accessories = list(db.accessories.find({}))

            return jsonify({"result": "success"})
        
        except Exception as e:
            return jsonify({"result": "error", "message": str(e)}), 400  # Return error message and HTTP status 400 (Bad Request) for client-side debugging

@app.route('/edit-outwear/<outwear_id>', methods=['GET', 'POST'])
def edit_outwear(outwear_id):
    if request.method == 'GET':
        outwear = db.outwear.find_one({'_id': ObjectId(outwear_id)})
        if not outwear:
          return 'Product not found', 404
        return render_template('editOutwear.html', outwear=outwear)
    elif request.method == 'POST':
        try:
            product_name = request.form['productName']
            product_category = request.form['productCategory']
            product_quantity = int(request.form['productQuantity'])
            product_price = float(request.form['productPrice'])

            update_data = {
                'name': product_name,
                'category': product_category,
                'quantity': product_quantity,
                'price': product_price
            }

            if 'outwearImage' in request.files:
                file = request.files['outwearImage']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    update_data['image'] = filename
            result = db.outwear.update_one({'_id': ObjectId(outwear_id)}, {'$set': update_data})

            if result.modified_count == 1:
                return jsonify({'result': 'success', 'msg': 'Produk Outwear berhasil diupdate'})
            return jsonify({'result': 'failure', 'msg': 'Produk Outwear tidak ditemukan atau update tidak berhasil'})
        except Exception as e:
            return jsonify({'result': 'failure', 'msg': str(e)})
        
@app.route('/delete-outwear/<outwear_id>', methods=['DELETE'])
def delete_outwear(outwear_id):
    try:
        result = db.outwear.delete_one({'_id': ObjectId(outwear_id)})
        if result.deleted_count == 0:
            return jsonify({'result': 'failure', 'msg': 'Produk outwear tidak ditemukan'})
        return jsonify({'result': 'success', 'msg': 'Produk outwear berhasil terhapus'})
    except Exception as e:
        return jsonify({'result': 'failure', 'msg': str(e)})
            
    except Exception as e:
            return jsonify({"result": "error", "message": str(e)}), 400  # Return error message and HTTP status 400 (Bad Request) for client-side debugging

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

