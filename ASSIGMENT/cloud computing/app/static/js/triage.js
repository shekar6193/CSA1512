// AI Triage & Real-Time Emergency Classifier UI Component
let triageDebounceTimer = null;

function setupTriageListeners() {
    const titleInput = document.getElementById("req-title");
    const descInput = document.getElementById("req-desc");
    const catSelect = document.getElementById("req-category");

    const triggerTriage = () => {
        clearTimeout(triageDebounceTimer);
        triageDebounceTimer = setTimeout(async () => {
            const title = titleInput?.value.trim() || "";
            const desc = descInput?.value.trim() || "";
            const cat = catSelect?.value || "";

            if (title.length < 3 && desc.length < 5) {
                resetTriageBox();
                return;
            }

            try {
                const box = document.getElementById("ai-triage-card");
                if (box) box.classList.add("opacity-60");

                const result = await API.analyzeTriage({
                    title: title,
                    description: desc,
                    category: cat
                });

                updateTriageUI(result);
            } catch (e) {
                console.error("AI Triage evaluation failed:", e);
            } finally {
                const box = document.getElementById("ai-triage-card");
                if (box) box.classList.remove("opacity-60");
            }
        }, 350);
    };

    if (titleInput) titleInput.addEventListener("input", triggerTriage);
    if (descInput) descInput.addEventListener("input", triggerTriage);
    if (catSelect) catSelect.addEventListener("change", triggerTriage);
}

function updateTriageUI(result) {
    const box = document.getElementById("ai-triage-card");
    const badge = document.getElementById("ai-priority-badge");
    const rationale = document.getElementById("ai-triage-rationale");
    const slaText = document.getElementById("ai-triage-sla");
    const teamText = document.getElementById("ai-triage-team");
    const prioritySelect = document.getElementById("req-priority");
    const catSelect = document.getElementById("req-category");

    if (!box) return;

    box.classList.remove("hidden");

    if (result.is_emergency) {
        box.className = "p-4 rounded-xl border-2 border-red-500 bg-red-50/90 dark:bg-red-950/40 ai-glow-emergency transition-all";
        badge.className = "px-2.5 py-0.5 rounded-full text-xs font-black bg-red-600 text-white animate-pulse";
        badge.textContent = `🚨 ${result.recommended_priority} EMERGENCY (${Math.round(result.confidence_score * 100)}% Confidence)`;
    } else {
        box.className = "p-4 rounded-xl border border-blue-300 dark:border-blue-800 bg-blue-50/80 dark:bg-blue-950/30 ai-glow transition-all";
        badge.className = "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-600 text-white";
        badge.textContent = `🤖 Recommended: ${result.recommended_priority} (${Math.round(result.confidence_score * 100)}% Confidence)`;
    }

    if (rationale) rationale.textContent = result.triage_rationale;
    if (slaText) slaText.textContent = `Target SLA: ${result.suggested_sla_hours} Hours`;
    if (teamText) teamText.textContent = `Auto-Routed To: ${result.suggested_dispatch_team}`;

    // Auto-suggest priority in form if user hasn't explicitly locked it
    if (prioritySelect && (result.is_emergency || prioritySelect.value === "MEDIUM")) {
        prioritySelect.value = result.recommended_priority;
    }

    // Auto-suggest category if currently default/empty
    if (catSelect && (!catSelect.value || catSelect.value === "") && result.recommended_category) {
        catSelect.value = result.recommended_category;
    }
}

function resetTriageBox() {
    const box = document.getElementById("ai-triage-card");
    if (box) box.classList.add("hidden");
}
