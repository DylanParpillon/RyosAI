# =============================================================================
# MEMORY/STORAGE.PY - Système de stockage MongoDB
# =============================================================================
# Ce fichier gère la persistance des données - tout ce que Ryosa doit retenir
# est sauvegardé dans MongoDB pour ne pas être perdu.
#
# Pourquoi MongoDB?
# - Base de données flexible (documents JSON)
# - Facile à explorer avec MongoDB Compass
# - Performant pour les lectures/écritures fréquentes
# =============================================================================

from pymongo import MongoClient
from typing import Any, Dict, Optional, List
from datetime import datetime
import logging

from config.settings import configuration

logger = logging.getLogger("ryosa.storage")

# =============================================================================
# CONNEXION MONGODB
# =============================================================================

# Variable globale pour la connexion MongoDB
_client_mongo: Optional[MongoClient] = None
_base_de_donnees = None


def obtenir_connexion():
    """
    Obtient la connexion MongoDB (la crée si nécessaire).
    
    Returns:
        La base de données MongoDB
    """
    global _client_mongo, _base_de_donnees
    
    if _client_mongo is None:
        try:
            _client_mongo = MongoClient(configuration.mongodb_url)
            _base_de_donnees = _client_mongo[configuration.mongodb_base]
            logger.info(f"Connexion MongoDB établie: {configuration.mongodb_base}")
        except Exception as erreur:
            logger.error(f"Erreur connexion MongoDB: {erreur}")
            raise
    
    return _base_de_donnees


def obtenir_collection(nom_collection: str):
    """
    Obtient une collection MongoDB.
    
    Args:
        nom_collection: Nom de la collection (ex: "utilisateurs", "messages")
    
    Returns:
        La collection MongoDB
    """
    base = obtenir_connexion()
    return base[nom_collection]


# =============================================================================
# FONCTIONS CRUD (Create, Read, Update, Delete)
# =============================================================================

def sauvegarder_document(
    collection: str,
    document_id: str,
    donnees: Dict[str, Any]
) -> bool:
    """
    Sauvegarde un document dans MongoDB.
    
    Args:
        collection: Nom de la collection
        document_id: Identifiant unique du document
        donnees: Les données à sauvegarder
    
    Returns:
        True si la sauvegarde a réussi, False sinon
    
    Exemple:
        sauvegarder_document("utilisateurs", "tosachii", {"niveau": 10})
    """
    try:
        col = obtenir_collection(collection)
        
        # On utilise upsert pour créer ou mettre à jour
        col.update_one(
            {"_id": document_id},
            {"$set": donnees},
            upsert=True
        )
        
        logger.debug(f"Document sauvegardé: {collection}/{document_id}")
        return True
        
    except Exception as erreur:
        logger.error(f"Erreur sauvegarde {collection}/{document_id}: {erreur}")
        return False


def charger_document(
    collection: str,
    document_id: str,
    defaut: Any = None
) -> Any:
    """
    Charge un document depuis MongoDB.
    
    Args:
        collection: Nom de la collection
        document_id: Identifiant du document
        defaut: Valeur par défaut si le document n'existe pas
    
    Returns:
        Les données du document, ou la valeur par défaut
    
    Exemple:
        utilisateur = charger_document("utilisateurs", "tosachii", defaut={})
    """
    try:
        col = obtenir_collection(collection)
        document = col.find_one({"_id": document_id})
        
        if document is None:
            logger.debug(f"Document non trouvé, utilisation du défaut: {collection}/{document_id}")
            return defaut if defaut is not None else {}
        
        # Retirer le _id car on utilise document_id séparément
        document.pop("_id", None)
        
        logger.debug(f"Document chargé: {collection}/{document_id}")
        return document
        
    except Exception as erreur:
        logger.error(f"Erreur chargement {collection}/{document_id}: {erreur}")
        return defaut if defaut is not None else {}


def supprimer_document(collection: str, document_id: str) -> bool:
    """
    Supprime un document de MongoDB.
    
    Args:
        collection: Nom de la collection
        document_id: Identifiant du document à supprimer
    
    Returns:
        True si la suppression a réussi
    """
    try:
        col = obtenir_collection(collection)
        col.delete_one({"_id": document_id})
        logger.debug(f"Document supprimé: {collection}/{document_id}")
        return True
    except Exception as erreur:
        logger.error(f"Erreur suppression {collection}/{document_id}: {erreur}")
        return False


def charger_tous_les_documents(collection: str) -> Dict[str, Any]:
    """
    Charge tous les documents d'une collection.
    
    Args:
        collection: Nom de la collection
    
    Returns:
        Dictionnaire avec document_id -> données
    """
    try:
        col = obtenir_collection(collection)
        documents = {}
        
        for doc in col.find():
            doc_id = doc.pop("_id")
            documents[doc_id] = doc
        
        logger.debug(f"Chargé {len(documents)} documents de {collection}")
        return documents
        
    except Exception as erreur:
        logger.error(f"Erreur chargement collection {collection}: {erreur}")
        return {}


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
    
    COLLECTION = "historique_messages"
    DOCUMENT_ID = "messages_recents"
    
    def __init__(self, nombre_max: int = 10):
        """
        Args:
            nombre_max: Nombre de messages à garder en mémoire
        """
        self.nombre_max = nombre_max
        self.liste_messages: List[Dict] = []
        self._charger()
    
    def _charger(self):
        """Charge l'historique depuis MongoDB."""
        donnees = charger_document(
            self.COLLECTION,
            self.DOCUMENT_ID,
            defaut={"messages": []}
        )
        self.liste_messages = donnees.get("messages", [])[-self.nombre_max:]
    
    def _sauvegarder(self):
        """Sauvegarde l'historique dans MongoDB."""
        sauvegarder_document(
            self.COLLECTION,
            self.DOCUMENT_ID,
            {"messages": self.liste_messages}
        )
    
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
            if not msg["est_ryosa"]:
                contenu = f"[{msg['auteur']}]: {msg['contenu']}"
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
    print("💾 Test du système de stockage MongoDB")
    print("=" * 50)
    
    # Test de connexion
    print("\n🔌 Test de connexion MongoDB...")
    try:
        base = obtenir_connexion()
        print(f"   ✅ Connecté à: {configuration.mongodb_base}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        print("   Assure-toi que MongoDB est lancé!")
        exit(1)
    
    # Test de sauvegarde/chargement
    print("\n1. Test sauvegarde/chargement document:")
    donnees_test = {"test": "données", "nombre": 42}
    sauvegarder_document("test", "doc_test", donnees_test)
    charge = charger_document("test", "doc_test")
    print(f"   Sauvegardé: {donnees_test}")
    print(f"   Chargé: {charge}")
    print(f"   ✅ OK!" if donnees_test == charge else "   ❌ Erreur!")
    
    # Nettoyage
    supprimer_document("test", "doc_test")
    
    # Test de l'historique des messages
    print("\n2. Test historique des messages:")
    historique = HistoriqueMessages(nombre_max=5)
    historique.effacer()
    
    historique.ajouter_message("viewer1", "Salut tout le monde!")
    historique.ajouter_message("tosachii", "Yo! Bienvenue sur le stream!")
    historique.ajouter_message("ryosa", "Coucou! 💫", est_ryosa=True)
    
    print(f"   Messages en mémoire: {len(historique.liste_messages)}")
    print(f"   Format IA: {historique.obtenir_contexte_pour_ia()}")
    
    print(f"\n📁 Base MongoDB: {configuration.mongodb_base}")
