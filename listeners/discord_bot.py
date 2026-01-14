# =============================================================================
# LISTENERS/DISCORD_BOT.PY - Bot Discord de Ryosa
# =============================================================================
# Ce bot connecte Ryosa à Discord!
#
# Fonctionnalités:
# - Écoute les messages dans un channel spécifique
# - Répond quand elle est mentionnée
# - Partage le même cerveau (RyosaIA) que le bot Twitch
# =============================================================================

import discord
from discord.ext import commands as commandes_discord
import asyncio
import logging

from config.settings import configuration
from core.ryosa import RyosaIA
from listeners.smart_brain import CerveauDecisionnel

logger = logging.getLogger("ryosa.discord")


class BotDiscord(commandes_discord.Bot):
    """
    Bot Discord qui permet à Ryosa de participer aux discussions.
    
    Exemple:
        bot = BotDiscord(cerveau_ryosa=cerveau_partage)
        await bot.start(token)
    """
    
    def __init__(
        self,
        cerveau_ryosa: RyosaIA = None,
        cerveau_decisionnel: CerveauDecisionnel = None
    ):
        """
        Initialise le bot Discord.
        
        Args:
            cerveau_ryosa: Instance partagée de RyosaIA (optionnel)
            cerveau_decisionnel: Instance partagée de CerveauDecisionnel (optionnel)
        """
        # Configuration des intents Discord
        # Les intents disent à Discord quels événements on veut recevoir
        intents = discord.Intents.default()
        intents.message_content = True  # Pour lire le contenu des messages
        intents.members = True  # Pour voir les membres
        
        super().__init__(
            command_prefix="!",
            intents=intents
        )
        
        # Utiliser le cerveau partagé ou en créer un nouveau
        self.ryosa = cerveau_ryosa or RyosaIA()
        self.cerveau_decisionnel = cerveau_decisionnel or CerveauDecisionnel()
        
        # Channel où Ryosa répond
        self.id_channel_cible = configuration.discord_channel_id
        
        logger.info(f"BotDiscord initialisé - Channel: {self.id_channel_cible}")
    
    async def on_ready(self):
        """
        Appelé quand le bot est connecté à Discord.
        """
        logger.info(f"✅ Ryosa connectée à Discord!")
        logger.info(f"   Nom: {self.user.name}")
        logger.info(f"   ID: {self.user.id}")
        
        # Notifier le channel de démarrage (optionnel)
        if configuration.mode_debug and self.id_channel_cible:
            channel = self.get_channel(self.id_channel_cible)
            if channel:
                await channel.send("💫 Ryosa est connectée à Discord! Hihi~")
    
    async def on_message(self, message: discord.Message):
        """
        Appelé pour chaque message dans les channels accessibles.
        
        Args:
            message: L'objet message Discord
        """
        # Ignorer les messages du bot lui-même
        if message.author == self.user:
            return
        
        # Vérifier si c'est le bon channel
        if self.id_channel_cible and message.channel.id != self.id_channel_cible:
            return
        
        auteur = message.author.name
        contenu = message.content
        
        logger.debug(f"[Discord][{auteur}]: {contenu}")
        
        # ===== ÉTAPE 1: Demander au CerveauDecisionnel =====
        decision = self.cerveau_decisionnel.doit_repondre(auteur, contenu)
        
        if not decision["doit_repondre"]:
            # Quand même ajouter au contexte
            self.ryosa.historique_messages.ajouter_message(
                auteur=auteur,
                contenu=contenu,
                plateforme="discord",
                est_ryosa=False
            )
            self.ryosa.memoire_utilisateurs.mettre_a_jour_activite(auteur)
            return
        
        # ===== ÉTAPE 2: Générer une réponse =====
        logger.info(f"[Discord] Ryosa va répondre à {auteur}")
        
        # Montrer que Ryosa "tape"
        async with message.channel.typing():
            reponse = self.ryosa.traiter_message(
                auteur=auteur,
                contenu=contenu,
                plateforme="discord",
                forcer_reponse=True
            )
        
        if reponse:
            # ===== ÉTAPE 3: Envoyer la réponse =====
            await message.channel.send(reponse)
            self.cerveau_decisionnel.enregistrer_reponse()
            logger.info(f"[Discord] Réponse envoyée: {reponse[:50]}...")
        
        # Traiter les commandes
        await self.process_commands(message)
    
    @commandes_discord.command(name="ryosa")
    async def commande_ryosa(self, ctx):
        """Commande !ryosa - Force Ryosa à répondre."""
        contenu_message = ctx.message.content[7:].strip()
        
        if not contenu_message:
            await ctx.send("Tu voulais me parler? 💫")
            return
        
        async with ctx.typing():
            reponse = self.ryosa.traiter_message(
                auteur=ctx.author.name,
                contenu=contenu_message,
                plateforme="discord",
                forcer_reponse=True
            )
        
        if reponse:
            await ctx.send(reponse)
            self.cerveau_decisionnel.enregistrer_reponse()
    
    @commandes_discord.command(name="status")
    async def commande_statut(self, ctx):
        """Commande !status - Affiche le statut de Ryosa."""
        statut = self.ryosa.obtenir_statut()
        
        embed = discord.Embed(
            title="💫 Statut de Ryosa",
            color=discord.Color.pink()
        )
        embed.add_field(name="Modèle", value=statut["modele"], inline=True)
        embed.add_field(name="Utilisateurs", value=str(statut["utilisateurs_suivis"]), inline=True)
        embed.add_field(name="Contexte", value=f"{statut['taille_contexte']} messages", inline=True)
        
        await ctx.send(embed=embed)


# Alias pour compatibilité
DiscordBot = BotDiscord


async def lancer_bot_discord(
    cerveau_ryosa: RyosaIA = None,
    cerveau_decisionnel: CerveauDecisionnel = None
):
    """
    Lance le bot Discord de manière asynchrone.
    
    Args:
        cerveau_ryosa: Cerveau partagé (optionnel)
        cerveau_decisionnel: CerveauDecisionnel partagé (optionnel)
    """
    if not configuration.discord_token:
        logger.warning("Token Discord non configuré - Bot Discord désactivé")
        return
    
    bot = BotDiscord(cerveau_ryosa, cerveau_decisionnel)
    await bot.start(configuration.discord_token)


# Alias pour compatibilité
run_discord_bot = lancer_bot_discord


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG if configuration.mode_debug else logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    
    print("🎮 Lancement du bot Discord Ryosa")
    print("=" * 50)
    
    from config.settings import verifier_configuration
    resultat = verifier_configuration()
    
    if not configuration.discord_token:
        print("❌ DISCORD_TOKEN non configuré!")
        exit(1)
    
    asyncio.run(lancer_bot_discord())
