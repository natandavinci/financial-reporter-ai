from typing import (TypedDict, Literal, Optional)
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables.graph import MermaidDrawMethod
from pydantic import BaseModel,Field
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import json
load_dotenv()

memory = MemorySaver()

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


def human_approval(state: GraphState) -> dict:
    print("\n" + "="*20 + " PAINEL DE REVISÃO HUMANA " + "="*20)
    print(f"Empresa analisada: {state['nome']}")
    print("\n📝 RASCUNHO DO RELATÓRIO ATUAL:")
    print("-" * 50)
    print(state["draft"])
    print("-" * 50)

    feedback = input("\nDigite seu feedback (Aprovar, pedir correções ou alterações): ")

    return {"feedback": feedback}

def router_condition(state: GraphState):

    if state["feedback"] == "aceito":

        return "finalizar"
    else:

        return "corrigir"


# Creating graph

graph = StateGraph(GraphState)


# Nodes
graph.add_node("generate_draft",
               generate_draft)

graph.add_node("evaluate_feedback",
               evaluate_feedback)

graph.add_node("human_approval",
               human_approval)

# Edges

graph.set_entry_point("generate_draft")

graph.add_edge("generate_draft", "human_approval")
graph.add_edge("human_approval","evaluate_feedback")

graph.add_conditional_edges("evaluate_feedback",
                            router_condition,
                            {
                                "finalizar": END,
                                "corrigir": "generate_draft"
                            })

# Compilando

app = graph.compile(checkpointer=memory)



#TESTE
if __name__ == "__main__":
     
    png_bytes = app.get_graph().draw_mermaid_png(
                    draw_method=MermaidDrawMethod.API
    )

    with open("grafo_exemplo1.png", "wb") as f:
        f.write(png_bytes)

    # 1. Definimos a configuração com o ID da sessão do relatório
    config = {"configurable": {"thread_id": "relatorio_apple_001"}}

    # 2. Criamos o estado inicial com o nome da empresa
    estado_inicial = {
        "nome": "Apple Inc.",
        "draft": None,
        "feedback": None,
        "status": None
    }

    print("🚀 Iniciando o Grafo do Gerador de Relatórios Financeiros...")
    
    # 3. Rodamos o grafo usando o .stream() para ver os nós executando em tempo real
    # Passamos o estado apenas na primeira vez. O Grafo vai rodar, pedir seu feedback no terminal e decidir o rumo.
    for evento in app.stream(estado_inicial, config, stream_mode="values"):
        # Se o grafo terminou e o status for aceito, comemoramos
        if evento.get("status") == "aceito":
            print("\n✅ [SISTEMA]: Relatório Aprovado com Sucesso e Finalizado!")
            print("=" * 60)
            break