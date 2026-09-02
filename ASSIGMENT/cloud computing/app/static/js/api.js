// REST API Client for CampusPulse Cloud Platform
const API_BASE = "/api/v1";

const API = {
    async fetchRequests(filters = {}) {
        const params = new URLSearchParams();
        if (filters.category) params.append("category", filters.category);
        if (filters.status) params.append("status", filters.status);
        if (filters.priority) params.append("priority", filters.priority);
        if (filters.building_name) params.append("building_name", filters.building_name);
        if (filters.search) params.append("search", filters.search);
        if (filters.emergency_only) params.append("emergency_only", "true");

        const response = await fetch(`${API_BASE}/requests?${params.toString()}`);
        if (!response.ok) throw new Error("Failed to fetch requests");
        return await response.json();
    },

    async fetchRequestById(id) {
        const response = await fetch(`${API_BASE}/requests/${id}`);
        if (!response.ok) throw new Error("Failed to fetch request details");
        return await response.json();
    },

    async createRequest(data) {
        const response = await fetch(`${API_BASE}/requests`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to create service request");
        }
        return await response.json();
    },

    async updateStatus(id, statusData) {
        const response = await fetch(`${API_BASE}/staff/requests/${id}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(statusData)
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to update status");
        }
        return await response.json();
    },

    async assignRequest(id, assignData) {
        const response = await fetch(`${API_BASE}/staff/requests/${id}/assign`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(assignData)
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to assign ticket");
        }
        return await response.json();
    },

    async deleteRequest(id) {
        const response = await fetch(`${API_BASE}/requests/${id}`, {
            method: "DELETE"
        });
        if (!response.ok) throw new Error("Failed to delete request");
        return true;
    },

    async fetchBuildings() {
        const response = await fetch(`${API_BASE}/requests/buildings`);
        if (!response.ok) throw new Error("Failed to fetch campus buildings");
        return await response.json();
    },

    async fetchAnalyticsSummary() {
        const response = await fetch(`${API_BASE}/analytics/summary`);
        if (!response.ok) throw new Error("Failed to fetch analytics summary");
        return await response.json();
    },

    async fetchBuildingHotspots() {
        const response = await fetch(`${API_BASE}/analytics/building-hotspots`);
        if (!response.ok) throw new Error("Failed to fetch building hotspots");
        return await response.json();
    },

    async fetchTrends() {
        const response = await fetch(`${API_BASE}/analytics/trends`);
        if (!response.ok) throw new Error("Failed to fetch trends");
        return await response.json();
    },

    async analyzeTriage(payload) {
        const response = await fetch(`${API_BASE}/triage/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error("Failed to run AI triage");
        return await response.json();
    },

    async uploadEvidence(file) {
        const formData = new FormData();
        formData.append("file", file);
        const response = await fetch(`${API_BASE}/requests/upload-evidence`, {
            method: "POST",
            body: formData
        });
        if (!response.ok) throw new Error("Failed to upload evidence");
        return await response.json();
    },

    async fetchTechnicians() {
        const response = await fetch(`${API_BASE}/staff/technicians`);
        if (!response.ok) throw new Error("Failed to fetch technicians");
        return await response.json();
    },

    async fetchDemoUsers() {
        const response = await fetch(`${API_BASE}/auth/users`);
        if (!response.ok) throw new Error("Failed to fetch users");
        return await response.json();
    },

    async checkHealth() {
        const response = await fetch(`${API_BASE}/health`);
        if (!response.ok) return { status: "degraded", database_connected: false };
        return await response.json();
    }
};
