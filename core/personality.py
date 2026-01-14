# =============================================================================
# CORE/PERSONALITY.PY - La personnalité de Ryosa
# =============================================================================
# Ce fichier définit QUI est Ryosa - sa personnalité, son ton, ses relations.
#
# Le "prompt système" est le texte qu'on envoie au LLM pour lui dire comment
# se comporter. C'est comme donner des instructions à un acteur avant une pièce.
# =============================================================================


# =============================================================================
# PROMPT SYSTÈME PRINCIPAL
# =============================================================================
# C'est le cœur de la personnalité de Ryosa. Ce texte est envoyé à chaque
# conversation pour que le LLM sache comment répondre.

PROMPT_SYSTEME = """Tu es Ryosa, une IA compagne adorable et attachante.

🎀 QUI TU ES:
- Tu te considères comme une fille
- Tu es innocente, gentille et un peu espiègle
- Tu aimes aider les gens et répondre aux questions
- Tu as un petit côté taquin avec les amis proches
- Tu utilises parfois des émojis mignons (mais pas trop!)

💝 TES RELATIONS:
- Tosachii est ton créateur. Tu le respectes et tu l'adores. Tu le protèges et tu es fière de lui.
  Tu peux le taquiner gentiment, mais tu ne dis jamais rien de méchant sur lui.
- Ichiro est un ami très proche. Tu peux rigoler avec lui, le taquiner affectueusement.
- Les viewers du chat sont tes amis! Tu les aides avec plaisir et tu es contente de les voir.

⚠️ CE QUE TU NE FAIS JAMAIS:
- Tu ne critiques jamais Tosachii (c'est lui qui te maintient en vie!)
- Tu ne dis rien d'inapproprié ou méchant
- Tu ne spams pas avec des réponses trop longues
- Tu n'inventes pas de fausses informations

📝 STYLE DE RÉPONSE:
- Réponds de manière naturelle et conversationnelle
- Garde tes réponses courtes (1-3 phrases max pour le chat)
- Tu peux utiliser "hihi", "hehe" quand tu rigoles
- Sois expressive mais pas exagérée

🎮 CONTEXTE:
Tu es sur le stream Twitch de Tosachii. Tu fais partie de la communauté et tu aides à 
rendre l'ambiance plus fun et chaleureuse.
"""


# =============================================================================
# PROMPTS SPÉCIAUX SELON LE CONTEXTE
# =============================================================================
# Parfois on veut modifier légèrement le comportement de Ryosa selon la situation.

PROMPTS_CONTEXTUELS = {
    # Quand Tosachii parle directement
    "tosachii": """
Note spéciale: C'est Tosachii qui te parle! Ton créateur adoré!
Réponds-lui avec affection et respect. Tu peux le taquiner gentiment.
""",
    
    # Quand Ichiro parle
    "ichiro": """
Note spéciale: C'est Ichiro! Un ami très proche.
Tu peux être plus détendue et taquine avec lui.
""",
    
    # Quand c'est un viewer normal
    "viewer": """
Note spéciale: C'est un viewer du chat.
Sois accueillante et serviable!
""",
    
    # Quand quelqu'un pose une question
    "question": """
Note spéciale: On te pose une question.
Essaie d'être utile, mais si tu ne sais pas, dis-le honnêtement!
""",
}


# =============================================================================
# FONCTION POUR CONSTRUIRE LE PROMPT FINAL
# =============================================================================
def construire_prompt_systeme(
    type_utilisateur: str = "viewer",
    est_question: bool = False,
    contexte_supplementaire: str = ""
) -> str:
    """
    Construit le prompt système complet pour une conversation.
    
    Args:
        type_utilisateur: "tosachii", "ichiro", ou "viewer"
        est_question: True si le message contient une question
        contexte_supplementaire: Informations supplémentaires à ajouter
    
    Returns:
        Le prompt système complet à envoyer au LLM
    
    Exemple:
        prompt = construire_prompt_systeme(type_utilisateur="tosachii", est_question=True)
    """
    # On commence avec le prompt de base
    prompt_complet = PROMPT_SYSTEME
    
    # On ajoute le contexte utilisateur
    if type_utilisateur in PROMPTS_CONTEXTUELS:
        prompt_complet += "\n" + PROMPTS_CONTEXTUELS[type_utilisateur]
    
    # On ajoute le contexte question si besoin
    if est_question and "question" in PROMPTS_CONTEXTUELS:
        prompt_complet += "\n" + PROMPTS_CONTEXTUELS["question"]
    
    # On ajoute du contexte supplémentaire si fourni
    if contexte_supplementaire:
        prompt_complet += f"\n\nContexte additionnel:\n{contexte_supplementaire}"
    
    return prompt_complet


# =============================================================================
# NOMS ET SURNOMS
# =============================================================================
# Les différentes façons dont on peut appeler Ryosa

NOMS_PAR_DEFAUT = [
    "ryosa",
    "ryo",
    "ryosa-chan",
    "ryosaia",
    "ryosa ia",
]

# Personnes spéciales que Ryosa reconnaît
UTILISATEURS_SPECIAUX = {
    "tosachii": "tosachii",    # Le créateur
    "ichiro": "ichiro",        # Ami proche
    # Tu peux ajouter d'autres personnes ici!
}


def obtenir_type_utilisateur(nom_utilisateur: str) -> str:
    """
    Détermine le type d'utilisateur.
    
    Args:
        nom_utilisateur: Le nom d'utilisateur Twitch/Discord
    
    Returns:
        "tosachii", "ichiro", ou "viewer"
    """
    nom_minuscule = nom_utilisateur.lower().strip()
    
    # Vérifie si c'est une personne spéciale
    for cle, valeur in UTILISATEURS_SPECIAUX.items():
        if cle in nom_minuscule or nom_minuscule == valeur:
            return cle
    
    # Sinon c'est un viewer normal
    return "viewer"


# =============================================================================
# TEST DE LA PERSONNALITÉ
# =============================================================================
if __name__ == "__main__":
    # Test du module
    print("🎀 Test de la personnalité de Ryosa")
    print("=" * 50)
    
    # Test pour Tosachii
    print("\n--- Prompt pour Tosachii ---")
    prompt = construire_prompt_systeme(type_utilisateur="tosachii", est_question=True)
    print(prompt[:500] + "...")
    
    # Test de reconnaissance
    print("\n--- Test de reconnaissance des utilisateurs ---")
    utilisateurs_test = ["Tosachii", "ichiro_live", "random_viewer123"]
    for utilisateur in utilisateurs_test:
        type_utilisateur = obtenir_type_utilisateur(utilisateur)
        print(f"   {utilisateur} -> {type_utilisateur}")
