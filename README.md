# 🎀 RyosAI - Compagne de Stream IA

> Une IA compagne adorable pour ton stream Twitch et Discord, propulsée par **Ollama** (IA locale) et **MongoDB**.

## ✨ Fonctionnalités

- 🎮 **Bot Twitch** - Ryosa participe au chat de ton stream
- 💬 **Bot Discord** - Ryosa répond aussi sur Discord
- 🧠 **IA Locale** - Utilise Ollama, pas besoin de clé API cloud
- 💾 **Mémoire MongoDB** - Se souvient des utilisateurs et des conversations
- 🎭 **Personnalité Unique** - Ryosa a sa propre personnalité attachante
- 🛡️ **Anti-Spam** - Rate limiting et cooldown intégrés

## 🚀 Installation Rapide

### Prérequis

1. **Python 3.10+**
2. **MongoDB** (en local ou MongoDB Atlas)
3. **Ollama** avec un modèle installé

### Étape 1: Installer les dépendances

```bash
# Cloner le repo
git clone https://github.com/TON_USERNAME/RyosAI.git
cd RyosAI

# Créer un environnement virtuel (recommandé)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate   # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### Étape 2: Configurer Ollama

```bash
# Installer Ollama depuis https://ollama.ai

# Télécharger un modèle
ollama pull llama3.1

# Vérifier qu'Ollama tourne
ollama serve
```

### Étape 3: Configurer MongoDB

```bash
# Option 1: MongoDB local
# Télécharge depuis https://www.mongodb.com/try/download/community

# Option 2: Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### Étape 4: Configurer l'environnement

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer .env avec tes tokens
# (TWITCH_TOKEN, DISCORD_TOKEN, etc.)
```

### Étape 5: Lancer RyosAI

```bash
python main.py
```

## 📁 Structure du Projet

```
RyosAI/
├── config/
│   ├── __init__.py
│   └── settings.py         # Configuration (Ollama, MongoDB, Twitch, Discord)
├── core/
│   ├── __init__.py
│   ├── llm.py               # Client Ollama (IA)
│   ├── personality.py       # Personnalité de Ryosa
│   └── ryosa.py             # Cerveau principal
├── memory/
│   ├── __init__.py
│   ├── storage.py           # Stockage MongoDB
│   └── users.py             # Mémoire des utilisateurs
├── listeners/
│   ├── __init__.py
│   ├── twitch_bot.py        # Bot Twitch
│   ├── discord_bot.py       # Bot Discord
│   └── smart_brain.py       # Décideur (quand répondre)
├── web/
│   ├── __init__.py
│   ├── server.py            # API FastAPI
│   └── index.html           # Interface web de test
├── data/                    # (Legacy, maintenant dans MongoDB)
├── main.py                  # Point d'entrée
├── requirements.txt         # Dépendances Python
├── .env.example             # Exemple de configuration
└── README.md                # Ce fichier!
```

## ⚙️ Configuration

Toutes les variables de configuration sont dans `.env`:

| Variable | Description | Exemple |
|----------|-------------|---------|
| `OLLAMA_URL` | URL du serveur Ollama | `http://localhost:11434` |
| `OLLAMA_MODELE` | Modèle à utiliser | `llama3.1` |
| `MONGODB_URL` | URL MongoDB | `mongodb://localhost:27017` |
| `MONGODB_BASE` | Nom de la base | `ryosai` |
| `TWITCH_TOKEN` | Token OAuth Twitch | `oauth:xxx...` |
| `TWITCH_CHANNEL` | Ta chaîne Twitch | `tosachii` |
| `DISCORD_TOKEN` | Token bot Discord | `xxx...` |
| `DISCORD_CHANNEL_ID` | ID du salon | `123456789` |

## 🎭 Personnalité de Ryosa

Ryosa est une IA compagne avec sa propre personnalité:

- 🎀 Elle se considère comme une fille
- 💝 Elle adore son créateur (toi!)
- 😊 Elle est gentille et serviable avec les viewers
- 😜 Elle peut être taquine avec les amis proches
- ⚡ Elle répond en français, de manière naturelle

## 🛠️ Commandes

### Twitch / Discord

| Commande | Description |
|----------|-------------|
| `!ryosa <message>` | Force Ryosa à répondre |
| `!status` | Affiche le statut de Ryosa |
| `!clear` | Efface le contexte (modo seulement) |

### Mention

Tu peux aussi simplement mentionner Ryosa dans ton message:
- `Hey Ryosa, t'es là?`
- `@Ryosa comment ça va?`

## 🧪 Tests

```bash
# Tester la connexion Ollama
python core/llm.py

# Tester MongoDB
python memory/storage.py

# Tester la mémoire utilisateurs
python memory/users.py
```

## 📝 License

Créé par **Tosachii** pour **La Cabane Virtuelle**.

---

💫 *"Coucou! Je suis Ryosa, ravie de faire ta connaissance! Hihi~"*
