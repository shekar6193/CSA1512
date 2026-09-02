// Analytics Visualizations & KPI Charts (Chart.js)
let categoryChartInstance = null;
let priorityChartInstance = null;
let trendChartInstance = null;
let hotspotChartInstance = null;

async function loadAnalyticsCharts() {
    try {
        const [summary, hotspots, trends] = await Promise.all([
            API.fetchAnalyticsSummary(),
            API.fetchBuildingHotspots(),
            API.fetchTrends()
        ]);

        renderCategoryChart(summary.category_breakdown);
        renderPriorityChart(summary.priority_breakdown);
        renderTrendsChart(trends);
        renderHotspotsChart(hotspots);
        updateSlaMetrics(summary);
    } catch (e) {
        console.error("Error loading analytics charts:", e);
    }
}

function renderCategoryChart(categoryData) {
    const ctx = document.getElementById("chart-categories");
    if (!ctx) return;

    if (categoryChartInstance) categoryChartInstance.destroy();

    const labels = Object.keys(categoryData);
    const data = Object.values(categoryData);

    categoryChartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
                    "#8b5cf6", "#ec4899", "#06b6d4", "#64748b"
                ],
                borderWidth: 2,
                borderColor: document.documentElement.classList.contains("dark") ? "#111827" : "#ffffff"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "right",
                    labels: {
                        color: document.documentElement.classList.contains("dark") ? "#cbd5e1" : "#475569",
                        boxWidth: 12,
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

function renderPriorityChart(priorityData) {
    const ctx = document.getElementById("chart-priorities");
    if (!ctx) return;

    if (priorityChartInstance) priorityChartInstance.destroy();

    const labels = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "EMERGENCY"];
    const values = labels.map(l => priorityData[l] || 0);

    priorityChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Incidents Count",
                data: values,
                backgroundColor: ["#94a3b8", "#3b82f6", "#f59e0b", "#f97316", "#ef4444"],
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1, color: document.documentElement.classList.contains("dark") ? "#94a3b8" : "#64748b" },
                    grid: { color: document.documentElement.classList.contains("dark") ? "#1f2937" : "#f1f5f9" }
                },
                x: {
                    ticks: { color: document.documentElement.classList.contains("dark") ? "#94a3b8" : "#64748b" },
                    grid: { display: false }
                }
            }
        }
    });
}

function renderTrendsChart(trends) {
    const ctx = document.getElementById("chart-trends");
    if (!ctx) return;

    if (trendChartInstance) trendChartInstance.destroy();

    trendChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: trends.days,
            datasets: [
                {
                    label: "Reported",
                    data: trends.reported,
                    borderColor: "#3b82f6",
                    backgroundColor: "rgba(59, 130, 246, 0.1)",
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2
                },
                {
                    label: "Resolved",
                    data: trends.resolved,
                    borderColor: "#10b981",
                    backgroundColor: "transparent",
                    tension: 0.35,
                    borderWidth: 2
                },
                {
                    label: "Emergencies",
                    data: trends.emergencies,
                    borderColor: "#ef4444",
                    backgroundColor: "transparent",
                    borderDash: [4, 4],
                    tension: 0.35,
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "top",
                    labels: { color: document.documentElement.classList.contains("dark") ? "#cbd5e1" : "#475569" }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: document.documentElement.classList.contains("dark") ? "#94a3b8" : "#64748b" },
                    grid: { color: document.documentElement.classList.contains("dark") ? "#1f2937" : "#f1f5f9" }
                },
                x: {
                    ticks: { color: document.documentElement.classList.contains("dark") ? "#94a3b8" : "#64748b" },
                    grid: { display: false }
                }
            }
        }
    });
}

function renderHotspotsChart(hotspots) {
    const ctx = document.getElementById("chart-hotspots");
    if (!ctx) return;

    if (hotspotChartInstance) hotspotChartInstance.destroy();

    const topHotspots = hotspots.slice(0, 6);
    const labels = topHotspots.map(h => h.building_name);
    const issues = topHotspots.map(h => h.total_issues);

    hotspotChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Total Incidents Logged",
                data: issues,
                backgroundColor: "#8b5cf6",
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { stepSize: 1, color: document.documentElement.classList.contains("dark") ? "#94a3b8" : "#64748b" },
                    grid: { color: document.documentElement.classList.contains("dark") ? "#1f2937" : "#f1f5f9" }
                },
                y: {
                    ticks: { color: document.documentElement.classList.contains("dark") ? "#94a3b8" : "#64748b" },
                    grid: { display: false }
                }
            }
        }
    });
}

function updateSlaMetrics(summary) {
    const mttrEl = document.getElementById("kpi-mttr-val");
    const slaEl = document.getElementById("kpi-sla-val");
    const totalEl = document.getElementById("kpi-total-val");
    const activeEl = document.getElementById("kpi-active-val");
    const emergEl = document.getElementById("kpi-emerg-val");

    if (mttrEl) mttrEl.textContent = `${summary.mean_time_to_resolution_hours}h`;
    if (slaEl) slaEl.textContent = `${summary.sla_compliance_rate}%`;
    if (totalEl) totalEl.textContent = summary.total_requests;
    if (activeEl) activeEl.textContent = summary.active_requests;
    if (emergEl) emergEl.textContent = summary.emergency_requests;
}
