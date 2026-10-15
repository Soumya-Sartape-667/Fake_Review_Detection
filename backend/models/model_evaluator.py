import os
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from models.ml_engine import generate_training_data, preprocess_text, MODEL_PATH, VECTORIZER_PATH

def evaluate_all_models():
    """Trains and compares Logistic Regression, Random Forest, Naive Bayes, and SVM classifiers."""
    df = generate_training_data()
    
    vectorizer = TfidfVectorizer(max_features=2500, ngram_range=(1, 2))
    X = vectorizer.fit_transform(df['cleaned'])
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    
    classifiers = {
        'Logistic Regression': LogisticRegression(C=1.5, max_iter=500),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'Multinomial Naive Bayes': MultinomialNB(alpha=0.5),
        'Support Vector Machine (SVM)': SVC(kernel='linear', probability=True, random_state=42)
    }
    
    results = {}
    best_model_name = None
    best_f1 = -1
    best_model = None
    
    for name, clf in classifiers.items():
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred).tolist()
        
        results[name] = {
            'accuracy': round(acc * 100, 2),
            'precision': round(prec * 100, 2),
            'recall': round(rec * 100, 2),
            'f1_score': round(f1 * 100, 2),
            'confusion_matrix': {
                'true_negative': cm[0][0],
                'false_positive': cm[0][1],
                'false_negative': cm[1][0],
                'true_positive': cm[1][1]
            }
        }
        
        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model = clf
            
    # Save the overall best performing model and vectorizer
    if best_model is not None:
        joblib.dump(best_model, MODEL_PATH)
        joblib.dump(vectorizer, VECTORIZER_PATH)
        
    return {
        'best_model': best_model_name,
        'model_metrics': results,
        'dataset_size': len(df),
        'train_samples': X_train.shape[0],
        'test_samples': X_test.shape[0]
    }
