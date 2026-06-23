from typing import (TypedDict, Literal, Optional)
from langgraph.graph import StateGraph, END
from pydantic import BaseModel,Field
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import json
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


def evaluate_feedback(state: GraphState) -> dict:
    feedback_humano = state.get("feedback")

    if not feedback_humano:
        return{"status": "revisando"}

    prompt = f"""
    Você é um gerente de compliance financeiro. Sua tarefa é ler o feedback deixado por um analista sênior sobre um relatório e classificar a sua intenção de acordo com as seguintes regras:
    
    - Se o analista aprovou, disse que está bom, deu 'ok' ou aceitou o relatório -> classifique como "aceito".
    - Se o analista criticou, pediu correções, apontou erros ou mandou refazer -> classifique como "rejeitado".
    - Se o analista não tomou uma decisão clara ou pediu para analisar mais um pouco -> classifique como "revisando".
    
    Feedback do analista sênior:
    "{feedback_humano}"
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Status_classify,
        )
    )

    dados_validados = json.loads(response.text)

    return {"status": dados_validados["status"]}


def human_aproval(state: GraphState) -> dict:
    print("\n" + "="*20 + " PAINEL DE REVISÃO HUMANA " + "="*20)
    print(f"Empresa analisada: {state['nome']}")
    print("\n📝 RASCUNHO DO RELATÓRIO ATUAL:")
    print("-" * 50)
    print(state["draft"])
    print("-" * 50)

    feedback = input("\nDigite seu feedback (Aprovar, pedir correções ou alterações): ")

    return {"feedback": feedback}

#TESTE
#TESTE
if __name__ == "__main__":
    # 1. Primeira Execução: Criando o rascunho
    estado: GraphState = {
        "nome": "Apple Inc.",
        "draft": None,
        "feedback": None,
        "status": None
    }

    print("🚀 1. Gerando rascunho inicial...")
    resultado_draft = generate_draft(estado)
    
    # Atualizamos o nosso estado com o rascunho criado
    estado["draft"] = resultado_draft["draft"]
    print("📝 Rascunho gerado com sucesso!")

    # 2. Simulando o Fator Humano: Você digitando uma crítica negativa
    print("\n👥 2. Simulando feedback do Analista Sênior...")
    estado["feedback"] = human_aproval(estado)
    # 3. Rodando o nó de avaliação para ver se o SDK nativo classifica como 'rejeitado'
    print("🧠 3. Classificando a intenção do feedback...")
    resultado_avaliacao = evaluate_feedback(estado)
    estado["status"] = resultado_avaliacao["status"]
    
    print("-" * 50)
    print("📊 STATUS DA AVALIAÇÃO DA IA:", estado["status"]) # Deve printar: "rejeitado"
    print("-" * 50)
    
    # 4. Rodando o nó de rascunho novamente para ver se ele corrige com base no feedback!
    if estado["status"] == "rejeitado":
        print("\n🔄 4. O relatório foi rejeitado! Rodando 'generate_draft' novamente com o feedback...")
        resultado_correcao = generate_draft(estado)
        print("\n📝 RELATÓRIO CORRIGIDO:")
        print("-" * 50)
        print(resultado_correcao["draft"])
        print("-" * 50)
