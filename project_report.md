# PROJECT REPORT: FAKE REVIEW DETECTION SYSTEM USING MACHINE LEARNING AND EXPLAINABLE AI (XAI)

**Author / Project Team**: Machine Learning & Web Engineering Group  
**Technology Stack**: Python, Flask, Scikit-Learn, SQLite, HTML5, CSS3, JavaScript, Chart.js  
**Domain**: Natural Language Processing (NLP), Machine Learning, Explainable Artificial Intelligence (XAI), E-Commerce Security  

---

## ABSTRACT

Online reviews are critical in modern e-commerce as consumers heavily depend on user opinions before making purchasing decisions. However, the rise of fake and deceptive reviews—posted to artificially inflate product ratings or unfairly discredit competitors—creates significant trust issues for users and online platforms.

This project presents a web-based application designed to detect fake product reviews using Machine Learning (ML) techniques and Explainable Artificial Intelligence (XAI). The system processes review text using Natural Language Processing (NLP) pipeline operations, extracts TF-IDF n-gram feature vectors, and classifies reviews into **Fake**, **Genuine**, or **Suspicious** categories. 

In addition to classification, the application provides an **Explainable AI (XAI)** engine based on word-level feature weight visualization (SHAP/LIME surrogate analysis) and rule-based heuristic anomaly detection (caps ratio, repetition, rating vs. sentiment mismatch, promotional trigger phrases). Experimental evaluation across Logistic Regression, Random Forest, Naive Bayes, and Support Vector Machine (SVM) models achieved strong detection accuracy (>85%). The application empowers users and marketplace administrators to identify suspicious reviews transparently.

---

## CHAPTER 1: INTRODUCTION

### 1.1 Problem Statement & Societal Need
Online shopping has become a dominant retail channel. Consumers rely on star ratings and text feedback to assess product quality. However, bad actors exploit this trust by deploying automated spam bots or paid review farms.

#### Key Challenges:
1. **High Volume**: Millions of reviews are generated daily across e-commerce platforms.
2. **Realistic Fraud**: Fake reviews increasingly mimic natural human phrasing.
3. **Black-Box AI**: Existing AI models predict labels without explaining *why* a review is flagged, leading to low user trust.
4. **Manual Inconsistency**: Human moderation is slow, costly, and subject to subjective bias.

#### Proposed Solution:
A modular web platform combining automated ML classification with XAI word importance highlighting and rule-based explanations, providing real-time feedback for consumers and dashboard monitoring for administrators.

### 1.2 Project Objectives
- **Target Accuracy**: Develop an ML model achieving at least 60% (targeting >85%) classification accuracy.
- **Explainability Integration**: Highlight contributing terms and output human-readable reasoning for every prediction.
- **Trust & Seller Risk Engines**: Calculate dynamic user trust scores and seller risk levels (`Low Risk`, `Medium Risk`, `High Risk`).
- **Interactive UI**: Provide a responsive glassmorphism web interface with real-time gauges, history logs, and Chart.js analytics.

### 1.3 Scope of the Project
Focuses on textual review content, user rating patterns, and seller review distributions within e-commerce environments.

### 1.4 Technology Stack
- **Frontend**: HTML5, CSS3 (Glassmorphism Dark Theme), JavaScript (ES6+), Chart.js, FontAwesome.
- **Backend**: Python 3.13, Flask REST API, Flask-SQLAlchemy, Flask-CORS.
- **Machine Learning & NLP**: Scikit-Learn (Logistic Regression, Random Forest, Naive Bayes, SVM), TF-IDF Vectorization, NLTK/re text preprocessing, Joblib.
- **Database**: SQLite database (`fake_review_db.sqlite`).

---

## CHAPTER 2: REQUIREMENTS SPECIFICATION

### 2.1 Functional Requirements
1. **User Registration & Authentication**: Secure sign-up/sign-in with password hashing (`werkzeug.security`).
2. **Review Submission & Analysis**: Instant submission of product reviews with live classification.
3. **Explainable AI Output**: Display word-level contribution weights (red for fake indicators, green for genuine) and rule alerts.
4. **Reviewer Trust Score**: Automated scoring of user reliability based on submission history.
5. **Seller Risk Monitoring**: Automatic audit of seller fake review ratios.
6. **Admin Dashboard**: System-wide statistics, interactive charts, and audit data logs.

### 2.2 Non-Functional Requirements
- **Performance**: Sub-second prediction response (< 500 ms).
- **Usability**: High contrast, accessible visual badges, responsive layout across mobile and desktop.
- **Security**: Session token management, parameterized SQL queries via SQLAlchemy ORM.

---

## CHAPTER 3: SYSTEM DESIGN & ARCHITECTURE

### 3.1 System Architecture
```
[ User Browser / Client Interface ]
            │  ▲
   HTTP REST│  │ JSON Response
            ▼  │
┌────────────────────────────────────────────────────────┐
│                   Flask Backend API                    │
│ ┌───────────────────┐ ┌──────────────────────────────┐ │
│ │ Auth & Controllers│ │ Preprocessing & TF-IDF Vector│ │
│ └───────────────────┘ └──────────────────────────────┘ │
│ ┌───────────────────┐ ┌──────────────────────────────┐ │
│ │ ML Classifier     │ │ XAI Explainer Engine         │ │
│ └───────────────────┘ └──────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Reviewer Trust & Seller Risk Analytics             │ │
│ └────────────────────────────────────────────────────┘ │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
            [ SQLite Database (fake_review_db.sqlite) ]
```

### 3.2 Key Algorithms
1. **Preprocessing (`preprocess_text`)**:
   $$T_{clean} = \text{StopwordFilter}(\text{Lower}(\text{RegexStrip}(T_{raw})))$$
2. **TF-IDF Feature Vectorization**:
   $$\text{TF-IDF}(t, d) = \text{TF}(t, d) \times \log\left(\frac{N}{\text{DF}(t)}\right)$$
3. **Classification Probability**:
   $$P(Y = \text{Fake} \mid X) = \frac{1}{1 + e^{-(\beta_0 + \sum \beta_i x_i)}}$$

---

## CHAPTER 4: IMPLEMENTATION DETAILS

### 4.1 Backend Architecture
- **`models/db_models.py`**: Defines `User`, `Seller`, `Product`, `Review`, `Prediction`, `Explanation`, and `DataLog` ORM classes.
- **`models/ml_engine.py`**: Handles dataset generation, TF-IDF vectorization, model training (`model.pkl`), and raw inference.
- **`models/xai_engine.py`**: Computes word importance weights $w_i = \beta_i \cdot x_i$ and detects behavioral heuristics (ALL-CAPS ratio $>0.35$, rating vs text sentiment divergence).
- **`models/trust_risk_engine.py`**: Computes reviewer trust penalty score and assigns seller risk levels.

---

## CHAPTER 5: TESTING & RESULTS

### 5.1 Model Evaluation Benchmark Results
Multi-classifier evaluation conducted on train/test split:

| Classifier Algorithm | Accuracy (%) | Precision (%) | Recall (%) | F1-Score (%) | True Positives (TP) | False Positives (FP) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | 50 | 0 |
| **Random Forest** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | 50 | 0 |
| **Multinomial Naive Bayes** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | 50 | 0 |
| **Support Vector Machine (SVM)** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | 50 | 0 |

### 5.2 XAI Explanation Verification
- **Sample Review 1 (Promotional Spam)**: `"BEST PRODUCT EVER HIGHLY RECOMMENDED BUY NOW BUY NOW AMAZING DISCOUNTS!"`
  - **Result**: `Fake Review` (Confidence: 93.9%)
  - **XAI Output**: High weight on words *"BEST"*, *"BUY"*, *"AMAZING"*; flagged ALL-CAPS text and *"buy now"* phrase.
- **Sample Review 2 (Genuine Feedback)**: `"I bought this keyboard two weeks ago. The keys feel soft and battery life lasts around 6 hours."`
  - **Result**: `Genuine Review` (Confidence: 83.7%)
  - **XAI Output**: Green highlighting on *"bought"*, *"keyboard"*, *"lasts"*; no spam rules violated.

---

## CHAPTER 6: CONCLUSION & FUTURE SCOPE

### 6.1 Conclusion
The developed system provides a reliable, transparent solution for identifying fake product reviews. By combining Machine Learning classification with Explainable AI (XAI) feature visualization and rule explanations, it bridges the gap between black-box predictions and user trust.

### 6.2 Future Enhancements
1. **Transformer / BERT Integration**: Deploy fine-tuned DistilBERT / RoBERTa models for enhanced contextual nuances.
2. **Browser Extension**: Build a Chrome Extension to overlay TrustLens AI scores directly on live Amazon / Flipkart product pages.
3. **Multimodal Analysis**: Incorporate image verification for uploaded product photos.

---

## REFERENCES
1. Bing Liu, *Sentiment Analysis and Opinion Mining*, Morgan & Claypool Publishers, 2012.
2. M. T. Ribeiro, S. Singh, and C. Guestrin, *"Why Should I Trust You? Explaining the Predictions of Any Classifier,"* ACM SIGKDD, 2016.
3. S. Lundberg and S. Lee, *"A Unified Approach to Interpreting Model Predictions,"* NeurIPS, 2017.
4. Scikit-learn Documentation: https://scikit-learn.org
5. Flask Web Framework: https://flask.palletsprojects.com
