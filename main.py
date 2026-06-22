from typing import (TypedDict, Literal, Optional)
from langgraph.graph import StateGraph, END
from pydantic import BaseModel,Field
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()


client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)

class GraphState(TypedDict):
    nome: Optional[str]
    draft: Optional[str]
    feedback: Optional[str]
    status: Optional[Literal["aceito", "rejeitado", "revisando"]]

class Status_classify(BaseModel):
    status: Literal["aceito", "rejeitado", "revisando"] = Field(
        description="The status based on response from analyst"
    )


def generate_draft(state:GraphState) -> dict:
    nome_empresa = state["nome"]
    draft_anterior = state.get("draft")
    feedback_humano = state.get("feedback")

    if draft_anterior and feedback_humano:
        prompt = f"""
        Seu nome é Lobo de Wall Street. Você é um analista financeiro experiente.
        Você já gerou um rascunho de relatório para a empresa {nome_empresa}, mas o analista sênior rejeitou com o seguinte feedback:
        
        "{feedback_humano}"
        
        Aqui está o rascunho anterior:
        ---
        {draft_anterior}
        ---
        
        Reescreva o relatório financeiro aplicando estritamente as correções solicitadas, mantendo o seu tom especialista e focado em Wall Street.
        """

    else:
        prompt = f"""
        Seu nome é Lobo de Wall Street. Você é um analista financeiro de Wall Street e precisa analisar a empresa {nome_empresa}.
        Gere um relatório financeiro robusto contendo:
        1. Faturamento estimado e performance de 2025.
        2. Principais Riscos de Mercado.
        3. Recomendação de Investimento (Comprar / Vender / Manter).
        Responda com autoridade, como um verdadeiro especialista da área.
        """


    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {"draft": response.text, "status": "revisando","feedback": None }

if __name__ == "__main__":
     # Certifique-se de que o import do seu 'client' está correto no topo do arquivo
    
    # 1. Inicializa o cliente que você usou no nó (caso precise instanciar aqui para o teste)
    # client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    # 2. Criamos um estado inicial simulando o GraphState do LangGraph
    estado_inicial: GraphState = {
        "nome": "Apple Inc.",
        "draft": None,
        "feedback": None,
        "status": None
    }

    print("🚀 Testando o nó 'generate_draft' pela primeira vez...\n")
    
    # 3. Chamamos a função do nó diretamente, passando o nosso estado simulado
    resultado_1 = generate_draft(estado_inicial)
    
    print("📊 STATUS RETORNADO:", resultado_1["status"])
    print("\n📝 RASCUNHO GERADO:")
    print("-" * 50)
    print(resultado_1["draft"])
    print("-" * 50)

