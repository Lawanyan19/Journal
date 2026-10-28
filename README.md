# Journal

Revue de presse quotidienne automatisée : le script récupère les articles récents de plusieurs médias, en fait rédiger une synthèse concise par un LLM (Gemini), puis l'envoie sur Telegram. L'exécution est automatisée avec GitHub Actions, sans serveur à maintenir.

## Fonctionnement

1. **Collecte** : lecture des flux RSS de plusieurs médias avec `feedparser`.
2. **Filtrage temporel** : seuls les articles des dernières 48 h sont conservés, 96 h pour les médias musicaux afin de ne pas manquer les sorties du vendredi.
3. **Synthèse** : les titres et résumés sont envoyés à Gemini avec des consignes strictes : 500 mots maximum, 5 rubriques (Géopolitique & International, National, Sports, Tech & Innovation, Culture & Musique), fusion des doublons et mise en forme compatible avec Telegram.
4. **Robustesse** : en cas de surcharge des serveurs (erreur 503), le script réessaie jusqu’à 3 fois, puis tente un second modèle. Si tous échouent, un message d’erreur est envoyé sur Telegram à la place du journal.
5. **Envoi** : le journal est publié dans une conversation Telegram via l'API Bot.

## Installation

```bash
pip install feedparser google-genai
```

Le script lit trois variables d'environnement :

| Variable | Rôle |
|---|---|
| `GEMINI_API_KEY` | clé de l'API Gemini |
| `TELEGRAM_TOKEN` | jeton du bot Telegram |
| `TELEGRAM_CHAT_ID` | identifiant de la conversation qui reçoit le journal |

Pour l'exécution automatique, elles sont enregistrées comme secrets du dépôt (**Settings**, **Secrets and variables**, **Actions**) et injectées par le workflow situé dans `.github/workflows/`. Aucune clé n'est stockée dans le code.

Pour une exécution locale :

```bash
python journal.py
```

## Personnalisation

- **Sources** : ajouter ou retirer des flux dans le dictionnaire `SOURCES_RSS`.
- **Rubriques et longueur** : modifier les consignes dans `prompt_instructions`.
- **Modèles** : ajuster la liste `modeles_a_tenter`.
