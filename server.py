from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import json

app = FastAPI()
active_viewers = []  # Stores connected dashboard browsers

html_dashboard = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>IT Telemetry Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #ffffff; padding: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background-color: #1e1e1e; padding: 20px; border-radius: 10px; border-left: 5px solid #00ffcc; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        h1 { color: #00ffcc; text-align: center; margin-bottom: 30px; }
        .metric { font-size: 1.2rem; margin: 10px 0; display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding-bottom: 5px; }
        .value { font-weight: bold; color: #00ffcc; }
        .warning { color: #ff4757; font-weight: bold; }
    </style>
</head>
<body>
    <h1>IT Telemetry Helpdesk</h1>
    <div class="grid" id="dashboard-grid">
        <!-- Live PCs will appear here automatically -->
    </div>

    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws/viewer`);
        const grid = document.getElementById('dashboard-grid');
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            const hostId = 'card-' + data.hostname.replace(/[^a-zA-Z0-9]/g, '-');

            let card = document.getElementById(hostId);
            if (!card) {
                card = document.createElement('div');
                card.id = hostId;
                card.className = 'card';
                grid.appendChild(card);
            }

            const tempClass = data.cpu_temp_c > 85 ? 'warning' : 'value';

            card.innerHTML = `
                <h2>💻 ${data.hostname}</h2>
                <div class="metric"><span>CPU Temp:</span> <span class="${tempClass}">${data.cpu_temp_c}°C</span></div>
                <div class="metric"><span>RAM Usage:</span> <span class="value">${data.ram_usage_percent}%</span></div>
                <div class="metric"><span>BIOS Ver:</span> <span style="color:#aaa; font-size: 0.9rem">${data.bios_version}</span></div>
            `;
        };
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return html_dashboard

@app.websocket("/ws/viewer")
async def viewer_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_viewers.append(websocket)
    try:
        while True:
            await websocket.receive_text() 
    except Exception:
        active_viewers.remove(websocket)

@app.websocket("/ws/telemetry")
async def telemetry_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()

            for viewer in active_viewers:
                try:
                    await viewer.send_text(data)
                except Exception:
                    pass
    except Exception as e:
        print(f"Agent disconnected: {e}")