import re
import numpy as np
from models.ml_engine import get_ml_components, preprocess_text

def generate_xai_explanation(review_text, rating, ml_result):
    clf, vectorizer = get_ml_components()
    cleaned = ml_result.get('cleaned_text', '')
    classification = ml_result.get('classification', 'Genuine')
    confidence = ml_result.get('confidence', 50.0)
    fake_prob = ml_result.get('fake_probability', 0.5)
    
    words = review_text.split()
    feature_names = vectorizer.get_feature_names_out()
    coefficients = clf.coef_[0] if hasattr(clf, 'coef_') else np.zeros(len(feature_names))
    
    # Map feature names to coefficients
    feature_coeff_map = {feat: coef for feat, coef in zip(feature_names, coefficients)}
    
    word_contributions = []
    reasons = []
    
    # 1. Word level weight computation
    for word in words:
        clean_w = re.sub(r'[^a-zA-Z0-9]', '', word.lower())
        weight = feature_coeff_map.get(clean_w, 0.0)
        
        # Heuristic modifiers for word importance
        if clean_w in ['scam', 'fraud', 'buy', 'discount', 'unbelievable', 'guaranteed', '100', 'must']:
            weight += 0.35
        elif word.isupper() and len(word) > 2:
            weight += 0.25 # ALL CAPS penalty
            
        impact = 'neutral'
        if weight > 0.15:
            impact = 'fake' # pushes towards Fake
        elif weight < -0.15:
            impact = 'genuine' # pushes towards Genuine
            
        word_contributions.append({
            'word': word,
            'weight': round(float(weight), 3),
            'impact': impact
        })

    # 2. Rule-Based XAI Heuristics Analysis
    # Rule A: Excessive Capitalization
    upper_chars = sum(1 for c in review_text if c.isupper())
    total_chars = max(len(review_text), 1)
    caps_ratio = upper_chars / total_chars
    if caps_ratio > 0.35 and len(review_text) > 15:
        reasons.append("High ratio of ALL-CAPS characters detected (indicative of promotional spam or artificial hype).")

    # Rule B: Repetitive Words / Phrasing
    clean_words = [w for w in cleaned.split() if len(w) > 2]
    if len(clean_words) > 0:
        unique_ratio = len(set(clean_words)) / len(clean_words)
        if unique_ratio < 0.55:
            reasons.append("High degree of repetitive word patterns found in the text.")

    # Rule C: Rating vs Sentiment Mismatch
    negative_spam_keywords = ['terrible', 'worst', 'scam', 'fraud', 'defective', 'broken', 'waste', 'trash']
    positive_hype_keywords = ['best', 'amazing', 'super', 'unbelievable', '100%', 'guaranteed', 'discount']
    
    neg_count = sum(1 for w in clean_words if w in negative_spam_keywords)
    pos_count = sum(1 for w in clean_words if w in positive_hype_keywords)
    
    if rating >= 4 and neg_count >= 2:
        reasons.append("Rating Mismatch: 4-5 star rating provided despite strong negative criticism keywords in review text.")
    elif rating <= 2 and pos_count >= 2 and fake_prob < 0.4:
        reasons.append("Rating Mismatch: 1-2 star rating given for overwhelmingly positive praising text.")

    # Rule D: Generic Promotional Triggers
    promo_triggers = ['buy now', 'discount code', 'best seller', 'link below', '100% genuine', 'order immediately']
    for p in promo_triggers:
        if p in review_text.lower():
            reasons.append(f"Contains commercial promotional trigger phrase: '{p}'.")
            break

    # Final summary construction
    if not reasons:
        if classification == 'Genuine':
            reasons.append("Review exhibits balanced vocabulary, normal sentence structure, and authentic user feedback patterns.")
        elif classification == 'Fake':
            reasons.append("Review exhibits statistical term weights highly correlated with synthetic/spam promotional content.")
        else:
            reasons.append("Review shows mixed indicators between genuine sentiment and automated writing characteristics.")

    explanation_summary = f"Classified as {classification} with {confidence:.1f}% confidence. " + " ".join(reasons)

    return {
        'contributing_words': word_contributions,
        'reason_summary': explanation_summary,
        'detected_rules': reasons,
        'xai_method': 'TF-IDF Linear Surrogate + Heuristic XAI Engine'
    }
