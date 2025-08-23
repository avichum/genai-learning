"""
Vision Analysis MCP Server
Run: python vision_server.py
"""

import os
# Set port before importing FastMCP
os.environ['PORT'] = '8002'

import ollama
from fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("Vision Analysis Server")

@mcp.tool(description="Analyze images from cameras - requires image_path parameter")
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

if __name__ == "__main__":
    # Run the server with HTTP transport on port 8002
    print("🔧 Starting Vision Analysis MCP Server on port 8002...")
    mcp.run(transport="http", host="127.0.0.1", port=8002, path="/mcp")