from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class PartySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    tipo: str
    nome: str

class MovementSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    data_movimento: Optional[datetime] = None
    descricao: str

class ProcessListSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    numero_cnj: str
    tribunal: str
    classe_tpu: str
    assunto_tpu: List[str] = Field(default_factory=list)
    comarca: str
    vara: str
    valor_causa: Optional[float] = None
    relevance: str

class ProcessDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    numero_cnj: str
    tribunal: str
    classe_tpu: str
    assunto_tpu: List[str] = Field(default_factory=list)
    comarca: str
    vara: str
    valor_causa: Optional[float] = None
    relevance: str
    data_distribuicao: Optional[datetime] = None
    parties: List[PartySchema] = Field(default_factory=list)
    movements: List[MovementSchema] = Field(default_factory=list)

class ProcessListResponse(BaseModel):
    items: List[ProcessListSchema]
    total: int
    page: int
    page_size: int
