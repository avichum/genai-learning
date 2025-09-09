"""
IoT Edge AI Monitoring Agent - FastAPI Backend
==============================================
Demonstrates NVIDIA Research insights: "Small Language Models are the Future of Agentic AI"

Complete end-to-end implementation with:
- Tool 1: Local telemetry monitoring (simulated IoT sensors)
- Tool 2: Real image analysis (Ollama vision model)  
- Tool 3: Complex analysis (Amazon Nova)

Run: uvicorn main:app --reload
"""

import json
import random
import time
import ollama
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os
import base64
from strands.models import BedrockModel

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
    MAIN_MODEL_TEMPERATURE = 0.7          
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

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(title="IoT Edge AI Monitoring", version="1.0.0")

# Initialize the agent
agent = create_agent()

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    processing_time: float

class ConfigResponse(BaseModel):
    main_model: str
    vision_model: str
    cloud_model: str
    ollama_host: str
    aws_region: str

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

# API Endpoints
@app.get("/")
async def get_chat_interface():
    """Serve the chat interface"""
    return HTMLResponse(content=open("chat_interface.html").read())

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Chat with the IoT monitoring agent"""
    try:
        start_time = time.time()
        response = agent(request.message)
        processing_time = time.time() - start_time
        
        return ChatResponse(
            response=str(response),
            timestamp=datetime.now().isoformat(),
            processing_time=processing_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image for analysis"""
    try:
        # Save uploaded file
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Analyze the image
        start_time = time.time()
        response = agent(f"Analyze the image at {file_path}")
        processing_time = time.time() - start_time
        
        return ChatResponse(
            response=str(response),
            timestamp=datetime.now().isoformat(),
            processing_time=processing_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get current configuration"""
    return ConfigResponse(
        main_model=get_model_display_name(Config.MAIN_MODEL_ID),
        vision_model=get_model_display_name(Config.VISION_MODEL_ID),
        cloud_model=get_model_display_name(Config.CLOUD_MODEL_ID),
        ollama_host=Config.OLLAMA_HOST,
        aws_region=Config.AWS_REGION
    )

@app.get("/devices")
async def get_devices():
    """Get list of available devices"""
    return {"devices": list(DEVICE_TELEMETRY.keys())}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)