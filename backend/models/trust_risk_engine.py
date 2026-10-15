from models.db_models import db, User, Seller, Review, Prediction

def calculate_reviewer_trust_score(user_id):
    """Calculates and updates user trust score based on review activity history."""
    if not user_id:
        return 80.0
        
    user = User.query.get(user_id)
    if not user:
        return 80.0
        
    reviews = Review.query.filter_by(user_id=user_id).all()
    if not reviews:
        user.trust_score = 100.0
        db.session.commit()
        return 100.0
        
    total_reviews = len(reviews)
    fake_count = 0
    suspicious_count = 0
    
    for r in reviews:
        if r.prediction:
            if r.prediction.classification == 'Fake':
                fake_count += 1
            elif r.prediction.classification == 'Suspicious':
                suspicious_count += 1
                
    # Penalty calculation
    fake_ratio = fake_count / total_reviews
    suspicious_ratio = suspicious_count / total_reviews
    
    base_score = 100.0
    penalty = (fake_ratio * 70.0) + (suspicious_ratio * 30.0)
    
    # Review velocity penalty if > 10 reviews
    if total_reviews > 15 and fake_count > 3:
        penalty += 10.0
        
    trust_score = max(0.0, min(100.0, base_score - penalty))
    user.trust_score = trust_score
    db.session.commit()
    
    return round(trust_score, 1)

def analyze_seller_risk(seller_id):
    """Calculates seller risk profile and assigns risk classification level."""
    seller = Seller.query.get(seller_id)
    if not seller:
        return {
            'risk_level': 'Low Risk',
            'fake_ratio': 0.0,
            'status': 'active'
        }
        
    reviews = Review.query.filter_by(seller_id=seller_id).all()
    seller.total_reviews = len(reviews)
    
    fake_count = 0
    suspicious_count = 0
    
    for r in reviews:
        if r.prediction:
            if r.prediction.classification == 'Fake':
                fake_count += 1
            elif r.prediction.classification == 'Suspicious':
                suspicious_count += 1
                
    seller.fake_count = fake_count
    seller.suspicious_count = suspicious_count
    
    if seller.total_reviews > 0:
        fake_ratio = (fake_count / seller.total_reviews) * 100.0
    else:
        fake_ratio = 0.0
        
    if fake_ratio >= 35.0 or fake_count >= 5:
        seller.risk_level = 'High Risk'
    elif fake_ratio >= 15.0 or fake_count >= 2:
        seller.risk_level = 'Medium Risk'
    else:
        seller.risk_level = 'Low Risk'
        
    db.session.commit()
    
    return {
        'id': seller.id,
        'name': seller.name,
        'brand': seller.brand,
        'total_reviews': seller.total_reviews,
        'fake_count': seller.fake_count,
        'fake_ratio': round(fake_ratio, 1),
        'risk_level': seller.risk_level
    }
