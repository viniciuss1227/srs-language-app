from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta

app = FastAPI()

# Modelo Pydantic para validação
class CardCreate(BaseModel):
    frente: str
    verso: str

# Banco temporário (lista em memória)
cards_db = []

@app.get("/health")
def health():
    return {"status": "ok", "msg": "SRS MVP funcionando!"}

@app.post("/cards")
def create_card(card: CardCreate):
    """Criar um card novo"""
    try:
        novo_card = {
            "id": len(cards_db) + 1,
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
        raise HTTPException(status_code=500, detail=f"Erro ao criar card: {str(e)}")

@app.get("/cards")
def list_cards():
    """Listar todos os cards"""
    return {"total": len(cards_db), "cards": cards_db}

@app.get("/cards/revisar")
def cards_para_revisar():
    """Pegar cards que precisam ser revisados HOJE"""
    agora = datetime.now()
    para_revisar = [c for c in cards_db if datetime.fromisoformat(c["proxima_revisao"]) <= agora]
    return {"para_revisar": len(para_revisar), "total": len(cards_db), "cards": para_revisar}

@app.post("/cards/{card_id}/revisar")
def revisar_card(card_id: int, acertou: bool):
    """Marcar card como revisado"""
    try:
        card = next((c for c in cards_db if c["id"] == card_id), None)
        if not card:
            raise HTTPException(status_code=404, detail="Card não encontrado")
        
        if acertou:
            card["intervalo_dias"] *= 2  # Dobra o intervalo
            card["acertos"] += 1
        else:
            card["intervalo_dias"] = 1  # Volta pro começo
            card["erros"] += 1
        
        card["proxima_revisao"] = (datetime.now() + timedelta(days=card["intervalo_dias"])).isoformat()
        return {
            "msg": "Revisado!", 
            "acertou": acertou, 
            "proxima_revisao_em": f"{card['intervalo_dias']} dias", 
            "card": card
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao revisar card: {str(e)}")

@app.delete("/cards/{card_id}")
def delete_card(card_id: int):
    """Deletar um card"""
    global cards_db
    card = next((c for c in cards_db if c["id"] == card_id), None)
    if not card:
        raise HTTPException(status_code=404, detail="Card não encontrado")
    
    cards_db = [c for c in cards_db if c["id"] != card_id]
    return {"msg": "Card deletado!", "card_deletado": card}
