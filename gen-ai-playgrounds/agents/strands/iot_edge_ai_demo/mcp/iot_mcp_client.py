"""
IoT Edge AI Monitoring Agent - Using MCP Servers
================================================
Updated to use MCP servers instead of local tools

Prerequisites:
1. Start the MCP servers:
   - python telemetry_server.py
   - python vision_server.py  
   - python expert_server.py

2. Run: python iot_mcp_client.py
"""

import time
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models.ollama import OllamaModel
from strands.tools.mcp import MCPClient

# ============================================================================
# MCP CLIENT CONNECTIONS
# ============================================================================

# Connect to the three MCP servers using HTTP transport
telemetry_client = MCPClient(lambda: streamablehttp_client("http://127.0.0.1:8001/mcp"))
vision_client = MCPClient(lambda: streamablehttp_client("http://127.0.0.1:8002/mcp"))
expert_client = MCPClient(lambda: streamablehttp_client("http://127.0.0.1:8003/mcp"))

# ============================================================================
# AGENT SETUP
# ============================================================================

# Configure the local Ollama model for orchestration
model = OllamaModel(
    model_id="llama3.2:1b",
    host="http://localhost:11434",
    params={
        "max_tokens": 300,
        "temperature": 0.3,
        "stream": False,
    },
)

# System prompt for the IoT monitoring assistant
system_prompt = """You are a helpful IoT monitoring assistant for industrial facilities. 
You have access to device telemetry tools, camera analysis capabilities, and expert insights to help monitor operations effectively.

When users ask for:
- Device status or telemetry → use get_device_telemetry
- Image or camera analysis → use analyze_camera_feed  
- Expert advice or complex questions → use get_expert_insights

Always return the complete tool results directly to the user."""

# ============================================================================
# DEMO AND INTERACTIVE FUNCTIONS
# ============================================================================

def run_iot_demo():
    """Run IoT edge AI demonstration using MCP servers"""
    
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                    🏭 IoT EDGE AI MONITORING AGENT (MCP)                 ║
    ║                                                                          ║
    ║  Connected Edge Intelligence Demo with MCP Servers                       ║
    ║                                                                          ║
    ║  📡 Telemetry Server: Port 8001                                         ║
    ║  📷 Vision Server: Port 8002                                            ║
    ║  🧠 Expert Server: Port 8003                                            ║
    ║                                                                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Demo scenarios
    demo_scenarios = [
        {
            "query": "Check the current device telemetry",
            "expected_server": "Telemetry Server",
            "description": "IoT sensor monitoring"
        },
        {
            "query": "Analyze the image at sample_image.png",
            "expected_server": "Vision Server", 
            "description": "Visual inspection analysis"
        },
        {
            "query": "What optimization opportunities do you see based on current operations?",
            "expected_server": "Expert Server",
            "description": "Advanced analysis"
        },
        {
            "query": "Show me device status",
            "expected_server": "Telemetry Server",
            "description": "Quick sensor check"
        },
        {
            "query": "Analyze camera image factory_floor.jpg", 
            "expected_server": "Vision Server",
            "description": "Camera feed analysis"
        },
        {
            "query": "Give me expert recommendations for equipment maintenance",
            "expected_server": "Expert Server",
            "description": "Expert insights"
        }
    ]
    
    print("\n🎭 **Demo: IoT Edge AI with MCP Servers**\n")
    
    # Use all MCP servers within context managers
    with telemetry_client, vision_client, expert_client:
        # Combine tools from all servers
        all_tools = (
            telemetry_client.list_tools_sync() + 
            vision_client.list_tools_sync() + 
            expert_client.list_tools_sync()
        )
        
        # Create agent with all MCP tools
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            tools=all_tools
        )
        
        telemetry_requests = 0
        vision_requests = 0
        expert_requests = 0
        
        for i, scenario in enumerate(demo_scenarios, 1):
            print(f"{'='*70}")
            print(f"📋 **Scenario {i}:** {scenario['description']}")
            print(f"👤 **Request:** {scenario['query']}")
            print(f"🎯 **Expected Server:** {scenario['expected_server']}")
            print("-" * 70)
            
            start_time = time.time()
            response = agent(scenario['query'])
            response_time = time.time() - start_time
            
            print(f"🤖 **Agent Response:**\n{response}")
            
            # Determine which server was used
            response_str = str(response)
            if "Device Telemetry Report" in response_str:
                print(f"\n📡 **MCP Server:** Telemetry (Port 8001)")
                telemetry_requests += 1
            elif "Object Detection Report" in response_str:
                print(f"\n📷 **MCP Server:** Vision Analysis (Port 8002)")
                vision_requests += 1
            elif "Expert Analysis Report" in response_str:
                print(f"\n🧠 **MCP Server:** Expert Insights (Port 8003)")
                expert_requests += 1
            else:
                print(f"\n🤖 **Agent Response** - Processing completed")
                
            print(f"⏱️  **Response Time:** {response_time:.2f}s")
            print()
            time.sleep(1.5)  # Demo pause
        
        # Show summary
        print(f"{'='*70}")
        print("📊 **DEMO SUMMARY - MCP Server Usage**")
        print(f"""
📡 **Telemetry Server (8001):** {telemetry_requests} requests
📷 **Vision Server (8002):** {vision_requests} requests  
🧠 **Expert Server (8003):** {expert_requests} requests

💡 **MCP Benefits Demonstrated:**
✅ Distributed AI services across multiple HTTP servers
✅ Modular architecture with independent services
✅ Easy scaling and maintenance of individual components
✅ Modern HTTP transport (streamable HTTP)
✅ Service isolation for better reliability
✅ Hot-swappable tools without client changes
""")

def interactive_iot_mode():
    """Interactive IoT monitoring mode using MCP servers"""
    print("\n🎮 **Interactive IoT Edge AI Mode (MCP)**")
    print("Connected to MCP servers for distributed AI processing!")
    print("\nExample queries:")
    print("  • 'Check sensor status'")
    print("  • 'Analyze image factory_floor.jpg'")
    print("  • 'Check the camera feed image cam_01.png'")
    print("  • 'What optimization opportunities do you see?'")
    print("  • 'Predict maintenance needs'")
    print("\nType 'exit' to quit\n")
    
    # Use all MCP servers within context managers
    with telemetry_client, vision_client, expert_client:
        # Combine tools from all servers
        all_tools = (
            telemetry_client.list_tools_sync() + 
            vision_client.list_tools_sync() + 
            expert_client.list_tools_sync()
        )
        
        # Create agent with all MCP tools
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            tools=all_tools
        )
        
        while True:
            try:
                user_input = input("IoT Admin > ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print("🏭 IoT monitoring session ended. MCP servers disconnected!")
                    break
                    
                if not user_input:
                    continue
                    
                start_time = time.time()
                response = agent(user_input)
                response_time = time.time() - start_time
                
                print(f"\nAgent > {response}")
                print(f"⏱️  ({response_time:.2f}s)")
                
            except KeyboardInterrupt:
                print("\n🏭 IoT monitoring session ended!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def check_mcp_servers():
    """Check if MCP servers are running"""
    print("🔧 **Checking MCP Server Status...**\n")
    
    servers = [
        ("Telemetry Server", "http://127.0.0.1:8001/mcp"),
        ("Vision Server", "http://127.0.0.1:8002/mcp"),
        ("Expert Server", "http://127.0.0.1:8003/mcp")
    ]
    
    for server_name, url in servers:
        try:
            # Try to connect to each server
            test_client = MCPClient(lambda url=url: streamablehttp_client(url))
            with test_client:
                tools = test_client.list_tools_sync()
                print(f"✅ {server_name}: Running ({len(tools)} tools available)")
        except Exception as e:
            print(f"❌ {server_name}: Not accessible - {e}")
            print(f"   Make sure to start: python {server_name.lower().replace(' ', '_')}_server.py")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            interactive_iot_mode()
        elif sys.argv[1] == "--check":
            check_mcp_servers()
        else:
            print("Usage:")
            print("  python iot_mcp_client.py                # Run demo")
            print("  python iot_mcp_client.py --interactive  # Interactive mode")
            print("  python iot_mcp_client.py --check        # Check MCP servers")
    else:
        check_mcp_servers()
        print("\n🚀 **Starting IoT Edge AI Demo with MCP...**\n")
        run_iot_demo()
        print("\n💡 **Try interactive mode:** python iot_mcp_client.py --interactive")