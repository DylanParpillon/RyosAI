# =============================================================================
# CORE/LLM.PY - Connexion au cerveau IA (Ollama)
# =============================================================================
# Ce fichier gère la communication avec Ollama, le service d'IA locale.
#
# Comment ça marche:
# 1. On envoie un "prompt système" (la personnalité de Ryosa)
# 2. On envoie l'historique de la conversation
# 3. Ollama génère une réponse intelligente
# 4. On retourne cette réponse
# =============================================================================

import ollama
from typing import List, Dict, Optional
import logging

# Configuration du logging
logger = logging.getLogger("ryosa.llm")


class ClientIA:
    """
    Client pour communiquer avec Ollama (le cerveau de Ryosa).
    
    Exemple d'utilisation:
        client = ClientIA()
        reponse = client.generer_reponse(
            prompt_systeme="Tu es Ryosa...",
            messages=[{"role": "user", "content": "Salut!"}]
        )
    """
    
    def __init__(
        self,
        url_ollama: str = "http://localhost:11434",
        modele: str = "llama3.1"
    ):
        """
        Initialise le client Ollama.
        
        Args:
            url_ollama: URL du serveur Ollama (par défaut: localhost:11434)
            modele: Le modèle à utiliser (par défaut: llama3.1)
                   Autres options: mistral, qwen2, phi3, etc.
        """
        self.url_ollama = url_ollama
        self.modele = modele
        
        # Paramètres de génération
        self.creativite = 0.7      # 0 = très prévisible, 1 = très créatif
        self.longueur_max = 150    # Limite la longueur des réponses
        
        # Configurer le client Ollama
        self.client = ollama.Client(host=url_ollama)
        
        logger.info(f"ClientIA initialisé - Modèle: {modele}, URL: {url_ollama}")
    
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
            # On construit la requête pour Ollama
            tous_les_messages = [
                {"role": "system", "content": prompt_systeme}
            ] + messages
            
            # On appelle l'API Ollama
            reponse = self.client.chat(
                model=self.modele,
                messages=tous_les_messages,
                options={
                    "temperature": creativite or self.creativite,
                    "num_predict": self.longueur_max,
                }
            )
            
            # On extrait le texte de la réponse
            texte_genere = reponse["message"]["content"]
            
            logger.debug(f"Réponse générée: {texte_genere[:50]}...")
            return texte_genere.strip()
            
        except Exception as erreur:
            # En cas d'erreur, on log et on retourne un message par défaut
            logger.error(f"Erreur lors de la génération: {erreur}")
            return self._obtenir_reponse_secours()
    
    def _obtenir_reponse_secours(self) -> str:
        """
        Réponse de secours si Ollama ne fonctionne pas.
        
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
    
    def verifier_connexion(self) -> bool:
        """
        Vérifie que la connexion à Ollama fonctionne.
        
        Returns:
            True si Ollama est accessible, False sinon
        """
        try:
            # Teste la connexion en listant les modèles
            modeles = self.client.list()
            logger.info(f"Connexion Ollama OK - {len(modeles.get('models', []))} modèles disponibles")
            return True
        except Exception as erreur:
            logger.error(f"Impossible de se connecter à Ollama: {erreur}")
            return False


# =============================================================================
# TEST DU CLIENT IA
# =============================================================================
if __name__ == "__main__":
    # Ce code s'exécute uniquement si tu lances ce fichier directement
    # python core/llm.py
    
    print("🧠 Test du client IA (Ollama)")
    print("=" * 50)
    
    client = ClientIA()
    
    # Vérifier la connexion
    print("\n🔌 Vérification de la connexion Ollama...")
    if not client.verifier_connexion():
        print("❌ Impossible de se connecter à Ollama!")
        print("   Assure-toi qu'Ollama est lancé: ollama serve")
        exit(1)
    
    print("✅ Connexion OK!")
    
    # Test simple
    prompt_systeme = "Tu es Ryosa, une IA mignonne et serviable. Réponds en français."
    messages = [
        {"role": "user", "content": "Salut Ryosa! Comment tu vas?"}
    ]
    
    print("\n📤 Envoi du message de test...")
    reponse = client.generer_reponse(prompt_systeme, messages)
    print(f"\n📥 Réponse de Ryosa:\n   {reponse}")
