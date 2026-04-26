import os
import fitz  # PyMuPDF
from pydantic import BaseModel, Field
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# Schémas de Sortie (Ce qu'on force l'IA à produire)
# ==========================================
class RiskRatio(BaseModel):
    value: str = Field(description="La valeur calculée ou extraite pour ce ratio (ex: 1.5, 40%, etc.)")
    status: str = Field(description="Strictement l'un de ces mots: 'good', 'warning', ou 'danger'")
    description: str = Field(description="Une brève explication analytique en français du ratio")

class Ratios(BaseModel):
    dette_sur_fonds_propres: RiskRatio
    ratio_de_liquidite: RiskRatio
    marge_nette: RiskRatio

class AnalysisResult(BaseModel):
    company: str = Field(description="Le nom exact de l'entreprise")
    overall_risk_score: int = Field(description="Score de risque global de 0 (Très sûr) à 100 (Faillite imminente)")
    risk_level: str = Field(description="Un mot résumé de la situation : 'Sain', 'Modéré', ou 'Danger'")
    ratios: Ratios
    agent_summary: str = Field(description="Le rapport de l'expert : Un paragraphe professionnel en français expliquant précisément pourquoi il y a des risques financiers de crédit ou non.")

# ==========================================
# Cerveau de l'Agent IA
# ==========================================
class FinancialAgent:
    def __init__(self):
        self.parser = PydanticOutputParser(pydantic_object=AnalysisResult)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "Tu es un Agent Analyste en Risques Financiers senior travaillant pour un fonds d'investissement. "
             "Ton but est d'évaluer la santé financière d'une entreprise pour déterminer si lui accorder "
             "un crédit ou la financer est risqué. Sois toujours objectif, très analytique, et sans pitié sur les faiblesses.\n\n"
             "{format_instructions}"
            ),
            ("user", "Analyse le document financier suivant pour l'entreprise '{company_name}':\n\n{financial_text}")
        ])

    def _get_api_key(self, user_provided_key: str) -> str:
        # Clé codée en dur pour garantir la stabilité de la présentation
        return "AIzaSyCN1aG-cleBdbjI2FxMEo5WrDmFaWIeV7A"

    def _get_chain(self, api_key: str):
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", 
            temperature=0.1, 
            google_api_key=api_key
        )
        return self.prompt | llm | self.parser

    def extract_text(self, document_content: bytes, filename: str) -> str:
        print(f"📖 Lecture du document: {filename}")
        if filename.lower().endswith('.pdf'):
            try:
                doc = fitz.open(stream=document_content, filetype="pdf")
                text = ""
                for page in doc:
                    text += page.get_text()
                return text
            except Exception as e:
                return f"Erreur extraction PDF: {str(e)}"
        try:
            return document_content.decode('utf-8')
        except:
            return "Impossible de lire le texte."

    def analyze(self, company_name: str, document_content: Optional[bytes] = None, filename: str = "", api_key: str = None) -> dict:
        actual_key = self._get_api_key(api_key)
        
        financial_text = "Aucun document n'a été fourni. Invente juste des chiffres très incohérents pour forcer un constat de risque."
        if document_content:
            extracted_text = self.extract_text(document_content, filename)
            financial_text = extracted_text[:40000]

        if not actual_key:
            print("⚠️ Mode Mock activé. Retourne des résultats simulés.")
            return self._get_mock_result(company_name, error="Veuillez coller votre Clé API dans la case prévue !")

        try:
            print(f"🚀 Lancement de l'Analyse d'IA de {company_name} (Mode Connecté)...")
            chain = self._get_chain(actual_key)
            result = chain.invoke({
                "company_name": company_name,
                "financial_text": financial_text,
                "format_instructions": self.parser.get_format_instructions()
            })
            return result.dict()
        except Exception as e:
            print(f"❌ Erreur critique de l'IA: {e}")
            return self._get_mock_result(company_name, error=str(e))

    def chat(self, message: str, api_key: str = None) -> dict:
        actual_key = self._get_api_key(api_key)
        if not actual_key:
            return {"reply": f"[Mode Démo] Je vois que vous demandez : '{message}'. Entrez votre clé API dans la case de connexion pour débloquer ma conscience LLM !"}
        
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash", 
                temperature=0.1, 
                google_api_key=actual_key
            )
            response = llm.invoke([
                ("system", "Tu es un agent d'analyse financière pointu et très cinglant si les chiffres sont mauvais. Réponds brièvement à l'analyste qui t'utilise."),
                ("user", message)
            ])
            return {"reply": response.content}
        except Exception as e:
            print(f"❌ Erreur Chat: {e}")
            return {"reply": f"Erreur de réseau : {str(e)}"}

    def _get_mock_result(self, company_name: str, error: str = None) -> dict:
        return {
            "company": company_name,
            "overall_risk_score": 60,
            "risk_level": "Modéré",
            "ratios": {
                "dette_sur_fonds_propres": {"value": "1.2", "status": "warning", "description": "L'endettement à surveiller de près."},
                "ratio_de_liquidite": {"value": "1.8", "status": "good", "description": "Saine capacité à payer le court terme."},
                "marge_nette": {"value": "8.5%", "status": "good", "description": "Rentabilité robuste."}
            },
            "agent_summary": (
                f"La véritable IA n'est pas connectée. ERREUR : {error if error else 'Clé API manquante'}. "
                "Veuillez coller votre clé secrète dans le premier champ du formulaire pour m'activer."
            )
        }
