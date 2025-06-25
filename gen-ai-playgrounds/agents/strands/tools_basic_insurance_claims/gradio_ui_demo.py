# Simple Device Protection Demo with Knowledge Base
# Consolidated multi-tool responses

import logging
import datetime
import asyncio
import io
from typing import Dict
from dataclasses import dataclass
import gradio as gr

# Configure logging - EXACTLY AS YOUR ORIGINAL
logging.getLogger("strands").setLevel(logging.INFO)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

# Create a string buffer to capture both logs and print statements
log_buffer = io.StringIO()

# Custom print function that captures to our buffer
original_print = print
def custom_print(*args, **kwargs):
    # Print to console as usual
    original_print(*args, **kwargs)
    # Also capture to our buffer
    if args:
        message = ' '.join(str(arg) for arg in args)
        log_buffer.write(message + '\n')
        log_buffer.flush()

# Replace the built-in print function
print = custom_print

from strands import Agent, tool

# Simple knowledge base - EXACTLY AS YOUR ORIGINAL
DEVICE_KB = {
    "coverage_types": {
        "complete": ["cracked_screen", "water_damage", "theft", "lost"],
        "basic": ["cracked_screen", "accidental_damage"],
        "theft_only": ["theft", "lost"]
    },
    "deductibles": {
        "iPhone": 199,
        "Samsung": 149, 
        "iPad": 99
    },
    "repair_times": {
        "cracked_screen": "2-3 days",
        "water_damage": "replace immediately",
        "theft": "24 hours after police report",
        "lost": "24 hours"
    }
}

# Simple data structures - EXACTLY AS YOUR ORIGINAL
@dataclass
class SimpleClaimData:
    claim_id: str
    customer: str
    device: str
    issue: str
    status: str
    deductible: int

# Mock databases - EXACTLY AS YOUR ORIGINAL
claims_db = {}
customers_db = {
    "DEV-001": {"name": "John Smith", "device": "iPhone 15", "coverage": "complete"},
    "DEV-002": {"name": "Sarah Johnson", "device": "Samsung S24", "coverage": "basic"},
    "DEV-003": {"name": "Mike Brown", "device": "iPad Pro", "coverage": "theft_only"}
}

# Enhanced tools with detailed logging - GRADIO COMPATIBLE
@tool
def get_user_input(prompt: str = "What's your device protection policy number") -> str:
    """Get missing information from the customer to complete their device protection request.
    
    Use this tool when a customer needs help but hasn't provided required information
    like their policy number or details about what happened to their device.
    Essential for identifying the customer and understanding their claim before processing.
    
    Args:
        prompt: Question to ask the customer for missing information
        
    Returns:
        str: The customer's response with the requested information
    """
    print(f"🛠️ USING TOOL: get_user_input")
    print(f"🔍 DATABASE LOG: Prompting user for input...")
    print(f"❓ ASKING USER: {prompt}")
    
    # Instead of blocking input(), return a special message that tells the agent to ask the user
    # This will cause the agent to respond with a question instead of hanging
    special_response = f"NEED_USER_INPUT: {prompt}"
    print(f"📝 RETURNING REQUEST FOR USER INPUT: {special_response}")
    return special_response

@tool
def check_customer(policy_id: str) -> Dict:
    """Look up customer information and device details by their protection policy number.
    
    Use this tool to validate a customer's device protection policy and retrieve their
    account information including covered device, coverage type, and personal details.
    This is the first step in most claim processing workflows.
    
    Args:
        policy_id: The device protection policy number (format: DEV-XXX)
        
    Returns:
        Dict: Customer information including name, device type, coverage level, and policy status
    """
    print(f"🛠️ USING TOOL: check_customer")
    print(f"🔍 DATABASE LOG: Searching customers_db for policy '{policy_id}'")
    print(f"📊 AVAILABLE POLICIES: {list(customers_db.keys())}")
    
    if policy_id in customers_db:
        customer = customers_db[policy_id]
        print(f"✅ CUSTOMER FOUND: {customer}")
        return {
            "found": True,
            "name": customer["name"],
            "device": customer["device"], 
            "coverage": customer["coverage"]
        }
    
    print(f"❌ CUSTOMER NOT FOUND: Policy {policy_id} not in database")
    return {"found": False, "message": "Policy not found"}

@tool
def check_coverage(coverage_type: str, incident: str) -> Dict:
    """Verify if a specific type of device incident is covered under the customer's protection plan.
    
    Use this tool to determine coverage eligibility for different types of device damage
    or loss incidents. Essential for claim approval decisions and setting customer expectations.
    
    Args:
        coverage_type: The customer's coverage plan type (complete, basic, theft_only)
        incident: The type of incident that occurred (cracked_screen, water_damage, theft, lost, etc.)
        
    Returns:
        Dict: Coverage determination with incident details and coverage type confirmation
    """
    print(f"🛠️ USING TOOL: check_coverage")
    print(f"🔍 KNOWLEDGE BASE LOG: Checking coverage for incident '{incident}' under '{coverage_type}' plan")
    print(f"📚 KB COVERAGE_TYPES: {DEVICE_KB['coverage_types']}")
    
    covered_incidents = DEVICE_KB["coverage_types"].get(coverage_type, [])
    is_covered = incident in covered_incidents
    
    print(f"📋 COVERAGE RESULT: '{incident}' {'✅ COVERED' if is_covered else '❌ NOT COVERED'} under '{coverage_type}'")
    print(f"📋 COVERED INCIDENTS FOR {coverage_type}: {covered_incidents}")
    
    return {
        "covered": is_covered,
        "incident": incident,
        "coverage_type": coverage_type
    }

@tool
def calculate_cost(device: str, incident: str) -> Dict:
    """Calculate the deductible amount and estimated repair timeline for a device incident.
    
    Use this tool to provide customers with cost information and service timelines
    based on their device type and the nature of the damage. Helps customers make
    informed decisions about proceeding with claims.
    
    Args:
        device: The specific device model (e.g., "iPhone 15 Pro", "Samsung Galaxy S24")
        incident: The type of incident requiring service (cracked_screen, water_damage, theft, etc.)
        
    Returns:
        Dict: Deductible amount, estimated timeline, and device information
    """
    device_type = device.split()[0]  # iPhone, Samsung, iPad
    print(f"🛠️ USING TOOL: calculate_cost")
    print(f"🔍 KNOWLEDGE BASE LOG: Looking up costs for device type '{device_type}' and incident '{incident}'")
    print(f"💰 KB DEDUCTIBLES: {DEVICE_KB['deductibles']}")
    print(f"⏰ KB REPAIR_TIMES: {DEVICE_KB['repair_times']}")
    
    deductible = DEVICE_KB["deductibles"].get(device_type, 150)
    timeline = DEVICE_KB["repair_times"].get(incident, "3-5 days")
    
    print(f"💵 COST CALCULATION: {device_type} → ${deductible} deductible")
    print(f"⏱️ TIME CALCULATION: {incident} → {timeline}")
    
    return {
        "deductible": deductible,
        "timeline": timeline,
        "device": device
    }

@tool
def file_claim(policy_id: str, incident: str) -> Dict:
    """Create and process a new device protection claim in the system.
    
    Use this tool to officially file a claim after verifying policy validity and coverage.
    This generates a claim ID, calculates final costs, and initiates the claim workflow.
    Only use after confirming policy and incident details.
    
    Args:
        policy_id: Valid device protection policy number (format: DEV-XXX)
        incident: Specific description of what happened to the device
        
    Returns:
        Dict: Claim confirmation with claim ID, customer details, device info, and deductible amount
    """
    print(f"🛠️ USING TOOL: file_claim")
    print(f"🔍 DATABASE LOG: Filing claim for policy '{policy_id}' with incident '{incident}'")
    print(f"📊 CURRENT CLAIMS COUNT: {len(claims_db)}")
    
    if policy_id not in customers_db:
        print(f"❌ CLAIM FILING FAILED: Policy {policy_id} not found in customers_db")
        return {"success": False, "message": "Policy not found"}
    
    claim_id = f"CLM-{len(claims_db) + 1:03d}"
    customer = customers_db[policy_id]
    
    device_type = customer["device"].split()[0]
    deductible = DEVICE_KB["deductibles"].get(device_type, 150)
    
    print(f"🆔 GENERATING CLAIM ID: {claim_id}")
    print(f"👤 CUSTOMER FROM DB: {customer}")
    print(f"💰 DEDUCTIBLE FROM KB: ${deductible}")
    
    claim = SimpleClaimData(
        claim_id=claim_id,
        customer=customer["name"],
        device=customer["device"],
        issue=incident,
        status="approved",
        deductible=deductible
    )
    
    claims_db[claim_id] = claim
    print(f"✅ CLAIM STORED: {claim_id} added to claims_db")
    print(f"📊 NEW CLAIMS COUNT: {len(claims_db)}")
    
    return {
        "success": True,
        "claim_id": claim_id,
        "customer": customer["name"],
        "device": customer["device"],
        "deductible": deductible
    }

@tool
def get_claim_summary() -> Dict:
    """Generate a comprehensive summary report of all device protection claims in the system.
    
    Use this tool to provide customers or agents with an overview of claim activity,
    including total claims count, recent claim details, and system status.
    Useful for reporting and customer service inquiries.
    
    Returns:
        Dict: Summary statistics and list of recent claims with key details
    """
    print(f"🛠️ USING TOOL: get_claim_summary")
    print(f"🔍 DATABASE LOG: Generating claims summary from claims_db")
    print(f"📊 TOTAL CLAIMS IN DB: {len(claims_db)}")
    print(f"📋 ALL CLAIMS: {list(claims_db.keys())}")
    
    if not claims_db:
        print(f"📝 SUMMARY RESULT: No claims found")
        return {"total": 0, "message": "No claims filed"}
    
    recent_claims = list(claims_db.values())[-3:]
    print(f"📋 RECENT CLAIMS (last 3): {[claim.claim_id for claim in recent_claims]}")
    
    return {
        "total": len(claims_db),
        "recent_claims": [
            {
                "id": claim.claim_id,
                "customer": claim.customer,
                "device": claim.device,
                "issue": claim.issue,
                "status": claim.status
            }
            for claim in recent_claims
        ]
    }

# Create simple agent - UPDATED TO HANDLE USER INPUT REQUESTS
device_agent = Agent(
    system_prompt="""You are DeviceBot, a helpful device protection assistant.

Use the available tools to help customers with device claims. Always:
1. Check customer info first
2. Verify coverage for their issue  
3. Calculate costs and timeline
4. File claim if everything checks out

Keep responses simple and friendly. Consolidate information from multiple tools into clear, helpful answers.

IMPORTANT: If any tool returns "NEED_USER_INPUT: [question]", immediately ask the user that question and wait for their response in the next message. Do not continue processing until you get the user's answer.""",
    
    tools=[check_customer, check_coverage, calculate_cost, file_claim, get_claim_summary, get_user_input]
)

# Function to capture and return current logs
def get_current_logs():
    """Get current logs from the buffer"""
    log_content = log_buffer.getvalue()
    return log_content

def clear_logs():
    """Clear the log buffer"""
    global log_buffer
    log_buffer.truncate(0)
    log_buffer.seek(0)

# Simple streaming function
async def stream_agent_response(query: str):
    """Stream agent response similar to FastAPI example"""
    try:
        async for event in device_agent.stream_async(query):
            # Capture tool events in logs - SIMPLE VERSION            
            if "data" in event:
                # Only stream the final text chunks to the client
                yield event["data"]
    except Exception as e:
        error_msg = f"❌ STREAM ERROR: {str(e)}"
        log_buffer.write(error_msg + '\n')
        log_buffer.flush()
        yield f"Error: {str(e)}"

# Simple chat function for Gradio
def stream_chat_response(message: str, history, logs_display: str):
    """Simple streaming chat function"""
    if not message.strip():
        yield history, "", logs_display
        return
    
    # Clear previous logs
    #clear_logs()
    
    # Add user message to history - SIMPLE TUPLE FORMAT
    history.append([message, ""])
    yield history, "", logs_display
    
    # Stream the response
    response_text = ""
    try:
        # Create new event loop for this request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Get the async generator
            async_gen = stream_agent_response(message)
            
            while True:
                try:
                    # Get next chunk from stream
                    chunk = loop.run_until_complete(async_gen.__anext__())
                    response_text += chunk
                    
                    # Update the last message in history - SIMPLE TUPLE FORMAT
                    history[-1][1] = response_text
                    
                    # Get current logs
                    current_logs = get_current_logs()
                    
                    # Yield updated state
                    yield history, "", current_logs
                    
                except StopAsyncIteration:
                    break
                    
        finally:
            loop.close()
            
    except Exception as e:
        history[-1][1] = f"Error: {str(e)}"
        current_logs = get_current_logs() + f"\n❌ ERROR: {str(e)}"
        yield history, "", current_logs

def clear_chat():
    """Clear chat history and logs"""
    clear_logs()
    return [], "", ""

def load_example_and_reset(example_text):
    """Load example query and reset session for new scenario"""
    # Clear logs for fresh start
    clear_logs()
    # Return: empty chat history, example text in input, empty logs
    return [], example_text, ""

# Simple Gradio Interface
def create_gradio_interface():
    """Create the Gradio interface"""
    
    # Example queries for quick testing - EXACTLY AS YOUR ORIGINAL
    examples = [
        "Policy DEV-001, cracked iPhone screen. Check coverage, cost, timeline, and file claim if covered.",
        "Policy DEV-002, water damage Samsung. Check if covered, get replacement cost, timeline, and process claim.",
        "Policy DEV-003, iPad theft. Verify theft coverage and process claim immediately.",
        "Policy DEV-001, both cracked screen and water damage. Check coverage for both, compare costs, recommend best approach.",
        "My phone broke. Can you help me file a claim?",
        "Show me a summary of all claims in the system."
    ]
    
    with gr.Blocks(title="DeviceBot - Device Protection Assistant", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 📱 DeviceBot - Device Protection Assistant
        
        **Available Test Policies:**
        - DEV-001: John Smith, iPhone 15, Complete Coverage
        - DEV-002: Sarah Johnson, Samsung S24, Basic Coverage  
        - DEV-003: Mike Brown, iPad Pro, Theft Only Coverage
        
        **Supported Incidents:** cracked_screen, water_damage, theft, lost, accidental_damage
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                # Simple chat interface
                chatbot = gr.Chatbot(
                    height=400,
                    show_label=False,
                    container=True
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="Ask about device protection, file claims, check coverage...",
                        show_label=False,
                        scale=4,
                        container=False
                    )
                    submit_btn = gr.Button("Send", scale=1, variant="primary")
                
                with gr.Row():
                    clear_btn = gr.Button("Clear Chat", scale=1)
                
            with gr.Column(scale=1):
                gr.Markdown("### 📋 Quick Examples")
                
                example_buttons = []
                for i, example in enumerate(examples):
                    btn = gr.Button(f"Example {i+1}: {example[:30]}...", size="sm")
                    example_buttons.append((btn, example))
        
        # Logs area
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 🔍 Live Agent Logs (What's happening behind the scenes)")
                logs_display = gr.Textbox(
                    label="Agent Activity Logs",
                    lines=15,
                    max_lines=20,
                    interactive=False,
                    show_copy_button=True,
                    placeholder="Tool execution logs will appear here in real-time..."
                )
        
        # Event handlers - ALWAYS USE STREAMING
        submit_btn.click(
            stream_chat_response,
            inputs=[msg, chatbot, logs_display],
            outputs=[chatbot, msg, logs_display]
        )
        
        msg.submit(
            stream_chat_response,
            inputs=[msg, chatbot, logs_display], 
            outputs=[chatbot, msg, logs_display]
        )
        
        clear_btn.click(
            clear_chat,
            outputs=[chatbot, msg, logs_display]
        )
        
        # Wire up example buttons - RESET SESSION FOR NEW SCENARIOS
        for btn, example_text in example_buttons:
            btn.click(
                load_example_and_reset,
                inputs=[gr.State(example_text)],
                outputs=[chatbot, msg, logs_display]
            )
    
    return demo

# Main execution
if __name__ == "__main__":
    # Use original print for startup messages
    original_print("🚀 Starting DeviceBot with Gradio UI...")
    original_print("📊 Database initialized with 3 test policies")
    original_print("🔧 Tools loaded: check_customer, check_coverage, calculate_cost, file_claim, get_claim_summary")
    original_print("🌐 Starting Gradio interface...")
    
    # Create and launch the interface
    demo = create_gradio_interface()
    
    # Launch with proper settings
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=True,
        show_error=True,
        quiet=False
    )