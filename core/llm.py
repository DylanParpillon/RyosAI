# =============================================================================
# CORE/LLM.PY - Connexion au cerveau IA (Groq)
# =============================================================================
# Ce fichier gère la communication avec Groq, le service qui fournit l'IA.
#
# Comment ça marche:
# 1. On envoie un "prompt système" (la personnalité de Ryosa)
# 2. On envoie l'historique de la conversation
# 3. Groq génère une réponse intelligente
# 4. On retourne cette réponse
#
# NOTE: Ce fichier est prévu pour être migré vers Ollama quand tu auras
#       installé ta VM. Pour l'instant, on utilise Groq (cloud).
# =============================================================================

from groq import Groq
from typing import List, Dict, Optional
import logging

# Configuration du logging
logger = logging.getLogger("ryosa.llm")


class ClientIA:
    """
    Client pour communiquer avec Groq (le cerveau de Ryosa).
    
    Exemple d'utilisation:
        client = ClientIA(cle_api="ta_clé_api")
        reponse = client.generer_reponse(
            prompt_systeme="Tu es Ryosa...",
            messages=[{"role": "user", "content": "Salut!"}]
        )
    """
    
    def __init__(
        self,
        cle_api: str,
        modele: str = "llama-3.1-8b-instant"
    ):
        """
        Initialise le client Groq.
        
        Args:
            cle_api: Ta clé API Groq (depuis console.groq.com)
            modele: Le modèle à utiliser (par défaut: llama-3.1-8b-instant)
                   Autres options: llama-3.3-70b-versatile, mixtral-8x7b-32768
        """
        self.client = Groq(api_key=cle_api)
        self.modele = modele
        
        # Paramètres de génération
        self.creativite = 0.7      # 0 = très prévisible, 1 = très créatif
        self.longueur_max = 150    # Limite la longueur des réponses
        
        logger.info(f"ClientIA initialisé avec le modèle: {modele}")
    
    def generer_reponse(
        self,
        prompt_systeme: str,
        messages: List[Dict[str, str]],
        creativite: Optional[float] = None
    ) -> str:
        """
        Génère une réponse de Ryosa.
        
        Args:
            prompt_systeme: La personnalité de Ryosa (instructions pour l'IA)
            messages: L'historique de conversation sous forme de liste
                      [{"role": "user", "content": "Salut!"}]
            creativite: Créativité (optionnel, utilise la valeur par défaut sinon)
        
        Returns:
            La réponse générée par Ryosa
        
        Exemple:
            messages = [
                {"role": "user", "content": "Salut Ryosa!"},
                {"role": "assistant", "content": "Coucou! Comment ça va?"},
                {"role": "user", "content": "Ça va bien, et toi?"}
            ]
            reponse = client.generer_reponse(prompt_systeme, messages)
        """
        try:
            # On construit la requête pour Groq
            tous_les_messages = [
                {"role": "system", "content": prompt_systeme}
            ] + messages
            
            # On appelle l'API Groq
            reponse = self.client.chat.completions.create(
                model=self.modele,
                messages=tous_les_messages,
                temperature=creativite or self.creativite,
                max_tokens=self.longueur_max,
            )
            
            # On extrait le texte de la réponse
            texte_genere = reponse.choices[0].message.content
            
            logger.debug(f"Réponse générée: {texte_genere[:50]}...")
            return texte_genere.strip()
            
        except Exception as erreur:
            # En cas d'erreur, on log et on retourne un message par défaut
            logger.error(f"Erreur lors de la génération: {erreur}")
            return self._obtenir_reponse_secours()
    
    def _obtenir_reponse_secours(self) -> str:
        """
        Réponse de secours si Groq ne fonctionne pas.
        
        C'est important d'avoir un fallback pour que Ryosa puisse
        toujours répondre quelque chose même en cas de problème.
        """
        reponses_secours = [
            "Hmm, j'ai un petit bug là... Réessaie dans un moment! 💫",
            "Oups, mon cerveau fait une pause! Attends un peu~ 🌙",
            "Ah, je réfléchis trop fort là! Redemande-moi ça? ✨",
        ]
        import random
        return random.choice(reponses_secours)
    
    def definir_creativite(self, niveau: str):
        """
        Ajuste la créativité de Ryosa.
        
        Args:
            niveau: "bas" (prévisible), "moyen" (équilibré), "haut" (créatif)
        """
        niveaux = {
            "bas": 0.3,
            "moyen": 0.7,
            "haut": 0.9
        }
        self.creativite = niveaux.get(niveau, 0.7)
        logger.info(f"Créativité ajustée: {niveau} (temp={self.creativite})")


# =============================================================================
# TEST DU CLIENT IA
# =============================================================================
if __name__ == "__main__":
    # Ce code s'exécute uniquement si tu lances ce fichier directement
    # python core/llm.py
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    cle_api = os.getenv("GROQ_API_KEY")
    
    if not cle_api:
        print("❌ GROQ_API_KEY non trouvée dans .env!")
        print("   Va sur https://console.groq.com pour en obtenir une")
        exit(1)
    
    print("🧠 Test du client IA (Groq)")
    print("=" * 50)
    
    client = ClientIA(cle_api=cle_api)
    
    # Test simple
    prompt_systeme = "Tu es Ryosa, une IA mignonne et serviable. Réponds en français."
    messages = [
        {"role": "user", "content": "Salut Ryosa! Comment tu vas?"}
    ]
    
    print("\n📤 Envoi du message de test...")
    reponse = client.generer_reponse(prompt_systeme, messages)
    print(f"\n📥 Réponse de Ryosa:\n   {reponse}")
