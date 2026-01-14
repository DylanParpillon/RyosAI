# =============================================================================
# CONFIG/SETTINGS.PY - Configuration centralisée de RyosAI
# =============================================================================
# Ce fichier charge toutes les variables d'environnement depuis le fichier .env
# et les rend accessibles partout dans l'application.
#
# Comment ça marche:
# 1. Le fichier .env contient tes tokens secrets
# 2. Ce fichier lit le .env et crée un objet "configuration"
# 3. Partout dans le code, on importe configuration pour accéder aux valeurs
# =============================================================================

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os

# On charge le fichier .env au démarrage
from dotenv import load_dotenv
load_dotenv()


class Configuration(BaseSettings):
    """
    Classe qui contient TOUTE la configuration de RyosAI.
    
    Pydantic va automatiquement:
    - Lire les variables d'environnement
    - Les convertir dans le bon type (str, int, bool, list...)
    - Valider que tout est correct
    """
    
    # =========================================================================
    # OLLAMA (IA Locale)
    # =========================================================================
    ollama_url: str = Field(
        default="http://localhost:11434",
        description="URL du serveur Ollama (IA locale)"
    )
    ollama_modele: str = Field(
        default="llama3.1",
        description="Nom du modèle Ollama à utiliser"
    )
    
    # =========================================================================
    # MONGODB (Base de données)
    # =========================================================================
    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        description="URL de connexion à MongoDB"
    )
    mongodb_base: str = Field(
        default="ryosai",
        description="Nom de la base de données MongoDB"
    )
    
    # =========================================================================
    # TWITCH
    # =========================================================================
    twitch_token: str = Field(
        default="",
        description="Token OAuth pour se connecter à Twitch"
    )
    twitch_channel: str = Field(
        default="tosachii",
        description="Nom de la chaîne Twitch à surveiller"
    )
    twitch_nom_bot: str = Field(
        default="RyosaIA",
        description="Nom du compte bot sur Twitch"
    )
    
    # =========================================================================
    # DISCORD
    # =========================================================================
    discord_token: str = Field(
        default="",
        description="Token du bot Discord"
    )
    discord_channel_id: int = Field(
        default=0,
        description="ID du salon Discord où Ryosa parle"
    )
    
    # =========================================================================
    # CONFIGURATION RYOSA
    # =========================================================================
    ryosa_noms: str = Field(
        default="ryosa,ryo",
        description="Noms auxquels Ryosa répond (séparés par des virgules)"
    )
    nombre_messages_contexte: int = Field(
        default=10,
        description="Nombre de messages à garder pour le contexte"
    )
    mode_debug: bool = Field(
        default=False,
        description="Mode debug pour plus de logs"
    )
    
    def obtenir_liste_noms(self) -> List[str]:
        """
        Convertit la chaîne de noms en liste.
        
        Exemple:
            "ryosa,ryo,ryosa-chan" -> ["ryosa", "ryo", "ryosa-chan"]
        """
        return [nom.strip().lower() for nom in self.ryosa_noms.split(",")]
    
    class Config:
        # Pydantic va chercher les variables avec ces préfixes
        env_file = ".env"
        env_file_encoding = "utf-8"


# =============================================================================
# INSTANCE GLOBALE
# =============================================================================
# On crée UNE SEULE instance de Configuration qui sera utilisée partout
# Pour l'utiliser ailleurs: from config.settings import configuration

configuration = Configuration()


# =============================================================================
# FONCTION DE VÉRIFICATION
# =============================================================================
def verifier_configuration() -> dict:
    """
    Vérifie que la configuration est complète.
    
    Retourne un dictionnaire avec:
    - "valide": True si tout est OK, False sinon
    - "manquants": Liste des éléments manquants
    - "avertissements": Avertissements non-bloquants
    """
    resultat = {
        "valide": True,
        "manquants": [],
        "avertissements": []
    }
    
    # Vérifications obligatoires
    if not configuration.twitch_token:
        resultat["manquants"].append("TWITCH_TOKEN (requis pour Twitch)")
        resultat["valide"] = False
    
    # Avertissements
    if not configuration.discord_token:
        resultat["avertissements"].append("DISCORD_TOKEN manquant - Discord sera désactivé")
    
    if configuration.discord_channel_id == 0:
        resultat["avertissements"].append("DISCORD_CHANNEL_ID non configuré")
    
    return resultat


# =============================================================================
# TEST DE LA CONFIG
# =============================================================================
if __name__ == "__main__":
    # Ce code s'exécute uniquement si tu lances ce fichier directement
    # python config/settings.py
    
    print("🔧 Test de la configuration RyosAI")
    print("=" * 50)
    
    resultat = verifier_configuration()
    
    if resultat["valide"]:
        print("✅ Configuration valide!")
    else:
        print("❌ Configuration incomplète:")
        for manquant in resultat["manquants"]:
            print(f"   - {manquant}")
    
    if resultat["avertissements"]:
        print("\n⚠️ Avertissements:")
        for avertissement in resultat["avertissements"]:
            print(f"   - {avertissement}")
    
    print("\n📋 Valeurs actuelles:")
    print(f"   Noms de Ryosa: {configuration.obtenir_liste_noms()}")
    print(f"   Channel Twitch: {configuration.twitch_channel}")
    print(f"   Ollama URL: {configuration.ollama_url}")
    print(f"   Ollama Modèle: {configuration.ollama_modele}")
    print(f"   MongoDB URL: {configuration.mongodb_url}")
    print(f"   MongoDB Base: {configuration.mongodb_base}")
    print(f"   Mode debug: {configuration.mode_debug}")
