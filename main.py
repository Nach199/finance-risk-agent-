from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from agent.financial_agent import FinancialAgent

app = FastAPI(title="Finance Risk AI Agent API")

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

financial_agent = FinancialAgent()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r") as f:
        return f.read()

@app.post("/api/analyze")
async def analyze_company(
    company_name: str = Form(...),
    document: UploadFile = File(None),
    api_key: str = Form(None)
):
    reports = []
    document_content = None
    filename = ""
    
    if document and document.filename:
        document_content = await document.read()
        filename = document.filename
        reports.append(f"Document reçu: {filename} ({len(document_content)} octets)")

    analysis_result = financial_agent.analyze(company_name, document_content, filename, api_key=api_key)
    analysis_result["logs"] = reports
    return analysis_result

@app.post("/api/chat")
async def chat_with_agent(
    message: str = Form(...),
    api_key: str = Form(None)
):
    return financial_agent.chat(message, api_key)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
