// WebSocket Manager and Live Campus Notification Dispatcher
class WebSocketManager {
    constructor() {
        this.socket = null;
        this.reconnectInterval = 3000;
        this.listeners = [];
        this.isConnected = false;
    }

    connect() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/events`;

        try {
            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => {
                this.isConnected = true;
                this.updateCloudStatusBadge(true);
                console.log("[CampusPulse WebSocket] Connected to real-time event stream.");
            };

            this.socket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleIncomingEvent(message);
                } catch (e) {
                    console.error("Error parsing WS message:", e);
                }
            };

            this.socket.onclose = () => {
                this.isConnected = false;
                this.updateCloudStatusBadge(false);
                console.warn("[CampusPulse WebSocket] Disconnected. Retrying in 3s...");
                setTimeout(() => this.connect(), this.reconnectInterval);
            };

            this.socket.onerror = (err) => {
                this.isConnected = false;
                this.updateCloudStatusBadge(false);
                this.socket.close();
            };
        } catch (e) {
            console.error("WebSocket connection error:", e);
            setTimeout(() => this.connect(), this.reconnectInterval);
        }
    }

    addListener(callback) {
        this.listeners.push(callback);
    }

    handleIncomingEvent(message) {
        // Trigger all custom callbacks
        this.listeners.forEach(cb => cb(message));

        // Display Visual Toast Notification
        if (message.event === "REQUEST_CREATED") {
            const isEmergency = message.data.is_emergency;
            showToast(
                isEmergency ? "🚨 CRITICAL EMERGENCY REPORTED" : "📋 New Service Request Logged",
                `${message.data.ticket_code}: ${message.data.title} (${message.data.building_name})`,
                isEmergency ? "emergency" : "info"
            );
        } else if (message.event === "STATUS_UPDATED") {
            showToast(
                "⚡ Status Updated",
                `${message.data.ticket_code} moved to ${message.data.new_status} by ${message.data.actor_name}`,
                "success"
            );
        } else if (message.event === "TICKET_ASSIGNED") {
            showToast(
                "👤 Technician Assigned",
                `${message.data.ticket_code} assigned to ${message.data.assigned_to}`,
                "info"
            );
        }
    }

    updateCloudStatusBadge(connected) {
        const badge = document.getElementById("cloud-status-badge");
        const text = document.getElementById("cloud-status-text");
        const dot = document.getElementById("cloud-status-dot");
        if (badge && text && dot) {
            if (connected) {
                text.textContent = "Cloud Live";
                dot.className = "pulse-beacon";
                badge.className = "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800";
            } else {
                text.textContent = "Reconnecting...";
                dot.className = "w-2 h-2 rounded-full bg-amber-500 animate-ping";
                badge.className = "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800";
            }
        }
    }
}

// Global Toast Dispatcher
function showToast(title, body, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    let borderClass = "border-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100";
    let icon = "info";

    if (type === "emergency") {
        borderClass = "border-red-500 bg-red-50 dark:bg-red-950/90 text-red-900 dark:text-red-100 ai-glow-emergency";
        icon = "alert-triangle";
    } else if (type === "success") {
        borderClass = "border-emerald-500 bg-emerald-50 dark:bg-emerald-950/90 text-emerald-900 dark:text-emerald-100";
        icon = "check-circle";
    }

    toast.className = `p-4 rounded-xl shadow-xl border-l-4 ${borderClass} flex items-start gap-3 transform transition-all duration-300 translate-y-2 opacity-0 animate-slide-in max-w-sm pointer-events-auto`;
    toast.innerHTML = `
        <div class="mt-0.5">
            <i data-lucide="${icon}" class="w-5 h-5 ${type === 'emergency' ? 'text-red-600 animate-pulse' : 'text-blue-600'}"></i>
        </div>
        <div class="flex-1 text-sm">
            <h4 class="font-bold">${title}</h4>
            <p class="text-xs mt-0.5 opacity-90">${body}</p>
        </div>
        <button onclick="this.parentElement.remove()" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-sm font-bold">&times;</button>
    `;

    container.appendChild(toast);
    if (window.lucide) lucide.createIcons();

    setTimeout(() => {
        toast.style.opacity = "1";
        toast.style.transform = "translateY(0)";
    }, 10);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(8px)";
        setTimeout(() => toast.remove(), 300);
    }, type === "emergency" ? 8000 : 5000);
}

const wsManager = new WebSocketManager();
