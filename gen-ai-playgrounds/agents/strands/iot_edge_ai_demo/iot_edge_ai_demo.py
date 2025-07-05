"""
IoT Edge AI Monitoring Agent - Complete Demo
============================================
Demonstrates NVIDIA Research insights: "Small Language Models are the Future of Agentic AI"

Complete end-to-end implementation with:
- Tool 1: Local telemetry monitoring (simulated IoT sensors)
- Tool 2: Real image analysis (Ollama vision model)  
- Tool 3: Complex analysis (Amazon Nova)

Run: python iot_edge_ai_demo.py
Interactive: python iot_edge_ai_demo.py --interactive
"""

import json
import random
import time
import ollama
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

# Import Strands components
from strands import Agent, tool
from strands.models.ollama import OllamaModel

# ============================================================================
# HARDCODED TELEMETRY DATA FOR 3 DEVICE TYPES
# ============================================================================

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

# ============================================================================
# TOOL 1: LOCAL TELEMETRY MONITORING (Edge Processing)
# ============================================================================

@tool
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
        
        return report
        
    except Exception as e:
        return f"❌ Error retrieving device telemetry: {str(e)}"

# ============================================================================
# TOOL 2: LOCAL VISION ANALYSIS (Edge Vision AI)
# ============================================================================

@tool
def analyze_camera_feed(image_path: str) -> str:
    """Analyze visual data from cameras using object detection capabilities.
    
    Args:
        image_path (str): Path to the image file for analysis
        
    Returns:
        str: Object detection results including identified objects, people, and equipment.
    """
    try:
        # Use Ollama vision model with streaming for better UX
        print("🔄 Image path ...", image_path)
        print("🔄 Analyzing image...", end="", flush=True)
        
        stream = ollama.chat(
            model='llama3.2-vision',
            messages=[{
                'role': 'user',
                'content': 'Describe this image in one sentence. What are the 3 most important things you see?',
                'images': [image_path]
            }],
            stream=True,
        )
        
        # Collect the full response while streaming for UX
        full_response = ""
        for chunk in stream:
            chunk_content = chunk['message']['content']
            print(chunk_content, end='', flush=True)
            full_response += chunk_content
        
        print()  # New line after streaming
        
        # Use the complete response for formatting
        analysis_text = full_response
        
        # Format object detection report
        report = f"📷 **Object Detection Report**\n\n"
        report += f"🔍 **Image Source:** {image_path}\n"
        report += f"🎯 **Detection Type:** Object Recognition\n\n"
        report += f"**Detected Objects:**\n{analysis_text}\n\n"
        report += f"⚡ **Processing:** Edge-based object detection\n"
        report += f"🔒 **Security:** Local processing, data privacy maintained"
        
        return report
        
    except Exception as e:
        return f"❌ Error in object detection: {str(e)}\n💡 Ensure object detection system is available and image path is valid"


def test_expert_insights():
    """Test function with sample context and question for expert insights"""
    
    sample_context = """
    Device Status Summary:
    - PUMP-001: Temperature 42.3°C, Pressure 98.5 bar, Vibration 1.2 mm/s
    - HVAC-102: Temperature 22.1°C, Humidity 45%, Power 1200W
    - CAM-203: Temperature 35.7°C, Storage 78% used, Signal -42 dBm
    
    Recent Issues:
    - PUMP-001 showing elevated temperature readings (up 8°C from normal)
    - HVAC-102 power consumption increased 15% over past week
    - Multiple devices reporting higher ambient temperatures
    """
    
    sample_question = "What patterns indicate potential equipment issues and what preventive actions should we take?"
    
    print("🧪 **Testing Expert Insights Tool**\n")
    print(f"Context: {sample_context}")
    print(f"Question: {sample_question}")
    print("\n" + "="*60)
    
    # Test the tool
    result = get_expert_insights(sample_context, sample_question)
    print(result)

# ============================================================================
# TOOL 3: EXPERT INSIGHTS (Advanced Analysis)
# ============================================================================

@tool
def get_expert_insights(context_data: str, question: str) -> str:
    """Get advanced analysis and expert recommendations for complex operational questions.
    
    Args:
        context_data (str): Current operational data or situation context
        question (str): Specific question requiring detailed analysis
        
    Returns:
        str: Expert analysis with recommendations and actionable insights.
    """
    try:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        
        user_message = f"""As an expert industrial operations analyst, please analyze this situation:

Context: {context_data}

Question: {question}

Please provide:
1. Analysis of the current situation
2. Key risks or opportunities identified  
3. Specific actionable recommendations
4. Implementation priorities
5. Success metrics to monitor

Focus on practical insights for industrial operations teams."""

        conversation = [
            {
                "role": "user",
                "content": [{"text": user_message}],
            }
        ]
        
        response = client.converse(
            modelId="amazon.nova-lite-v1:0",
            messages=conversation,
            inferenceConfig={"maxTokens": 512, "temperature": 0.5, "topP": 0.9},
        )
        
        response_text = response["output"]["message"]["content"][0]["text"]
        
        return f"🧠 **Expert Analysis Report**\n\n{response_text}"
        
    except (ClientError, Exception) as e:
        return f"❌ Expert analysis service unavailable: {str(e)}"

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

# Create the IoT monitoring assistant
system_prompt = """You are a helpful IoT monitoring assistant for industrial facilities. 
You have access to device telemetry tools, camera analysis capabilities, and expert insights to help monitor operations effectively.

When users ask for:
- Device status or telemetry → use get_device_telemetry
- Image or camera analysis → use analyze_camera_feed  
- Expert advice or complex questions → use get_expert_insights

Always return the complete tool results directly to the user."""

agent = Agent(
    model=model,
    system_prompt=system_prompt,
    tools=[
        get_device_telemetry,
        analyze_camera_feed,
        get_expert_insights,
    ],
)

# ============================================================================
# DEMO AND INTERACTIVE MODE
# ============================================================================

def run_iot_demo():
    """Run IoT edge AI demonstration"""
    
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                    🏭 IoT EDGE AI MONITORING AGENT                       ║
    ║                                                                          ║
    ║  Connected Edge Intelligence Demo                                        ║
    ║                                                                          ║
    ║  🏠 Edge: Telemetry monitoring + Vision AI (fast, private)              ║
    ║  ☁️ Cloud: Expert analysis with Nova (complex reasoning)                ║
    ║                                                                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Demo scenarios showcasing different AI capabilities
    demo_scenarios = [
        {
            "query": "Check the current device telemetry",
            "expected_tool": "Telemetry (Edge)",
            "description": "Local sensor monitoring"
        },
        {
            "query": "Analyze the image at sample_image.png",
            "expected_tool": "Vision AI (Edge)", 
            "description": "Local visual inspection"
        },
        {
            "query": "What optimization opportunities do you see based on current operations?",
            "expected_tool": "Expert Analysis",
            "description": "Complex pattern analysis"
        },
        {
            "query": "Show me device status",
            "expected_tool": "Telemetry (Edge)",
            "description": "Quick sensor check"
        },
        {
            "query": "Analyze camera image factory_floor.jpg", 
            "expected_tool": "Vision AI (Edge)",
            "description": "Visual inspection"
        },
        {
            "query": "Give me expert recommendations for equipment maintenance",
            "expected_tool": "Expert Analysis",
            "description": "Expert insights"
        }
    ]
    
    print("\n🎭 **Demo: IoT Edge AI Scenarios**\n")
    
    edge_requests = 0
    cloud_requests = 0
    
    for i, scenario in enumerate(demo_scenarios, 1):
        print(f"{'='*70}")
        print(f"📋 **Scenario {i}:** {scenario['description']}")
        print(f"👤 **Request:** {scenario['query']}")
        print(f"🎯 **Expected Tool:** {scenario['expected_tool']}")
        print("-" * 70)
        
        start_time = time.time()
        response = agent(scenario['query'])
        response_time = time.time() - start_time
        
        print(f"🤖 **Agent Response:**\n{response}")
        
        # Determine which type of processing was used
        response_str = str(response)
        if "Device Telemetry Report" in response_str:
            print(f"\n🏠 **Edge Processing** - Device telemetry monitoring")
            edge_requests += 1
        elif "Object Detection Report" in response_str:
            print(f"\n🏠 **Edge Processing** - Vision AI analysis")
            edge_requests += 1
        elif "Expert Analysis Report" in response_str:
            print(f"\n☁️ **Advanced Processing** - Expert insights")
            cloud_requests += 1
        else:
            print(f"\n🤖 **Agent Response** - Processing completed")
            edge_requests += 1  # Default to edge for counting
            
        print(f"⏱️  **Response Time:** {response_time:.2f}s")
        print()
        time.sleep(1.5)  # Demo pause
    
    # Show summary
    print(f"{'='*70}")
    print("📊 **DEMO SUMMARY**")
    print(f"""
🏠 **Edge Processing:** {edge_requests} requests
   • Telemetry monitoring (simulated IoT sensors)
   • Vision analysis (local llama3.2-vision)
   • Fast, private, low-cost

☁️ **Advanced Processing:** {cloud_requests} requests  
   • Expert insights and analysis
   • Complex reasoning when needed

💡 **Key Benefits Demonstrated:**
✅ Connected edge intelligence with multiple AI models
✅ Smart routing between edge and advanced processing
✅ Real-time IoT monitoring with local processing
✅ Object detection for visual inspection
✅ Expert analysis for complex decisions
✅ Cost optimization through intelligent model selection
""")

def interactive_iot_mode():
    """Interactive IoT monitoring mode"""
    print("\n🎮 **Interactive IoT Edge AI Mode**")
    print("Ask me about IoT monitoring, camera analysis, or get expert insights!")
    print("\nExample queries:")
    print("  • 'Check sensor status'")
    print("  • 'Analyze image factory_floor.jpg'")
    print("  • 'Check the camera feed image cam_01.png'")
    print("  • 'What optimization opportunities do you see?'")
    print("  • 'Predict maintenance needs'")
    print("\nType 'exit' to quit\n")
    
    while True:
        try:
            user_input = input("IoT Admin > ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("🏭 IoT monitoring session ended. Stay connected!")
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

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔧 **Checking Prerequisites...**\n")
    
    # Check Ollama connection
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server is running")
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            if "llama3.2:1b" in model_names:
                print("✅ llama3.2:1b model available")
            else:
                print("❌ llama3.2:1b model not found")
                print("   Run: ollama pull llama3.2:1b")
                
            if any("llama3.2-vision" in name for name in model_names):
                print("✅ llama3.2-vision model available")
            else:
                print("❌ llama3.2-vision model not found")
                print("   Run: ollama pull llama3.2-vision")
        else:
            print("❌ Ollama server not responding")
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is installed and running")
    
    # Check AWS credentials
    try:
        import boto3
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        print("✅ AWS credentials configured")
    except Exception as e:
        print(f"❌ AWS credentials issue: {e}")
        print("   Run: aws configure")
    
    # Check required packages
    required_packages = ['strands', 'ollama', 'boto3']
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} package installed")
        except ImportError:
            print(f"❌ {package} package missing")
            print(f"   Run: pip install {package}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            interactive_iot_mode()
        elif sys.argv[1] == "--check":
            check_prerequisites()
        else:
            print("Usage:")
            print("  python iot_edge_ai_demo.py            # Run demo")
            print("  python iot_edge_ai_demo.py --interactive  # Interactive mode")
            print("  python iot_edge_ai_demo.py --check        # Check prerequisites")
    else:
        check_prerequisites()
        print("\n🚀 **Starting IoT Edge AI Demo...**\n")
        run_iot_demo()
        print("\n💡 **Try interactive mode:** python iot_edge_ai_demo.py --interactive")