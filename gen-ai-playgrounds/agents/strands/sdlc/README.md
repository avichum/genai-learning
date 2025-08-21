# AI Software Development Workshop

An interactive workshop demonstrating multi-agent AI collaboration for software development using the Strands framework.

## What This Does

This workshop shows how AI agents can work together to build software from a simple user request:

1. **Requirements Analyst** - Analyzes your request and creates requirements document
2. **Design Architect** - Reads requirements and creates system design 
3. **Code Developer** - Reads design and generates working code files

## How to Run

```bash
python strands_dev_pipeline.py
```

The system will:
- Ask you to enter a software development request
- Automatically create an `sdlc/` folder for all artifacts
- Run the 3-agent pipeline
- Generate requirements, design, and code files

## Example Requests

- "Build a simple front end chatbot that uses a Bedrock Knowledge base to answer questions"
- "Create a todo list web application"
- "Build a weather dashboard with API integration"

## Output

All generated files are saved in the `sdlc/` folder:
- `requirements.md` - Project requirements
- `design.md` - System design and architecture  
- Various code files based on the design

## Workshop Focus

This demo emphasizes:
- **Agents as Tools** pattern
- Simple, workshop-appropriate outputs
- File-based agent communication
- Sequential pipeline execution

Perfect for demonstrating AI collaboration in software development! 🚀