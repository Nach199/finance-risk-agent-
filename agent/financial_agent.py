import os
import fitz  # PyMuPDF
from pydantic import BaseModel, Field
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from dotenv import load_dotenv

# Charger les variables d'environnement (comme GEMINI_API_KEY)
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
        # Vérification de la configuration d'API Key
        api_key = os.getenv("GEMINI_API_KEY")
        self.mock_mode = not api_key
        
        if not self.mock_mode:
            print("🧠 Modèle LLM initialisé avec LangChain et Gemini.")
            # On utilise le modèle le plus avancé disponible pour ses capacités analytiques
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro", 
                temperature=0.1, 
                google_api_key=api_key
            )
            # Paramétrage du parseur Pydantic pour avoir une certitude structurelle
            self.parser = PydanticOutputParser(pydantic_object=AnalysisResult)
            
            # Prompting avancé avec instructions de formattage injectées
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", 
                 "Tu es un Agent Analyste en Risques Financiers senior travaillant pour un fonds d'investissement. "
                 "Ton but est d'évaluer la santé financière d'une entreprise pour déterminer si lui accorder "
                 "un crédit ou la financer est risqué. Sois toujours objectif, très analytique, et sans pitié sur les faiblesses.\n\n"
                 "{format_instructions}"
                ),
                ("user", "Analyse le document financier suivant pour l'entreprise '{company_name}':\n\n{financial_text}")
            ])
            # Création du pipeline LangChain
            self.chain = self.prompt | self.llm | self.parser

    def extract_text(self, document_content: bytes, filename: str) -> str:
        """Utilise PyMuPDF pour parser numériquement le texte d'un PDF."""
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

    def analyze(self, company_name: str, document_content: Optional[bytes] = None, filename: str = "") -> dict:
        """Lance la chaîne cognitive LangChain sur le contexte."""
        
        financial_text = "Aucun document n'a été fourni. Invente juste des chiffres très incohérents pour forcer un constat de risque."
        
        if document_content:
            extracted_text = self.extract_text(document_content, filename)
            # Limite le token context window (Gemini 1.5 gère beaucoup, mais par sécurité)
            financial_text = extracted_text[:40000] 

        if self.mock_mode:
            print("⚠️ Mode Mock activé (Pas de GEMINI_API_KEY). Retourne des résultats simulés.")
            return self._get_mock_result(company_name)

        try:
            print(f"🚀 Lancement de l'Analyse d'IA de {company_name}...")
            # Déclenchement de la magie LangChain !
            result = self.chain.invoke({
                "company_name": company_name,
                "financial_text": financial_text,
                "format_instructions": self.parser.get_format_instructions()
            })
            return result.dict()
        except Exception as e:
            print(f"❌ Erreur critique de l'IA: {e}")
            return self._get_mock_result(company_name, error=str(e))

    def _get_mock_result(self, company_name: str, error: str = None) -> dict:
        """Résultat de rechange quand il n'y a pas d'API."""
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
                "Pour activer mon cerveau, créez un fichier .env à la racine avec: GEMINI_API_KEY=votre_clé."
            )
        }
