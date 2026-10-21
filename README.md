# SmartBazaar AI — Amazon Developer Hackathon 2026

**Honest scope:** A local Alexa+-inspired *simulation* plus a separate MCP Streamable HTTP server. This project **does not** connect to actual Alexa+, Amazon accounts, or real inventory. Searches use a fictional sample catalog and deterministic rules. Voice recognition uses browser functionality where available, not a paid AI API.

## Setup — Windows / PyCharm / Python 3.11

Create a new virtual environment, then run:

```powershell
python -m pip install -r requirements.txt
```

### Start web demo (Terminal 1)
```powershell
python main.py
```
Open http://127.0.0.1:5001

### Start MCP server (Terminal 2)
```powershell
python mcp_server.py
```
Streamable HTTP MCP endpoint: http://127.0.0.1:8000/mcp

### Test HTTP and MCP tools
```powershell
python verify.py
```
This exercises the Flask chat/search API and the actual MCP Streamable HTTP tool calls. Run both services first.

## Demo suggestions
1. Show the web demo and click “Blue kurti under ₹1000”.
2. Click the Telugu and Hindi sample prompts, explaining that query matching is multilingual and rule-based.
3. Try “yellow dress under 900” and explain why the filtered result is empty.
4. Show `python verify.py` passing to demonstrate the MCP search tool running over HTTP.
5. Clearly state that Alexa+ is simulated, not integrated, and that inventory/prices are fictional.

## Technology
Python, Flask, HTML/CSS/JavaScript, official Python `mcp` SDK, browser SpeechRecognition (optional); no cloud services and no generative model/API.

## Limitations
- Rule-based language matching (small supported vocabulary), not general multilingual understanding.
- Browser microphone recognition is browser/platform dependent; typed prompts work even without it.
- MCP endpoint is bound to localhost only. For judges to test remotely, they should clone repo and follow the README.
- No live inventory, checkout, Alexa+ account integration, or real Alexa device.

## Submission
Publish source code to a public GitHub repository with a suitable open-source license (e.g., MIT, if you choose to grant those permissions). The Devpost submission also requires a public English YouTube/Vimeo demo under 3 minutes and real developer-tool feedback. Add team member in Devpost Manage team.
