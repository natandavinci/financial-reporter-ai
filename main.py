from typing import (TypedDict, Literal, Optional)
from langgraph.graph import StateGraph, END
from pydantic import BaseModel,Field

class GraphState(TypedDict):
    nome: Optional[str]
    draft: Optional[str]
    feedback: Optional[str]
    status: Optional[Literal["aceito", "rejeitado", "revisando"]]

class Status_classify(BaseModel):
    status: Literal["aceito", "rejeitado", "revisando"] = Field(
        description="The status based on response from analyst"
    )



