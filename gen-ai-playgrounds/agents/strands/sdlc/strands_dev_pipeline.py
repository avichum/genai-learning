from strands import Agent, tool
from strands_tools import file_write, file_read
import os
import shutil

# Setup SDLC folder for workshop artifacts
def setup_workshop_folder():
    """Setup clean SDLC folder for workshop artifacts"""
    if os.path.exists("sdlc"):
        shutil.rmtree("sdlc")
    os.makedirs("sdlc")
    os.chdir("sdlc")

# Initialize workshop environment
setup_workshop_folder()

# Requirements creation agent
REQUIREMENTS_ANALYST_PROMPT = """You are a specialized requirements analyst. 
Your job is to analyze use cases and generate CONCISE, focused requirements documents 
suitable for workshops. Keep it short and clear - include only essential functional 
requirements, basic technical requirements, and key acceptance criteria. 
Maximum 10-15 lines total."""

@tool
def requirements_analyst(use_case: str) -> str:
    """
    Analyze use case and generate comprehensive requirements document.
    
    Args:
        use_case: A use case description to analyze and create requirements for
        
    Returns:
        Path to the generated requirements file
    """
    try:
        # Create specialized requirements agent
        requirements_agent = Agent(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            system_prompt=REQUIREMENTS_ANALYST_PROMPT,
            tools=[file_write]
        )
        
        # Generate requirements and save to file
        prompt = f"Analyze this use case: '{use_case}' and generate comprehensive requirements. Save the requirements document to 'requirements.md' file."
        
        response = requirements_agent(prompt)
        return "requirements.md"
        
    except Exception as e:
        return f"Error in requirements analysis: {str(e)}"

# Design architect agent
DESIGN_ARCHITECT_PROMPT = """You are a specialized system architect. 
Your job is to read requirements documents and create concise design documents that include:
1. System design and architecture 
2. Task breakdown and development plan
3. Simple directory structure (this is a workshop - keep it simple, not complex)
Keep it workshop-friendly and focused. Focus ONLY on creating the design document."""

@tool
def design_architect(requirements_file_path: str) -> str:
    """
    Read requirements and create system design with directory structure.
    
    Args:
        requirements_file_path: Path to the requirements document to read
        
    Returns:
        Path to the generated design document
    """
    try:
        # Create specialized design architect agent
        architect_agent = Agent(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            system_prompt=DESIGN_ARCHITECT_PROMPT,
            tools=[file_read, file_write]
        )
        
        # Read requirements and create simple design document for workshop
        prompt = f"Read the requirements from '{requirements_file_path}' using file_read tool, then create a design document that includes: 1) System design and architecture, 2) Task breakdown and development plan, 3) Simple directory structure (workshop format - keep it simple). Save to 'design.md' file."
        
        response = architect_agent(prompt)
        return "design.md"
        
    except Exception as e:
        return f"Error in system design: {str(e)}"

# Code developer agent
CODE_DEVELOPER_PROMPT = """You are a specialized software developer. 
Your job is to read design documents and create working code files based on the design.
Create simple, clean, workshop-appropriate code. Focus on functionality over complexity.
Read the design document and implement all necessary code files."""

@tool
def code_developer(design_file_path: str) -> str:
    """
    Read design document and create code files based on the design.
    
    Args:
        design_file_path: Path to the design document to read
        
    Returns:
        Status of code generation
    """
    try:
        # Create specialized code developer agent
        developer_agent = Agent(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            system_prompt=CODE_DEVELOPER_PROMPT,
            tools=[file_read, file_write]
        )
        
        # Read design and create code files
        prompt = f"Read the design document from '{design_file_path}' using file_read tool, then create all necessary code files based on the design specifications. Use file_write to create each code file."
        
        response = developer_agent(prompt)
        return "Code files created successfully"
        
    except Exception as e:
        return f"Error in code development: {str(e)}"

# Orchestrator agent
ORCHESTRATOR_PROMPT = """You are a software development orchestrator. 
For any software development request:
1. First use the requirements_analyst tool to create requirements
2. Then use the design_architect tool to create system design and structure
3. Then use the code_developer tool to create the actual code"""

# Create orchestrator with all tools
orchestrator = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    system_prompt=ORCHESTRATOR_PROMPT,
    tools=[requirements_analyst, design_architect, code_developer]
)

# Usage - Ask user for input
print("🚀 Welcome to the AI Software Development Workshop!")
print("=" * 50)
use_case = input("Please enter your software development request: ")
print(f"\n📝 Processing request: {use_case}")
print("🤖 Starting development pipeline...\n")

result = orchestrator(use_case)