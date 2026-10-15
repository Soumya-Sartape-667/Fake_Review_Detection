import os
import json
import uuid
from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from models.db_models import db, User, Seller, Product, Review, Prediction, Explanation, DataLog
from models.ml_engine import predict_review_raw, train_model
from models.xai_engine import generate_xai_explanation
from models.trust_risk_engine import calculate_reviewer_trust_score, analyze_seller_risk
from models.model_evaluator import evaluate_all_models
from models.ocr_engine import extract_text_from_image

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'tif'}


app = Flask(__name__)
app.config['SECRET_KEY'] = 'fake_review_detection_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'database', 'fake_review_db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

# Upload folder for OCR images
UPLOAD_FOLDER = os.path.join(app.root_path, 'database', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

CORS(app, supports_credentials=True, origins="*")
db.init_app(app)

# Helper function for logging actions
def log_action(user_id, action, target, details=""):
    try:
        log = DataLog(user_id=user_id, action=action, target=target, details=details)
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Log Error: {e}")

# Database Initializer & Seed Data Loader
def init_db():
    os.makedirs(os.path.join(app.root_path, 'database'), exist_ok=True)
    with app.app_context():
        db.create_all()
        
        # Seed Admin User if missing
        admin = User.query.filter_by(email='admin@fakecheck.ai').first()
        if not admin:
            admin = User(name='System Administrator', email='admin@fakecheck.ai', role='admin', trust_score=100.0)
            admin.set_password('admin123')
            db.session.add(admin)
            
        # Seed Standard Demo User if missing
        demo_user = User.query.filter_by(email='user@fakecheck.ai').first()
        if not demo_user:
            demo_user = User(name='Alex Johnson', email='user@fakecheck.ai', role='user', trust_score=95.0)
            demo_user.set_password('user123')
            db.session.add(demo_user)
            
        # Seed Sellers if missing
        if Seller.query.count() == 0:
            sellers = [
                Seller(name='Apex Tech Store', brand='Apex', rating=4.8, total_reviews=42, fake_count=1, risk_level='Low Risk'),
                Seller(name='Gadget Express Direct', brand='GadgetX', rating=3.2, total_reviews=35, fake_count=12, risk_level='High Risk'),
                Seller(name='Nova Retailers', brand='Nova', rating=4.1, total_reviews=28, fake_count=4, risk_level='Medium Risk'),
                Seller(name='EcoLiving Supplies', brand='EcoGreen', rating=4.9, total_reviews=19, fake_count=0, risk_level='Low Risk')
            ]
            db.session.add_all(sellers)
            
        # Seed Products if missing
        if Product.query.count() == 0:
            products = [
                Product(name='Wireless Noise Cancelling Headphones', category='Electronics', brand='Apex', price=149.99, rating=4.7),
                Product(name='Ultra Slim Bluetooth Keyboard', category='Electronics', brand='GadgetX', price=29.99, rating=3.5),
                Product(name='Ergonomic Office Mesh Chair', category='Furniture', brand='Nova', price=189.50, rating=4.2),
                Product(name='Stainless Steel Water Flask 1L', category='Home & Kitchen', brand='EcoGreen', price=24.95, rating=4.9)
            ]
            db.session.add_all(products)
            
        db.session.commit()
        
        # Pre-seed a rich review dataset for immediate visualization
        if Review.query.count() == 0:
            demo_u = User.query.filter_by(email='user@fakecheck.ai').first()
            seller1 = Seller.query.filter_by(name='Gadget Express Direct').first()
            seller2 = Seller.query.filter_by(name='Apex Tech Store').first()
            seller3 = Seller.query.filter_by(name='Nova Retailers').first()
            seller4 = Seller.query.filter_by(name='EcoLiving Supplies').first()
            
            sample_data = [
                {
                    'text': "BEST KEYBOARD EVER BUY NOW AMAZING DISCOUNT 100% GENUINE GUARANTEED FIVE STARS!!!!!",
                    'rating': 5,
                    'product': 'Ultra Slim Bluetooth Keyboard',
                    'category': 'Electronics',
                    'seller': seller1
                },
                {
                    'text': "I bought these headphones last week. The active noise cancelling works well in office settings, though battery life is closer to 6 hours.",
                    'rating': 4,
                    'product': 'Wireless Noise Cancelling Headphones',
                    'category': 'Electronics',
                    'seller': seller2
                },
                {
                    'text': "Terrible product fake box broken packaging zero stars scam fraud refund immediately!!",
                    'rating': 1,
                    'product': 'Ultra Slim Bluetooth Keyboard',
                    'category': 'Electronics',
                    'seller': seller1
                },
                {
                    'text': "Super high quality stainless steel flask. Kept my tea warm for over 12 hours during hiking.",
                    'rating': 5,
                    'product': 'Stainless Steel Water Flask 1L',
                    'category': 'Home & Kitchen',
                    'seller': seller4
                },
                {
                    'text': "AMAZING LOVED IT WORKS PERFECTLY BEST PURCHASE OF MY LIFE HIGHLY RECOMMEND BUY NOW DISCOUNT ACTIVE!",
                    'rating': 5,
                    'product': 'Ergonomic Office Mesh Chair',
                    'category': 'Furniture',
                    'seller': seller3
                },
                {
                    'text': "The chair lumbar support is good, but the assembly manual had missing steps. Overall acceptable for home office.",
                    'rating': 3,
                    'product': 'Ergonomic Office Mesh Chair',
                    'category': 'Furniture',
                    'seller': seller3
                },
                {
                    'text': "Fast shipping and genuine product. The Bluetooth pairing was instant on my laptop.",
                    'rating': 5,
                    'product': 'Ultra Slim Bluetooth Keyboard',
                    'category': 'Electronics',
                    'seller': seller2
                },
                {
                    'text': "Total waste of money worst product ever scam fraud don't buy terrible quality seller fake!",
                    'rating': 1,
                    'product': 'Wireless Noise Cancelling Headphones',
                    'category': 'Electronics',
                    'seller': seller1
                },
                {
                    'text': "Decent design and fabric. The color is slightly darker than the product photos, but sizing fits well.",
                    'rating': 4,
                    'product': 'Cotton Casual Hoodie',
                    'category': 'Fashion',
                    'seller': seller3
                },
                {
                    'text': "Order immediately 100% genuine top seller best deal ever unbelievable quality link below!",
                    'rating': 5,
                    'product': 'Organic Face Serum',
                    'category': 'Beauty',
                    'seller': seller1
                }
            ]
            
            for item in sample_data:
                r = Review(
                    user_id=demo_u.id if demo_u else None,
                    seller_id=item['seller'].id if item['seller'] else None,
                    product_name=item['product'],
                    category=item['category'],
                    review_text=item['text'],
                    rating=item['rating']
                )
                db.session.add(r)
                db.session.flush()
                
                # Run prediction
                raw_pred = predict_review_raw(item['text'], item['rating'])
                xai_info = generate_xai_explanation(item['text'], item['rating'], raw_pred)
                
                pred = Prediction(
                    review_id=r.id,
                    classification=raw_pred['classification'],
                    confidence_score=raw_pred['confidence']
                )
                db.session.add(pred)
                db.session.flush()
                
                exp = Explanation(
                    prediction_id=pred.id,
                    contributing_words_json=json.dumps(xai_info['contributing_words']),
                    reason_summary=xai_info['reason_summary'],
                    xai_method=xai_info['xai_method']
                )
                db.session.add(exp)
                
            db.session.commit()
            print("Database populated with initial seed dataset!")


# --- ROUTES ---

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "name": "TrustLens.ai Explainable Review AI Backend REST API Server",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/me, /api/login, /api/register, /api/logout",
            "detection": "/api/submit-review, /api/reviews, /api/review/<id>",
            "sellers": "/api/sellers",
            "admin": "/api/admin/stats",
            "metrics": "/api/model-performance"
        }
    })

# 1. User Registration (Requirement 2.1 - Req 1)
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required.'}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'An account with this email already exists.'}), 400

    user = User(name=name, email=email, role='user', trust_score=100.0)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    session['user_id'] = user.id
    session['user_name'] = user.name
    session['user_role'] = user.role

    log_action(user.id, "REGISTER", f"User {user.email}", "New user registration")

    return jsonify({
        'message': 'Registration successful!',
        'user': user.to_dict()
    }), 201

# 2. User Login (Requirement 2.1 - Req 2)
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password credentials.'}), 401

    session['user_id'] = user.id
    session['user_name'] = user.name
    session['user_role'] = user.role

    log_action(user.id, "LOGIN", f"User {user.email}", "User logged into system")

    return jsonify({
        'message': 'Login successful!',
        'user': user.to_dict()
    })

# 3. User Logout (Requirement 2.1 - Req 12)
@app.route('/api/logout', methods=['POST'])
def logout():
    uid = session.get('user_id')
    if uid:
        log_action(uid, "LOGOUT", "User Session", "User logged out")
    session.clear()
    return jsonify({'message': 'Logged out successfully.'})

# 4. Get Current User Status
@app.route('/api/me', methods=['GET'])
def get_me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'logged_in': False, 'user': None})

    user = User.query.get(user_id)
    if not user:
        session.clear()
        return jsonify({'logged_in': False, 'user': None})

    return jsonify({
        'logged_in': True,
        'user': user.to_dict()
    })

# 5. Quick Instant Prediction API (Requirement 2.1 - Req 4, 5, 6)
@app.route('/api/predict', methods=['POST'])
def predict_quick():
    data = request.json or {}
    review_text = data.get('review_text', '').strip()
    rating = int(data.get('rating', 5))

    if not review_text:
        return jsonify({'error': 'Review text cannot be empty.'}), 400

    raw_pred = predict_review_raw(review_text, rating)
    xai_info = generate_xai_explanation(review_text, rating, raw_pred)

    return jsonify({
        'classification': raw_pred['classification'],
        'confidence_score': round(raw_pred['confidence'], 1),
        'fake_probability': round(raw_pred['fake_probability'] * 100, 1),
        'genuine_probability': round(raw_pred['genuine_probability'] * 100, 1),
        'explanation': xai_info
    })

# 6. Submit Review API (Requirement 2.1 - Req 3, 4, 5, 6, 7, 9, 10)
@app.route('/api/submit-review', methods=['POST'])
def submit_review():
    data = request.json or {}
    review_text = data.get('review_text', '').strip()
    rating = int(data.get('rating', 5))
    product_name = data.get('product_name', 'General Product').strip()
    category = data.get('category', 'Electronics').strip()
    seller_id = data.get('seller_id')

    if not review_text:
        return jsonify({'error': 'Review text is required.'}), 400

    user_id = session.get('user_id')
    
    # Create Review Record
    review = Review(
        user_id=user_id,
        seller_id=seller_id if seller_id else None,
        product_name=product_name,
        category=category,
        review_text=review_text,
        rating=rating
    )
    db.session.add(review)
    db.session.flush()

    # Perform Machine Learning Prediction
    raw_pred = predict_review_raw(review_text, rating)
    xai_info = generate_xai_explanation(review_text, rating, raw_pred)

    prediction = Prediction(
        review_id=review.id,
        classification=raw_pred['classification'],
        confidence_score=raw_pred['confidence']
    )
    db.session.add(prediction)
    db.session.flush()

    explanation = Explanation(
        prediction_id=prediction.id,
        contributing_words_json=json.dumps(xai_info['contributing_words']),
        reason_summary=xai_info['reason_summary'],
        xai_method=xai_info['xai_method']
    )
    db.session.add(explanation)
    db.session.commit()

    # Update Reviewer Trust Score & Seller Risk Profile
    trust_score = calculate_reviewer_trust_score(user_id) if user_id else 80.0
    seller_profile = analyze_seller_risk(seller_id) if seller_id else None

    log_action(user_id, "SUBMIT_REVIEW", f"Review #{review.id}", f"Classification: {raw_pred['classification']}")

    return jsonify({
        'message': 'Review successfully submitted and analyzed!',
        'review': review.to_dict(),
        'trust_score': trust_score,
        'seller_risk': seller_profile
    }), 201

# 7. Get Review History (Requirement 2.1 - Req 7)
@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    search = request.args.get('search', '').strip().lower()
    category = request.args.get('category', '').strip()
    classification = request.args.get('classification', '').strip()
    rating = request.args.get('rating', '').strip()

    query = db.session.query(Review).join(Prediction, Review.id == Prediction.review_id, isouter=True)

    if category and category != 'All':
        query = query.filter(Review.category == category)
    if rating and rating != 'All':
        try:
            query = query.filter(Review.rating == int(rating))
        except ValueError:
            pass
    if classification and classification != 'All':
        query = query.filter(Prediction.classification == classification)
    if search:
        query = query.filter(
            (Review.product_name.ilike(f'%{search}%')) |
            (Review.review_text.ilike(f'%{search}%'))
        )

    reviews = query.order_by(Review.timestamp.desc()).all()
    review_dicts = [r.to_dict() for r in reviews]

    total = len(review_dicts)
    fake_count = sum(1 for r in review_dicts if r.get('prediction') and r['prediction']['classification'] == 'Fake')
    genuine_count = sum(1 for r in review_dicts if r.get('prediction') and r['prediction']['classification'] == 'Genuine')
    suspicious_count = sum(1 for r in review_dicts if r.get('prediction') and r['prediction']['classification'] == 'Suspicious')

    return jsonify({
        'reviews': review_dicts,
        'stats': {
            'total': total,
            'fake_count': fake_count,
            'genuine_count': genuine_count,
            'suspicious_count': suspicious_count
        }
    })


# 7b. Get Single Review by ID (for XAI Drawer)
@app.route('/api/review/<int:review_id>', methods=['GET'])
def get_review_by_id(review_id):
    review = Review.query.get_or_404(review_id)
    return jsonify({'review': review.to_dict()})


# 8. Get Sellers List & Risk Levels (Requirement 2.1 - Req 10)
@app.route('/api/sellers', methods=['GET'])
def get_sellers():
    sellers = Seller.query.all()
    res = []
    for s in sellers:
        analyze_seller_risk(s.id)
        res.append(s.to_dict())
    return jsonify({'sellers': res})

# 9. Admin Dashboard Statistics API (Requirement 2.1 - Req 8)
@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    total_users = User.query.count()
    total_reviews = Review.query.count()
    
    fake_count = Prediction.query.filter_by(classification='Fake').count()
    genuine_count = Prediction.query.filter_by(classification='Genuine').count()
    suspicious_count = Prediction.query.filter_by(classification='Suspicious').count()

    fake_percentage = (fake_count / total_reviews * 100) if total_reviews > 0 else 0.0

    high_risk_sellers = Seller.query.filter_by(risk_level='High Risk').count()

    # Category Breakdown
    categories = db.session.query(Review.category, db.func.count(Review.id)).group_by(Review.category).all()
    cat_data = {cat: count for cat, count in categories}

    logs = DataLog.query.order_by(DataLog.timestamp.desc()).limit(15).all()

    return jsonify({
        'total_users': total_users,
        'total_reviews': total_reviews,
        'fake_count': fake_count,
        'genuine_count': genuine_count,
        'suspicious_count': suspicious_count,
        'fake_percentage': round(fake_percentage, 1),
        'high_risk_sellers': high_risk_sellers,
        'category_breakdown': cat_data,
        'recent_logs': [l.to_dict() for l in logs]
    })

# 10. Model Performance & Evaluation Benchmark API (Chapter 5 Requirements)
@app.route('/api/model-performance', methods=['GET'])
def get_model_performance():
    eval_results = evaluate_all_models()
    return jsonify(eval_results)

# OCR-A. Extract text from uploaded review image
@app.route('/api/ocr-extract', methods=['POST'])
def ocr_extract():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided. Please attach an image.'}), 400

    file = request.files['image']
    if not file or file.filename == '':
        return jsonify({'error': 'Empty file received.'}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({'error': f'Unsupported file type ".{ext}". Allowed: jpg, png, gif, bmp, webp.'}), 400

    image_bytes = file.read()
    result = extract_text_from_image(image_bytes)

    if not result['success']:
        return jsonify({'error': result['error']}), 422

    return jsonify({
        'text': result['text'],
        'word_count': result['word_count'],
        'message': f'Successfully extracted {result["word_count"]} words from image.'
    })


# OCR-B. Submit OCR review with image (multipart form)
@app.route('/api/submit-ocr-review', methods=['POST'])
def submit_ocr_review():
    review_text = request.form.get('review_text', '').strip()
    rating = int(request.form.get('rating', 5))
    product_name = request.form.get('product_name', 'OCR Scanned Product').strip()
    category = request.form.get('category', 'General').strip()
    seller_id = request.form.get('seller_id')

    if not review_text:
        return jsonify({'error': 'Review text is required.'}), 400

    user_id = session.get('user_id')

    # Save uploaded image
    image_filename = None
    if 'image' in request.files and request.files['image'].filename:
        file = request.files['image']
        ext = file.filename.rsplit('.', 1)[-1].lower()
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        file.seek(0)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], safe_name))
        image_filename = safe_name

    review = Review(
        user_id=user_id,
        seller_id=int(seller_id) if seller_id else None,
        product_name=product_name,
        category=category,
        review_text=review_text,
        rating=rating,
        source_type='ocr',
        image_filename=image_filename
    )
    db.session.add(review)
    db.session.flush()

    raw_pred = predict_review_raw(review_text, rating)
    xai_info = generate_xai_explanation(review_text, rating, raw_pred)

    prediction = Prediction(
        review_id=review.id,
        classification=raw_pred['classification'],
        confidence_score=raw_pred['confidence']
    )
    db.session.add(prediction)
    db.session.flush()

    explanation = Explanation(
        prediction_id=prediction.id,
        contributing_words_json=json.dumps(xai_info['contributing_words']),
        reason_summary=xai_info['reason_summary'],
        xai_method=xai_info['xai_method']
    )
    db.session.add(explanation)
    db.session.commit()

    trust_score = calculate_reviewer_trust_score(user_id) if user_id else 80.0
    seller_profile = analyze_seller_risk(int(seller_id)) if seller_id else None

    log_action(user_id, "SUBMIT_OCR_REVIEW", f"Review #{review.id}", f"OCR | Class: {raw_pred['classification']}")

    return jsonify({
        'message': 'OCR review submitted and analyzed!',
        'review': review.to_dict(),
        'trust_score': trust_score,
        'seller_risk': seller_profile
    }), 201


# OCR-C. Serve uploaded review images
@app.route('/api/review-image/<filename>', methods=['GET'])
def serve_review_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    # Initialize DB & Model
    with app.app_context():
        init_db()
        train_model()
    app.run(host='0.0.0.0', port=5000, debug=False)


