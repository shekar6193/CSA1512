// Campus GIS Interactive Map & Incident Pin Manager (Leaflet.js)
let campusMap = null;
let buildingLayers = [];
let incidentMarkers = [];
let selectedPinMarker = null;

const CAMPUS_CENTER = [37.7745, -122.4180];
const DEFAULT_ZOOM = 16;

function initCampusMap() {
    const mapContainer = document.getElementById("campus-map");
    if (!mapContainer || campusMap) return;

    campusMap = L.map("campus-map", {
        center: CAMPUS_CENTER,
        zoom: DEFAULT_ZOOM,
        zoomControl: true
    });

    // Clean OpenStreetMap tiles
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://openstreetmap.org">OpenStreetMap</a> | CampusPulse GIS',
        maxZoom: 19
    }).addTo(campusMap);

    // Map click listener for picking new incident location
    campusMap.on("click", (e) => {
        const { lat, lng } = e.latlng;
        setFormLocationCoordinates(lat, lng);
    });

    loadMapData();
}

async function loadMapData() {
    if (!campusMap) return;

    try {
        const [buildings, requests] = await Promise.all([
            API.fetchBuildings(),
            API.fetchRequests()
        ]);

        renderBuildings(buildings);
        renderIncidentPins(requests);
    } catch (e) {
        console.error("Error loading GIS map data:", e);
    }
}

function renderBuildings(buildings) {
    // Clear previous building layers
    buildingLayers.forEach(l => campusMap.removeLayer(l));
    buildingLayers = [];

    buildings.forEach(b => {
        const hasEmergencies = b.active_issues_count > 0;
        const color = hasEmergencies ? "#ef4444" : "#3b82f6";

        const circle = L.circle([b.latitude, b.longitude], {
            color: color,
            fillColor: color,
            fillOpacity: 0.15,
            radius: 50,
            weight: 2
        }).addTo(campusMap);

        circle.bindTooltip(`<b>${b.name}</b><br><span class="text-xs text-gray-500">${b.zone} • ${b.active_issues_count} active tickets</span>`, {
            permanent: false,
            direction: "top"
        });

        circle.on("click", () => {
            selectBuildingForReport(b);
        });

        buildingLayers.push(circle);
    });
}

function renderIncidentPins(requests) {
    // Clear previous pins
    incidentMarkers.forEach(m => campusMap.removeLayer(m));
    incidentMarkers = [];

    requests.forEach(req => {
        if (!req.latitude || !req.longitude) return;

        let pinColor = "#3b82f6"; // Blue (Medium/Low)
        let isEmergency = req.is_emergency || req.priority === "EMERGENCY" || req.priority === "CRITICAL";

        if (req.status === "RESOLVED" || req.status === "CLOSED") {
            pinColor = "#10b981"; // Green
        } else if (isEmergency) {
            pinColor = "#ef4444"; // Red
        } else if (req.priority === "HIGH") {
            pinColor = "#f59e0b"; // Orange
        }

        const iconHtml = `
            <div style="
                background-color: ${pinColor};
                width: ${isEmergency ? '22px' : '18px'};
                height: ${isEmergency ? '22px' : '18px'};
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 2px 6px rgba(0,0,0,0.35);
                ${isEmergency ? 'animation: pulse-ring-emergency 1.2s infinite;' : ''}
            "></div>
        `;

        const customIcon = L.divIcon({
            html: iconHtml,
            className: "custom-incident-pin",
            iconSize: [22, 22],
            iconAnchor: [11, 11]
        });

        const marker = L.marker([req.latitude, req.longitude], { icon: customIcon }).addTo(campusMap);

        const popupContent = `
            <div class="p-1 min-w-[200px]">
                <div class="flex items-center justify-between gap-2 mb-1">
                    <span class="text-xs font-bold text-gray-500">${req.ticket_code}</span>
                    <span class="text-[10px] font-black px-1.5 py-0.5 rounded ${isEmergency ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}">${req.priority}</span>
                </div>
                <h4 class="text-sm font-bold text-gray-900 leading-tight mb-1">${req.title}</h4>
                <p class="text-xs text-gray-600 mb-2">${req.location}</p>
                <div class="flex items-center justify-between pt-1 border-t border-gray-100">
                    <span class="text-xs font-semibold px-2 py-0.5 rounded bg-gray-100 text-gray-800">${req.status}</span>
                    <button onclick="openRequestDetails(${req.id})" class="text-xs font-bold text-blue-600 hover:underline">View Details &rarr;</button>
                </div>
            </div>
        `;

        marker.bindPopup(popupContent);
        incidentMarkers.push(marker);
    });
}

function selectBuildingForReport(building) {
    const buildingSelect = document.getElementById("req-building");
    if (buildingSelect) {
        buildingSelect.value = building.name;
    }
    const locInput = document.getElementById("req-location");
    if (locInput && (!locInput.value || locInput.value === "")) {
        locInput.value = `${building.name}, `;
    }
    setFormLocationCoordinates(building.latitude, building.longitude);
}

function setFormLocationCoordinates(lat, lng) {
    const latInput = document.getElementById("req-lat");
    const lngInput = document.getElementById("req-lng");
    const coordsBadge = document.getElementById("picked-coords-badge");

    if (latInput) latInput.value = lat.toFixed(5);
    if (lngInput) lngInput.value = lng.toFixed(5);

    if (coordsBadge) {
        coordsBadge.textContent = `📍 Selected GPS: ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        coordsBadge.classList.remove("hidden");
    }

    if (campusMap) {
        if (selectedPinMarker) campusMap.removeLayer(selectedPinMarker);
        selectedPinMarker = L.marker([lat, lng]).addTo(campusMap);
        selectedPinMarker.bindTooltip("New Report Location", { permanent: true, direction: "top" }).openTooltip();
    }
}
