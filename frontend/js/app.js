/* ==========================================================================
   TrustLens.ai - JavaScript Frontend Application Logic
   ========================================================================== */

const API_BASE = 'http://127.0.0.1:5000';

async function apiFetch(endpoint, options = {}) {
    options.headers = options.headers || {};
    options.credentials = 'include';
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
    return fetch(url, options);
}

let classificationChartInstance = null;
let categoryChartInstance = null;

// Preset Test Samples
const SAMPLES = {
    fake: {
        product: "Ultra Slim Bluetooth Keyboard",
        category: "Electronics",
        rating: "5",
        text: "BEST KEYBOARD EVER BUY NOW AMAZING DISCOUNT 100% GENUINE GUARANTEED FIVE STARS BEST SELLER LINK BELOW ORDER IMMEDIATELY!!!"
    },
    genuine: {
        product: "Wireless Noise Cancelling Headphones",
        category: "Electronics",
        rating: "4",
        text: "I bought these headphones two weeks ago. The active noise cancellation is effective in office environments, though battery life is closer to 6 hours rather than advertised 8."
    },
    suspicious: {
        product: "Ergonomic Office Mesh Chair",
        category: "Furniture",
        rating: "5",
        text: "Terrible quality fake item delivered with broken packaging and missing screws scam fraud refund immediately!"
    }
};

document.addEventListener("DOMContentLoaded", () => {
    checkAuthStatus();
    loadSellersSelect();
    loadSellersGrid();
    loadReviewHistory();
});

// Toast Notifications
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? 'fa-circle-check' : 'fa-triangle-exclamation';
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// Tab Switching Logic
function switchTab(tabId) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.remove('active');
        el.classList.remove('hidden'); // ensure hidden never blocks a tab
    });
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

    // Show selected tab
    const targetTab = document.getElementById(tabId);
    if (targetTab) {
        targetTab.classList.add('active');
    }

    // Highlight active nav item
    const btn = Array.from(document.querySelectorAll('.nav-item')).find(
        b => b.getAttribute('onclick') && b.getAttribute('onclick').includes(tabId)
    );
    if (btn) btn.classList.add('active');

    // Load data for each tab
    if (tabId === 'history-tab') loadReviewHistory();
    if (tabId === 'seller-tab') loadSellersGrid();
    if (tabId === 'admin-tab') loadAdminDashboard();
    if (tabId === 'metrics-tab') loadModelMetrics();
}


// Authentication Handlers
async function checkAuthStatus() {
    try {
        const res = await apiFetch('/api/me');
        const data = await res.json();
        const loggedOutView = document.getElementById('logged-out-view');
        const loggedInView = document.getElementById('logged-in-view');

        if (data.logged_in && data.user) {
            loggedOutView.classList.add('hidden');
            loggedInView.classList.remove('hidden');
            document.getElementById('user-display-name').textContent = data.user.name;
            document.getElementById('user-display-trust').textContent = `Trust: ${data.user.trust_score}%`;
        } else {
            loggedOutView.classList.remove('hidden');
            loggedInView.classList.add('hidden');
        }
    } catch (e) {
        console.error("Auth status check failed:", e);
    }
}

function openAuthModal(mode = 'login') {
    document.getElementById('auth-modal').classList.remove('hidden');
    switchAuthTab(mode);
}

function closeAuthModal() {
    document.getElementById('auth-modal').classList.add('hidden');
}

function switchAuthTab(mode) {
    const loginForm = document.getElementById('login-form');
    const regForm = document.getElementById('register-form');
    const tabLogin = document.getElementById('auth-tab-login');
    const tabReg = document.getElementById('auth-tab-register');

    if (mode === 'login') {
        loginForm.classList.remove('hidden');
        regForm.classList.add('hidden');
        tabLogin.classList.add('active');
        tabReg.classList.remove('active');
    } else {
        loginForm.classList.add('hidden');
        regForm.classList.remove('hidden');
        tabLogin.classList.remove('active');
        tabReg.classList.add('active');
    }
}

function fillAuth(email, pass) {
    document.getElementById('login-email').value = email;
    document.getElementById('login-password').value = pass;
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const res = await apiFetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (res.ok) {
            showToast(data.message, 'success');
            closeAuthModal();
            checkAuthStatus();
        } else {
            showToast(data.error || 'Login failed', 'error');
        }
    } catch (err) {
        showToast('Server connection error.', 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById('reg-name').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;

    try {
        const res = await apiFetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });
        const data = await res.json();

        if (res.ok) {
            showToast(data.message, 'success');
            closeAuthModal();
            checkAuthStatus();
        } else {
            showToast(data.error || 'Registration failed', 'error');
        }
    } catch (err) {
        showToast('Server connection error.', 'error');
    }
}

async function logout() {
    try {
        await apiFetch('/api/logout', { method: 'POST' });
        showToast('Logged out successfully.');
        checkAuthStatus();
    } catch (e) {
        console.error(e);
    }
}

// Preset Fill Function
function fillSample(type) {
    const sample = SAMPLES[type];
    if (!sample) return;
    document.getElementById('product-name').value = sample.product;
    document.getElementById('category').value = sample.category;
    document.getElementById('review-text').value = sample.text;

    const rad = document.querySelector(`input[name="rating"][value="${sample.rating}"]`);
    if (rad) rad.checked = true;
}

// Populate Sellers Select Dropdown
async function loadSellersSelect() {
    try {
        const res = await apiFetch('/api/sellers');
        const data = await res.json();
        const select = document.getElementById('seller-select');
        select.innerHTML = '';
        (data.sellers || []).forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = `${s.name} (${s.brand}) - ${s.risk_level}`;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error(e);
    }
}

// Review Submission & XAI Rendering
async function handleReviewSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById('btn-analyze');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running Machine Learning & XAI Engine...';

    const productName = document.getElementById('product-name').value;
    const category = document.getElementById('category').value;
    const sellerId = document.getElementById('seller-select').value;
    const rating = document.querySelector('input[name="rating"]:checked').value;
    const reviewText = document.getElementById('review-text').value;

    try {
        const res = await apiFetch('/api/submit-review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_name: productName,
                category: category,
                seller_id: sellerId,
                rating: parseInt(rating),
                review_text: reviewText
            })
        });

        const data = await res.json();
        if (res.ok) {
            showToast('Review analyzed successfully!', 'success');
            renderPredictionResults(data.review);
            checkAuthStatus();
        } else {
            showToast(data.error || 'Prediction failed.', 'error');
        }
    } catch (err) {
        showToast('Failed to connect to backend server.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-magnifying-glass-chart"></i> Analyze Review Authenticity';
    }
}

function renderPredictionResults(reviewData) {
    const placeholder = document.getElementById('result-placeholder');
    const activeResult = document.getElementById('result-active');
    placeholder.classList.add('hidden');
    activeResult.classList.remove('hidden');

    const pred = reviewData.prediction || {};
    const exp = pred.explanation || {};
    const classification = pred.classification || 'Genuine';
    const confidence = pred.confidence_score || 50.0;

    // Update Badge
    const badge = document.getElementById('classification-badge');
    const title = document.getElementById('class-title');
    badge.className = `prediction-badge ${classification.toLowerCase()}`;

    if (classification === 'Fake') {
        badge.innerHTML = `
            <div class="badge-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
            <div class="badge-content">
                <span class="badge-label">Prediction Status</span>
                <h3>FAKE REVIEW DETECTED 🚨</h3>
            </div>`;
    } else if (classification === 'Genuine') {
        badge.innerHTML = `
            <div class="badge-icon"><i class="fa-solid fa-circle-check"></i></div>
            <div class="badge-content">
                <span class="badge-label">Prediction Status</span>
                <h3>GENUINE REVIEW VERIFIED ✅</h3>
            </div>`;
    } else {
        badge.innerHTML = `
            <div class="badge-icon"><i class="fa-solid fa-shield-cat"></i></div>
            <div class="badge-content">
                <span class="badge-label">Prediction Status</span>
                <h3>SUSPICIOUS / CONTRADICTORY REVIEW ⚠️</h3>
            </div>`;
    }

    // Update Gauge & Metrics
    document.getElementById('confidence-progress').style.width = `${confidence}%`;
    document.getElementById('confidence-value').textContent = `${confidence}%`;

    const isFake = classification === 'Fake';
    const fakeProb = isFake ? confidence : (100 - confidence);
    const genuineProb = 100 - fakeProb;

    document.getElementById('fake-prob-value').textContent = `${fakeProb.toFixed(1)}%`;
    document.getElementById('genuine-prob-value').textContent = `${genuineProb.toFixed(1)}%`;

    // Render XAI Word Pill Highlighting
    const wordBox = document.getElementById('xai-word-container');
    wordBox.innerHTML = '';

    const words = exp.contributing_words || [];
    if (words.length > 0) {
        words.forEach(w => {
            const span = document.createElement('span');
            span.className = `word-pill ${w.impact}`;
            span.title = `Weight: ${w.weight} (${w.impact.toUpperCase()})`;
            span.textContent = w.word;
            wordBox.appendChild(span);
        });
    } else {
        wordBox.textContent = reviewData.review_text;
    }

    // Render Summary & Rules
    document.getElementById('explanation-text').textContent = exp.reason_summary || "Feature extraction complete.";
    document.getElementById('result-timestamp').textContent = `Analyzed at ${new Date().toLocaleTimeString()}`;

    const rulesList = document.getElementById('rules-list');
    rulesList.innerHTML = '';
    const rules = exp.detected_rules || [];
    if (rules.length > 0) {
        rules.forEach(rule => {
            const li = document.createElement('li');
            li.textContent = rule;
            rulesList.appendChild(li);
        });
    } else {
        const li = document.createElement('li');
        li.textContent = "No severe spam rule violations detected.";
        rulesList.appendChild(li);
    }
}

// ─── Review History ──────────────────────────────────────────────
let _allReviews = [];

async function loadReviewHistory() {
    try {
        const res = await apiFetch('/api/reviews?limit=200');
        const data = await res.json();
        _allReviews = data.reviews || [];
        renderHistory(_allReviews);
        updateHistoryStats(_allReviews);
    } catch (e) {
        console.error(e);
        const tbody = document.getElementById('history-table-body');
        tbody.innerHTML = '<tr><td colspan="9" class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i> Failed to load reviews.</td></tr>';
    }
}

function updateHistoryStats(reviews) {
    const fake = reviews.filter(r => (r.prediction?.classification || '').toLowerCase() === 'fake').length;
    const genuine = reviews.filter(r => (r.prediction?.classification || '').toLowerCase() === 'genuine').length;
    const suspicious = reviews.filter(r => (r.prediction?.classification || '').toLowerCase() === 'suspicious').length;
    document.getElementById('hs-total').textContent = reviews.length;
    document.getElementById('hs-fake').textContent = fake;
    document.getElementById('hs-genuine').textContent = genuine;
    document.getElementById('hs-suspicious').textContent = suspicious;
}

function applyHistoryFilters() {
    const search = (document.getElementById('hist-search').value || '').toLowerCase();
    const cat    = (document.getElementById('hist-category').value || 'All');
    const rating = (document.getElementById('hist-rating').value || 'All');
    const cls    = (document.getElementById('hist-class').value || 'All');

    const filtered = _allReviews.filter(r => {
        const matchSearch = !search ||
            r.product_name.toLowerCase().includes(search) ||
            r.review_text.toLowerCase().includes(search) ||
            (r.seller_name || '').toLowerCase().includes(search);
        const matchCat    = cat === 'All' || r.category === cat;
        const matchRating = rating === 'All' || String(r.rating) === rating;
        const matchCls    = cls === 'All' || (r.prediction?.classification || '') === cls;
        return matchSearch && matchCat && matchRating && matchCls;
    });

    renderHistory(filtered);
    updateHistoryStats(filtered);
}

function clearHistoryFilters() {
    document.getElementById('hist-search').value = '';
    document.getElementById('hist-category').value = 'All';
    document.getElementById('hist-rating').value = 'All';
    document.getElementById('hist-class').value = 'All';
    renderHistory(_allReviews);
    updateHistoryStats(_allReviews);
}

function renderHistory(reviews) {
    const tbody = document.getElementById('history-table-body');
    const empty = document.getElementById('history-empty');
    tbody.innerHTML = '';

    if (!reviews.length) {
        tbody.innerHTML = '<tr><td colspan="11" class="empty-state"><i class="fa-solid fa-inbox"></i> No reviews found.</td></tr>';
        empty && empty.classList.remove('hidden');
        return;
    }
    empty && empty.classList.add('hidden');

    reviews.forEach(r => {
        const pred = r.prediction || {};
        const cls  = pred.classification || 'N/A';
        const conf = pred.confidence_score != null ? pred.confidence_score : 0;
        const clsLow = cls.toLowerCase();

        let badgeClass = 'badge-genuine';
        if (clsLow === 'fake') badgeClass = 'badge-fake';
        if (clsLow === 'suspicious') badgeClass = 'badge-suspicious';

        const stars = '★'.repeat(r.rating || 0) + '☆'.repeat(5 - (r.rating || 0));
        const snippet = (r.review_text || '').length > 70
            ? r.review_text.substring(0, 68) + '…'
            : r.review_text;

        // Source badge
        const isOCR = r.source_type === 'ocr';
        const sourceBadge = isOCR
            ? '<span class="source-badge ocr"><i class="fa-solid fa-image"></i> OCR</span>'
            : '<span class="source-badge manual"><i class="fa-solid fa-keyboard"></i> Manual</span>';

        // Image thumbnail
        let imgCell = '<span style="color:var(--text-muted);font-size:0.75rem">—</span>';
        if (r.has_image && r.image_filename) {
            const imgUrl = `${API_BASE}/api/review-image/${r.image_filename}`;
            imgCell = `<img src="${imgUrl}" alt="Review image" class="history-img-thumb"
                onclick="openImageModal('${imgUrl}')" title="Click to enlarge">`;
        }

        const tr = document.createElement('tr');
        tr.dataset.id = r.id;
        tr.innerHTML = `
            <td><span style="color:var(--text-muted);font-size:0.8rem">#${r.id}</span></td>
            <td>${sourceBadge}</td>
            <td>
                <strong>${escHtml(r.product_name)}</strong>
                <br><small style="color:var(--primary-cyan);opacity:.7">${escHtml(r.category)}</small>
            </td>
            <td><small>${escHtml(r.seller_name || '—')}</small></td>
            <td><span class="stars">${stars}</span></td>
            <td><em style="color:var(--text-muted);font-size:0.82rem">"${escHtml(snippet)}"</em></td>
            <td><span class="badge ${badgeClass}">${cls}</span></td>
            <td>
                <div class="conf-bar-wrap"><div class="conf-bar-fill ${clsLow}" style="width:${conf}%"></div></div>
                <small>${conf}%</small>
            </td>
            <td><small style="color:var(--text-muted)">${r.timestamp || '—'}</small></td>
            <td class="img-thumb-cell">${imgCell}</td>
            <td><button class="btn-xai" onclick="openXaiDrawer(${r.id})"><i class="fa-solid fa-wand-sparkles"></i> XAI</button></td>
        `;
        tbody.appendChild(tr);
    });
}

function escHtml(str) {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(str));
    return d.innerHTML;
}

async function openXaiDrawer(reviewId) {
    // Fetch detailed prediction
    try {
        const res  = await apiFetch(`/api/review/${reviewId}`);
        const data = await res.json();
        const rev  = data.review || {};
        const pred = rev.prediction || {};
        const exp  = pred.explanation || {};
        const cls  = pred.classification || 'N/A';
        const clsLow = cls.toLowerCase();

        // Badge
        const badge = document.getElementById('xai-drawer-badge');
        badge.className = `prediction-badge ${clsLow}`;
        const icons = { fake: '🔴', genuine: '🟢', suspicious: '🟡' };
        badge.innerHTML = `${icons[clsLow] || '⚪'} ${cls} — ${rev.product_name || ''}`;

        // Scores
        const conf = pred.confidence_score || 0;
        document.getElementById('drawer-conf-val').textContent = `${conf}%`;
        document.getElementById('drawer-progress').style.width = `${conf}%`;
        document.getElementById('drawer-fake-val').textContent    = `${pred.fake_probability || 0}%`;
        document.getElementById('drawer-genuine-val').textContent = `${pred.genuine_probability || 0}%`;

        // Word highlights
        const wordBox = document.getElementById('drawer-words');
        wordBox.innerHTML = '';
        if (exp.word_contributions && exp.word_contributions.length) {
            exp.word_contributions.forEach(w => {
                const span = document.createElement('span');
                span.className = `word-chip ${w.category || 'neutral'}`;
                span.textContent = w.word;
                wordBox.appendChild(span);
            });
        } else {
            wordBox.textContent = rev.review_text || '';
        }

        // Summary
        document.getElementById('drawer-summary').textContent = exp.reason_summary || 'Feature extraction complete.';
        const rulesList = document.getElementById('drawer-rules');
        rulesList.innerHTML = '';
        const rules = exp.detected_rules || ['No severe rule violations detected.'];
        rules.forEach(rule => {
            const li = document.createElement('li');
            li.textContent = rule;
            rulesList.appendChild(li);
        });

        // Show drawer
        const drawer = document.getElementById('xai-drawer');
        drawer.classList.remove('hidden');
        drawer.scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (e) {
        showToast('Could not load XAI details.', 'error');
        console.error(e);
    }
}

function closeXaiDrawer() {
    document.getElementById('xai-drawer').classList.add('hidden');
}

// ─── Seller Risk Analysis ────────────────────────────────────────
let _allSellers = [];

async function loadSellersGrid() {
    try {
        const res = await apiFetch('/api/sellers');
        const data = await res.json();
        _allSellers = data.sellers || [];
        renderSellers(_allSellers);
        updateSellerStats(_allSellers);
    } catch (e) {
        console.error(e);
        const grid = document.getElementById('sellers-grid');
        grid.innerHTML = '<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i> Failed to load seller directory.</div>';
    }
}

function updateSellerStats(sellers) {
    const high = sellers.filter(s => s.risk_level === 'High Risk').length;
    const medium = sellers.filter(s => s.risk_level === 'Medium Risk').length;
    const low = sellers.filter(s => s.risk_level === 'Low Risk').length;
    
    document.getElementById('ss-total').textContent = sellers.length;
    document.getElementById('ss-high').textContent = high;
    document.getElementById('ss-medium').textContent = medium;
    document.getElementById('ss-low').textContent = low;
}

function applySellerFilters() {
    const search = (document.getElementById('seller-search').value || '').toLowerCase();
    const risk   = (document.getElementById('seller-risk-filter').value || 'All');

    const filtered = _allSellers.filter(s => {
        const matchSearch = !search || 
            s.name.toLowerCase().includes(search) || 
            (s.brand || '').toLowerCase().includes(search);
        const matchRisk   = risk === 'All' || s.risk_level === risk;
        return matchSearch && matchRisk;
    });

    renderSellers(filtered);
}

function clearSellerFilters() {
    document.getElementById('seller-search').value = '';
    document.getElementById('seller-risk-filter').value = 'All';
    renderSellers(_allSellers);
}

function renderSellers(sellers) {
    const grid = document.getElementById('sellers-grid');
    const empty = document.getElementById('seller-empty');
    grid.innerHTML = '';

    if (!sellers.length) {
        empty && empty.classList.remove('hidden');
        return;
    }
    empty && empty.classList.add('hidden');

    sellers.forEach(s => {
        let riskBadge = 'badge-low';
        let cardClass = 'seller-card';
        if (s.risk_level === 'Medium Risk') {
            riskBadge = 'badge-medium';
        } else if (s.risk_level === 'High Risk') {
            riskBadge = 'badge-high';
            cardClass += ' high-risk-highlight';
        }

        const card = document.createElement('div');
        card.className = cardClass;
        card.innerHTML = `
            <div class="seller-header">
                <div>
                    <h4 class="seller-name">${escHtml(s.name)}</h4>
                    <span class="seller-brand">Brand: ${escHtml(s.brand || '—')}</span>
                </div>
                <span class="badge ${riskBadge}">${s.risk_level}</span>
            </div>
            <div class="seller-stat-row">
                <span>Total Reviews:</span> <strong>${s.total_reviews}</strong>
            </div>
            <div class="seller-stat-row">
                <span>Fake Reviews Flagged:</span> <strong class="danger-text">${s.fake_count}</strong>
            </div>
            <div class="seller-stat-row">
                <span>Deceptive Ratio:</span> <strong>${s.fake_ratio}%</strong>
            </div>
            <div class="seller-stat-row">
                <span>Store Rating:</span> <span style="color:#f59e0b;">${'★'.repeat(Math.round(s.rating || 0)) + '☆'.repeat(5 - Math.round(s.rating || 0))}</span>
            </div>
        `;
        grid.appendChild(card);
    });
}


// Load Admin Dashboard & Render Charts
async function loadAdminDashboard() {
    try {
        const res = await apiFetch('/api/admin/stats');
        const data = await res.json();

        document.getElementById('stat-total-reviews').textContent = data.total_reviews;
        document.getElementById('stat-fake-reviews').textContent = `${data.fake_count} (${data.fake_percentage}%)`;
        document.getElementById('stat-genuine-reviews').textContent = data.genuine_count;
        document.getElementById('stat-high-risk-sellers').textContent = data.high_risk_sellers;

        // Render Logs
        const logsBody = document.getElementById('admin-logs-body');
        logsBody.innerHTML = '';
        (data.recent_logs || []).forEach(l => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>#${l.id}</td>
                <td>${l.user_id ? 'User #' + l.user_id : 'System'}</td>
                <td><strong>${l.action}</strong></td>
                <td>${l.target}</td>
                <td><small>${l.details}</small></td>
                <td><small>${l.timestamp}</small></td>
            `;
            logsBody.appendChild(tr);
        });

        // Render Classification Doughnut Chart
        const ctx1 = document.getElementById('classificationChart').getContext('2d');
        if (classificationChartInstance) classificationChartInstance.destroy();
        classificationChartInstance = new Chart(ctx1, {
            type: 'doughnut',
            data: {
                labels: ['Genuine', 'Fake', 'Suspicious'],
                datasets: [{
                    data: [data.genuine_count, data.fake_count, data.suspicious_count],
                    backgroundColor: ['#10b981', '#f43f5e', '#f59e0b'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#94a3b8' } }
                }
            }
        });

        // Render Category Bar Chart
        const catData = data.category_breakdown || {};
        const ctx2 = document.getElementById('categoryChart').getContext('2d');
        if (categoryChartInstance) categoryChartInstance.destroy();
        categoryChartInstance = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: Object.keys(catData),
                datasets: [{
                    label: 'Reviews',
                    data: Object.values(catData),
                    backgroundColor: '#00f2fe',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });

    } catch (e) {
        console.error(e);
    }
}

let modelComparisonChartInstance = null;

async function loadModelMetrics() {
    try {
        const res = await apiFetch('/api/model-performance');
        const data = await res.json();
        
        const tbody = document.getElementById('metrics-table-body');
        tbody.innerHTML = '';
        
        const metrics = data.model_metrics || {};
        const labels = [];
        const accuracies = [];
        
        for (const [modelName, m] of Object.entries(metrics)) {
            labels.push(modelName);
            accuracies.push(m.accuracy);
            
            const cm = m.confusion_matrix || {};
            const cmText = `TN:${cm.true_negative} | FP:${cm.false_positive} | FN:${cm.false_negative} | TP:${cm.true_positive}`;
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${modelName}</strong></td>
                <td><span class="badge badge-genuine">${m.accuracy}%</span></td>
                <td>${m.precision}%</td>
                <td>${m.recall}%</td>
                <td><strong>${m.f1_score}%</strong></td>
                <td><small>${cmText}</small></td>
            `;
            tbody.appendChild(tr);
        }
        
        // Render Best Model Info
        const bestTitle = document.getElementById('best-model-title');
        const bestDesc = document.getElementById('best-model-desc');
        bestTitle.innerHTML = `<i class="fa-solid fa-trophy"></i> Best Classifier: ${data.best_model}`;
        
        const bestMetrics = metrics[data.best_model] || {};
        bestDesc.innerHTML = `The <strong>${data.best_model}</strong> classifier achieved the highest overall performance with <strong>${bestMetrics.accuracy}% Accuracy</strong> and an <strong>F1-Score of ${bestMetrics.f1_score}%</strong>. Evaluation was conducted on a split test set of ${data.test_samples} sample reviews.`;
        
        // Render Model Accuracy Comparison Bar Chart
        const ctx = document.getElementById('modelComparisonChart').getContext('2d');
        if (modelComparisonChartInstance) modelComparisonChartInstance.destroy();
        modelComparisonChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Accuracy (%)',
                    data: accuracies,
                    backgroundColor: ['#00f2fe', '#10b981', '#a855f7', '#f59e0b'],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
                    y: { min: 50, max: 100, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
        
    } catch (e) {
        console.error("Failed to load model metrics:", e);
    }
}

/* ═══════════════════════════════════════════════════════════════════
   OCR IMAGE UPLOAD — TrustLens.ai
   ═══════════════════════════════════════════════════════════════════ */

let _ocrFile = null;   // holds the selected File object

// ── 1. File selected via input or drag-drop ──────────────────────
function handleOCRFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    _setOCRFile(file);
}

function _setOCRFile(file) {
    _ocrFile = file;

    // Show image preview
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('ocr-preview-img').src = e.target.result;
        document.getElementById('ocr-file-name').textContent = `${file.name}  (${(file.size / 1024).toFixed(1)} KB)`;
        document.getElementById('ocr-preview-container').classList.remove('hidden');
        document.getElementById('btn-extract-ocr').disabled = false;
        // Reset result box
        document.getElementById('ocr-result-box').classList.add('hidden');
    };
    reader.readAsDataURL(file);
}

// ── 2. Drag-and-drop support ─────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const zone = document.getElementById('ocr-drop-zone');
    if (!zone) return;

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            _setOCRFile(file);
        } else {
            showToast('Please drop a valid image file.', 'error');
        }
    });
});

// ── 3. Clear OCR upload ──────────────────────────────────────────
function clearOCRImage() {
    _ocrFile = null;
    document.getElementById('ocr-file-input').value = '';
    document.getElementById('ocr-preview-container').classList.add('hidden');
    document.getElementById('ocr-result-box').classList.add('hidden');
    document.getElementById('btn-extract-ocr').disabled = true;
    document.getElementById('ocr-preview-img').src = '';
}

// ── 4. Run OCR via backend ────────────────────────────────────────
async function runOCR() {
    if (!_ocrFile) {
        showToast('Please select an image first.', 'error');
        return;
    }

    const btn = document.getElementById('btn-extract-ocr');
    const loading = document.getElementById('ocr-loading');
    btn.disabled = true;
    loading.classList.remove('hidden');

    const formData = new FormData();
    formData.append('image', _ocrFile);

    try {
        const res = await fetch(`${API_BASE}/api/ocr-extract`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        const data = await res.json();

        if (!res.ok) {
            showToast(data.error || 'OCR extraction failed.', 'error');
            return;
        }

        document.getElementById('ocr-extracted-text').value = data.text;
        document.getElementById('ocr-word-count').textContent =
            `✅ Extracted ${data.word_count} word${data.word_count !== 1 ? 's' : ''} successfully`;
        document.getElementById('ocr-result-box').classList.remove('hidden');
        showToast(`OCR complete — ${data.word_count} words extracted!`, 'success');

    } catch (err) {
        showToast('Failed to reach OCR backend. Is the server running?', 'error');
        console.error(err);
    } finally {
        btn.disabled = false;
        loading.classList.add('hidden');
    }
}

// ── 5. Use extracted text → fill the main review form ────────────
function useOCRText() {
    const text = document.getElementById('ocr-extracted-text').value.trim();
    if (!text) {
        showToast('No text to use — run OCR extraction first.', 'error');
        return;
    }
    document.getElementById('review-text').value = text;
    showToast('Review text filled from OCR — click Analyze to classify!', 'success');
    // Scroll up to the form
    document.getElementById('review-form').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── 6. Analyze OCR review directly (saves image + text together) ──
async function submitOCRReview() {
    const text = document.getElementById('ocr-extracted-text').value.trim();
    if (!text) {
        showToast('No extracted text available. Run OCR first.', 'error');
        return;
    }
    if (!_ocrFile) {
        showToast('Original image file is missing. Please re-upload.', 'error');
        return;
    }

    const productName = document.getElementById('product-name').value || 'OCR Scanned Product';
    const category    = document.getElementById('category').value || 'General';
    const sellerId    = document.getElementById('seller-select').value;
    const rating      = document.querySelector('input[name="rating"]:checked')?.value || '5';

    const formData = new FormData();
    formData.append('review_text', text);
    formData.append('product_name', productName);
    formData.append('category', category);
    formData.append('seller_id', sellerId);
    formData.append('rating', rating);
    formData.append('image', _ocrFile);

    const btn = document.querySelector('#ocr-result-box .btn-success');
    if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...'; }

    try {
        const res = await fetch(`${API_BASE}/api/submit-ocr-review`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        const data = await res.json();

        if (res.ok) {
            showToast('OCR review analyzed and saved! ✅', 'success');
            renderPredictionResults(data.review);
            loadReviewHistory();   // refresh history tab
        } else {
            showToast(data.error || 'Submission failed.', 'error');
        }
    } catch (err) {
        showToast('Server error during OCR submission.', 'error');
        console.error(err);
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fa-solid fa-magnifying-glass-chart"></i> Analyze OCR Review Directly'; }
    }
}

// ── 7. Image Modal (full-size view) ──────────────────────────────
function openImageModal(imgUrl) {
    // Create or reuse modal
    let modal = document.getElementById('image-view-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'image-view-modal';
        modal.className = 'img-modal-overlay';
        modal.innerHTML = `
            <div class="img-modal-inner">
                <button class="img-modal-close" onclick="closeImageModal()">
                    <i class="fa-solid fa-xmark"></i>
                </button>
                <img id="img-modal-photo" src="" alt="Review image" class="img-modal-photo">
                <p class="img-modal-caption">Original review screenshot / photo</p>
            </div>`;
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeImageModal();
        });
        document.body.appendChild(modal);
    }
    document.getElementById('img-modal-photo').src = imgUrl;
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeImageModal() {
    const modal = document.getElementById('image-view-modal');
    if (modal) modal.classList.add('hidden');
    document.body.style.overflow = '';
}

