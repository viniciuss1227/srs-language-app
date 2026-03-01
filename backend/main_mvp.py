from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
import uuid

app = FastAPI(title="SRS Language App MVP")

# CORS habilitado para frontend.localhost e todos origins (Render)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend.localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Banco temporário em memória
cards_db: List[dict] = []

class CardCreate(BaseModel):
    frente: str
    verso: str

class RevisarRequest(BaseModel):
    acertou: bool

@app.get("/health")
async def health():
    return {"status": "ok", "msg": "SRS MVP funcionando!"}

@app.post("/cards")
async def create_card(card: CardCreate):
    """POST /cards - Cria card novo (frente, verso)"""
    try:
        novo_card = {
            "id": str(uuid.uuid4()),  # ID único para frontend
            "frente": card.frente,
            "verso": card.verso,
            "proxima_revisao": datetime.now().isoformat(),
            "intervalo_dias": 1,
            "acertos": 0,
            "erros": 0
        }
        cards_db.append(novo_card)
        return {"msg": "Card criado!", "card": novo_card}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/cards")
async def list_cards():
    """GET /cards - Lista todos os cards {"total":N, "cards":[]}"""
    return {"total": len(cards_db), "cards": cards_db}

@app.get("/cards/revisar")
async def cards_para_revisar():
    """GET /cards/revisar - [{"total":N, "cards":[]}]"""
    agora = datetime.now()
    para_revisar = [
        c for c in cards_db 
        if datetime.fromisoformat(c["proxima_revisao"]) <= agora
    ]
    return [{"total": len(cards_db), "cards": para_revisar}]

@app.post("/cards/{card_id}/revisar")
async def revisar_card(card_id: str, request: RevisarRequest):
    """POST /cards/{id}/revisar - {acertou: bool}"""
    try:
        card = next((c for c in cards_db if c["id"] == card_id), None)
        if not card:
            raise HTTPException(status_code=404, detail="Card não encontrado")
        
        if request.acertou:
            card["intervalo_dias"] = min(card["intervalo_dias"] * 2, 30)  # Cap 30 dias
            card["acertos"] += 1
        else:
            card["intervalo_dias"] = 1
            card["erros"] += 1
        
        card["proxima_revisao"] = (datetime.now() + timedelta(days=card["intervalo_dias"])).isoformat()
        return {
            "msg": "Revisado!",
            "acertou": request.acertou,
            "proxima_revisao_em": f"{card['intervalo_dias']} dias",
            "card": card
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao revisar: {str(e)}")

@app.delete("/cards/{card_id}")
async def delete_card(card_id: str):
    """DELETE /cards/{id} - Para debug frontend"""
    global cards_db
    cards_db = [c for c in cards_db if c["id"] != card_id]
    return {"msg": "Card deletado!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
