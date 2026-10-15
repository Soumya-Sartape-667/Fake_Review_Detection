import os
import re
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, 'fake_review_model.pkl')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'vectorizer.pkl')

STOPWORDS = set([
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren\'t', 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can\'t', 'cannot', 'could',
    'couldn\'t', 'did', 'didn\'t', 'do', 'does', 'doesn\'t', 'doing', 'don\'t', 'down', 'during', 'each', 'few', 'for',
    'from', 'further', 'had', 'hadn\'t', 'has', 'hasn\'t', 'have', 'haven\'t', 'having', 'he', 'he\'d', 'he\'ll', 'he\'s',
    'her', 'here', 'here\'s', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'how\'s', 'i', 'i\'d', 'i\'ll', 'i\'m',
    'i\'ve', 'if', 'in', 'into', 'is', 'isn\'t', 'it', 'it\'s', 'its', 'itself', 'let\'s', 'me', 'more', 'most', 'mustn\'t',
    'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours',
    'ourselves', 'out', 'over', 'own', 'same', 'shan\'t', 'she', 'she\'d', 'she\'ll', 'she\'s', 'should', 'shouldn\'t',
    'so', 'some', 'such', 'than', 'that', 'that\'s', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there',
    'there\'s', 'these', 'they', 'they\'d', 'they\'ll', 'they\'re', 'they\'ve', 'this', 'those', 'through', 'to', 'too',
    'under', 'until', 'up', 'very', 'was', 'wasn\'t', 'we', 'we\'d', 'we\'ll', 'we\'re', 'we\'ve', 'were', 'weren\'t',
    'what', 'what\'s', 'when', 'when\'s', 'where', 'where\'s', 'which', 'while', 'who', 'who\'s', 'whom', 'why', 'why\'s',
    'with', 'won\'t', 'would', 'wouldn\'t', 'you', 'you\'d', 'you\'ll', 'you\'re', 'you\'ve', 'your', 'yours', 'yourself',
    'yourselves'
])

def preprocess_text(text):
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Remove HTML tags & special characters
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    # Remove extra spaces & stopwords
    tokens = text.split()
    tokens = [t for t in tokens if len(t) > 1 and t not in STOPWORDS]
    return " ".join(tokens)

def generate_training_data():
    """Generates a realistic review dataset with genuine and fake review patterns."""
    fake_reviews = [
        "BEST PRODUCT EVER HIGHLY RECOMMENDED BUY NOW BUY NOW AMAZING SUPER FAST DISCOUNTS!",
        "Must buy product 100% genuine guaranteed amazing quality five stars best seller link below",
        "Total waste money worst product ever scam scam fraud don't buy terrible seller",
        "AMAZING AMAZING LOVED IT WORKS PERFECTLY BEST PURCHASE OF MY LIFE HIGHLY RECOMMEND!!",
        "Fake product delivered broken box scam seller zero stars refund immediately fraud",
        "Great product buy now discount code active best seller top rated unbelievable item",
        "Superior quality item unbelievable results buy today guaranteed satisfaction 10/10",
        "Horrible scam completely defective fake item seller refused refund stay away fraud!!",
        "Unbelievable offer best product on amazon buy now fast delivery love love love it",
        "Super super super quality item very cheap price order immediately best deals ever"
    ] * 20

    genuine_reviews = [
        "I bought this laptop two weeks ago. The battery lasts about 6 hours and the keyboard is comfortable.",
        "The sound quality is crisp, but the plastic casing feels slightly cheap. Good value for money.",
        "Received the item in 3 days. Packaging was undamaged. Fits well and does the job expected.",
        "Decent smart watch. The heart rate tracking is mostly accurate, though sleep tracking misses cat naps.",
        "The shoes fit as sized. Material is comfortable for daily walking, but stitching could be tighter.",
        "Camera resolution is clear in daylight. Low light photos have minor noise. Overall satisfied.",
        "It took a while to assemble the desk chair. Once built, it offers solid lumbar support for office work.",
        "The blender is a bit noisy when crushing ice, but smooths out fruits easily. Easy to clean.",
        "Works as expected for a budget phone. Display is bright and responsive. Micro-USB charging is slow.",
        "Good set of kitchen knives. Sharp out of the box, though the wooden block has a minor scratch."
    ] * 20

    data = []
    for r in fake_reviews:
        data.append({'text': r, 'label': 1}) # 1 = Fake
    for r in genuine_reviews:
        data.append({'text': r, 'label': 0}) # 0 = Genuine

    df = pd.DataFrame(data)
    df['cleaned'] = df['text'].apply(preprocess_text)
    return df

def train_model():
    print("Training Fake Review Detection Model...")
    df = generate_training_data()
    
    vectorizer = TfidfVectorizer(max_features=2500, ngram_range=(1, 2))
    X = vectorizer.fit_transform(df['cleaned'])
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    clf = LogisticRegression(C=1.5, max_iter=500)
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Model trained successfully! Test Accuracy: {acc * 100:.2f}%")
    
    # Save artifacts
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    return clf, vectorizer

def load_or_train_model():
    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        try:
            clf = joblib.load(MODEL_PATH)
            vectorizer = joblib.load(VECTORIZER_PATH)
            return clf, vectorizer
        except Exception:
            return train_model()
    else:
        return train_model()

# Global instances
_model = None
_vectorizer = None

def get_ml_components():
    global _model, _vectorizer
    if _model is None or _vectorizer is None:
        _model, _vectorizer = load_or_train_model()
    return _model, _vectorizer

def predict_review_raw(review_text, rating):
    clf, vectorizer = get_ml_components()
    cleaned = preprocess_text(review_text)
    
    if not cleaned:
        return {
            'classification': 'Suspicious',
            'confidence': 50.0,
            'fake_probability': 0.5,
            'genuine_probability': 0.5
        }
        
    feature_vector = vectorizer.transform([cleaned])
    probs = clf.predict_proba(feature_vector)[0]
    genuine_prob = float(probs[0])
    fake_prob = float(probs[1])
    
    # Classification decision logic with thresholds
    if fake_prob >= 0.65:
        classification = 'Fake'
        confidence = fake_prob * 100.0
    elif genuine_prob >= 0.65:
        classification = 'Genuine'
        confidence = genuine_prob * 100.0
    else:
        classification = 'Suspicious'
        confidence = max(fake_prob, genuine_prob) * 100.0
        
    return {
        'classification': classification,
        'confidence': confidence,
        'fake_probability': fake_prob,
        'genuine_probability': genuine_prob,
        'feature_vector': feature_vector,
        'cleaned_text': cleaned
    }
