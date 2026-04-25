from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from agent.financial_agent import FinancialAgent

app = FastAPI(title="Finance Risk AI Agent API")

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialisation du cerveau de notre application
financial_agent = FinancialAgent()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r") as f:
        return f.read()

@app.post("/api/analyze")
async def analyze_company(
    company_name: str = Form(...),
    document: UploadFile = File(None)
):
    reports = []
    document_content = None
    filename = ""
    
    if document and document.filename:
        document_content = await document.read()
        filename = document.filename
        reports.append(f"Document reçu: {filename} ({len(document_content)} octets)")

    # La véritable passe de l'Agent IA !
    analysis_result = financial_agent.analyze(company_name, document_content, filename)
    analysis_result["logs"] = reports
    
    return analysis_result

@app.post("/api/chat")
async def chat_with_agent(message: str = Form(...)):
    """ Tchat IA Intercatif """
    if financial_agent.mock_mode:
        reply = f"[Mode Démo] Je vois que vous demandez : '{message}'. Entrez une clé API Gemini dans le fichier `.env` pour débloquer ma conscience LLM !"
    else:
        try:
            response = financial_agent.llm.invoke([
                ("system", "Tu es un agent d'analyse financière pointu et très cinglant si les chiffres sont mauvais. Réponds brièvement à l'analyste qui t'utilise."),
                ("user", message)
            ])
            reply = response.content
        except Exception as e:
            reply = f"Erreur de réseau : {str(e)}"
            
    return {"reply": reply}

if __name__ == "__main__":
    import uvicorn
    # Important de pas mettre use_reloader si lancé programmatiquement en background parfois.
    uvicorn.run(app, host="0.0.0.0", port=8000)
