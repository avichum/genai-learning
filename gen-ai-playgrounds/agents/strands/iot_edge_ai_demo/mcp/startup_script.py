#!/usr/bin/env python3
"""
Start All MCP Servers Script
============================
Starts all three MCP servers in separate processes

Usage: python start_all_servers.py
"""

import subprocess
import sys
import time
import signal
import os

# Server configurations
SERVERS = [
    {
        "name": "Telemetry Server",
        "file": "telemetry_server.py",
        "port": 8001,
        "process": None
    },
    {
        "name": "Vision Server", 
        "file": "vision_server.py",
        "port": 8002,
        "process": None
    },
    {
        "name": "Expert Server",
        "file": "expert_server.py", 
        "port": 8003,
        "process": None
    }
]

def start_servers():
    """Start all MCP servers"""
    print("🚀 **Starting All MCP Servers...**\n")
    
    for server in SERVERS:
        try:
            print(f"Starting {server['name']} on port {server['port']}...")
            
            # Start server process
            process = subprocess.Popen([
                sys.executable, server['file']
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            server['process'] = process
            print(f"✅ {server['name']} started (PID: {process.pid})")
            
        except Exception as e:
            print(f"❌ Failed to start {server['name']}: {e}")
    
    print(f"\n{'='*50}")
    print("🏭 **All MCP Servers Started!**")
    print("\nServer Status:")
    for server in SERVERS:
        if server['process']:
            status = "🟢 Running" if server['process'].poll() is None else "🔴 Stopped"
            print(f"  {server['name']}: {status} (Port {server['port']})")
    
    print(f"\n💡 **Next Steps:**")
    print("1. Wait a few seconds for servers to initialize")
    print("2. Run: python iot_mcp_client.py")
    print("3. Or run: python iot_mcp_client.py --interactive")
    print("\nPress Ctrl+C to stop all servers")

def stop_servers():
    """Stop all MCP servers"""
    print("\n\n🛑 **Stopping All MCP Servers...**")
    
    for server in SERVERS:
        if server['process'] and server['process'].poll() is None:
            try:
                server['process'].terminate()
                server['process'].wait(timeout=5)
                print(f"✅ {server['name']} stopped")
            except subprocess.TimeoutExpired:
                server['process'].kill()
                print(f"🔥 {server['name']} force killed")
            except Exception as e:
                print(f"❌ Error stopping {server['name']}: {e}")
    
    print("🏁 All servers stopped!")

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    stop_servers()
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        start_servers()
        
        # Keep the script running
        while True:
            time.sleep(1)
            
            # Check if any server died
            for server in SERVERS:
                if server['process'] and server['process'].poll() is not None:
                    print(f"\n⚠️  {server['name']} stopped unexpectedly!")
                    # Could restart here if desired
                    
    except KeyboardInterrupt:
        stop_servers()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        stop_servers()