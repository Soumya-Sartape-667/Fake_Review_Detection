import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user') # 'user' or 'admin'
    status = db.Column(db.String(20), default='active')
    trust_score = db.Column(db.Float, default=100.0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    reviews = db.relationship('Review', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'trust_score': round(self.trust_score, 1),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Seller(db.Model):
    __tablename__ = 'sellers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(120), nullable=False)
    total_reviews = db.Column(db.Integer, default=0)
    fake_count = db.Column(db.Integer, default=0)
    suspicious_count = db.Column(db.Integer, default=0)
    risk_level = db.Column(db.String(20), default='Low Risk') # 'Low Risk', 'Medium Risk', 'High Risk'
    rating = db.Column(db.Float, default=4.5)
    status = db.Column(db.String(20), default='active')
    
    reviews = db.relationship('Review', backref='seller', lazy=True)

    def to_dict(self):
        fake_ratio = (self.fake_count / self.total_reviews * 100) if self.total_reviews > 0 else 0
        return {
            'id': self.id,
            'name': self.name,
            'brand': self.brand,
            'total_reviews': self.total_reviews,
            'fake_count': self.fake_count,
            'suspicious_count': self.suspicious_count,
            'fake_ratio': round(fake_ratio, 1),
            'risk_level': self.risk_level,
            'rating': self.rating,
            'status': self.status
        }

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float, default=4.2)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'brand': self.brand,
            'price': self.price,
            'rating': self.rating
        }

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id'), nullable=True)
    product_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), default='General')
    review_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(20), default='analyzed')
    # OCR image fields
    image_filename = db.Column(db.String(255), nullable=True)   # stored filename
    source_type = db.Column(db.String(20), default='manual')    # 'manual' or 'ocr'
    
    prediction = db.relationship('Prediction', backref='review', uselist=False, lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        pred = self.prediction.to_dict() if self.prediction else None
        user_name = self.user.name if self.user else "Anonymous User"
        seller_name = self.seller.name if self.seller else "Direct Marketplace"
        return {
            'id': self.id,
            'user_name': user_name,
            'seller_name': seller_name,
            'product_name': self.product_name,
            'category': self.category,
            'review_text': self.review_text,
            'rating': self.rating,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None,
            'status': self.status,
            'source_type': self.source_type or 'manual',
            'image_filename': self.image_filename,
            'has_image': bool(self.image_filename),
            'prediction': pred
        }

class Prediction(db.Model):
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    classification = db.Column(db.String(30), nullable=False) # 'Fake', 'Genuine', 'Suspicious'
    confidence_score = db.Column(db.Float, nullable=False) # 0.0 to 100.0
    predicted_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    explanation = db.relationship('Explanation', backref='prediction', uselist=False, lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        exp = self.explanation.to_dict() if self.explanation else None
        return {
            'id': self.id,
            'review_id': self.review_id,
            'classification': self.classification,
            'confidence_score': round(self.confidence_score, 1),
            'predicted_at': self.predicted_at.strftime('%Y-%m-%d %H:%M:%S') if self.predicted_at else None,
            'explanation': exp
        }

class Explanation(db.Model):
    __tablename__ = 'explanations'
    
    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey('predictions.id'), nullable=False)
    contributing_words_json = db.Column(db.Text, nullable=False) # JSON string of word weights
    reason_summary = db.Column(db.Text, nullable=False)
    xai_method = db.Column(db.String(50), default='TF-IDF + Heuristic LIME Explainer')

    def to_dict(self):
        import json
        words = []
        try:
            words = json.loads(self.contributing_words_json)
        except Exception:
            words = []
        return {
            'id': self.id,
            'contributing_words': words,
            'reason_summary': self.reason_summary,
            'xai_method': self.xai_method
        }

class DataLog(db.Model):
    __tablename__ = 'data_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(100), nullable=False)
    target = db.Column(db.String(150), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    details = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'target': self.target,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None,
            'details': self.details
        }
