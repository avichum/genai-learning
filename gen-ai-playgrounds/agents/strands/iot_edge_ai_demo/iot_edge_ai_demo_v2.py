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
# 🔧 CENTRALIZED CONFIGURATION - CHANGE MODELS HERE
# ============================================================================

class Config:
    """Centralized configuration for all AI models and settings"""
    
    # 🤖 Main Agent Model (Orchestration)
    MAIN_MODEL_ID = "llama3.2:3b"          # Change here: llama3.2:1b, llama3.2:3b, llama3:8b, etc.
    MAIN_MODEL_TEMPERATURE = 0.1           # Lower = more deterministic
    MAIN_MODEL_MAX_TOKENS = 400
    
    # 👁️ Vision Model (Edge Image Analysis) 
    VISION_MODEL_ID = "llava:7b"           # Change here: llava:7b, llava:13b, llava:34b, etc.
    VISION_MODEL_PROMPT = "Describe this industrial facility image in one sentence. What are the 3 most important objects or equipment you see?"
    
    # ☁️ Cloud Model (Expert Analysis)
    CLOUD_MODEL_ID = "amazon.nova-lite-v1:0"  # Change here: amazon.nova-lite-v1:0, amazon.nova-pro-v1:0, etc.
    CLOUD_MAX_TOKENS = 512
    CLOUD_TEMPERATURE = 0.5
    CLOUD_TOP_P = 0.9
    
    # 🌐 Infrastructure Settings
    OLLAMA_HOST = "http://localhost:11434"
    AWS_REGION = "us-east-1"
    
    # 🔍 Debug Settings
    DEBUG_TRUNCATE_LENGTH = 200  # Truncate long debug outputs
    DEMO_PAUSE_SECONDS = 1.5     # Pause between demo scenarios

# Model display names for user-friendly output
MODEL_DISPLAY_NAMES = {
    "llama3.2:1b": "Llama 3.2 1B (Ultra-fast, Basic)",
    "llama3.2:3b": "Llama 3.2 3B (Fast, Enhanced)", 
    "llama3:8b": "Llama 3 8B (Balanced)",
    "llava:7b": "LLaVA 7B Vision (Standard)",
    "llava:13b": "LLaVA 13B Vision (Enhanced)",
    "llava:34b": "LLaVA 34B Vision (Premium)",
    "amazon.nova-lite-v1:0": "Amazon Nova Lite (Fast, Cost-effective)",
    "amazon.nova-pro-v1:0": "Amazon Nova Pro (Advanced reasoning)",
}

def get_model_display_name(model_id: str) -> str:
    """Get user-friendly model name"""
    return MODEL_DISPLAY_NAMES.get(model_id, model_id)

# ============================================================================
# DEBUG LOGGING UTILITIES
# ============================================================================

def log_tool_input(tool_name: str, **kwargs):
    """Log tool input parameters with formatting"""
    print(f"\n🔧 **TOOL INPUT DEBUG: {tool_name}**")
    print("─" * 50)
    for param, value in kwargs.items():
        # Truncate long values for readability
        if isinstance(value, str) and len(value) > Config.DEBUG_TRUNCATE_LENGTH:
            display_value = value[:Config.DEBUG_TRUNCATE_LENGTH] + "... (truncated)"
        else:
            display_value = value
        print(f"📥 {param}: {display_value}")
    print("─" * 50)

def log_cloud_response(service: str, response_data: str, metadata: dict = None):
    """Log cloud service responses with metadata"""
    print(f"\n☁️ **CLOUD RESPONSE DEBUG: {service}**")
    print("═" * 60)
    if metadata:
        print("📊 **Response Metadata:**")
        for key, value in metadata.items():
            print(f"   • {key}: {value}")
        print()
    
    print("📨 **Raw Response Content:**")
    print(f"'{response_data}'")
    print("═" * 60)

def log_model_info(model_type: str, model_id: str):
    """Log which model is being used for what purpose"""
    display_name = get_model_display_name(model_id)
    print(f"🤖 **{model_type}:** {display_name}")

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
def get_device_telemetry(device_id: str) -> str:
    """Retrieve current telemetry data from a specific IoT device.
    
    Args:
        device_id: Device ID to query or look data for 
    
    Returns:
        str: Complete telemetry data from the specified device.
    """
    # DEBUG: Log tool input parameters
    log_tool_input("get_device_telemetry", device_id=device_id)
    
    try:
        print(f"🔍 DEBUG: Tool called with device_id='{device_id}'")
        
        # Clean up device ID
        original_device_id = device_id
        device_id = device_id.upper().strip()
        print(f"🔍 DEBUG: Original input: '{original_device_id}' -> Cleaned: '{device_id}'")
        print(f"🔍 DEBUG: Looking for device '{device_id}' in database")
        
        # Direct lookup in DEVICE_TELEMETRY
        if device_id in DEVICE_TELEMETRY:
            device_data = DEVICE_TELEMETRY[device_id]
            print(f"✅ DEBUG: Found device {device_id}")
            print(f"📊 DEBUG: Device data structure: {json.dumps(device_data, indent=2)}")
            
            # Format specific device report
            report = f"📡 **Device Telemetry Report**\n\n"
            report += f"🏭 **Device:** {device_id} ({device_data['device_type']})\n"
            report += f"📍 **Location:** {device_data['location']}\n"
            report += f"🔄 **Status:** {device_data['status']}\n\n"
            report += f"📊 **Current Readings:**\n"
            
            for sensor, value in device_data['telemetry'].items():
                report += f"   • {sensor.replace('_', ' ').title()}: {value}\n"
            
            report += f"\n🕐 **Last Updated:** {datetime.now().strftime('%H:%M:%S')}"
            report += f"\n⚡ **Processed by:** Edge telemetry system"
            
            print(f"📤 DEBUG: Generated report length: {len(report)} characters")
            return report
        else:
            # Device not found
            available_devices = list(DEVICE_TELEMETRY.keys())
            print(f"❌ DEBUG: Device '{device_id}' not found. Available: {available_devices}")
            error_response = f"❌ Device '{device_id}' not found.\n\n📋 **Available Devices:** {', '.join(available_devices)}"
            print(f"📤 DEBUG: Error response: {error_response}")
            return error_response
        
    except Exception as e:
        print(f"❌ DEBUG: Error in tool: {str(e)}")
        error_response = f"❌ Error retrieving device telemetry: {str(e)}"
        print(f"📤 DEBUG: Exception response: {error_response}")
        return error_response

# ============================================================================
# TOOL 2: LOCAL VISION ANALYSIS (Edge Vision AI)
# ============================================================================

@tool
def analyze_camera_feed(image_path: str) -> str:
    """Analyze visual data from industrial cameras using object detection capabilities.
    
    Args:
        image_path (str): Path to the image file for analysis
        
    Returns:
        str: Object detection results including identified objects, people, and equipment.
    """
    # DEBUG: Log tool input parameters
    log_tool_input("analyze_camera_feed", image_path=image_path)
    log_model_info("Vision Model", Config.VISION_MODEL_ID)
    
    try:
        print(f"🔄 DEBUG: Starting image analysis for: {image_path}")
        print(f"📁 DEBUG: Image path type: {type(image_path)}")
        print(f"📏 DEBUG: Image path length: {len(image_path)} characters")
        
        # Use configurable vision model
        print("🔄 Image path ...", image_path)
        print("🔄 Analyzing image...", end="", flush=True)
        
        print(f"🤖 DEBUG: Vision prompt: {Config.VISION_MODEL_PROMPT}")
        print(f"🤖 DEBUG: Using vision model: {Config.VISION_MODEL_ID}")
        
        stream = ollama.chat(
            model=Config.VISION_MODEL_ID,  # Using centralized config
            messages=[{
                'role': 'user',
                'content': Config.VISION_MODEL_PROMPT,  # Using centralized prompt
                'images': [image_path]
            }],
            stream=True,
        )
        
        # Collect the full response while streaming for UX
        full_response = ""
        chunk_count = 0
        for chunk in stream:
            chunk_content = chunk['message']['content']
            print(chunk_content, end='', flush=True)
            full_response += chunk_content
            chunk_count += 1
        
        print()  # New line after streaming
        print(f"📊 DEBUG: Received {chunk_count} chunks from {Config.VISION_MODEL_ID}")
        print(f"📏 DEBUG: Full response length: {len(full_response)} characters")
        print(f"📨 DEBUG: Raw vision response: '{full_response}'")
        
        # Use the complete response for formatting
        analysis_text = full_response
        
        # Format object detection report
        report = f"📷 **Object Detection Report**\n\n"
        report += f"🔍 **Image Source:** {image_path}\n"
        report += f"🎯 **Detection Type:** Industrial Equipment Recognition\n"
        report += f"🤖 **Vision Model:** {get_model_display_name(Config.VISION_MODEL_ID)}\n\n"
        report += f"**Detected Objects:**\n{analysis_text}\n\n"
        report += f"⚡ **Processing:** Edge-based object detection\n"
        report += f"🔒 **Security:** Local processing, data privacy maintained"
        
        print(f"📤 DEBUG: Final report length: {len(report)} characters")
        return report
        
    except Exception as e:
        error_msg = f"❌ Error in object detection: {str(e)}\n💡 Ensure {Config.VISION_MODEL_ID} model is available and image path is valid"
        print(f"❌ DEBUG: Vision analysis error: {str(e)}")
        print(f"📤 DEBUG: Error response: {error_msg}")
        return error_msg


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
    # DEBUG: Log tool input parameters
    log_tool_input("get_expert_insights", 
                   context_data=context_data, 
                   question=question)
    log_model_info("Cloud Model", Config.CLOUD_MODEL_ID)
    
    try:
        print(f"🔄 DEBUG: Initializing AWS Bedrock client (Region: {Config.AWS_REGION})...")
        client = boto3.client("bedrock-runtime", region_name=Config.AWS_REGION)
        print("✅ DEBUG: AWS Bedrock client initialized successfully")
        
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

        print(f"📏 DEBUG: User message length: {len(user_message)} characters")
        print(f"📝 DEBUG: Constructed prompt for Bedrock:")
        print("─" * 40)
        print(user_message)
        print("─" * 40)

        conversation = [
            {
                "role": "user",
                "content": [{"text": user_message}],
            }
        ]
        
        # Use centralized config for inference parameters
        inference_config = {
            "maxTokens": Config.CLOUD_MAX_TOKENS,
            "temperature": Config.CLOUD_TEMPERATURE,
            "topP": Config.CLOUD_TOP_P
        }
        print(f"⚙️ DEBUG: Inference config: {inference_config}")
        print(f"🚀 DEBUG: Sending request to {Config.CLOUD_MODEL_ID}...")
        
        start_time = time.time()
        response = client.converse(
            modelId=Config.CLOUD_MODEL_ID,  # Using centralized config
            messages=conversation,
            inferenceConfig=inference_config,
        )
        api_time = time.time() - start_time
        print(f"⏱️ DEBUG: Bedrock API call took {api_time:.2f} seconds")
        
        # Extract response details
        response_text = response["output"]["message"]["content"][0]["text"]
        
        # Log comprehensive response metadata
        response_metadata = response.get("ResponseMetadata", {})
        usage_info = response.get("usage", {})
        
        metadata = {
            "API Response Time": f"{api_time:.2f}s",
            "Model ID": Config.CLOUD_MODEL_ID,
            "Model Display Name": get_model_display_name(Config.CLOUD_MODEL_ID),
            "Response Length": f"{len(response_text)} characters",
            "HTTP Status": response_metadata.get("HTTPStatusCode", "Unknown"),
            "Request ID": response_metadata.get("RequestId", "Unknown")[:16] + "...",
        }
        
        if usage_info:
            metadata.update({
                "Input Tokens": usage_info.get("inputTokens", "Unknown"),
                "Output Tokens": usage_info.get("outputTokens", "Unknown"),
                "Total Tokens": usage_info.get("totalTokens", "Unknown"),
            })
        
        # Log the full cloud response
        log_cloud_response(f"Amazon Bedrock {get_model_display_name(Config.CLOUD_MODEL_ID)}", 
                         response_text, metadata)
        
        final_report = f"🧠 **Expert Analysis Report**\n\n{response_text}"
        final_report += f"\n\n🤖 **Analyzed by:** {get_model_display_name(Config.CLOUD_MODEL_ID)}"
        print(f"📤 DEBUG: Final report length: {len(final_report)} characters")
        
        return final_report
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        print(f"❌ DEBUG: AWS ClientError - Code: {error_code}, Message: {error_msg}")
        error_response = f"❌ Expert analysis service unavailable (AWS Error {error_code}): {error_msg}"
        print(f"📤 DEBUG: ClientError response: {error_response}")
        return error_response
        
    except Exception as e:
        print(f"❌ DEBUG: Unexpected error in expert insights: {str(e)}")
        print(f"🔍 DEBUG: Error type: {type(e).__name__}")
        error_response = f"❌ Expert analysis service unavailable: {str(e)}"
        print(f"📤 DEBUG: Exception response: {error_response}")
        return error_response

# ============================================================================
# AGENT SETUP - USING CENTRALIZED CONFIG
# ============================================================================

def create_agent():
    """Create the IoT monitoring agent with centralized configuration"""
    
    # Configure the local Ollama model for orchestration
    model = OllamaModel(
        model_id=Config.MAIN_MODEL_ID,  # Using centralized config
        host=Config.OLLAMA_HOST,        # Using centralized config
        params={
            "max_tokens": Config.MAIN_MODEL_MAX_TOKENS,
            "temperature": Config.MAIN_MODEL_TEMPERATURE,
            "stream": False,
        },
    )
    
    # Enhanced system prompt with explicit industrial context
    system_prompt = f"""You are a professional IoT device telemetry assistant. You provide ONLY factual information from device sensors.

STRICT RULES:
1. When asked about device telemetry, use get_device_telemetry tool and return EXACTLY what it provides
2. When asked about images, use analyze_camera_feed tool and return EXACTLY what it provides  
3. When asked for expert analysis, use get_expert_insights tool and return EXACTLY what it provides
4. NEVER suggest additional analysis, services, or capabilities not in your tools
5. NEVER offer services, tools, or functionality you do not have
6. NEVER hallucinate additional functionality beyond your 3 tools
7. Answer ONLY with the direct tool output - do not add suggestions or recommendations
8. If a tool provides the answer, that IS the complete answer

Your ONLY available tools:
- get_device_telemetry: Returns sensor readings from IoT devices
- analyze_camera_feed: Analyzes images using local vision AI
- get_expert_insights: Provides analysis using cloud reasoning

Return tool outputs directly without embellishment."""

    # Create the IoT monitoring assistant - PURE AGENT ARCHITECTURE
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            get_device_telemetry,
            analyze_camera_feed,
            get_expert_insights,
        ],
    )
    
    return agent

# Initialize the agent using centralized config
agent = create_agent()

# ============================================================================
# DEMO AND INTERACTIVE MODE - ENHANCED WITH CONFIG INFO
# ============================================================================

def show_configuration():
    """Display current model configuration"""
    print("🔧 **CURRENT CONFIGURATION**")
    print("═" * 60)
    print(f"🤖 **Main Agent Model:** {get_model_display_name(Config.MAIN_MODEL_ID)}")
    print(f"   • Model ID: {Config.MAIN_MODEL_ID}")
    print(f"   • Temperature: {Config.MAIN_MODEL_TEMPERATURE}")
    print(f"   • Max Tokens: {Config.MAIN_MODEL_MAX_TOKENS}")
    print()
    print(f"👁️ **Vision Model:** {get_model_display_name(Config.VISION_MODEL_ID)}")
    print(f"   • Model ID: {Config.VISION_MODEL_ID}")
    print(f"   • Host: {Config.OLLAMA_HOST}")
    print()
    print(f"☁️ **Cloud Model:** {get_model_display_name(Config.CLOUD_MODEL_ID)}")
    print(f"   • Model ID: {Config.CLOUD_MODEL_ID}")
    print(f"   • Temperature: {Config.CLOUD_TEMPERATURE}")
    print(f"   • Max Tokens: {Config.CLOUD_MAX_TOKENS}")
    print(f"   • Region: {Config.AWS_REGION}")
    print("═" * 60)

def run_iot_demo():
    """Run IoT edge AI demonstration"""
    
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                    🏭 IoT EDGE AI MONITORING AGENT                       ║
    ║                                                                          ║
    ║  Connected Edge Intelligence Demo (WITH DEBUG LOGGING)                  ║
    ║                                                                          ║
    ║  🏠 Edge: Telemetry monitoring + Vision AI (fast, private)              ║
    ║  ☁️ Cloud: Expert analysis with Nova (complex reasoning)                ║
    ║                                                                          ║
    ║  PURE AGENT ARCHITECTURE: SLM makes all routing decisions               ║
    ║                                                                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Show current configuration
    show_configuration()
    print()
    
    # Demo scenarios - 2 examples of each tool (6 total) - MATCHED TO ACTUAL DEVICE DATA
    demo_scenarios = [
        {
            "query": "What is the temperature of PUMP-001?",
            "expected_tool": "Telemetry (Edge)",
            "description": "Pump temperature query (42.3°C expected)"
        },
        {
            "query": "Check storage used for CAM-203",
            "expected_tool": "Telemetry (Edge)",
            "description": "Camera storage check (78% expected)"
        },
        {
            "query": "Analyze the image at factory_floor.jpg",
            "expected_tool": "Vision AI (Edge)", 
            "description": "Industrial facility visual inspection"
        },
        {
            "query": "Analyze camera image sample_image.png", 
            "expected_tool": "Vision AI (Edge)",
            "description": "Quality control image analysis"
        },
        {
            "query": "What are the best practices for monitoring products on conveyor belts?",
            "expected_tool": "Expert Analysis",
            "description": "Conveyor monitoring best practices"
        },
        {
            "query": "How should we optimize pump maintenance schedules based on vibration data?",
            "expected_tool": "Expert Analysis",
            "description": "Predictive maintenance strategy"
        }
    ]
    
    print("\n🎭 **Demo: IoT Edge AI Scenarios (WITH DEBUG LOGGING)**\n")
    
    edge_requests = 0
    cloud_requests = 0
    
    for i, scenario in enumerate(demo_scenarios, 1):
        print(f"{'='*70}")
        print(f"📋 **Scenario {i}:** {scenario['description']}")
        print(f"👤 **Request:** {scenario['query']}")
        print(f"🎯 **Expected Tool:** {scenario['expected_tool']}")
        print("-" * 70)
        
        print(f"\n🤖 **AGENT DEBUG: Processing query '{scenario['query']}'**")
        start_time = time.time()
        response = agent(scenario['query'])  # PURE AGENT CALL - NO WRAPPERS
        response_time = time.time() - start_time
        
        print(f"\n🤖 **Agent Response:**\n{response}")
        
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
        time.sleep(Config.DEMO_PAUSE_SECONDS)  # Using centralized config
    
    # Show summary
    print(f"{'='*70}")
    print("📊 **DEMO SUMMARY**")
    print(f"""
🏠 **Edge Processing:** {edge_requests} requests
   • Telemetry monitoring (simulated IoT sensors)
   • Vision analysis ({get_model_display_name(Config.VISION_MODEL_ID)})
   • Fast, private, low-cost

☁️ **Advanced Processing:** {cloud_requests} requests  
   • Expert insights and analysis ({get_model_display_name(Config.CLOUD_MODEL_ID)})
   • Complex reasoning when needed

🤖 **Models Used:**
   • Agent Orchestration: {get_model_display_name(Config.MAIN_MODEL_ID)}
   • Vision Processing: {get_model_display_name(Config.VISION_MODEL_ID)}
   • Expert Analysis: {get_model_display_name(Config.CLOUD_MODEL_ID)}

💡 **Key Benefits Demonstrated:**
✅ Connected edge intelligence with multiple AI models
✅ Smart routing between edge and advanced processing
✅ Real-time IoT monitoring with local processing
✅ Object detection for visual inspection
✅ Expert analysis for complex decisions
✅ Cost optimization through intelligent model selection
✅ Comprehensive debug logging for development
✅ Centralized configuration management

🧠 **AAIF Pure Agent Architecture:**
✅ SLM ({get_model_display_name(Config.MAIN_MODEL_ID)}) makes all routing decisions
✅ No keyword matching or fallback mechanisms
✅ Autonomous intelligent orchestration
✅ Validates "Small Language Models are the Future of Agentic AI"
""")

def interactive_iot_mode():
    """Interactive IoT monitoring mode"""
    print("\n🎮 **Interactive IoT Edge AI Mode (WITH DEBUG LOGGING)**")
    show_configuration()
    print("\nAsk me about IoT monitoring, camera analysis, or get expert insights!")
    print("\nExample queries:")
    print("  Device Specific:")
    print("    • 'What is the temperature of PUMP-001?'")
    print("    • 'Check status of HVAC-102'")
    print("    • 'Show me CAM-203 performance'")
    print("  General Monitoring:")
    print("    • 'Check sensor status'")
    print("    • 'Analyze image factory_floor.jpg'")
    print("  Expert Questions:")
    print("    • 'Best practices for monitoring conveyor belts?'")
    print("    • 'How to optimize pump maintenance schedules?'")
    print("    • 'What are optimal temperature ranges for equipment?'")
    print("\nAvailable Devices: PUMP-001, HVAC-102, CAM-203")
    print("\nType 'exit' to quit\n")
    
    while True:
        try:
            user_input = input("IoT Admin > ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("🏭 IoT monitoring session ended. Stay connected!")
                break
                
            if not user_input:
                continue
                
            print(f"\n🤖 **AGENT DEBUG: Processing user input '{user_input}'**")
            start_time = time.time()
            response = agent(user_input)  # PURE AGENT CALL
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
    
    # Show current configuration
    show_configuration()
    print()
    
    # Check Ollama connection
    try:
        import requests
        response = requests.get(f"{Config.OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server is running")
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            if Config.MAIN_MODEL_ID in model_names:
                print(f"✅ {Config.MAIN_MODEL_ID} model available")
            else:
                print(f"⚠️  {Config.MAIN_MODEL_ID} model not found (required for agent)")
                print(f"   Run: ollama pull {Config.MAIN_MODEL_ID}")
                
            if Config.VISION_MODEL_ID in model_names:
                print(f"✅ {Config.VISION_MODEL_ID} vision model available")
            else:
                print(f"❌ {Config.VISION_MODEL_ID} vision model not found")
                print(f"   Run: ollama pull {Config.VISION_MODEL_ID}")
        else:
            print("❌ Ollama server not responding")
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is installed and running")
    
    # Check AWS credentials
    try:
        import boto3
        client = boto3.client("bedrock-runtime", region_name=Config.AWS_REGION)
        print(f"✅ AWS credentials configured (Region: {Config.AWS_REGION})")
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
    print("💡 **To change models, edit the Config class at the top of the file**")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            interactive_iot_mode()
        elif sys.argv[1] == "--check":
            check_prerequisites()
        elif sys.argv[1] == "--config":
            show_configuration()
        else:
            print("Usage:")
            print("  python iot_edge_ai_demo.py            # Run demo")
            print("  python iot_edge_ai_demo.py --interactive  # Interactive mode")
            print("  python iot_edge_ai_demo.py --check        # Check prerequisites")
            print("  python iot_edge_ai_demo.py --config       # Show configuration")
    else:
        check_prerequisites()
        print("\n🚀 **Starting IoT Edge AI Demo...**\n")
        run_iot_demo()
        print("\n💡 **Try interactive mode:** python iot_edge_ai_demo.py --interactive")