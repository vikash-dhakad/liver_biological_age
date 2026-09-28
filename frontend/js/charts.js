/**
 * Chart.js Integration Engine
 * ============================
 * Renders interactive SHAP biomarker contribution bar charts
 * and populates the SHAP data table.
 */

let shapChartInstance = null;

function renderShapChart(shapData) {
    const canvas = document.getElementById('shapChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Show top 8 biomarkers — fits perfectly in one screen
    const top8 = shapData.slice(0, 8);
    const labels = top8.map(item => item.feature);
    const values = top8.map(item => item.shap_value || item.importance || 0.0);
    const bgColors = values.map(val =>
        val > 0 ? 'rgba(244, 63, 94, 0.85)' : 'rgba(16, 185, 129, 0.85)'
    );
    const borderColors = values.map(val =>
        val > 0 ? '#f43f5e' : '#10b981'
    );

    if (shapChartInstance) {
        shapChartInstance.destroy();
    }

    shapChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'SHAP Contribution (Years)',
                data: values,
                backgroundColor: bgColors,
                borderColor: borderColors,
                borderWidth: 2,
                borderRadius: 6,
                borderSkipped: false,
                barPercentage: 0.7,
                categoryPercentage: 0.85
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: { left: 5, right: 20, top: 10, bottom: 10 }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#f8fafc',
                    bodyColor: '#f8fafc',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    callbacks: {
                        title: function(items) {
                            return `Biomarker: ${items[0].label}`;
                        },
                        label: function(context) {
                            const val = context.raw;
                            const sign = val > 0 ? '+' : '';
                            const dir = val > 0 ? '↑ Accelerates Aging' : '↓ Protective / Anti-Aging';
                            return [
                                ` Impact: ${sign}${val.toFixed(2)} Years`,
                                ` ${dir}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.06)',
                        drawTicks: false
                    },
                    ticks: {
                        color: '#94a3b8',
                        font: { size: 12 },
                        callback: function(val) {
                            return (val > 0 ? '+' : '') + val.toFixed(2) + ' yrs';
                        }
                    },
                    title: {
                        display: true,
                        text: '← Younger (Protective)          Effect on Biological Age (Years)          Older (Accelerated) →',
                        color: '#64748b',
                        font: { size: 11, weight: '600' }
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: {
                        color: '#e2e8f0',
                        font: { size: 13, weight: '700' },
                        padding: 8
                    }
                }
            }
        }
    });

    // Also populate the SHAP data table
    renderShapTable(shapData.slice(0, 10));
}

function renderShapTable(shapData) {
    const tbody = document.getElementById('shapTableBody');
    if (!tbody) return;

    let html = '';
    shapData.forEach((item) => {
        const val = item.shap_value || item.importance || 0.0;
        const valColor = val > 0 ? '#f43f5e' : '#10b981';
        const tagBg = val > 0 ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)';
        const tagColor = val > 0 ? '#fb7185' : '#34d399';
        const dirText = val > 0 ? '↑ Accelerates Aging' : '↓ Protective';
        const sign = val > 0 ? '+' : '';

        html += `
            <tr>
                <td><strong>${item.feature}</strong> <span style="font-size: 11px; color: var(--text-secondary); display: block;">${item.full_name || ''}</span></td>
                <td style="color: ${valColor}; font-weight: 700;">${sign}${val.toFixed(2)} yrs</td>
                <td><span style="background: ${tagBg}; color: ${tagColor}; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">${dirText}</span></td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}
