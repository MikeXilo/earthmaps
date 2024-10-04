// Initialize the map and set its view to a default location
var map = L.map('map').setView([31.37, -97.95], 13);

// Add OpenStreetMap tiles as the base layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Add drawing tools to the map (polygon drawing enabled)
var drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

// Restore control buttons for drawing, zoom, and layer management
var drawControl = new L.Control.Draw({
    edit: {
        featureGroup: drawnItems
    },
    draw: {
        polygon: true,   // Enable polygon drawing
        polyline: false,
        rectangle: false,
        circle: false,
        marker: false,
        circlemarker: false
    }
});
map.addControl(drawControl);

var lastDrawnPolygon = null;

// Event listener for when a shape (polygon) is drawn
map.on(L.Draw.Event.CREATED, function (event) {
    var layer = event.layer;
    drawnItems.addLayer(layer);
    lastDrawnPolygon = layer.toGeoJSON();

    document.getElementById('status').innerText = "Polygon drawn. Ready for clipping.";
});

function clipSRTM() {
    if (!lastDrawnPolygon) {
        alert("Please draw a polygon on the map first.");
        return;
    }

    document.getElementById('status').innerText = "Clipping SRTM data. Please wait...";

    fetch('http://127.0.0.1:8000/clip_srtm', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ polygon: lastDrawnPolygon }),
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById('status').innerText = "SRTM clipping completed! Download the clipped file.";
            alert(`Clipped SRTM saved successfully: ${data.output_file}`);
        })
        .catch((error) => {
            document.getElementById('status').innerText = "Error during SRTM clipping.";
            alert('Error during SRTM clipping: ' + error.message);
        });
}
