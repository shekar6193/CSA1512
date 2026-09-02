// Main CampusPulse Application Controller
let currentRoleUser = {
    username: "alex.student",
    name: "Alex Rivera",
    role: "STUDENT",
    email: "alex.r@campus.edu"
};

let currentTab = "incidents";
let allRequestsCache = [];
let activeViewingRequestId = null;

document.addEventListener("DOMContentLoaded", async () => {
    // 1. Initialize Lucide icons
    if (window.lucide) lucide.createIcons();

    // 2. Load stored preferences (Language, Theme)
    initTheme();
    const storedLang = localStorage.getItem("campus_lang") || "en";
    const langSelect = document.getElementById("lang-select");
    if (langSelect) langSelect.value = storedLang;
    setLanguage(storedLang);

    // 3. Connect WebSocket for real-time live events
    wsManager.connect();
    wsManager.addListener(handleRealtimeUpdate);

    // 4. Populate building dropdowns & technicians
    await loadInitialLookups();

    // 5. Load Incidents table and KPIs
    await refreshIncidentList();
    await refreshKPIs();

    // 6. Setup Form listeners & AI Triage
    setupTriageListeners();
    setupFormSubmission();
    setupFilterListeners();
    setupEvidenceUpload();

    // 7. Check server health
    API.checkHealth();
});

function handleRealtimeUpdate(event) {
    // Refresh incident table and KPIs silently on incoming live events
    refreshIncidentList(false);
    refreshKPIs();

    // If map tab is active, refresh pins
    if (currentTab === "map") {
        loadMapData();
    }
    // If viewing the updated ticket detail modal, refresh it
    if (activeViewingRequestId && (event.event === "STATUS_UPDATED" || event.event === "TICKET_ASSIGNED")) {
        if (event.data.id === activeViewingRequestId) {
            openRequestDetails(activeViewingRequestId);
        }
    }
}

async function loadInitialLookups() {
    try {
        const buildings = await API.fetchBuildings();
        const buildingSelect = document.getElementById("req-building");
        const filterBuilding = document.getElementById("filter-building");

        if (buildingSelect) {
            buildingSelect.innerHTML = '<option value="">-- Select Campus Building --</option>';
            buildings.forEach(b => {
                buildingSelect.innerHTML += `<option value="${b.name}">${b.name} (${b.zone})</option>`;
            });
        }

        if (filterBuilding) {
            filterBuilding.innerHTML = '<option value="" data-i18n="allBuildings">All Buildings</option>';
            buildings.forEach(b => {
                filterBuilding.innerHTML += `<option value="${b.name}">${b.name}</option>`;
            });
        }
    } catch (e) {
        console.error("Error loading lookups:", e);
    }
}

async function refreshKPIs() {
    try {
        const summary = await API.fetchAnalyticsSummary();
        updateSlaMetrics(summary);
    } catch (e) {
        console.error("Error refreshing KPIs:", e);
    }
}

async function refreshIncidentList(showLoading = true) {
    const tableBody = document.getElementById("incidents-table-body");
    const countBadge = document.getElementById("table-results-count");

    if (showLoading && tableBody) {
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-gray-500"><div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div> Loading campus incidents...</td></tr>`;
    }

    const filters = {
        category: document.getElementById("filter-category")?.value,
        status: document.getElementById("filter-status")?.value,
        priority: document.getElementById("filter-priority")?.value,
        building_name: document.getElementById("filter-building")?.value,
        search: document.getElementById("search-input")?.value,
        emergency_only: document.getElementById("filter-emergency")?.checked
    };

    try {
        const requests = await API.fetchRequests(filters);
        allRequestsCache = requests;

        if (countBadge) countBadge.textContent = `${requests.length} Requests Found`;

        if (!tableBody) return;

        if (requests.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-12 text-gray-400 font-medium">No service requests match the selected criteria.</td></tr>`;
            return;
        }

        tableBody.innerHTML = requests.map(req => {
            const isEmergency = req.is_emergency || req.priority === "EMERGENCY" || req.priority === "CRITICAL";
            
            let statusBadgeClass = "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300";
            if (req.status === "SUBMITTED") statusBadgeClass = "bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-200 dark:border-blue-800";
            if (req.status === "TRIAGED") statusBadgeClass = "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800";
            if (req.status === "ASSIGNED") statusBadgeClass = "bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 border border-purple-200 dark:border-purple-800";
            if (req.status === "IN_PROGRESS") statusBadgeClass = "bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800 animate-pulse";
            if (req.status === "RESOLVED") statusBadgeClass = "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800";
            if (req.status === "CLOSED") statusBadgeClass = "bg-gray-200 text-gray-800 dark:bg-gray-800 dark:text-gray-400";
            if (req.status === "REJECTED") statusBadgeClass = "bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200 dark:border-rose-800";

            let priorityBadgeClass = "bg-gray-100 text-gray-700";
            if (req.priority === "LOW") priorityBadgeClass = "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";
            if (req.priority === "MEDIUM") priorityBadgeClass = "bg-blue-100 text-blue-800 dark:bg-blue-900/60 dark:text-blue-200";
            if (req.priority === "HIGH") priorityBadgeClass = "bg-orange-100 text-orange-800 dark:bg-orange-900/60 dark:text-orange-200";
            if (req.priority === "CRITICAL" || req.priority === "EMERGENCY") priorityBadgeClass = "bg-red-100 text-red-800 dark:bg-red-900/80 dark:text-red-200 font-bold animate-pulse";

            const timeFormatted = new Date(req.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ", " + new Date(req.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' });

            return `
                <tr class="hover:bg-slate-50/70 dark:hover:bg-slate-800/50 transition-colors border-b border-gray-100 dark:border-gray-800 ${isEmergency ? 'bg-red-50/30 dark:bg-red-950/20' : ''}">
                    <td class="py-3.5 px-4 font-mono text-xs font-bold text-blue-600 dark:text-blue-400 whitespace-nowrap">
                        ${req.ticket_code}
                        ${isEmergency ? '<span class="ml-1 inline-block w-2 h-2 rounded-full bg-red-500 animate-ping" title="Emergency"></span>' : ''}
                    </td>
                    <td class="py-3.5 px-4">
                        <div class="font-bold text-sm text-gray-900 dark:text-gray-100">${req.title}</div>
                        <div class="text-xs text-gray-500 dark:text-gray-400 truncate max-w-xs mt-0.5">${req.description}</div>
                    </td>
                    <td class="py-3.5 px-4 text-xs font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                            ${req.category}
                        </span>
                    </td>
                    <td class="py-3.5 px-4 text-xs text-gray-600 dark:text-gray-300">
                        <div class="font-medium">${req.building_name}</div>
                        <div class="text-[11px] text-gray-400">${req.floor_room || req.location}</div>
                    </td>
                    <td class="py-3.5 px-4 whitespace-nowrap">
                        <span class="px-2.5 py-0.5 rounded-full text-xs font-bold ${priorityBadgeClass}">
                            ${req.priority}
                        </span>
                    </td>
                    <td class="py-3.5 px-4 whitespace-nowrap">
                        <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold ${statusBadgeClass}">
                            ${req.status}
                        </span>
                    </td>
                    <td class="py-3.5 px-4 text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                        ${timeFormatted}
                    </td>
                    <td class="py-3.5 px-4 whitespace-nowrap text-right">
                        <div class="flex items-center justify-end gap-1.5">
                            <button onclick="openRequestDetails(${req.id})" class="px-2.5 py-1 rounded-lg text-xs font-bold bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900 transition">
                                Manage
                            </button>
                            ${isStaffOrAdmin() ? `
                                <button onclick="openQuickStatusModal(${req.id})" class="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800" title="Quick Status Update">
                                    <i data-lucide="refresh-cw" class="w-4 h-4"></i>
                                </button>
                            ` : ''}
                        </div>
                    </td>
                </tr>
            `;
        }).join("");

        if (window.lucide) lucide.createIcons();
    } catch (e) {
        console.error("Error refreshing request list:", e);
        if (tableBody) tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-red-500">Failed to load requests from server.</td></tr>`;
    }
}

function setupFilterListeners() {
    ["filter-category", "filter-status", "filter-priority", "filter-building"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("change", () => refreshIncidentList());
    });

    const searchInput = document.getElementById("search-input");
    if (searchInput) {
        let timer = null;
        searchInput.addEventListener("input", () => {
            clearTimeout(timer);
            timer = setTimeout(() => refreshIncidentList(), 250);
        });
    }

    const emergCheckbox = document.getElementById("filter-emergency");
    if (emergCheckbox) {
        emergCheckbox.addEventListener("change", () => refreshIncidentList());
    }
}

function switchTab(tab) {
    currentTab = tab;

    document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.classList.remove("border-blue-600", "text-blue-600", "dark:text-blue-400", "font-bold");
        btn.classList.add("border-transparent", "text-gray-500", "dark:text-gray-400");
    });

    const targetContent = document.getElementById(`tab-content-${tab}`);
    const targetBtn = document.getElementById(`tab-btn-${tab}`);

    if (targetContent) targetContent.classList.remove("hidden");
    if (targetBtn) {
        targetBtn.classList.remove("border-transparent", "text-gray-500", "dark:text-gray-400");
        targetBtn.classList.add("border-blue-600", "text-blue-600", "dark:text-blue-400", "font-bold");
    }

    if (tab === "map") {
        setTimeout(() => {
            initCampusMap();
            if (campusMap) campusMap.invalidateSize();
            loadMapData();
        }, 100);
    } else if (tab === "analytics") {
        setTimeout(() => loadAnalyticsCharts(), 100);
    }
}

function setRole(username) {
    const roleMap = {
        "alex.student": { name: "Alex Rivera", role: "STUDENT", email: "alex.r@campus.edu", label: "Student Reporter" },
        "dr.chen": { name: "Dr. Elena Chen", role: "FACULTY", email: "echen@campus.edu", label: "Faculty / Researcher" },
        "tech.dave": { name: "Dave Miller", role: "TECHNICIAN", email: "dmiller@facilities.campus.edu", label: "Lead Technician" },
        "sec.rodriguez": { name: "Officer Carlos Rodriguez", role: "SECURITY", email: "crodriguez@security.campus.edu", label: "Campus Security Officer" },
        "admin.clara": { name: "Clara Oswald", role: "ADMIN", email: "admin@campus.edu", label: "Operations Admin" }
    };

    if (roleMap[username]) {
        currentRoleUser = { ...roleMap[username], username };
        const labelEl = document.getElementById("active-user-badge");
        if (labelEl) labelEl.textContent = `${currentRoleUser.name} (${currentRoleUser.role})`;

        showToast("User Context Switched", `Active as ${currentRoleUser.name} [${currentRoleUser.role}]`, "info");
        refreshIncidentList();
    }
}

function isStaffOrAdmin() {
    return ["TECHNICIAN", "SECURITY", "ADMIN"].includes(currentRoleUser.role);
}

// Modal Handlers
function openNewRequestModal() {
    const modal = document.getElementById("create-request-modal");
    if (modal) {
        modal.classList.remove("hidden");
        // Autofill reporter name and email
        const repName = document.getElementById("req-reporter-name");
        const repEmail = document.getElementById("req-reporter-email");
        if (repName) repName.value = currentRoleUser.name;
        if (repEmail) repEmail.value = currentRoleUser.email;
        resetTriageBox();
    }
}

function closeNewRequestModal() {
    const modal = document.getElementById("create-request-modal");
    if (modal) modal.classList.add("hidden");
}

function setupFormSubmission() {
    const form = document.getElementById("create-request-form");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const submitBtn = document.getElementById("req-submit-btn");
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `<span class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span> Submitting...`;
        }

        const title = document.getElementById("req-title").value.trim();
        const category = document.getElementById("req-category").value;
        const building = document.getElementById("req-building").value;
        const room = document.getElementById("req-room").value.trim();
        const locationText = document.getElementById("req-location").value.trim() || `${building}, ${room}`;
        const priority = document.getElementById("req-priority").value;
        const description = document.getElementById("req-desc").value.trim();
        const lat = parseFloat(document.getElementById("req-lat").value) || null;
        const lng = parseFloat(document.getElementById("req-lng").value) || null;
        const evidenceUrl = document.getElementById("req-evidence-url").value || null;

        const payload = {
            title,
            category,
            building_name: building,
            floor_room: room,
            location: locationText,
            priority,
            description,
            latitude: lat,
            longitude: lng,
            reporter_name: currentRoleUser.name,
            reporter_email: currentRoleUser.email,
            reporter_role: currentRoleUser.role,
            evidence_url: evidenceUrl
        };

        try {
            const created = await API.createRequest(payload);
            closeNewRequestModal();
            form.reset();
            document.getElementById("evidence-preview-container")?.classList.add("hidden");
            document.getElementById("picked-coords-badge")?.classList.add("hidden");

            showToast(
                "Request Created Successfully!",
                `Ticket #${created.ticket_code} logged and dispatched to ${created.assigned_team || 'Facilities'}.`,
                "success"
            );

            await refreshIncidentList();
            await refreshKPIs();
        } catch (err) {
            alert("Failed to submit request: " + err.message);
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = `Submit Service Request`;
            }
        }
    });
}

function setupEvidenceUpload() {
    const fileInput = document.getElementById("req-evidence-file");
    const previewContainer = document.getElementById("evidence-preview-container");
    const previewImg = document.getElementById("evidence-preview-img");
    const urlHidden = document.getElementById("req-evidence-url");

    if (!fileInput) return;

    fileInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        try {
            const res = await API.uploadEvidence(file);
            if (urlHidden) urlHidden.value = res.file_url;
            if (previewImg) previewImg.src = res.file_url;
            if (previewContainer) previewContainer.classList.remove("hidden");
        } catch (err) {
            alert("File upload failed: " + err.message);
        }
    });
}

// Request Details & Audit Trail Modal
async function openRequestDetails(id) {
    activeViewingRequestId = id;
    const modal = document.getElementById("request-details-modal");
    if (!modal) return;

    modal.classList.remove("hidden");

    try {
        const req = await API.fetchRequestById(id);
        const technicians = await API.fetchTechnicians();

        document.getElementById("detail-ticket-code").textContent = req.ticket_code;
        document.getElementById("detail-title").textContent = req.title;
        document.getElementById("detail-desc").textContent = req.description;
        document.getElementById("detail-category").textContent = req.category;
        document.getElementById("detail-building").textContent = req.building_name;
        document.getElementById("detail-location").textContent = req.location;
        document.getElementById("detail-status").textContent = req.status;
        document.getElementById("detail-priority").textContent = req.priority;
        document.getElementById("detail-reporter").textContent = `${req.reporter_name} (${req.reporter_role}) • ${req.reporter_email}`;
        document.getElementById("detail-assigned").textContent = req.assigned_to ? `${req.assigned_to} (${req.assigned_team || 'General'})` : "Unassigned";
        document.getElementById("detail-sla").textContent = `${req.sla_hours} Hours (Target SLA)`;

        // AI Triage Box in details
        const aiBox = document.getElementById("detail-ai-box");
        if (aiBox) {
            aiBox.innerHTML = `
                <div class="p-3 rounded-lg bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 text-xs">
                    <div class="font-bold text-blue-900 dark:text-blue-300 flex items-center justify-between">
                        <span>🤖 AI NLP Triage Diagnosis (${Math.round(req.ai_confidence * 100)}% Confidence)</span>
                        <span class="font-bold ${req.is_emergency ? 'text-red-600' : 'text-blue-600'}">${req.is_emergency ? 'EMERGENCY PROTOCOL' : 'STANDARD'}</span>
                    </div>
                    <p class="mt-1 text-gray-700 dark:text-gray-300">${req.ai_triage_notes || 'Routine triage assigned.'}</p>
                </div>
            `;
        }

        // Attached Evidence Photo
        const evidenceContainer = document.getElementById("detail-evidence-container");
        if (evidenceContainer) {
            if (req.evidence_url) {
                evidenceContainer.innerHTML = `
                    <div class="mt-3">
                        <label class="text-xs font-bold text-gray-500 uppercase">Attached Photo Evidence</label>
                        <a href="${req.evidence_url}" target="_blank" class="block mt-1">
                            <img src="${req.evidence_url}" class="rounded-lg max-h-48 border border-gray-200 object-cover shadow-sm hover:opacity-90" alt="Incident Evidence">
                        </a>
                    </div>
                `;
            } else {
                evidenceContainer.innerHTML = "";
            }
        }

        // Staff Controls (Assign & Status Update)
        const staffControls = document.getElementById("detail-staff-controls");
        if (staffControls) {
            if (isStaffOrAdmin()) {
                staffControls.classList.remove("hidden");
                
                // Status Select
                const statusSelect = document.getElementById("detail-status-select");
                if (statusSelect) statusSelect.value = req.status;

                // Technician Assignment Select
                const assignSelect = document.getElementById("detail-assign-select");
                if (assignSelect) {
                    assignSelect.innerHTML = `<option value="">-- Assign Technician --</option>`;
                    technicians.forEach(t => {
                        const selected = t.full_name === req.assigned_to ? "selected" : "";
                        assignSelect.innerHTML += `<option value="${t.full_name}" data-team="${t.department}" ${selected}>${t.full_name} (${t.department} - ${t.active_assigned_tasks} tasks)</option>`;
                    });
                }
            } else {
                staffControls.classList.add("hidden");
            }
        }

        // Render Audit Logs Timeline
        const auditTimeline = document.getElementById("detail-audit-timeline");
        if (auditTimeline && req.audit_logs) {
            auditTimeline.innerHTML = req.audit_logs.map(log => {
                const logTime = new Date(log.timestamp).toLocaleString([], { dateStyle: "short", timeStyle: "short" });
                return `
                    <div class="relative pl-6 pb-4 border-l-2 border-blue-200 dark:border-blue-900 last:border-l-0">
                        <div class="timeline-dot bg-blue-600"></div>
                        <div class="flex items-center justify-between text-xs">
                            <span class="font-bold text-gray-900 dark:text-gray-100">${log.actor_name} <span class="text-gray-400 font-normal">(${log.actor_role})</span></span>
                            <span class="text-gray-400">${logTime}</span>
                        </div>
                        <div class="text-xs text-blue-600 dark:text-blue-400 font-semibold mt-0.5">${log.action}: ${log.new_status}</div>
                        ${log.notes ? `<p class="text-xs text-gray-600 dark:text-gray-400 mt-1 bg-gray-50 dark:bg-gray-800/60 p-2 rounded">${log.notes}</p>` : ''}
                    </div>
                `;
            }).join("");
        }
    } catch (e) {
        console.error("Error loading request details:", e);
    }
}

function closeRequestDetails() {
    activeViewingRequestId = null;
    const modal = document.getElementById("request-details-modal");
    if (modal) modal.classList.add("hidden");
}

async function saveStatusChangeFromModal() {
    if (!activeViewingRequestId) return;

    const statusSelect = document.getElementById("detail-status-select");
    const notesInput = document.getElementById("detail-resolution-notes");

    const newStatus = statusSelect?.value;
    const notes = notesInput?.value.trim() || null;

    try {
        await API.updateStatus(activeViewingRequestId, {
            status: newStatus,
            resolution_notes: notes,
            actor_name: currentRoleUser.name,
            actor_role: currentRoleUser.role
        });

        showToast("Status Updated", `Ticket #${activeViewingRequestId} status changed to ${newStatus}`, "success");
        openRequestDetails(activeViewingRequestId);
        refreshIncidentList();
        refreshKPIs();
    } catch (e) {
        alert("Failed to update status: " + e.message);
    }
}

async function saveAssignmentFromModal() {
    if (!activeViewingRequestId) return;

    const assignSelect = document.getElementById("detail-assign-select");
    const selectedOption = assignSelect?.selectedOptions[0];
    const techName = assignSelect?.value;
    const techTeam = selectedOption?.getAttribute("data-team") || "Facilities Rapid Response";

    if (!techName) {
        alert("Please select a technician.");
        return;
    }

    try {
        await API.assignRequest(activeViewingRequestId, {
            assigned_to: techName,
            assigned_team: techTeam,
            actor_name: currentRoleUser.name,
            actor_role: currentRoleUser.role
        });

        showToast("Assigned", `Ticket assigned to ${techName}`, "success");
        openRequestDetails(activeViewingRequestId);
        refreshIncidentList();
    } catch (e) {
        alert("Failed to assign ticket: " + e.message);
    }
}

// Quick Status Modal
let quickStatusId = null;
function openQuickStatusModal(id) {
    quickStatusId = id;
    const modal = document.getElementById("quick-status-modal");
    if (modal) modal.classList.remove("hidden");
}

function closeQuickStatusModal() {
    quickStatusId = null;
    const modal = document.getElementById("quick-status-modal");
    if (modal) modal.classList.add("hidden");
}

async function submitQuickStatus() {
    if (!quickStatusId) return;

    const newStatus = document.getElementById("quick-status-select")?.value;
    const notes = document.getElementById("quick-status-notes")?.value.trim() || null;

    try {
        await API.updateStatus(quickStatusId, {
            status: newStatus,
            resolution_notes: notes,
            actor_name: currentRoleUser.name,
            actor_role: currentRoleUser.role
        });

        closeQuickStatusModal();
        showToast("Status Updated", `Ticket moved to ${newStatus}`, "success");
        refreshIncidentList();
        refreshKPIs();
    } catch (e) {
        alert("Failed to update status: " + e.message);
    }
}

// Theme Switcher
function initTheme() {
    const isDark = localStorage.getItem("campus_dark") === "true";
    if (isDark) document.documentElement.classList.add("dark");
}

function toggleDarkMode() {
    document.documentElement.classList.toggle("dark");
    const isDark = document.documentElement.classList.contains("dark");
    localStorage.setItem("campus_dark", isDark);
}

function toggleHighContrast() {
    document.documentElement.classList.toggle("high-contrast");
}
