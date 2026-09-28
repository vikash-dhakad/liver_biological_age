/**
 * ═══════════════════════════════════════════════════════════════
 * LIVER BIOLOGICAL AGE PREDICTOR — App Logic
 * Client-side prediction using exported Ridge Regression weights.
 * ═══════════════════════════════════════════════════════════════
 */

// ─── Model Weights (exported from train_model.py) ──────────────────
const MODEL = {
  featureNames: ["ALB", "ALT", "AST", "GGT", "ALP", "APOE", "APOC3", "AFP", "FGA", "SERPINC1", "CRP", "TGFB1", "IGF1", "GDF15", "SHBG", "FERRITIN", "CYP3A4", "SOD2", "HMGB1", "PCNA"],
  featureMeans: [4.252906, 26.626406, 27.6805, 35.960556, 82.015156, 4.407175, 12.306038, 3.777606, 319.878375, 97.602356, 3.165775, 21.0964, 177.704056, 768.704994, 48.265437, 129.847694, 76.767956, 140.803356, 5.318931, 5.69155],
  featureStds: [0.485774, 8.497269, 7.255407, 13.428335, 18.375409, 1.243711, 2.984282, 1.709887, 64.522564, 14.152832, 2.022379, 5.637485, 82.503279, 280.633586, 15.287074, 49.923277, 15.490434, 35.668249, 1.945995, 2.144728],
  coefficients: [-1.444046, -0.687826, 0.446966, 1.202184, 0.939055, -0.84263, 0.95782, 0.731652, 1.380851, -0.856829, 1.22696, 1.268986, -1.658329, 2.320195, 1.167853, 1.039778, -1.551943, -1.280583, 1.686341, -1.441581],
  intercept: 52.112875,
  featureImportance: [
    { name: "GDF15", importance: 2.320195, coefficient: 2.320195, direction: "increases_age" },
    { name: "HMGB1", importance: 1.686341, coefficient: 1.686341, direction: "increases_age" },
    { name: "IGF1", importance: 1.658329, coefficient: -1.658329, direction: "decreases_age" },
    { name: "CYP3A4", importance: 1.551943, coefficient: -1.551943, direction: "decreases_age" },
    { name: "ALB", importance: 1.444046, coefficient: -1.444046, direction: "decreases_age" },
    { name: "PCNA", importance: 1.441581, coefficient: -1.441581, direction: "decreases_age" },
    { name: "FGA", importance: 1.380851, coefficient: 1.380851, direction: "increases_age" },
    { name: "SOD2", importance: 1.280583, coefficient: -1.280583, direction: "decreases_age" },
    { name: "TGFB1", importance: 1.268986, coefficient: 1.268986, direction: "increases_age" },
    { name: "CRP", importance: 1.22696, coefficient: 1.22696, direction: "increases_age" },
    { name: "GGT", importance: 1.202184, coefficient: 1.202184, direction: "increases_age" },
    { name: "SHBG", importance: 1.167853, coefficient: 1.167853, direction: "increases_age" },
    { name: "FERRITIN", importance: 1.039778, coefficient: 1.039778, direction: "increases_age" },
    { name: "APOC3", importance: 0.95782, coefficient: 0.95782, direction: "increases_age" },
    { name: "ALP", importance: 0.939055, coefficient: 0.939055, direction: "increases_age" },
    { name: "SERPINC1", importance: 0.856829, coefficient: -0.856829, direction: "decreases_age" },
    { name: "APOE", importance: 0.84263, coefficient: -0.84263, direction: "decreases_age" },
    { name: "AFP", importance: 0.731652, coefficient: 0.731652, direction: "increases_age" },
    { name: "ALT", importance: 0.687826, coefficient: -0.687826, direction: "decreases_age" },
    { name: "AST", importance: 0.446966, coefficient: 0.446966, direction: "increases_age" }
  ],
  ageGroupMeans: {
    "20-30": { "ALB": 4.76, "ALT": 31.63, "AST": 24.61, "GGT": 24.71, "ALP": 67.5, "APOE": 5.28, "APOC3": 10.16, "AFP": 2.7, "FGA": 258.15, "SERPINC1": 108.68, "CRP": 1.51, "TGFB1": 15.62, "IGF1": 264.58, "GDF15": 431.7, "SHBG": 36.77, "FERRITIN": 88.82, "CYP3A4": 92.59, "SOD2": 175.43, "HMGB1": 3.28, "PCNA": 7.75 },
    "30-40": { "ALB": 4.53, "ALT": 29.82, "AST": 25.52, "GGT": 27.67, "ALP": 71.52, "APOE": 5.04, "APOC3": 10.73, "AFP": 2.93, "FGA": 275.39, "SERPINC1": 105.35, "CRP": 1.9, "TGFB1": 17.41, "IGF1": 235.61, "GDF15": 539.57, "SHBG": 38.84, "FERRITIN": 101.79, "CYP3A4": 87.8, "SOD2": 161.99, "HMGB1": 3.88, "PCNA": 7.08 },
    "40-50": { "ALB": 4.4, "ALT": 27.84, "AST": 26.55, "GGT": 30.91, "ALP": 76.24, "APOE": 4.78, "APOC3": 11.44, "AFP": 3.31, "FGA": 302.31, "SERPINC1": 101.83, "CRP": 2.34, "TGFB1": 19.46, "IGF1": 212.13, "GDF15": 644.1, "SHBG": 43.44, "FERRITIN": 112.24, "CYP3A4": 82.94, "SOD2": 155.84, "HMGB1": 4.51, "PCNA": 6.31 },
    "50-60": { "ALB": 4.22, "ALT": 26.15, "AST": 27.74, "GGT": 36.97, "ALP": 83.14, "APOE": 4.32, "APOC3": 12.63, "AFP": 3.79, "FGA": 319.79, "SERPINC1": 96.47, "CRP": 3.17, "TGFB1": 21.22, "IGF1": 166.78, "GDF15": 785.31, "SHBG": 49.49, "FERRITIN": 133.04, "CYP3A4": 75.71, "SOD2": 141.7, "HMGB1": 5.32, "PCNA": 5.51 },
    "60-70": { "ALB": 3.99, "ALT": 24.86, "AST": 29.38, "GGT": 41.12, "ALP": 88.83, "APOE": 4.02, "APOC3": 13.47, "AFP": 4.22, "FGA": 351.51, "SERPINC1": 91.99, "CRP": 4.05, "TGFB1": 23.83, "IGF1": 135.4, "GDF15": 925.95, "SHBG": 54.77, "FERRITIN": 145.74, "CYP3A4": 69.04, "SOD2": 123.81, "HMGB1": 6.29, "PCNA": 4.63 },
    "70-85": { "ALB": 3.78, "ALT": 21.59, "AST": 31.02, "GGT": 48.6, "ALP": 97.09, "APOE": 3.39, "APOC3": 14.5, "AFP": 4.96, "FGA": 385.38, "SERPINC1": 86.84, "CRP": 5.18, "TGFB1": 26.59, "IGF1": 86.93, "GDF15": 1122.51, "SHBG": 62.24, "FERRITIN": 171.57, "CYP3A4": 60.2, "SOD2": 105.76, "HMGB1": 7.51, "PCNA": 3.61 }
  }
};

// ─── Protein Metadata ──────────────────────────────────────────
const PROTEINS = [
  { name: "ALB", fullName: "Albumin", unit: "g/dL", normalLow: 3.5, normalHigh: 5.5, direction: "down" },
  { name: "ALT", fullName: "Alanine Aminotransferase", unit: "U/L", normalLow: 7, normalHigh: 56, direction: "down" },
  { name: "AST", fullName: "Aspartate Aminotransferase", unit: "U/L", normalLow: 10, normalHigh: 40, direction: "up" },
  { name: "GGT", fullName: "Gamma-Glutamyl Transferase", unit: "U/L", normalLow: 9, normalHigh: 48, direction: "up" },
  { name: "ALP", fullName: "Alkaline Phosphatase", unit: "U/L", normalLow: 44, normalHigh: 147, direction: "up" },
  { name: "APOE", fullName: "Apolipoprotein E", unit: "mg/dL", normalLow: 2.7, normalHigh: 6.7, direction: "down" },
  { name: "APOC3", fullName: "Apolipoprotein C-III", unit: "mg/dL", normalLow: 5, normalHigh: 18, direction: "up" },
  { name: "AFP", fullName: "Alpha-Fetoprotein", unit: "ng/mL", normalLow: 0, normalHigh: 10, direction: "up" },
  { name: "FGA", fullName: "Fibrinogen Alpha", unit: "mg/dL", normalLow: 200, normalHigh: 400, direction: "up" },
  { name: "SERPINC1", fullName: "Antithrombin III", unit: "%", normalLow: 80, normalHigh: 120, direction: "down" },
  { name: "CRP", fullName: "C-Reactive Protein", unit: "mg/L", normalLow: 0, normalHigh: 3, direction: "up" },
  { name: "TGFB1", fullName: "TGF-Beta 1", unit: "ng/mL", normalLow: 5, normalHigh: 35, direction: "up" },
  { name: "IGF1", fullName: "Insulin-like Growth Factor 1", unit: "ng/mL", normalLow: 50, normalHigh: 350, direction: "down" },
  { name: "GDF15", fullName: "Growth Differentiation Factor 15", unit: "pg/mL", normalLow: 200, normalHigh: 1200, direction: "up" },
  { name: "SHBG", fullName: "Sex Hormone Binding Globulin", unit: "nmol/L", normalLow: 20, normalHigh: 80, direction: "up" },
  { name: "FERRITIN", fullName: "Ferritin", unit: "ng/mL", normalLow: 20, normalHigh: 250, direction: "up" },
  { name: "CYP3A4", fullName: "CYP3A4 Activity Index", unit: "index", normalLow: 50, normalHigh: 100, direction: "down" },
  { name: "SOD2", fullName: "Superoxide Dismutase 2", unit: "U/mL", normalLow: 90, normalHigh: 200, direction: "down" },
  { name: "HMGB1", fullName: "HMGB1 Protein", unit: "ng/mL", normalLow: 1, normalHigh: 10, direction: "up" },
  { name: "PCNA", fullName: "Proliferating Cell Nuclear Antigen", unit: "ng/mL", normalLow: 2, normalHigh: 10, direction: "down" }
];

// ─── Chart instances (for cleanup) ─────────────────────────────
let charts = {};

// ─── Sample Data Profiles ──────────────────────────────────────
const SAMPLE_PROFILES = {
  young: { name: "Aarav Sharma", mobile: "9876543210", address: "B-12, Green Park, New Delhi", age: 28, values: { ALB: 4.9, ALT: 30, AST: 22, GGT: 20, ALP: 62, APOE: 5.5, APOC3: 9, AFP: 2.0, FGA: 240, SERPINC1: 112, CRP: 0.8, TGFB1: 14, IGF1: 290, GDF15: 350, SHBG: 32, FERRITIN: 70, CYP3A4: 95, SOD2: 185, HMGB1: 2.5, PCNA: 8.5 } },
  average: { name: "Rajesh Kumar", mobile: "9811223344", address: "Flat 402, Sunshine Apartments, Mumbai", age: 50, values: { ALB: 4.2, ALT: 26, AST: 28, GGT: 35, ALP: 82, APOE: 4.3, APOC3: 12, AFP: 3.5, FGA: 310, SERPINC1: 98, CRP: 2.8, TGFB1: 20, IGF1: 175, GDF15: 750, SHBG: 48, FERRITIN: 125, CYP3A4: 78, SOD2: 145, HMGB1: 5.0, PCNA: 5.8 } },
  old: { name: "Suresh Verma", mobile: "9717654321", address: "75, Civil Lines, Jaipur", age: 72, values: { ALB: 3.6, ALT: 20, AST: 33, GGT: 55, ALP: 102, APOE: 3.2, APOC3: 15, AFP: 5.5, FGA: 400, SERPINC1: 82, CRP: 6.0, TGFB1: 28, IGF1: 75, GDF15: 1200, SHBG: 65, FERRITIN: 180, CYP3A4: 55, SOD2: 100, HMGB1: 8.0, PCNA: 3.0 } }
};

// ─── DOB → Exact Age Calculation ──────────────────────────────
function calculateAgeFromDOB(dobString) {
  const dob = new Date(dobString);
  const today = new Date();
  let years = today.getFullYear() - dob.getFullYear();
  let months = today.getMonth() - dob.getMonth();
  let days = today.getDate() - dob.getDate();

  if (days < 0) {
    months--;
    const prevMonth = new Date(today.getFullYear(), today.getMonth(), 0);
    days += prevMonth.getDate();
  }
  if (months < 0) {
    years--;
    months += 12;
  }
  const exactAge = years + (months / 12) + (days / 365.25);
  return { years, months, days, exactAge: Math.round(exactAge * 100) / 100 };
}

function onDOBChange() {
  const dobInput = document.getElementById('dob-input');
  const display = document.getElementById('calculated-age-display');
  if (!dobInput.value) {
    display.textContent = '';
    return;
  }
  const age = calculateAgeFromDOB(dobInput.value);
  if (age.exactAge < 0 || age.exactAge > 120) {
    display.textContent = '';
    return;
  }
  display.textContent = `Age: ${age.years}y ${age.months}m ${age.days}d (${age.exactAge} yrs)`;
}

function dobFromAge(targetAge) {
  const today = new Date();
  const dob = new Date(today.getFullYear() - targetAge, today.getMonth(), today.getDate());
  return dob.toISOString().split('T')[0];
}

// ─── Initialize ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  buildProteinGrid();
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('dob-input').setAttribute('max', today);
  document.getElementById('dob-input').addEventListener('input', onDOBChange);
});

function buildProteinGrid() {
  const grid = document.getElementById('protein-grid');
  grid.innerHTML = '';

  PROTEINS.forEach(p => {
    const card = document.createElement('div');
    card.className = 'protein-input-card';
    card.id = `card-${p.name}`;

    const trendArrow = p.direction === 'up'
      ? '<span class="trend-arrow up">&#x2191; with age</span>'
      : '<span class="trend-arrow down">&#x2193; with age</span>';

    card.innerHTML = `
      <div class="protein-input-header">
        <span class="protein-name">${p.name} ${trendArrow}</span>
        <span class="protein-unit">${p.unit}</span>
      </div>
      <div class="protein-full-name">${p.fullName}</div>
      <div class="protein-input-row">
        <input type="number" id="input-${p.name}" step="any"
               placeholder="${p.normalLow} – ${p.normalHigh}"
               oninput="onProteinInput('${p.name}')">
      </div>
      <div class="protein-range">
        <span class="range-dot normal"></span>
        Normal: ${p.normalLow} – ${p.normalHigh} ${p.unit}
      </div>
    `;
    grid.appendChild(card);
  });
}

function onProteinInput(name) {
  const protein = PROTEINS.find(p => p.name === name);
  const input = document.getElementById(`input-${name}`);
  const card = document.getElementById(`card-${name}`);
  const val = parseFloat(input.value);

  card.classList.remove('abnormal-low', 'abnormal-high');
  if (!isNaN(val)) {
    if (val < protein.normalLow) card.classList.add('abnormal-low');
    else if (val > protein.normalHigh) card.classList.add('abnormal-high');
  }
}

// ─── Load Sample Data ──────────────────────────────────────────
function loadSampleData(profile) {
  const data = SAMPLE_PROFILES[profile];
  document.getElementById('patient-name').value = data.name;
  document.getElementById('patient-mobile').value = data.mobile;
  document.getElementById('patient-address').value = data.address;
  document.getElementById('dob-input').value = dobFromAge(data.age);
  onDOBChange();

  PROTEINS.forEach(p => {
    const input = document.getElementById(`input-${p.name}`);
    input.value = data.values[p.name];
    onProteinInput(p.name);
  });
}

// ─── Prediction Engine ─────────────────────────────────────────
function predictAge() {
  const nameInput = document.getElementById('patient-name');
  const dobInput = document.getElementById('dob-input');
  const mobileInput = document.getElementById('patient-mobile');
  const addressInput = document.getElementById('patient-address');

  if (!nameInput.value.trim()) {
    alert('Please enter Patient Name!');
    nameInput.focus();
    return;
  }
  if (!dobInput.value) {
    alert('Please select Date of Birth!');
    dobInput.focus();
    return;
  }
  if (!mobileInput.value.trim()) {
    alert('Please enter Mobile Number!');
    mobileInput.focus();
    return;
  }
  if (!addressInput.value.trim()) {
    alert('Please enter Patient Address!');
    addressInput.focus();
    return;
  }

  // Collect protein values
  const values = {};
  let allFilled = true;

  PROTEINS.forEach(p => {
    const input = document.getElementById(`input-${p.name}`);
    const val = parseFloat(input.value);
    if (isNaN(val)) {
      allFilled = false;
      input.style.borderColor = 'rgba(244, 63, 94, 0.5)';
      setTimeout(() => { input.style.borderColor = ''; }, 2000);
    } else {
      values[p.name] = val;
    }
  });

  if (!allFilled) {
    alert('Please fill in all 20 protein biomarker values!');
    return;
  }

  const ageData = calculateAgeFromDOB(dobInput.value);
  const chronoAge = ageData.exactAge;

  // Update Printable Patient Pathology Report Header
  document.getElementById('report-patient-name').textContent = nameInput.value.trim();
  document.getElementById('report-dob').textContent = `${dobInput.value} (${ageData.years}y ${ageData.months}m)`;
  document.getElementById('report-age').textContent = `${chronoAge} years`;
  document.getElementById('report-mobile').textContent = mobileInput.value.trim();
  document.getElementById('report-address').textContent = addressInput.value.trim();
  document.getElementById('report-generated-date').textContent = `Report Date: ${new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}`;

  // Normalize features and compute prediction
  let prediction = MODEL.intercept;
  const contributions = [];

  MODEL.featureNames.forEach((name, i) => {
    const rawVal = values[name];
    const normalized = (rawVal - MODEL.featureMeans[i]) / MODEL.featureStds[i];
    const contribution = MODEL.coefficients[i] * normalized;
    prediction += contribution;

    contributions.push({
      name: name,
      rawValue: rawVal,
      normalized: normalized,
      contribution: contribution,
      coefficient: MODEL.coefficients[i]
    });
  });

  // Clamp prediction to reasonable range
  prediction = Math.max(18, Math.min(95, prediction));
  const predictedAge = Math.round(prediction * 10) / 10;
  const ageGap = Math.round((predictedAge - chronoAge) * 10) / 10;

  // Show results
  showResults(predictedAge, chronoAge, ageGap, contributions, values);
}

// ─── Display Results ───────────────────────────────────────────
function showResults(predictedAge, chronoAge, ageGap, contributions, values) {
  const resultsSection = document.getElementById('results-section');
  resultsSection.classList.add('visible');

  // Scroll to results
  setTimeout(() => {
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 100);

  // Animate predicted age
  animateNumber('predicted-age-value', predictedAge, 1);

  // Chronological age
  document.getElementById('chrono-age-display').textContent = chronoAge;

  // Age gap
  const gapEl = document.getElementById('age-gap-display');
  const gapSign = ageGap > 0 ? '+' : '';
  gapEl.textContent = `${gapSign}${ageGap} yrs`;
  gapEl.className = 'gap-value ' + (ageGap > 3 ? 'gap-positive' : ageGap < -3 ? 'gap-negative' : 'gap-neutral');

  // Age category
  const catEl = document.getElementById('age-category');
  if (ageGap < -3) {
    catEl.className = 'age-category younger';
    catEl.innerHTML = '&#x2728; Liver is YOUNGER than expected';
  } else if (ageGap > 3) {
    catEl.className = 'age-category older';
    catEl.innerHTML = '&#x26A0; Liver is OLDER than expected';
  } else {
    catEl.className = 'age-category normal-age';
    catEl.innerHTML = '&#x2705; Liver age is NORMAL for your age';
  }

  // Render all charts
  renderContributionChart(contributions);
  renderRadarChart(values, chronoAge);
  renderImportanceChart();
  renderSummaryChart(values);
  renderBiomarkerList(values);
  renderInsights(values, predictedAge, chronoAge, ageGap, contributions);
}

// ─── Animated Counter ──────────────────────────────────────────
function animateNumber(elementId, target, decimals) {
  const el = document.getElementById(elementId);
  const duration = 1200;
  const start = performance.now();
  const startVal = 0;

  function tick(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    // Ease out cubic
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = startVal + (target - startVal) * eased;
    el.textContent = current.toFixed(decimals);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// ─── Chart: Protein Contributions ──────────────────────────────
function renderContributionChart(contributions) {
  if (charts.contribution) charts.contribution.destroy();

  // Sort by absolute contribution
  const sorted = [...contributions].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
  const top12 = sorted.slice(0, 12);

  const ctx = document.getElementById('contribution-chart').getContext('2d');
  charts.contribution = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: top12.map(c => c.name),
      datasets: [{
        label: 'Age Contribution (years)',
        data: top12.map(c => Math.round(c.contribution * 100) / 100),
        backgroundColor: top12.map(c =>
          c.contribution > 0 ? 'rgba(244, 63, 94, 0.7)' : 'rgba(52, 211, 153, 0.7)'
        ),
        borderColor: top12.map(c =>
          c.contribution > 0 ? 'rgba(244, 63, 94, 1)' : 'rgba(52, 211, 153, 1)'
        ),
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15, 22, 41, 0.95)',
          titleColor: '#e8ecf4',
          bodyColor: '#8892a8',
          borderColor: 'rgba(56, 189, 148, 0.3)',
          borderWidth: 1,
          cornerRadius: 8,
          callbacks: {
            label: (ctx) => {
              const val = ctx.raw;
              return val > 0
                ? `Adds +${val.toFixed(2)} years (ages liver)`
                : `Removes ${val.toFixed(2)} years (rejuvenates)`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#8892a8', font: { family: 'JetBrains Mono', size: 11 } },
          title: { display: true, text: 'Years ← rejuvenating | aging →', color: '#5a6478', font: { size: 10 } }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#e8ecf4', font: { family: 'Inter', size: 11, weight: 600 } }
        }
      }
    }
  });
}

// ─── Chart: Radar (vs age-matched reference) ──────────────────
function renderRadarChart(values, chronoAge) {
  if (charts.radar) charts.radar.destroy();

  // Find the reference age group
  let refGroup = '40-50';
  if (chronoAge < 30) refGroup = '20-30';
  else if (chronoAge < 40) refGroup = '30-40';
  else if (chronoAge < 50) refGroup = '40-50';
  else if (chronoAge < 60) refGroup = '50-60';
  else if (chronoAge < 70) refGroup = '60-70';
  else refGroup = '70-85';

  const refMeans = MODEL.ageGroupMeans[refGroup];

  // Select 8 key proteins for radar readability
  const radarProteins = ['ALB', 'GGT', 'IGF1', 'GDF15', 'CRP', 'CYP3A4', 'SOD2', 'FGA'];
  const labels = radarProteins;

  // Normalize both user and reference to percentage of normal range
  const userData = radarProteins.map(name => {
    const p = PROTEINS.find(pr => pr.name === name);
    const range = p.normalHigh - p.normalLow;
    return range > 0 ? ((values[name] - p.normalLow) / range) * 100 : 50;
  });

  const refData = radarProteins.map(name => {
    const p = PROTEINS.find(pr => pr.name === name);
    const range = p.normalHigh - p.normalLow;
    return range > 0 ? ((refMeans[name] - p.normalLow) / range) * 100 : 50;
  });

  const ctx = document.getElementById('radar-chart').getContext('2d');
  charts.radar = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Your Values',
          data: userData,
          backgroundColor: 'rgba(56, 189, 148, 0.15)',
          borderColor: 'rgba(56, 189, 148, 0.8)',
          borderWidth: 2,
          pointBackgroundColor: '#38bd94',
          pointBorderColor: '#fff',
          pointBorderWidth: 1,
          pointRadius: 4
        },
        {
          label: `Reference (${refGroup} yrs)`,
          data: refData,
          backgroundColor: 'rgba(167, 139, 250, 0.1)',
          borderColor: 'rgba(167, 139, 250, 0.5)',
          borderWidth: 1.5,
          borderDash: [4, 4],
          pointBackgroundColor: '#a78bfa',
          pointRadius: 3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#8892a8', font: { family: 'Inter', size: 11 }, usePointStyle: true, pointStyle: 'circle' }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 22, 41, 0.95)',
          titleColor: '#e8ecf4',
          bodyColor: '#8892a8',
          borderColor: 'rgba(56, 189, 148, 0.3)',
          borderWidth: 1,
          cornerRadius: 8
        }
      },
      scales: {
        r: {
          grid: { color: 'rgba(255,255,255,0.06)' },
          angleLines: { color: 'rgba(255,255,255,0.06)' },
          pointLabels: { color: '#e8ecf4', font: { family: 'Inter', size: 11, weight: 600 } },
          ticks: { display: false },
          suggestedMin: 0,
          suggestedMax: 120
        }
      }
    }
  });
}

// ─── Chart: Feature Importance ─────────────────────────────────
function renderImportanceChart() {
  if (charts.importance) charts.importance.destroy();

  const top10 = MODEL.featureImportance.slice(0, 10);

  const ctx = document.getElementById('importance-chart').getContext('2d');
  charts.importance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: top10.map(f => f.name),
      datasets: [{
        label: 'Importance',
        data: top10.map(f => Math.round(f.importance * 1000) / 1000),
        backgroundColor: [
          'rgba(56, 189, 148, 0.7)',
          'rgba(34, 211, 238, 0.7)',
          'rgba(167, 139, 250, 0.7)',
          'rgba(245, 158, 11, 0.7)',
          'rgba(244, 63, 94, 0.7)',
          'rgba(96, 165, 250, 0.7)',
          'rgba(56, 189, 148, 0.5)',
          'rgba(34, 211, 238, 0.5)',
          'rgba(167, 139, 250, 0.5)',
          'rgba(245, 158, 11, 0.5)'
        ],
        borderRadius: 6,
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15, 22, 41, 0.95)',
          titleColor: '#e8ecf4',
          bodyColor: '#8892a8',
          borderColor: 'rgba(56, 189, 148, 0.3)',
          borderWidth: 1,
          cornerRadius: 8,
          callbacks: {
            afterLabel: (ctx) => {
              const item = top10[ctx.dataIndex];
              return item.direction === 'increases_age'
                ? 'Higher → older liver'
                : 'Higher → younger liver';
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#e8ecf4', font: { family: 'Inter', size: 10, weight: 600 }, maxRotation: 45 }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#8892a8', font: { family: 'JetBrains Mono', size: 11 } },
          title: { display: true, text: 'Importance |w|', color: '#5a6478', font: { size: 10 } }
        }
      }
    }
  });
}

// ─── Chart: Biomarker Summary Doughnut ─────────────────────────
function renderSummaryChart(values) {
  if (charts.summary) charts.summary.destroy();

  let normal = 0, borderline = 0, abnormal = 0;
  PROTEINS.forEach(p => {
    const val = values[p.name];
    const range = p.normalHigh - p.normalLow;
    const margin = range * 0.1;
    if (val >= p.normalLow && val <= p.normalHigh) {
      normal++;
    } else if (val >= p.normalLow - margin && val <= p.normalHigh + margin) {
      borderline++;
    } else {
      abnormal++;
    }
  });

  const ctx = document.getElementById('summary-chart').getContext('2d');
  charts.summary = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Normal', 'Borderline', 'Abnormal'],
      datasets: [{
        data: [normal, borderline, abnormal],
        backgroundColor: [
          'rgba(52, 211, 153, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(244, 63, 94, 0.8)'
        ],
        borderColor: [
          'rgba(52, 211, 153, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(244, 63, 94, 1)'
        ],
        borderWidth: 2,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#8892a8',
            font: { family: 'Inter', size: 12 },
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 16
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 22, 41, 0.95)',
          titleColor: '#e8ecf4',
          bodyColor: '#8892a8',
          borderColor: 'rgba(56, 189, 148, 0.3)',
          borderWidth: 1,
          cornerRadius: 8,
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${ctx.raw} / 20 biomarkers`
          }
        }
      }
    }
  });
}

// ─── Biomarker Status List ─────────────────────────────────────
function renderBiomarkerList(values) {
  const container = document.getElementById('biomarker-list');
  container.innerHTML = '';

  PROTEINS.forEach(p => {
    const val = values[p.name];
    const range = p.normalHigh - p.normalLow;
    const margin = range * 0.1;

    let status, statusText;
    if (val >= p.normalLow && val <= p.normalHigh) {
      status = 'normal';
      statusText = 'Normal';
    } else if (val >= p.normalLow - margin && val <= p.normalHigh + margin) {
      status = 'warning';
      statusText = val < p.normalLow ? 'Slightly Low' : 'Slightly High';
    } else {
      status = 'danger';
      statusText = val < p.normalLow ? 'Low' : 'High';
    }

    const item = document.createElement('div');
    item.className = 'biomarker-item';
    item.innerHTML = `
      <div class="biomarker-status-dot status-${status}"></div>
      <div class="biomarker-info">
        <div class="bm-name">${p.name}</div>
        <div class="bm-detail">${statusText} · Range: ${p.normalLow}–${p.normalHigh} ${p.unit}</div>
      </div>
      <div class="biomarker-value" style="color: ${status === 'normal' ? '#34d399' : status === 'warning' ? '#f59e0b' : '#f43f5e'}">${val} ${p.unit}</div>
    `;
    container.appendChild(item);
  });
}

// ─── Health Insights ───────────────────────────────────────────
function renderInsights(values, predictedAge, chronoAge, ageGap, contributions) {
  const container = document.getElementById('insights-list');
  container.innerHTML = '';
  const insights = [];

  // Age gap insight
  if (ageGap < -5) {
    insights.push({ type: 'good', title: 'Excellent Liver Health', text: `Your liver appears ${Math.abs(ageGap).toFixed(1)} years younger than your chronological age. Your protein biomarkers suggest strong liver function and good antioxidant defense.` });
  } else if (ageGap > 5) {
    insights.push({ type: 'bad', title: 'Accelerated Liver Aging', text: `Your liver appears ${ageGap.toFixed(1)} years older than expected. Several biomarkers suggest oxidative stress, inflammation, or reduced synthetic function. Consider lifestyle modifications.` });
  } else {
    insights.push({ type: 'good', title: 'Normal Liver Aging', text: `Your liver age aligns closely with your chronological age (±${Math.abs(ageGap).toFixed(1)} years). Your protein profile is within expected ranges.` });
  }

  // Top contributing proteins
  const sorted = [...contributions].sort((a, b) => b.contribution - a.contribution);
  const topAging = sorted.slice(0, 2);
  const topYoung = sorted.slice(-2).reverse();

  if (topAging[0].contribution > 1) {
    const p = PROTEINS.find(pr => pr.name === topAging[0].name);
    insights.push({ type: 'warn', title: `${topAging[0].name} Driving Age Up`, text: `${p.fullName} (${topAging[0].name}) is the strongest aging driver, adding +${topAging[0].contribution.toFixed(1)} years. ${getProteinAdvice(topAging[0].name, 'high')}` });
  }

  if (topYoung[0].contribution < -1) {
    const p = PROTEINS.find(pr => pr.name === topYoung[0].name);
    insights.push({ type: 'good', title: `${topYoung[0].name} Keeping You Young`, text: `${p.fullName} (${topYoung[0].name}) is a strong protective factor, removing ${topYoung[0].contribution.toFixed(1)} years from your liver age.` });
  }

  // Specific biomarker insights
  if (values.ALB < 3.5) {
    insights.push({ type: 'bad', title: 'Low Albumin', text: 'Low albumin may indicate reduced liver synthetic capacity, malnutrition, or chronic inflammation. This is a key marker of liver function and overall health.' });
  }

  if (values.GGT > 48) {
    insights.push({ type: 'warn', title: 'Elevated GGT', text: 'High GGT suggests oxidative stress or bile duct issues. It is an independent predictor of liver-related morbidity. Consider reducing alcohol intake and checking metabolic health.' });
  }

  if (values.CRP > 3) {
    insights.push({ type: 'warn', title: 'Elevated CRP', text: 'High C-Reactive Protein indicates systemic inflammation, which accelerates liver aging. Anti-inflammatory dietary patterns (Mediterranean diet) and exercise may help.' });
  }

  if (values.IGF1 < 80) {
    insights.push({ type: 'warn', title: 'Low IGF-1', text: 'Low IGF-1 is associated with growth hormone deficiency and metabolic aging. Regular exercise and adequate protein intake support IGF-1 levels.' });
  }

  if (values.SOD2 < 100) {
    insights.push({ type: 'warn', title: 'Low SOD2 (Antioxidant)', text: 'Reduced Superoxide Dismutase 2 means lower antioxidant defense. Oxidative stress accelerates liver cell aging. Antioxidant-rich foods (berries, leafy greens) may support levels.' });
  }

  if (values.GDF15 > 1000) {
    insights.push({ type: 'bad', title: 'High GDF15 (Stress Marker)', text: 'Elevated GDF15 is one of the strongest aging biomarkers. It reflects mitochondrial stress and cellular senescence in the liver. This strongly drives your predicted age up.' });
  }

  if (values.CYP3A4 > 85) {
    insights.push({ type: 'good', title: 'Good Drug Metabolism', text: 'Your CYP3A4 activity index is healthy, indicating good drug metabolism capacity. This is often reduced with aging.' });
  }

  // Render insights
  insights.forEach(insight => {
    const iconSymbol = insight.type === 'good' ? '&#x2714;' : insight.type === 'warn' ? '&#x26A0;' : '&#x2718;';
    const item = document.createElement('div');
    item.className = 'insight-item';
    item.innerHTML = `
      <div class="insight-icon ${insight.type}">${iconSymbol}</div>
      <div class="insight-content">
        <h4>${insight.title}</h4>
        <p>${insight.text}</p>
      </div>
    `;
    container.appendChild(item);
  });
}

// ─── Report Download / Print Functionality ────────────────────
function downloadReport() {
  window.print();
}

function getProteinAdvice(name, direction) {
  const advice = {
    GDF15: 'GDF15 rises with mitochondrial stress. Regular exercise and caloric management may help.',
    HMGB1: 'HMGB1 is an inflammatory mediator. Anti-inflammatory strategies may reduce levels.',
    CRP: 'Consider anti-inflammatory diet, regular exercise, and stress management.',
    GGT: 'Reduce alcohol consumption, manage body weight, and monitor metabolic health.',
    FGA: 'High fibrinogen indicates inflammation. Omega-3 fatty acids and exercise may help.',
    TGFB1: 'Elevated TGF-β1 drives liver fibrosis. Liver health checkups recommended.',
    IGF1: 'Low IGF-1 associated with aging. Exercise and adequate protein intake support levels.',
    ALB: 'Low albumin reflects liver synthetic decline. Nutrition and liver function monitoring advised.',
    CYP3A4: 'Declining drug metabolism. Medication dosing may need adjustment with age.',
    SOD2: 'Low antioxidant defense. Antioxidant-rich diet and supplements may support levels.'
  };
  return advice[name] || 'Discuss with your healthcare provider.';
}
