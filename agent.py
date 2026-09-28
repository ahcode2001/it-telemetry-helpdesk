import asyncio
import websockets
import json
import psutil
import wmi
import platform

w = wmi.WMI()

def get_hardware_telemetry():
    bios = w.Win32_BIOS()[0]

    cpu_usage = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()

    try:
        temps = w.MSAcpi_ThermalZoneTemperature()
        cpu_temp = round((temps[0].CurrentTemperature / 10.0) - 273.15, 1) if temps else "N/A"
    except Exception:
        cpu_temp = "N/A"

    return {
        "hostname": platform.node(),
        "bios_version": bios.SMBIOSBIOSVersion,
        "manufacturer": bios.Manufacturer,
        "cpu_temp_c": cpu_temp,
        "ram_usage_percent": memory.percent
    }

async def stream_telemetry():
    uri = "ws://192.168.0.168:8000/ws/telemetry" 
    
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                while True:
                    payload = get_hardware_telemetry()
                    await websocket.send(json.dumps(payload))
                    await asyncio.sleep(2)
        except Exception:
            await asyncio.sleep(5)

if __name__ == "__main__":
    print("Agent started. Streaming telemetry...")
    asyncio.run(stream_telemetry())