from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .database import SessionLocal, engine, Base
from . import models

app = FastAPI()

# Cria tabelas automaticamente
Base.metadata.create_all(bind=engine)

# Pydantic models para receber dados
class UserCreate(BaseModel):
    username: str
    email: str
    hashed_password: str

class DeckCreate(BaseModel):
    title: str
    description: str

# Dependency para banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===== ENDPOINTS =====

@app.get("/health")
def health():
    return {"status": "ok"}

# USER ENDPOINTS
@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Criar novo usuário"""
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Pegar usuário por ID"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return {"error": "User not found"}
    return user

# DECK ENDPOINTS
@app.post("/decks/")
def create_deck(deck: DeckCreate, db: Session = Depends(get_db)):
    """Criar novo deck (owner_id=1 por enquanto)"""
    db_deck = models.Deck(**deck.dict(), owner_id=1)
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    return db_deck

@app.get("/decks/{deck_id}")
def get_deck(deck_id: int, db: Session = Depends(get_db)):
    """Pegar deck por ID"""
    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).first()
    if not deck:
        return {"error": "Deck not found"}
    return deck

@app.get("/users/{user_id}/decks")
def get_user_decks(user_id: int, db: Session = Depends(get_db)):
    """Listar todos os decks de um usuário"""
    decks = db.query(models.Deck).filter(models.Deck.owner_id == user_id).all()
    return decks