# =============================================================================
# LISTENERS/SMART_BRAIN.PY - Le cerveau qui décide quand répondre
# =============================================================================
# Ce module analyse les messages pour décider si Ryosa doit répondre.
#
# Critères pour répondre:
# 1. Mention directe (@Ryosa, "Ryosa", etc.)
# 2. Question posée au chat
# 3. Contexte conversationnel (réponse à une discussion)
#
# Protection:
# - Ne JAMAIS répondre à soi-même
# - Rate limiting (pas trop de réponses d'affilée)
# - Éviter le spam
# =============================================================================

import time
from typing import Optional, List
import logging
import re

from config.settings import configuration

logger = logging.getLogger("ryosa.smart_brain")


class CerveauDecisionnel:
    """
    Décide intelligemment quand Ryosa doit répondre.
    
    C'est le "filtre" avant de solliciter le LLM. On ne veut pas
    que Ryosa réponde à TOUS les messages, seulement quand c'est
    pertinent!
    
    Exemple:
        cerveau = CerveauDecisionnel()
        
        # Vérifier si on doit répondre
        if cerveau.doit_repondre(auteur, contenu):
            # Oui, on génère une réponse
            ...
        else:
            # Non, on reste silencieux
            ...
    """
    
    def __init__(
        self,
        noms: Optional[List[str]] = None,
        nom_bot: Optional[str] = None,
        delai_secondes: float = 2.0,
        max_reponses_par_minute: int = 10
    ):
        """
        Args:
            noms: Liste des noms/surnoms de Ryosa
            nom_bot: Nom du compte bot (pour ne pas se répondre)
            delai_secondes: Temps minimum entre deux réponses
            max_reponses_par_minute: Limite de réponses par minute
        """
        self.noms = noms or configuration.obtenir_liste_noms()
        self.nom_bot = (nom_bot or configuration.twitch_nom_bot).lower()
        
        # Anti-spam
        self.delai_secondes = delai_secondes
        self.max_reponses_par_minute = max_reponses_par_minute
        
        # Suivi des réponses
        self.derniere_reponse_timestamp = 0
        self.timestamps_reponses: List[float] = []
        
        logger.info(f"CerveauDecisionnel initialisé - Noms: {self.noms}")
    
    def est_soi_meme(self, auteur: str) -> bool:
        """
        Vérifie si le message vient de Ryosa elle-même.
        
        CRITIQUE: Une IA qui se répond à elle-même peut créer
        une boucle infinie! On doit absolument éviter ça.
        """
        auteur_minuscule = auteur.lower().strip()
        
        # Le nom du bot exactement
        if auteur_minuscule == self.nom_bot:
            return True
        
        # Contient un des noms de Ryosa
        for nom in self.noms:
            if nom.lower() == auteur_minuscule:
                return True
        
        return False
    
    def est_mentionnee(self, contenu: str) -> bool:
        """
        Vérifie si Ryosa est mentionnée dans le message.
        
        Détecte:
        - @ryosa ou @Ryosa
        - "ryosa" dans le texte
        - Variations du nom
        """
        contenu_minuscule = contenu.lower()
        
        for nom in self.noms:
            # Mention avec @
            if f"@{nom}" in contenu_minuscule:
                logger.debug(f"Mention @ détectée: {nom}")
                return True
            
            # Nom dans le texte
            if nom in contenu_minuscule:
                logger.debug(f"Nom détecté: {nom}")
                return True
        
        return False
    
    def est_question_au_chat(self, contenu: str) -> bool:
        """
        Détecte si le message est une question générale au chat.
        
        Ryosa peut choisir de répondre aux questions générales
        si le contexte semble approprié.
        """
        # Patterns de questions
        patterns_questions = [
            r"\?$",  # Finit par ?
            r"^(qui|quoi|comment|pourquoi|où|quand|est-ce que)",  # Mots interrogatifs
            r"quelqu'un (sait|peut|connaît)",  # Demande à quelqu'un
        ]
        
        contenu_minuscule = contenu.lower()
        
        for pattern in patterns_questions:
            if re.search(pattern, contenu_minuscule, re.IGNORECASE):
                return True
        
        return False
    
    def est_en_delai(self) -> bool:
        """
        Vérifie si Ryosa est en période de délai.
        
        Évite de répondre trop rapidement après la dernière réponse.
        """
        if self.derniere_reponse_timestamp == 0:
            return False
        
        temps_ecoule = time.time() - self.derniere_reponse_timestamp
        return temps_ecoule < self.delai_secondes
    
    def est_limite_atteinte(self) -> bool:
        """
        Vérifie si Ryosa a atteint sa limite de réponses par minute.
        
        Protection anti-spam pour ne pas flood le chat.
        """
        temps_actuel = time.time()
        il_y_a_une_minute = temps_actuel - 60
        
        # Nettoyer les vieux timestamps
        self.timestamps_reponses = [
            ts for ts in self.timestamps_reponses
            if ts > il_y_a_une_minute
        ]
        
        return len(self.timestamps_reponses) >= self.max_reponses_par_minute
    
    def doit_repondre(
        self,
        auteur: str,
        contenu: str,
        est_commande_directe: bool = False
    ) -> dict:
        """
        Décide si Ryosa doit répondre à ce message.
        
        Args:
            auteur: L'auteur du message
            contenu: Le contenu du message
            est_commande_directe: Si c'est une commande directe (force la réponse)
        
        Returns:
            Dictionnaire avec:
            - "doit_repondre": True/False
            - "raison": Explication de la décision
            - "priorite": 0-10 (importance de répondre)
        """
        resultat = {
            "doit_repondre": False,
            "raison": "",
            "priorite": 0
        }
        
        # ===== VÉRIFICATION 1: Self-message =====
        if self.est_soi_meme(auteur):
            resultat["raison"] = "Message de Ryosa elle-même"
            return resultat
        
        # ===== VÉRIFICATION 2: Rate limiting =====
        if self.est_limite_atteinte():
            resultat["raison"] = "Trop de réponses récentes (anti-spam)"
            return resultat
        
        # ===== VÉRIFICATION 3: Délai =====
        if self.est_en_delai() and not est_commande_directe:
            resultat["raison"] = f"Délai actif ({self.delai_secondes}s)"
            return resultat
        
        # ===== DÉCISION: Mention directe =====
        if self.est_mentionnee(contenu):
            resultat["doit_repondre"] = True
            resultat["raison"] = "Mention directe"
            resultat["priorite"] = 10
            return resultat
        
        # ===== DÉCISION: Commande directe =====
        if est_commande_directe:
            resultat["doit_repondre"] = True
            resultat["raison"] = "Commande directe"
            resultat["priorite"] = 9
            return resultat
        
        # ===== DÉCISION: Question au chat (optionnel) =====
        # Pour l'instant on ne répond qu'aux mentions directes
        # Décommente ce code si tu veux que Ryosa réponde aux questions
        """
        if self.est_question_au_chat(contenu):
            resultat["doit_repondre"] = True
            resultat["raison"] = "Question au chat"
            resultat["priorite"] = 5
            return resultat
        """
        
        # Par défaut: ne pas répondre
        resultat["raison"] = "Aucun critère de réponse"
        return resultat
    
    def enregistrer_reponse(self):
        """
        Enregistre qu'une réponse a été envoyée.
        
        À appeler APRÈS avoir envoyé une réponse pour le tracking.
        """
        temps_actuel = time.time()
        self.derniere_reponse_timestamp = temps_actuel
        self.timestamps_reponses.append(temps_actuel)
        logger.debug("Réponse enregistrée")
    
    def obtenir_statistiques(self) -> dict:
        """
        Retourne les statistiques du CerveauDecisionnel.
        """
        temps_actuel = time.time()
        il_y_a_une_minute = temps_actuel - 60
        
        reponses_recentes = len([
            ts for ts in self.timestamps_reponses
            if ts > il_y_a_une_minute
        ])
        
        delai_restant = 0
        if self.derniere_reponse_timestamp > 0:
            temps_ecoule = temps_actuel - self.derniere_reponse_timestamp
            if temps_ecoule < self.delai_secondes:
                delai_restant = self.delai_secondes - temps_ecoule
        
        return {
            "reponses_derniere_minute": reponses_recentes,
            "max_par_minute": self.max_reponses_par_minute,
            "delai_restant": round(delai_restant, 1),
            "limite_atteinte": self.est_limite_atteinte(),
        }


# Alias pour compatibilité avec l'ancien nom
SmartBrain = CerveauDecisionnel


# =============================================================================
# TEST DU CERVEAU DÉCISIONNEL
# =============================================================================
if __name__ == "__main__":
    print("🧠 Test du Cerveau Décisionnel")
    print("=" * 50)
    
    cerveau = CerveauDecisionnel(
        noms=["ryosa", "ryo"],
        nom_bot="RyosaIA"
    )
    
    # Test de différents scénarios
    cas_test = [
        ("viewer1", "Salut tout le monde!"),
        ("viewer2", "@Ryosa t'es là?"),
        ("RyosaIA", "Oui je suis là!"),  # Message de Ryosa
        ("tosachii", "Hey Ryo, ça va?"),
        ("viewer3", "C'est quoi ce jeu?"),
    ]
    
    print("\nTests de messages:")
    for auteur, contenu in cas_test:
        resultat = cerveau.doit_repondre(auteur, contenu)
        statut = "✅ RÉPONDRE" if resultat["doit_repondre"] else "⏸️ IGNORER"
        print(f"   [{auteur}]: {contenu}")
        print(f"      → {statut} - {resultat['raison']}")
        print()
        
        if resultat["doit_repondre"]:
            cerveau.enregistrer_reponse()
    
    print("\n📊 Stats:", cerveau.obtenir_statistiques())
