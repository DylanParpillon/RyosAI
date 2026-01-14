# =============================================================================
# CORE/RYOSA.PY - Le Cerveau Principal de Ryosa
# =============================================================================
# C'est LA classe centrale qui coordonne tout!
#
# Quand un message arrive:
# 1. Le Smart Brain décide si on doit répondre
# 2. Ryosa récupère le contexte (qui parle, historique)
# 3. Ryosa construit le prompt avec sa personnalité
# 4. Ryosa appelle le LLM pour générer une réponse
# 5. On sauvegarde l'interaction
#
# NOTE: Ce fichier utilise Groq pour l'instant. Il sera migré vers
#       Ollama quand tu auras installé ta VM.
# =============================================================================

from typing import Optional, Dict, Any
import logging

from .personality import construire_prompt_systeme, obtenir_type_utilisateur
from .llm import ClientIA
from memory.storage import HistoriqueMessages
from memory.users import MemoireUtilisateurs
from config.settings import configuration

logger = logging.getLogger("ryosa.brain")


class RyosaIA:
    """
    Le cerveau de Ryosa - coordonne toutes les interactions.
    
    C'est comme un chef d'orchestre qui s'assure que tous les
    éléments travaillent ensemble harmonieusement.
    
    Exemple:
        ryosa = RyosaIA()
        
        # Quand un message arrive
        reponse = ryosa.traiter_message(
            auteur="viewer123",
            contenu="Hey Ryosa, t'es là?",
            plateforme="twitch"
        )
        print(reponse)  # "Coucou! Oui je suis là! 💫"
    """
    
    def __init__(self):
        """
        Initialise Ryosa avec tous ses composants.
        """
        # Le client IA (Groq) - le "cerveau pensant"
        self.client_ia = ClientIA(cle_api=configuration.groq_api_key)
        
        # La mémoire des messages récents
        self.historique_messages = HistoriqueMessages(
            nombre_max=configuration.nombre_messages_contexte
        )
        
        # La mémoire des utilisateurs
        self.memoire_utilisateurs = MemoireUtilisateurs()
        
        # Les noms auxquels Ryosa répond
        self.noms = configuration.obtenir_liste_noms()
        
        # Le nom du bot (pour ne pas répondre à soi-même!)
        self.nom_bot = configuration.twitch_nom_bot.lower()
        
        logger.info(f"Ryosa initialisée! Noms reconnus: {self.noms}")
    
    def est_message_de_soi(self, auteur: str) -> bool:
        """
        Vérifie si le message vient de Ryosa elle-même.
        
        TRÈS IMPORTANT pour éviter que Ryosa ne se parle à elle-même!
        
        Args:
            auteur: Nom de l'auteur du message
        
        Returns:
            True si c'est un message de Ryosa
        """
        auteur_minuscule = auteur.lower().strip()
        
        # Vérifie si c'est le nom du bot ou un de ses noms
        if auteur_minuscule == self.nom_bot:
            return True
        
        for nom in self.noms:
            if nom in auteur_minuscule:
                return True
        
        return False
    
    def est_mentionnee(self, contenu: str) -> bool:
        """
        Vérifie si Ryosa est mentionnée dans le message.
        
        Args:
            contenu: Le contenu du message
        
        Returns:
            True si Ryosa est mentionnée
        """
        contenu_minuscule = contenu.lower()
        
        for nom in self.noms:
            if nom in contenu_minuscule:
                return True
        
        return False
    
    def traiter_message(
        self,
        auteur: str,
        contenu: str,
        plateforme: str = "twitch",
        forcer_reponse: bool = False
    ) -> Optional[str]:
        """
        Traite un message et génère une réponse si nécessaire.
        
        C'est LA fonction principale qui fait tout!
        
        Args:
            auteur: Qui a envoyé le message
            contenu: Le contenu du message
            plateforme: "twitch" ou "discord"
            forcer_reponse: Si True, répond même sans mention
        
        Returns:
            La réponse de Ryosa, ou None si elle ne doit pas répondre
        
        Exemple:
            reponse = ryosa.traiter_message(
                auteur="tosachii",
                contenu="Ryosa, dis bonjour!",
                plateforme="twitch"
            )
        """
        # ===============================================
        # ÉTAPE 1: Vérifications de sécurité
        # ===============================================
        
        # Ne JAMAIS répondre à soi-même
        if self.est_message_de_soi(auteur):
            logger.debug(f"Message ignoré (self): {auteur}")
            return None
        
        # ===============================================
        # ÉTAPE 2: Ajouter le message à l'historique
        # ===============================================
        
        # On garde toujours le message en mémoire pour le contexte
        self.historique_messages.ajouter_message(
            auteur=auteur,
            contenu=contenu,
            plateforme=plateforme,
            est_ryosa=False
        )
        
        # Mettre à jour l'activité de l'utilisateur
        self.memoire_utilisateurs.mettre_a_jour_activite(auteur)
        
        # ===============================================
        # ÉTAPE 3: Décider si on doit répondre
        # ===============================================
        
        doit_repondre = forcer_reponse or self.est_mentionnee(contenu)
        
        if not doit_repondre:
            logger.debug(f"Pas de mention détectée, on reste silencieux")
            return None
        
        logger.info(f"Ryosa va répondre à {auteur}: '{contenu[:50]}...'")
        
        # ===============================================
        # ÉTAPE 4: Construire le prompt
        # ===============================================
        
        # Déterminer le type d'utilisateur (tosachii, ichiro, viewer)
        type_utilisateur = obtenir_type_utilisateur(auteur)
        
        # Vérifier si c'est une question
        est_question = "?" in contenu
        
        # Récupérer le contexte de l'utilisateur
        contexte_utilisateur = self.memoire_utilisateurs.obtenir_contexte_utilisateur(auteur)
        
        # Construire le prompt système
        prompt_systeme = construire_prompt_systeme(
            type_utilisateur=type_utilisateur,
            est_question=est_question,
            contexte_supplementaire=contexte_utilisateur
        )
        
        # ===============================================
        # ÉTAPE 5: Récupérer le contexte de conversation
        # ===============================================
        
        # On donne les derniers messages au LLM pour le contexte
        contexte_conversation = self.historique_messages.obtenir_contexte_pour_ia()
        
        # ===============================================
        # ÉTAPE 6: Générer la réponse
        # ===============================================
        
        reponse = self.client_ia.generer_reponse(
            prompt_systeme=prompt_systeme,
            messages=contexte_conversation
        )
        
        # ===============================================
        # ÉTAPE 7: Sauvegarder la réponse
        # ===============================================
        
        # On ajoute la réponse à l'historique
        self.historique_messages.ajouter_message(
            auteur=self.nom_bot,
            contenu=reponse,
            plateforme=plateforme,
            est_ryosa=True
        )
        
        logger.info(f"Réponse générée: '{reponse[:50]}...'")
        return reponse
    
    def obtenir_statut(self) -> Dict[str, Any]:
        """
        Retourne le statut actuel de Ryosa.
        
        Utile pour le dashboard et le debugging.
        """
        stats_utilisateurs = self.memoire_utilisateurs.obtenir_statistiques()
        
        return {
            "en_ligne": True,
            "noms": self.noms,
            "modele": self.client_ia.modele,
            "taille_contexte": len(self.historique_messages.liste_messages),
            "utilisateurs_suivis": stats_utilisateurs["total_utilisateurs"],
            "total_interactions": stats_utilisateurs["total_messages"],
        }
    
    def apprendre(self, nom_utilisateur: str, fait: str):
        """
        Apprend un nouveau fait sur un utilisateur.
        
        Args:
            nom_utilisateur: Nom de l'utilisateur
            fait: Le fait à retenir
        
        Exemple:
            ryosa.apprendre("viewer123", "est développeur Python")
        """
        self.memoire_utilisateurs.ajouter_fait(nom_utilisateur, fait)
        logger.info(f"Nouveau fait appris pour {nom_utilisateur}: {fait}")
    
    def effacer_contexte(self):
        """
        Efface le contexte de conversation (utile entre les streams).
        """
        self.historique_messages.effacer()
        logger.info("Contexte de conversation effacé")


# =============================================================================
# TEST DU CERVEAU
# =============================================================================
if __name__ == "__main__":
    # Ce code s'exécute uniquement si tu lances ce fichier directement
    # python -m core.ryosa
    
    import sys
    sys.path.insert(0, ".")  # Pour les imports
    
    print("🧠 Test du cerveau de Ryosa")
    print("=" * 50)
    
    # Vérifier la config
    from config.settings import verifier_configuration
    resultat = verifier_configuration()
    
    if not resultat["valide"]:
        print("❌ Configuration incomplète:")
        for manquant in resultat["manquants"]:
            print(f"   - {manquant}")
        exit(1)
    
    # Créer Ryosa
    ryosa = RyosaIA()
    
    print("\n📊 Statut:")
    statut = ryosa.obtenir_statut()
    for cle, valeur in statut.items():
        print(f"   {cle}: {valeur}")
    
    # Test d'interaction
    print("\n💬 Test d'interaction:")
    
    # Simuler quelques messages
    messages = [
        ("viewer1", "Salut tout le monde!"),
        ("tosachii", "Hey le chat!"),
        ("viewer2", "@Ryosa t'es connectée?"),  # Mention = réponse!
    ]
    
    for auteur, contenu in messages:
        print(f"\n   [{auteur}]: {contenu}")
        reponse = ryosa.traiter_message(auteur, contenu, "twitch")
        if reponse:
            print(f"   [Ryosa]: {reponse}")
        else:
            print("   (Ryosa reste silencieuse)")
