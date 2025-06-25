# Simple Device Protection Demo with Knowledge Base
# Consolidated multi-tool responses

import logging
import datetime
from typing import Dict
from dataclasses import dataclass

# Configure logging
logging.getLogger("strands").setLevel(logging.INFO)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

from strands import Agent, tool

# Simple knowledge base
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

# Simple data structures
@dataclass
class SimpleClaimData:
    claim_id: str
    customer: str
    device: str
    issue: str
    status: str
    deductible: int

# Mock databases
claims_db = {}
customers_db = {
    "DEV-001": {"name": "John Smith", "device": "iPhone 15", "coverage": "complete"},
    "DEV-002": {"name": "Sarah Johnson", "device": "Samsung S24", "coverage": "basic"},
    "DEV-003": {"name": "Mike Brown", "device": "iPad Pro", "coverage": "theft_only"}
}

# Enhanced tools with detailed logging
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
    print(f"🔍 DATABASE LOG: Prompting user for input...")
    user_response = input(f"{prompt}: ")
    print(f"📝 INPUT RECEIVED: '{user_response}'")
    return user_response

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

@tool
def get_claim_summary() -> Dict:
    """Get simple claims summary"""
    if not claims_db:
        return {"total": 0, "message": "No claims filed"}
    
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
            for claim in list(claims_db.values())[-3:]
        ]
    }

# Create simple agent
device_agent = Agent(
    system_prompt="""You are DeviceBot, a helpful device protection assistant.

Use the available tools to help customers with device claims. Always:
1. Check customer info first
2. Verify coverage for their issue  
3. Calculate costs and timeline
4. File claim if everything checks out

Keep responses simple and friendly. Consolidate information from multiple tools into clear, helpful answers.""",
    
    tools=[check_customer, check_coverage, calculate_cost, file_claim, get_claim_summary, get_user_input]
)

# 5 Consolidated Scenarios Demo
def run_device_demo():
    """5 scenarios showing consolidated multi-tool responses"""
    
    def show_menu():
        print("\n📱 Insurance Claim Demo")
        print("=" * 40)
        print("Customers: DEV-001 (John/iPhone), DEV-002 (Sarah/Samsung), DEV-003 (Mike/iPad)")
        print("\n🎯 Choose scenario:")
        print("1. 📱 Cracked Screen + Coverage Check + File Claim")
        print("2. 💧 Water Damage + Cost + Timeline + Process") 
        print("3. 🚨 Theft + Coverage Validation + Quick Claim")
        print("4. ❌ Multiple Issues + Coverage + Best Option")
        print("5. 🤔 Missing Details - Agent Asks for Policy & Damage Info")
        print("6. 🆕 No Details Given - Agent Asks Questions")
        print("7. 📊 New Claim + Update Summary + Status")
        print("8. Exit")
        print("=" * 40)
    
    while True:
        show_menu()
        choice = input("\nChoice (1-6): ").strip()
        
        if choice == "8":
            print("Demo complete!")
            break
        
        print(f"\n🔄 Scenario {choice} - Multi-tool consolidation...")
        
        if choice == "1":
            print("📱 Customer: 'My iPhone screen cracked, what's covered and how much?'")
            query = "Policy DEV-001, cracked iPhone screen. Check coverage, cost, timeline, and file claim if covered."
            print(f"🔍 Query to Agent: {query}")
            response = device_agent(query)
            print(f"\n✅ Agent Response:\n{response}")
            
        elif choice == "2":
            print("💧 Customer: 'Dropped Samsung in water, need replacement cost and timeline'")
            query = "Policy DEV-002, water damage Samsung. Check if covered, get replacement cost, timeline, and process claim."
            print(f"🔍 Query to Agent: {query}")
            response = device_agent(query)
            print(f"\n✅ Agent Response:\n{response}")
            
        elif choice == "3":
            print("🚨 Customer: 'iPad stolen, check my coverage and file claim quickly'")
            query = "Policy DEV-003, iPad theft. Verify theft coverage and process claim immediately."
            print(f"🔍 Query to Agent: {query}")
            response = device_agent(query)
            print(f"\n✅ Agent Response:\n{response}")
            
        elif choice == "4":
            print("❌ Customer: 'I have cracked screen AND water damage, what's my best option?'")
            query = "Policy DEV-001, both cracked screen and water damage. Check coverage for both, compare costs, recommend best approach."
            print(f"🔍 Query to Agent: {query}")
            response = device_agent(query)
            print(f"\n✅ Agent Response:\n{response}")
            
        elif choice == "5":
            print("📊 Customer: 'My phone broke. Can you help me file a claim?'")
            query = "My phone broke. Can you help me file a claim?"
            print(f"🔍 Query to Agent: {query}")
            response = device_agent(query)
            print(f"\n✅ Agent Response:\n{response}")
            
        elif choice == "6":
            print("🆕 NEW SCENARIO: Customer without any details")
            print("📱 Customer: 'I need help with my device claim'")
            query = "Customer needs help with device claim."
            print(f"🔍 Query to Agent: {query}")
            response = device_agent(query)
            print(f"\n✅ Agent Response:\n{response}")
            
            # Interactive follow-up - user enters response  
            print(f"\n🔄 **Agent asked questions. Enter customer's response:**")
            user_followup = input("Customer: ").strip()
            if user_followup:
                print(f"🔍 Follow-up Query to Agent: {user_followup}")
                follow_response = device_agent(user_followup)
                print(f"\n✅ Agent Follow-up Response:\n{follow_response}")
            
        elif choice == "7":
            print("📊 Customer: 'File new claim and show me all my claims status'")
            query = "Policy DEV-002, accidental damage. File claim and show summary of all claims in system."
            print(f"🔍 Query to Agent: {query}")
            response = device_agent(query)
            print(f"\n✅ Agent Response:\n{response}")
            
        else:
            print("❌ Choose 1-8")
            continue
        
        print("\n" + "🎯" * 15)
        print("Notice: AI used multiple tools but gave ONE consolidated answer")
        print("🎯" * 15)
        
        input("\nPress Enter for menu...")

if __name__ == "__main__":
    run_device_demo()