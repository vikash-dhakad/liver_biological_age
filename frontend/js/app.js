/**
 * Liver Biological Age Predictor - Primary Frontend Logic
 * ========================================================
 * Tab switching, dynamic form rendering from /api/feature-schema,
 * single & batch predictions, history search/delete, theme toggling.
 */

let featureSchema = [];
let currentPredictionId = null;

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initTheme();
    fetchFeatureSchema();
    initFormSubmit();
    initBatchUpload();
    initHistorySearch();
});

// Tab Switching
function initTabs() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll('.nav-item').forEach(item => {
        if (item.getAttribute('data-tab') === tabId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    document.querySelectorAll('.tab-pane').forEach(pane => {
        if (pane.id === `tab-${tabId}`) {
            pane.classList.add('active');
        } else {
            pane.classList.remove('active');
        }
    });

    if (tabId === 'history') {
        loadHistory();
    }
}

// Dark/Light Theme Toggle
function initTheme() {
    const toggleBtn = document.getElementById('themeToggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const currentTheme = document.body.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.body.setAttribute('data-theme', newTheme);
        });
    }
}

// Fetch Biomarker Schema dynamically
async function fetchFeatureSchema() {
    const container = document.getElementById('proteinFieldsContainer');
    try {
        const apiUrl = window.location.origin + '/api/feature-schema';
        const res = await fetch(apiUrl);
        const data = await res.json();

        if (data.success) {
            featureSchema = data.proteins;
            renderProteinFields(featureSchema);
        } else {
            if (container) container.innerHTML = '<p class="error">Failed to load biomarker schema.</p>';
        }
    } catch (err) {
        if (container) container.innerHTML = '<p class="error">Unable to connect to backend server.</p>';
    }
}

function renderProteinFields(proteins) {
    const container = document.getElementById('proteinFieldsContainer');
    if (!container) return;
    let html = '';

    proteins.forEach(p => {
        html += `
            <div style="background: rgba(15, 23, 42, 0.4); padding: 8px 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);">
                <label for="prot_${p}" style="font-size: 11px; font-weight: 700; color: var(--accent-blue); display: block; margin-bottom: 4px;">${p}</label>
                <input type="number" step="any" id="prot_${p}" name="${p}" placeholder="0.0" class="form-control-custom" style="padding: 6px 8px; font-size: 12px;" value="0">
            </div>
        `;
    });

    container.innerHTML = html;
}

// Auto-fill sample patient data
function autoFillSampleData() {
    document.getElementById('patient_name').value = "Sample Patient (John Doe)";
    document.getElementById('gender').value = "Male";
    document.getElementById('dob').value = "1978-05-15"; // Chronological Age ~48

    // Pre-fill top sample protein intensities
    const sampleValues = {
        "DNAJB9": 145200.0,
        "PRKAA2": 85000.0,
        "ACP3": 32000.0,
        "UQCRH": 112000.0,
        "SIRT3": 45000.0,
        "ACTN4": 98000.0,
        "ENO2": 67000.0,
        "ALG14": 54000.0
    };

    featureSchema.forEach(p => {
        const input = document.getElementById(`prot_${p}`);
        if (input) {
            input.value = sampleValues[p] || (Math.random() * 50000 + 10000).toFixed(1);
        }
    });
}

// Single Prediction Form Submit
function initFormSubmit() {
    const form = document.getElementById('predictionForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const patientName = document.getElementById('patient_name').value || "Anonymous Patient";
        const gender = document.getElementById('gender').value;
        const dob = document.getElementById('dob').value;

        const proteinInputs = {};
        featureSchema.forEach(p => {
            const inputEl = document.getElementById(`prot_${p}`);
            const val = inputEl ? (parseFloat(inputEl.value) || 0.0) : 0.0;
            proteinInputs[p] = val;
        });

        try {
            const apiUrl = window.location.origin + '/api/predict/';
            const res = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    patient_name: patientName,
                    gender: gender,
                    dob: dob,
                    protein_inputs: proteinInputs
                })
            });

            const data = await res.json();
            if (data.data) {
                displayPredictionResult(data.data);
            } else if (data.predicted_biological_age || data.predicted_age) {
                displayPredictionResult(data);
            } else {
                alert("Prediction Error: " + (data.error || data.message || "Server processing failed."));
            }
        } catch (err) {
            console.error("Predict Error:", err);
            alert("Connection Notice: " + (err.message || "Failed to reach server. Please ensure Django server is running."));
        }
    });
}

function displayPredictionResult(res) {
    currentPredictionId = res.id;

    const resultCard = document.getElementById('resultCard');
    if (resultCard) resultCard.style.display = 'block';

    // Show the full-width SHAP section
    const shapSection = document.getElementById('shapSection');
    if (shapSection) shapSection.style.display = 'block';

    document.getElementById('resChronoAge').innerText = res.chronological_age.toFixed(1);
    document.getElementById('resPredAge').innerText = res.predicted_biological_age.toFixed(1);

    const badge = document.getElementById('resultBadge');
    badge.innerText = res.risk_category;
    let badgeClass = res.badge_class || 'badge-normal';
    if (!badgeClass.startsWith('badge-')) badgeClass = 'badge-' + badgeClass;
    badge.className = `badge-custom ${badgeClass}`;

    const riskBanner = document.getElementById('riskBanner');
    riskBanner.innerHTML = `<i data-lucide="info"></i> <span>${res.risk_description}</span>`;
    if (window.lucide) lucide.createIcons();

    // Render SHAP chart + table
    if (typeof renderShapChart === 'function') {
        renderShapChart(res.top_shap_contributions);
    }

    // Setup Download Report Button
    const btnDownload = document.getElementById('btnDownloadReport');
    if (btnDownload) {
        btnDownload.onclick = () => {
            window.open(`/api/download-report/${res.id}`, '_blank');
        };
    }

    // Scroll to SHAP section for full visibility
    if (shapSection) {
        setTimeout(() => {
            shapSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 300);
    }
}

// History & Database Search
async function loadHistory(query = '') {
    const tbody = document.getElementById('historyTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;"><div class="spinner"></div> Loading History...</td></tr>';

    try {
        const apiUrl = window.location.origin + `/api/history?q=${encodeURIComponent(query)}`;
        const res = await fetch(apiUrl);
        const data = await res.json();

        if (data.success) {
            renderHistoryTable(data.data);
        }
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; color: #f43f5e;">Failed to load prediction history.</td></tr>';
    }
}

function renderHistoryTable(records) {
    const tbody = document.getElementById('historyTableBody');
    if (!tbody) return;

    if (records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; color: #94a3b8;">No prediction records found.</td></tr>';
        return;
    }

    let html = '';
    records.forEach(r => {
        let badgeClass = 'badge-normal';
        if (r.risk_category.toLowerCase().includes('healthy') || r.risk_category.toLowerCase().includes('young') || r.age_difference <= -3.0) {
            badgeClass = 'badge-healthy';
        } else if (r.risk_category.toLowerCase().includes('accelerated') || r.age_difference >= 4.0) {
            badgeClass = 'badge-accelerated';
        }

        html += `
            <tr>
                <td>#${r.id}</td>
                <td><strong>${r.patient_name}</strong></td>
                <td><span style="text-transform: capitalize;">${r.gender}</span></td>
                <td>${r.dob || 'N/A'}</td>
                <td>${r.chronological_age.toFixed(1)} yrs</td>
                <td style="color: var(--accent-blue); font-weight: 700;">${r.predicted_age.toFixed(1)} yrs</td>
                <td><strong style="color: ${r.age_difference > 0 ? '#f43f5e' : '#10b981'};">${r.age_difference > 0 ? '+' : ''}${r.age_difference.toFixed(1)} yrs</strong></td>
                <td><span class="badge-custom ${badgeClass}">${r.risk_category}</span></td>
                <td style="font-size: 12px; color: var(--text-secondary);">${r.created_at}</td>
                <td>
                    <div style="display: flex; gap: 6px;">
                        <button class="btn-custom btn-secondary-custom" style="padding: 4px 10px; font-size: 12px;" onclick="window.open('/api/download-report/${r.id}', '_blank')">
                            <i data-lucide="file-text"></i> PDF
                        </button>
                        <button class="btn-custom btn-secondary-custom" style="padding: 4px 8px; font-size: 12px; color: #f43f5e;" onclick="deleteHistoryRecord(${r.id})">
                            <i data-lucide="trash-2"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
    if (window.lucide) lucide.createIcons();
}

function initHistorySearch() {
    const input = document.getElementById('historySearchInput');
    if (input) {
        input.addEventListener('input', (e) => {
            loadHistory(e.target.value);
        });
    }
}

async function deleteHistoryRecord(id) {
    if (!confirm(`Are you sure you want to delete prediction record #${id}?`)) return;

    try {
        const apiUrl = window.location.origin + `/api/history/${id}`;
        const res = await fetch(apiUrl, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            loadHistory();
        }
    } catch (err) {
        alert("Failed to delete record.");
    }
}

// Batch Upload Handler
function initBatchUpload() {
    const fileInput = document.getElementById('batchFileInput');
    if (!fileInput) return;

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch(window.location.origin + '/api/predict/batch/', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            if (data.success && data.results) {
                renderBatchResults(data.results);
            } else {
                alert("Batch Upload Error: " + (data.error || "Failed to process CSV cohort."));
            }
        } catch (err) {
            alert("Connection error uploading batch file.");
        }
    });
}

function renderBatchResults(rows) {
    const container = document.getElementById('batchResultsContainer');
    const tbody = document.getElementById('batchTableBody');
    const countEl = document.getElementById('batchCount');
    if (!container || !tbody) return;

    countEl.innerText = rows.length;
    container.style.display = 'block';

    let html = '';
    rows.forEach(r => {
        let badgeClass = 'badge-normal';
        if (r.risk_category.toLowerCase().includes('healthy') || r.risk_category.toLowerCase().includes('young') || r.age_difference <= -3.0) {
            badgeClass = 'badge-healthy';
        } else if (r.risk_category.toLowerCase().includes('accelerated') || r.age_difference >= 4.0) {
            badgeClass = 'badge-accelerated';
        }

        html += `
            <tr>
                <td><strong>${r.patient_name}</strong></td>
                <td><span style="text-transform: capitalize;">${r.gender}</span></td>
                <td>${r.chronological_age.toFixed(1)} yrs</td>
                <td style="color: var(--accent-blue); font-weight: 700;">${r.predicted_biological_age.toFixed(1)} yrs</td>
                <td><strong style="color: ${r.age_difference > 0 ? '#f43f5e' : '#10b981'};">${r.age_difference > 0 ? '+' : ''}${r.age_difference.toFixed(1)} yrs</strong></td>
                <td><span class="badge-custom ${badgeClass}">${r.risk_category}</span></td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

