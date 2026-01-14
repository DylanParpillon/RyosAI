# =============================================================================
# WEB/SERVER.PY - Serveur API pour tester Ryosa
# =============================================================================
# Ce serveur FastAPI te permet de tester Ryosa sans avoir besoin
# d'ouvrir Twitch ou Discord!
#
# Pour lancer: python -m uvicorn web.server:app --reload
# Puis ouvre: http://localhost:8000
# =============================================================================

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import os
import logging

from config.settings import settings
from core.ryosa import RyosaAI
from listeners.smart_brain import SmartBrain

logger = logging.getLogger("ryosa.web")

# Créer l'application FastAPI
app = FastAPI(
    title="Ryosa IA - Interface de Test",
    description="Interface web pour tester Ryosa avant de la déployer sur Twitch/Discord",
    version="1.0.0"
)

# Instances globales (créées au démarrage)
ryosa: RyosaAI = None
smart_brain: SmartBrain = None


@app.on_event("startup")
async def startup():
    """Initialise Ryosa au démarrage du serveur."""
    global ryosa, smart_brain
    
    ryosa = RyosaAI()
    smart_brain = SmartBrain()
    
    logger.info("🌐 Serveur web Ryosa démarré!")


# =============================================================================
# MODÈLES DE DONNÉES
# =============================================================================
# Pydantic valide automatiquement les données entrantes

class ChatMessage(BaseModel):
    """Message envoyé par l'utilisateur."""
    author: str = "TestUser"
    content: str
    
class ChatResponse(BaseModel):
    """Réponse de Ryosa."""
    response: str
    author: str
    should_respond: bool
    reason: str


# =============================================================================
# ROUTES API
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    """
    Page d'accueil - Interface de chat.
    """
    # Chercher le fichier index.html
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    
    if os.path.exists(html_path):
        return FileResponse(html_path)
    
    # Si pas de fichier HTML, retourner une page simple
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ryosa IA - Test</title>
        <style>
            body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }
            h1 { color: #ff69b4; }
            input, button { padding: 10px; margin: 5px; }
            #response { background: #f0f0f0; padding: 15px; margin-top: 20px; border-radius: 10px; }
        </style>
    </head>
    <body>
        <h1>🎀 Test Ryosa IA</h1>
        <p>Va voir /docs pour l'API interactive!</p>
        <p>Ou ouvre le fichier <code>web/index.html</code> complet.</p>
    </body>
    </html>
    """


@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Envoie un message à Ryosa.
    
    C'est l'endpoint principal pour interagir avec Ryosa via l'API.
    
    Exemple:
        POST /chat
        {"author": "TestUser", "content": "Salut Ryosa!"}
    """
    global ryosa, smart_brain
    
    if not ryosa:
        raise HTTPException(status_code=500, detail="Ryosa non initialisée")
    
    # Demander au SmartBrain si on doit répondre
    decision = smart_brain.should_respond(message.author, message.content)
    
    response_text = ""
    
    if decision["should_respond"]:
        # Générer une réponse
        response_text = ryosa.process_message(
            author=message.author,
            content=message.content,
            platform="web",
            force_response=True
        ) or ""
        
        if response_text:
            smart_brain.record_response()
    else:
        # Ajouter au contexte même sans répondre
        ryosa.message_history.add_message(
            author=message.author,
            content=message.content,
            platform="web",
            is_ryosa=False
        )
    
    return ChatResponse(
        response=response_text,
        author=message.author,
        should_respond=decision["should_respond"],
        reason=decision["reason"]
    )


@app.get("/status")
async def status():
    """
    Retourne le statut de Ryosa.
    """
    global ryosa, smart_brain
    
    if not ryosa:
        return {"online": False, "message": "Non initialisée"}
    
    ryosa_status = ryosa.get_status()
    brain_stats = smart_brain.get_stats()
    
    return {
        "online": True,
        "ryosa": ryosa_status,
        "smart_brain": brain_stats
    }


@app.get("/history")
async def get_history():
    """
    Retourne l'historique des messages récents.
    """
    global ryosa
    
    if not ryosa:
        return {"messages": []}
    
    messages = ryosa.message_history.get_recent_messages()
    return {"messages": messages}


@app.post("/clear")
async def clear_context():
    """
    Efface le contexte de conversation.
    
    Utile pour recommencer une conversation propre.
    """
    global ryosa
    
    if ryosa:
        ryosa.clear_context()
    
    return {"success": True, "message": "Contexte effacé!"}


@app.get("/users")
async def get_users():
    """
    Retourne la liste des utilisateurs connus.
    """
    global ryosa
    
    if not ryosa:
        return {"users": {}}
    
    return {"users": ryosa.user_memory.users}


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    
    print("🌐 Lancement du serveur web Ryosa")
    print("   URL: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "web.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
