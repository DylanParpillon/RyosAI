#!/bin/bash

# =============================================================================
# SCRIPT DE DÉMARRAGE RAPIDE (Linux/Mac)
# =============================================================================

echo "🚀 Démarrage de RyosAI..."

# Vérifier si venv existe
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
    source venv/bin/activate
    
    echo "📦 Installation des dépendances..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Vérifier .env
if [ ! -f ".env" ]; then
    echo "⚠️  Fichier .env manquant!"
    echo "➡️  Copie de .env.example vers .env..."
    cp .env.example .env
    echo "📝 Ouvre le fichier .env et ajoute tes tokens!"
    exit 1
fi

# Lancer Ryosa
python3 main.py
