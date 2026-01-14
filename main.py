# =============================================================================
# MAIN.PY - Point d'entrée principal de RyosAI
# =============================================================================
# Ce fichier lance tout le système Ryosa:
# - Bot Twitch
# - Bot Discord
# - Serveur Web (optionnel)
#
# Pour lancer Ryosa: python main.py
#
# NOTE: Version actuelle utilise Groq + JSON.
#       Une version future utilisera Ollama + MongoDB.
# =============================================================================

import asyncio
import logging
import sys

# Configuration du logging AVANT les autres imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ryosa")


def afficher_banniere():
    """Affiche la bannière de démarrage."""
    banniere = """
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║     🎀  RYOSAI - Compagne de Stream IA  🎀           ║
    ║                                                       ║
    ║     Version: 1.0.2 (Fix identité + format réponse) ║
    ║     Créée par: Tosachii                               ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """
    print(banniere)


def verifier_configuration_complete():
    """
    Vérifie que la configuration est correcte avant de lancer.
    
    Returns:
        True si tout est OK, False sinon
    """
    from config.settings import verifier_configuration, configuration
    
    print("🔧 Vérification de la configuration...")
    resultat = verifier_configuration()
    
    if not resultat["valide"]:
        print("\n❌ Configuration incomplète!")
        print("   Éléments manquants:")
        for manquant in resultat["manquants"]:
            print(f"   - {manquant}")
        print("\n   Copie .env.example vers .env et remplis les valeurs!")
        return False
    
    print("   ✅ Configuration valide!")
    
    if resultat["avertissements"]:
        print("\n   ⚠️ Avertissements:")
        for avertissement in resultat["avertissements"]:
            print(f"   - {avertissement}")
    
    print(f"\n   📋 Paramètres:")
    print(f"   - Channel Twitch: {configuration.twitch_channel}")
    print(f"   - Noms reconnus: {configuration.obtenir_liste_noms()}")
    print(f"   - Messages en contexte: {configuration.nombre_messages_contexte}")
    
    return True


async def lancer_twitch():
    """Lance le bot Twitch dans une boucle asyncio."""
    from listeners.twitch_bot import BotTwitch
    
    logger.info("🎮 Démarrage du bot Twitch...")
    bot = BotTwitch()
    await bot.start()


async def lancer_discord(cerveau_ryosa, cerveau_decisionnel):
    """Lance le bot Discord avec le cerveau partagé."""
    from config.settings import configuration
    
    if not configuration.discord_token:
        logger.warning("⚠️ Discord désactivé (pas de token)")
        return
    
    from listeners.discord_bot import lancer_bot_discord
    
    logger.info("💬 Démarrage du bot Discord...")
    await lancer_bot_discord(cerveau_ryosa, cerveau_decisionnel)


async def main_async():
    """
    Fonction principale asynchrone.
    
    Lance tous les bots en parallèle.
    """
    from core.ryosa import RyosaIA
    from listeners.smart_brain import CerveauDecisionnel
    from config.settings import configuration
    
    # Créer les instances partagées
    # Les deux bots vont utiliser le MÊME cerveau!
    cerveau_ryosa = RyosaIA()
    cerveau_decisionnel = CerveauDecisionnel()
    
    logger.info("🧠 Cerveau de Ryosa initialisé")
    
    # Créer les tâches pour chaque bot
    taches = []
    
    # Twitch (obligatoire)
    from listeners.twitch_bot import BotTwitch
    bot_twitch = BotTwitch()
    bot_twitch.ryosa = cerveau_ryosa  # Utiliser le cerveau partagé
    bot_twitch.cerveau_decisionnel = cerveau_decisionnel
    taches.append(bot_twitch.start())
    
    # Discord (optionnel)
    if configuration.discord_token:
        from listeners.discord_bot import BotDiscord
        bot_discord = BotDiscord(cerveau_ryosa, cerveau_decisionnel)
        taches.append(bot_discord.start(configuration.discord_token))
    
    logger.info(f"🚀 Lancement de {len(taches)} bot(s)...")
    
    # Lancer tous les bots en parallèle
    await asyncio.gather(*taches)


def main():
    """
    Point d'entrée principal.
    
    C'est cette fonction qui est appelée quand tu lances:
    python main.py
    """
    afficher_banniere()
    
    # Vérifier la configuration
    if not verifier_configuration_complete():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🚀 Démarrage de RyosAI...")
    print("=" * 60 + "\n")
    
    try:
        # Lancer la boucle asyncio
        asyncio.run(main_async())
        
    except KeyboardInterrupt:
        logger.info("\n👋 Arrêt de RyosAI demandé par l'utilisateur")
        
    except Exception as erreur:
        logger.error(f"❌ Erreur fatale: {erreur}")
        raise


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================
if __name__ == "__main__":
    main()
