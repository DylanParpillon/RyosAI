# =============================================================================
# MEMORY/STORAGE.PY - Système de sauvegarde JSON
# =============================================================================
# Ce fichier gère la persistance des données - tout ce que Ryosa doit retenir
# est sauvegardé dans des fichiers JSON pour ne pas être perdu.
#
# Pourquoi JSON?
# - Simple à lire (tu peux ouvrir les fichiers et voir le contenu)
# - Pas besoin d'installer une base de données
# - Facile à modifier manuellement si besoin
#
# NOTE: Ce fichier est prévu pour être migré vers MongoDB quand tu auras
#       installé ta VM. Pour l'instant, on utilise des fichiers JSON.
# =============================================================================

import json
import os
from typing import Any, Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger("ryosa.storage")

# Dossier où sont stockées toutes les données
DOSSIER_DONNEES = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def assurer_dossier_donnees():
    """
    Crée le dossier 'data' s'il n'existe pas.
    
    Cette fonction est appelée automatiquement au démarrage.
    """
    if not os.path.exists(DOSSIER_DONNEES):
        os.makedirs(DOSSIER_DONNEES)
        logger.info(f"Dossier data créé: {DOSSIER_DONNEES}")


def sauvegarder_json(nom_fichier: str, donnees: Any) -> bool:
    """
    Sauvegarde des données dans un fichier JSON.
    
    Args:
        nom_fichier: Nom du fichier (sans le chemin, exemple: "utilisateurs.json")
        donnees: Les données à sauvegarder (dict, list, etc.)
    
    Returns:
        True si la sauvegarde a réussi, False sinon
    
    Exemple:
        sauvegarder_json("utilisateurs.json", {"tosachii": {"niveau": 10}})
    """
    assurer_dossier_donnees()
    chemin_fichier = os.path.join(DOSSIER_DONNEES, nom_fichier)
    
    try:
        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            # indent=2 rend le fichier lisible par un humain
            # ensure_ascii=False permet les accents français
            json.dump(donnees, fichier, indent=2, ensure_ascii=False)
        
        logger.debug(f"Données sauvegardées: {nom_fichier}")
        return True
        
    except Exception as erreur:
        logger.error(f"Erreur sauvegarde {nom_fichier}: {erreur}")
        return False


def charger_json(nom_fichier: str, defaut: Any = None) -> Any:
    """
    Charge des données depuis un fichier JSON.
    
    Args:
        nom_fichier: Nom du fichier à charger
        defaut: Valeur par défaut si le fichier n'existe pas
    
    Returns:
        Les données chargées, ou la valeur par défaut
    
    Exemple:
        utilisateurs = charger_json("utilisateurs.json", defaut={})
    """
    assurer_dossier_donnees()
    chemin_fichier = os.path.join(DOSSIER_DONNEES, nom_fichier)
    
    if not os.path.exists(chemin_fichier):
        logger.debug(f"Fichier non trouvé, utilisation du défaut: {nom_fichier}")
        return defaut if defaut is not None else {}
    
    try:
        with open(chemin_fichier, "r", encoding="utf-8") as fichier:
            donnees = json.load(fichier)
        
        logger.debug(f"Données chargées: {nom_fichier}")
        return donnees
        
    except Exception as erreur:
        logger.error(f"Erreur chargement {nom_fichier}: {erreur}")
        return defaut if defaut is not None else {}


# =============================================================================
# HISTORIQUE DES MESSAGES (pour le contexte)
# =============================================================================

class HistoriqueMessages:
    """
    Gère l'historique des messages récents pour donner du contexte à Ryosa.
    
    C'est super important! Grâce à cet historique, Ryosa peut:
    - Comprendre de quoi on parle
    - Ne pas répondre hors sujet
    - Savoir si c'est le bon moment pour intervenir
    
    Exemple:
        historique = HistoriqueMessages(nombre_max=10)
        historique.ajouter_message("viewer123", "C'est quoi ce jeu?")
        historique.ajouter_message("tosachii", "C'est Hollow Knight!")
        
        # Ryosa voit les 2 messages et peut répondre intelligemment
    """
    
    def __init__(self, nombre_max: int = 10):
        """
        Args:
            nombre_max: Nombre de messages à garder en mémoire
        """
        self.nombre_max = nombre_max
        self.liste_messages: List[Dict] = []
        self._charger()
    
    def _charger(self):
        """Charge l'historique depuis le fichier."""
        donnees = charger_json("historique_messages.json", defaut={"messages": []})
        self.liste_messages = donnees.get("messages", [])[-self.nombre_max:]
    
    def _sauvegarder(self):
        """Sauvegarde l'historique dans le fichier."""
        sauvegarder_json("historique_messages.json", {"messages": self.liste_messages})
    
    def ajouter_message(
        self,
        auteur: str,
        contenu: str,
        plateforme: str = "twitch",
        est_ryosa: bool = False
    ):
        """
        Ajoute un message à l'historique.
        
        Args:
            auteur: Qui a envoyé le message
            contenu: Le contenu du message
            plateforme: "twitch" ou "discord"
            est_ryosa: True si c'est Ryosa qui a envoyé ce message
        """
        message = {
            "auteur": auteur,
            "contenu": contenu,
            "plateforme": plateforme,
            "est_ryosa": est_ryosa,
            "horodatage": datetime.now().isoformat()
        }
        
        self.liste_messages.append(message)
        
        # On garde seulement les X derniers messages
        if len(self.liste_messages) > self.nombre_max:
            self.liste_messages = self.liste_messages[-self.nombre_max:]
        
        self._sauvegarder()
    
    def obtenir_messages_recents(self, nombre: Optional[int] = None) -> List[Dict]:
        """
        Récupère les messages récents.
        
        Args:
            nombre: Nombre de messages à récupérer (None = tous)
        
        Returns:
            Liste des messages récents
        """
        if nombre is None:
            return self.liste_messages.copy()
        return self.liste_messages[-nombre:]
    
    def obtenir_contexte_pour_ia(self) -> List[Dict[str, str]]:
        """
        Formate l'historique pour l'envoyer au LLM.
        
        Le LLM attend un format spécifique:
        [
            {"role": "user", "content": "message de l'utilisateur"},
            {"role": "assistant", "content": "réponse de Ryosa"}
        ]
        """
        messages_formates = []
        
        for msg in self.liste_messages:
            role = "assistant" if msg["est_ryosa"] else "user"
            
            # On inclut le nom de l'auteur pour le contexte
            # On utilise un format différent pour que Ryosa ne le copie pas
            if not msg["est_ryosa"]:
                contenu = f"(Message de {msg['auteur']}): {msg['contenu']}"
            else:
                contenu = msg["contenu"]
            
            messages_formates.append({"role": role, "content": contenu})
        
        return messages_formates
    
    def effacer(self):
        """Vide l'historique (utile pour un nouveau stream)."""
        self.liste_messages = []
        self._sauvegarder()
        logger.info("Historique des messages vidé")


# =============================================================================
# TEST DU STORAGE
# =============================================================================
if __name__ == "__main__":
    print("💾 Test du système de stockage JSON")
    print("=" * 50)
    
    # Test de sauvegarde/chargement
    print("\n1. Test sauvegarde/chargement JSON:")
    donnees_test = {"test": "données", "nombre": 42}
    sauvegarder_json("test.json", donnees_test)
    charge = charger_json("test.json")
    print(f"   Sauvegardé: {donnees_test}")
    print(f"   Chargé: {charge}")
    print(f"   ✅ OK!" if donnees_test == charge else "   ❌ Erreur!")
    
    # Test de l'historique des messages
    print("\n2. Test historique des messages:")
    historique = HistoriqueMessages(nombre_max=5)
    historique.effacer()
    
    historique.ajouter_message("viewer1", "Salut tout le monde!")
    historique.ajouter_message("tosachii", "Yo! Bienvenue sur le stream!")
    historique.ajouter_message("ryosa", "Coucou! 💫", est_ryosa=True)
    
    print(f"   Messages en mémoire: {len(historique.liste_messages)}")
    print(f"   Format IA: {historique.obtenir_contexte_pour_ia()}")
    
    print(f"\n📁 Dossier data: {DOSSIER_DONNEES}")
