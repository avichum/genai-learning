"""
Telemetry MCP Server
Run: python telemetry_server.py
"""

import os
# Set port before importing FastMCP
os.environ['PORT'] = '8001'

import json
import random
from datetime import datetime
from fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("IoT Telemetry Server")

# Hardcoded telemetry data
DEVICE_TELEMETRY = {
    "PUMP-001": {
        "device_type": "Industrial Pump",
        "location": "Manufacturing Floor A",
        "telemetry": {
            "temperature": "42.3°C",
            "pressure": "98.5 bar",
            "vibration": "1.2 mm/s",
            "flow_rate": "150 L/min",
            "power_consumption": "850 W",
            "operating_hours": "2847 hrs"
        },
        "status": "OPERATIONAL"
    },
    "HVAC-102": {
        "device_type": "HVAC System",
        "location": "Building Zone B",
        "telemetry": {
            "temperature": "22.1°C",
            "humidity": "45%",
            "air_flow": "650 m³/h",
            "filter_pressure": "1.8 Pa",
            "power_consumption": "1200 W",
            "fan_speed": "1450 RPM"
        },
        "status": "OPERATIONAL"
    },
    "CAM-203": {
        "device_type": "Security Camera",
        "location": "Entrance Gate C",
        "telemetry": {
            "temperature": "35.7°C",
            "humidity": "38%",
            "power_consumption": "25 W",
            "signal_strength": "-42 dBm",
            "storage_used": "78%",
            "uptime": "142 days"
        },
        "status": "OPERATIONAL"
    }
}

@mcp.tool(description="Retrieve current telemetry data from connected IoT devices")
def get_device_telemetry() -> str:
    """Retrieve current telemetry data from connected IoT devices.
    
    Returns:
        str: Complete telemetry data from a randomly selected device.
    """
    try:
        # Randomly select one device
        device_id = random.choice(list(DEVICE_TELEMETRY.keys()))
        device_data = DEVICE_TELEMETRY[device_id]
        
        # Format complete telemetry report for the device
        report = f"📡 **Device Telemetry Report**\n\n"
        report += f"🏭 **Device:** {device_id} ({device_data['device_type']})\n"
        report += f"📍 **Location:** {device_data['location']}\n"
        report += f"🔄 **Status:** {device_data['status']}\n\n"
        report += f"📊 **Current Readings:**\n"
        
        for sensor, value in device_data['telemetry'].items():
            report += f"   • {sensor.replace('_', ' ').title()}: {value}\n"
        
        report += f"\n🕐 **Last Updated:** {datetime.now().strftime('%H:%M:%S')}"
        #print(report)
        
        return report
        
    except Exception as e:
        return f"❌ Error retrieving device telemetry: {str(e)}"

if __name__ == "__main__":
    # Run the server with HTTP transport on port 8001
    print("🔧 Starting Telemetry MCP Server on port 8001...")
    mcp.run(transport="http", host="127.0.0.1", port=8001, path="/mcp")