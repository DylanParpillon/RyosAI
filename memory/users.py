# =============================================================================
# MEMORY/USERS.PY - Mémoire des utilisateurs
# =============================================================================
# Ce fichier gère la mémoire de Ryosa concernant les utilisateurs.
# Elle peut se souvenir de choses sur chaque personne!
#
# Exemple de ce qu'elle peut retenir:
# - Jeux préférés de quelqu'un
# - Faits importants mentionnés
# - Dernière fois qu'ils sont venus
#
# NOTE: Ce fichier utilise des fichiers JSON. Il est prévu pour être
#       migré vers MongoDB quand tu auras installé ta VM.
# =============================================================================

from typing import Dict, Optional, List
from datetime import datetime
from .storage import sauvegarder_json, charger_json
import logging

logger = logging.getLogger("ryosa.users")


class MemoireUtilisateurs:
    """
    Gère la mémoire de Ryosa pour chaque utilisateur.
    
    Ryosa peut se souvenir de choses sur les gens, ce qui rend
    les conversations plus personnelles et naturelles!
    
    Exemple:
        memoire = MemoireUtilisateurs()
        
        # Ryosa apprend quelque chose
        memoire.ajouter_fait("viewer123", "aime les jeux de plateforme")
        
        # Plus tard, elle peut s'en souvenir
        faits = memoire.obtenir_faits("viewer123")
        # -> ["aime les jeux de plateforme"]
    """
    
    def __init__(self):
        """Initialise la mémoire des utilisateurs."""
        self.utilisateurs: Dict[str, dict] = {}
        self._charger()
    
    def _charger(self):
        """Charge la mémoire depuis le fichier JSON."""
        self.utilisateurs = charger_json("utilisateurs.json", defaut={})
        logger.info(f"Mémoire chargée: {len(self.utilisateurs)} utilisateurs")
    
    def _sauvegarder(self):
        """Sauvegarde la mémoire dans le fichier JSON."""
        sauvegarder_json("utilisateurs.json", self.utilisateurs)
    
    def _assurer_utilisateur(self, nom_utilisateur: str) -> dict:
        """
        S'assure qu'un utilisateur existe dans la mémoire.
        
        Args:
            nom_utilisateur: Nom de l'utilisateur
        
        Returns:
            Le dictionnaire de données de l'utilisateur
        """
        nom_utilisateur = nom_utilisateur.lower().strip()
        
        if nom_utilisateur not in self.utilisateurs:
            self.utilisateurs[nom_utilisateur] = {
                "premiere_visite": datetime.now().isoformat(),
                "derniere_visite": datetime.now().isoformat(),
                "nombre_messages": 0,
                "faits": [],          # Faits mémorisés
                "preferences": {},    # Préférences (jeux, etc.)
            }
            logger.debug(f"Nouvel utilisateur créé: {nom_utilisateur}")
        
        return self.utilisateurs[nom_utilisateur]
    
    def mettre_a_jour_activite(self, nom_utilisateur: str):
        """
        Met à jour l'activité d'un utilisateur (quand il envoie un message).
        
        Args:
            nom_utilisateur: Nom de l'utilisateur
        """
        utilisateur = self._assurer_utilisateur(nom_utilisateur)
        utilisateur["derniere_visite"] = datetime.now().isoformat()
        utilisateur["nombre_messages"] = utilisateur.get("nombre_messages", 0) + 1
        self._sauvegarder()
    
    def ajouter_fait(self, nom_utilisateur: str, fait: str):
        """
        Ajoute un fait mémorisé pour un utilisateur.
        
        Args:
            nom_utilisateur: Nom de l'utilisateur
            fait: Le fait à retenir
        
        Exemple:
            memoire.ajouter_fait("viewer123", "fan de Zelda")
        """
        utilisateur = self._assurer_utilisateur(nom_utilisateur)
        
        # On évite les doublons
        if fait not in utilisateur["faits"]:
            utilisateur["faits"].append(fait)
            logger.info(f"Nouveau fait pour {nom_utilisateur}: {fait}")
            self._sauvegarder()
    
    def obtenir_faits(self, nom_utilisateur: str) -> List[str]:
        """
        Récupère les faits mémorisés pour un utilisateur.
        
        Args:
            nom_utilisateur: Nom de l'utilisateur
        
        Returns:
            Liste des faits
        """
        nom_utilisateur = nom_utilisateur.lower().strip()
        if nom_utilisateur not in self.utilisateurs:
            return []
        return self.utilisateurs[nom_utilisateur].get("faits", [])
    
    def definir_preference(self, nom_utilisateur: str, cle: str, valeur: str):
        """
        Définit une préférence pour un utilisateur.
        
        Args:
            nom_utilisateur: Nom de l'utilisateur
            cle: Clé de la préférence (ex: "jeu_prefere")
            valeur: Valeur de la préférence (ex: "Hollow Knight")
        
        Exemple:
            memoire.definir_preference("viewer123", "jeu_prefere", "Hollow Knight")
        """
        utilisateur = self._assurer_utilisateur(nom_utilisateur)
        utilisateur["preferences"][cle] = valeur
        logger.debug(f"Préférence {nom_utilisateur}.{cle} = {valeur}")
        self._sauvegarder()
    
    def obtenir_preference(self, nom_utilisateur: str, cle: str) -> Optional[str]:
        """
        Récupère une préférence d'un utilisateur.
        
        Args:
            nom_utilisateur: Nom de l'utilisateur
            cle: Clé de la préférence
        
        Returns:
            La valeur de la préférence, ou None si non trouvée
        """
        nom_utilisateur = nom_utilisateur.lower().strip()
        if nom_utilisateur not in self.utilisateurs:
            return None
        return self.utilisateurs[nom_utilisateur].get("preferences", {}).get(cle)
    
    def obtenir_contexte_utilisateur(self, nom_utilisateur: str) -> str:
        """
        Génère un résumé de ce que Ryosa sait sur un utilisateur.
        
        Ce résumé est inclus dans le prompt pour personnaliser les réponses.
        
        Args:
            nom_utilisateur: Nom de l'utilisateur
        
        Returns:
            Texte de contexte à inclure dans le prompt
        """
        nom_utilisateur = nom_utilisateur.lower().strip()
        
        if nom_utilisateur not in self.utilisateurs:
            return f"{nom_utilisateur} est un nouveau visiteur!"
        
        utilisateur = self.utilisateurs[nom_utilisateur]
        parties_contexte = []
        
        # Nombre de messages
        nombre_messages = utilisateur.get("nombre_messages", 0)
        if nombre_messages > 100:
            parties_contexte.append(f"{nom_utilisateur} est un habitué ({nombre_messages} messages)")
        elif nombre_messages > 10:
            parties_contexte.append(f"{nom_utilisateur} vient régulièrement ({nombre_messages} messages)")
        else:
            parties_contexte.append(f"{nom_utilisateur} est relativement nouveau")
        
        # Faits mémorisés
        faits = utilisateur.get("faits", [])
        if faits:
            parties_contexte.append(f"Tu sais que: {', '.join(faits)}")
        
        # Préférences
        preferences = utilisateur.get("preferences", {})
        if preferences:
            texte_prefs = ", ".join([f"{c}: {v}" for c, v in preferences.items()])
            parties_contexte.append(f"Préférences: {texte_prefs}")
        
        return ". ".join(parties_contexte)
    
    def obtenir_statistiques(self) -> dict:
        """
        Retourne des statistiques sur la mémoire.
        
        Returns:
            Dictionnaire avec les stats
        """
        total_utilisateurs = len(self.utilisateurs)
        total_faits = sum(len(u.get("faits", [])) for u in self.utilisateurs.values())
        total_messages = sum(u.get("nombre_messages", 0) for u in self.utilisateurs.values())
        
        return {
            "total_utilisateurs": total_utilisateurs,
            "total_faits": total_faits,
            "total_messages": total_messages,
        }


# =============================================================================
# TEST DE LA MÉMOIRE UTILISATEURS
# =============================================================================
if __name__ == "__main__":
    print("🧠 Test de la mémoire des utilisateurs (JSON)")
    print("=" * 50)
    
    memoire = MemoireUtilisateurs()
    
    # Simuler des interactions
    print("\n1. Simulation d'interactions:")
    
    # Un nouveau viewer
    memoire.mettre_a_jour_activite("test_viewer")
    memoire.ajouter_fait("test_viewer", "aime les RPG")
    memoire.definir_preference("test_viewer", "jeu_prefere", "Final Fantasy")
    
    print(f"   Faits: {memoire.obtenir_faits('test_viewer')}")
    print(f"   Préférence jeu: {memoire.obtenir_preference('test_viewer', 'jeu_prefere')}")
    
    # Contexte pour le LLM
    print("\n2. Contexte généré pour l'IA:")
    contexte = memoire.obtenir_contexte_utilisateur("test_viewer")
    print(f"   {contexte}")
    
    # Stats
    print("\n3. Statistiques:")
    stats = memoire.obtenir_statistiques()
    for cle, valeur in stats.items():
        print(f"   {cle}: {valeur}")
