# =============================================================================
# LISTENERS/TWITCH_BOT.PY - Bot Twitch de Ryosa
# =============================================================================
# Ce bot connecte Ryosa au chat Twitch!
#
# Comment ça marche:
# 1. Le bot se connecte au channel Twitch
# 2. Il écoute TOUS les messages du chat
# 3. Pour chaque message, le CerveauDecisionnel décide si on répond
# 4. Si oui, RyosaIA génère une réponse
# 5. Le bot envoie la réponse dans le chat
# =============================================================================

from twitchio.ext import commands
from twitchio import Message
import asyncio
import logging

from config.settings import configuration
from core.ryosa import RyosaIA
from listeners.smart_brain import CerveauDecisionnel

logger = logging.getLogger("ryosa.twitch")


class BotTwitch(commands.Bot):
    """
    Bot Twitch qui permet à Ryosa de participer au chat.
    
    Hérite de commands.Bot de twitchio qui gère toute la
    connexion IRC à Twitch automatiquement.
    
    Exemple:
        bot = BotTwitch()
        bot.run()  # Lance le bot (bloquant)
    """
    
    def __init__(self):
        """
        Initialise le bot Twitch.
        """
        # Initialiser twitchio avec les credentials
        super().__init__(
            token=configuration.twitch_token,
            prefix="!",  # Préfixe pour les commandes (ex: !help)
            initial_channels=[configuration.twitch_channel]
        )
        
        # Le cerveau de Ryosa
        self.ryosa = RyosaIA()
        
        # Le décideur intelligent
        self.cerveau_decisionnel = CerveauDecisionnel()
        
        # Nom du channel
        self.nom_channel = configuration.twitch_channel
        
        logger.info(f"BotTwitch initialisé pour le channel: {self.nom_channel}")
    
    async def event_ready(self):
        """
        Appelé quand le bot est connecté et prêt.
        
        C'est un "événement" de twitchio - le framework appelle
        automatiquement cette fonction quand la connexion est établie.
        """
        logger.info(f"✅ Ryosa connectée à Twitch!")
        logger.info(f"   Nom: {self.nick}")
        logger.info(f"   Channel: {self.nom_channel}")
        
        # Message de debug optionnel dans le chat
        if configuration.mode_debug:
            channel = self.get_channel(self.nom_channel)
            if channel:
                await channel.send("💫 Ryosa est en ligne! Hihi~")
    
    async def event_message(self, message: Message):
        """
        Appelé pour CHAQUE message dans le chat.
        
        C'est LA fonction principale! Elle reçoit tous les messages
        et décide quoi faire avec.
        
        Args:
            message: L'objet message de twitchio contenant:
                     - message.author.name: Nom de l'auteur
                     - message.content: Contenu du message
                     - message.channel: Le channel
        """
        # Ignorer les messages sans auteur (messages système)
        if message.author is None:
            return
        
        auteur = message.author.name
        contenu = message.content
        
        logger.debug(f"[{auteur}]: {contenu}")
        
        # ===== ÉTAPE 1: Demander au CerveauDecisionnel =====
        decision = self.cerveau_decisionnel.doit_repondre(auteur, contenu)
        
        if not decision["doit_repondre"]:
            logger.debug(f"   → {decision['raison']}")
            
            # Quand même traiter le message pour le contexte
            # (Ryosa écoute même quand elle ne répond pas!)
            self.ryosa.historique_messages.ajouter_message(
                auteur=auteur,
                contenu=contenu,
                plateforme="twitch",
                est_ryosa=False
            )
            self.ryosa.memoire_utilisateurs.mettre_a_jour_activite(auteur)
            return
        
        # ===== ÉTAPE 2: Générer une réponse =====
        logger.info(f"Ryosa va répondre à {auteur}")
        
        reponse = self.ryosa.traiter_message(
            auteur=auteur,
            contenu=contenu,
            plateforme="twitch",
            forcer_reponse=True  # On a déjà décidé de répondre
        )
        
        if reponse:
            # ===== ÉTAPE 3: Envoyer la réponse =====
            await message.channel.send(reponse)
            
            # Enregistrer la réponse pour le rate limiting
            self.cerveau_decisionnel.enregistrer_reponse()
            
            logger.info(f"Réponse envoyée: {reponse[:50]}...")
        
        # ===== ÉTAPE 4: Traiter les commandes =====
        # Ceci permet d'avoir des commandes comme !help
        await self.handle_commands(message)
    
    # =========================================================================
    # COMMANDES OPTIONNELLES
    # =========================================================================
    # Tu peux ajouter des commandes avec le décorateur @commands.command()
    
    @commands.command(name="ryosa")
    async def commande_ryosa(self, ctx: commands.Context):
        """
        Commande !ryosa - Force Ryosa à répondre.
        
        Usage: !ryosa <message>
        """
        # Récupérer le message après !ryosa
        contenu_message = ctx.message.content[7:].strip()  # Enlève "!ryosa "
        
        if not contenu_message:
            await ctx.send("Tu voulais me dire quelque chose? 💫")
            return
        
        # Forcer une réponse
        reponse = self.ryosa.traiter_message(
            auteur=ctx.author.name,
            contenu=contenu_message,
            plateforme="twitch",
            forcer_reponse=True
        )
        
        if reponse:
            await ctx.send(reponse)
            self.cerveau_decisionnel.enregistrer_reponse()
    
    @commands.command(name="status")
    async def commande_statut(self, ctx: commands.Context):
        """
        Commande !status - Affiche le statut de Ryosa.
        
        Utile pour debug!
        """
        statut = self.ryosa.obtenir_statut()
        stats_cerveau = self.cerveau_decisionnel.obtenir_statistiques()
        
        await ctx.send(
            f"💫 Ryosa - En ligne | "
            f"Mémoire: {statut['utilisateurs_suivis']} utilisateurs | "
            f"Réponses/min: {stats_cerveau['reponses_derniere_minute']}/{stats_cerveau['max_par_minute']}"
        )
    
    @commands.command(name="clear")
    async def commande_effacer(self, ctx: commands.Context):
        """
        Commande !clear - Efface le contexte de conversation.
        
        Réservé à Tosachii!
        """
        # Vérifier que c'est Tosachii ou un modo
        if ctx.author.name.lower() not in ["tosachii"]:
            return
        
        self.ryosa.effacer_contexte()
        await ctx.send("🧹 Contexte effacé! Je repars à zéro~")


# Alias pour compatibilité
TwitchBot = BotTwitch


def lancer_bot_twitch():
    """
    Fonction pour lancer le bot Twitch.
    
    C'est une fonction helper pour simplifier le lancement.
    """
    bot = BotTwitch()
    bot.run()


# Alias pour compatibilité
run_twitch_bot = lancer_bot_twitch


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================
if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.DEBUG if configuration.mode_debug else logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    
    print("🎮 Lancement du bot Twitch Ryosa")
    print("=" * 50)
    
    # Vérifier la configuration
    from config.settings import verifier_configuration
    resultat = verifier_configuration()
    
    if not resultat["valide"]:
        print("❌ Configuration incomplète:")
        for manquant in resultat["manquants"]:
            print(f"   - {manquant}")
        exit(1)
    
    print(f"✅ Configuration OK")
    print(f"   Channel: {configuration.twitch_channel}")
    print(f"   Noms reconnus: {configuration.obtenir_liste_noms()}")
    print()
    
    # Lancer le bot
    lancer_bot_twitch()
