"""
Expert Insights MCP Server
Run: python expert_server.py
"""

import boto3
from botocore.exceptions import ClientError
from fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("Expert Insights Server")

@mcp.tool(description="Get expert analysis - requires context_data and question parameters")
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

if __name__ == "__main__":
    # Run the server with HTTP transport on port 8003
    print("🔧 Starting Expert Insights MCP Server on port 8003...")
    mcp.run(transport="http", host="127.0.0.1", port=8003, path="/mcp")