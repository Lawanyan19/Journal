import feedparser
from datetime import datetime, timedelta, timezone
from google import genai
import time
import urllib.request
import urllib.parse
import os

# GitHub va injecter tes clés de manière sécurisée ici
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Initialisation du client Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# Liste des flux RSS (Actualités, Tech, Éco, Musique et Sport)
SOURCES_RSS = {
    "Le Monde - International": "https://www.lemonde.fr/international/rss_full.xml",
    "France Info - Top Actualités": "https://www.francetvinfo.fr/titres.rss",
    "Courrier International": "https://www.courrierinternational.com/feed/all/rss.xml",
    "Booska-P - Rap Fr": "https://www.booska-p.com/feed/",
    "L'Équipe - À la une": "https://dwh.lequipe.fr/api/edito/rss?path=/"
}

# --- ÉTAPE 1 & 2 : COLLECTE ET FILTRAGE EXTENSIBLE ---
def collecter_actualites():
    print("⏳ Récupération des articles...")
    maintenant = datetime.now(timezone.utc)
    
    # Nos deux filtres de temps
    limite_general = maintenant - timedelta(hours=48)  # 2 jours pour l'actu générale
    limite_musique = maintenant - timedelta(hours=96)  # 4 jours pour ne pas rater le vendredi rap
    
    articles_collectes = []
    
    for nom_source, url in SOURCES_RSS.items():
        try:
            flux = feedparser.parse(url)
            for entree in flux.entries:
                if 'published_parsed' in entree and entree.published_parsed:
                    date_article = datetime.fromtimestamp(time.mktime(entree.published_parsed), timezone.utc)
                else:
                    continue
                
                # On applique la bonne limite selon la source
                est_media_musique = "Booska-P" in nom_source or "HipHopDX" in nom_source or "Pitchfork" in nom_source or "Complex" in nom_source
                limite_choisie = limite_musique if est_media_musique else limite_general
                
                if date_article > limite_choisie:
                    titre = entree.get('title', '')
                    resume = entree.get('summary', '')
                    articles_collectes.append(f"Source: {nom_source}\nTitre: {titre}\nRésumé: {resume}\n---")
        except Exception as e:
            print(f"⚠️ Erreur source {nom_source}: {e}")
                
    return "\n".join(articles_collectes)

# --- ÉTAPE 3 : IA GEMINI (VERSION SÉCURISÉE CONTRE LES ERREURS 503) ---
def generer_synthese(texte_brut):
    if not texte_brut.strip():
        return "Aucune actualité majeure trouvée ces dernières 48 heures."
        
    print(f"🤖 Analyse Gemini...")
    
    prompt_instructions = (
        "Tu es un analyste de haut niveau. Rédige une note de synthèse "
        "des actualités indispensables sur la base des données fournies.\n\n"
        "CONTRAINTES STRICTES :\n"
        "1. Le contenu DOIT être très concis et tenir sur une seule page (maximum 500 mots).\n"
        "2. Organise la note en 5 sections claires et bien distinctes avec des titres en gras :\n"
        "   - *GÉOPOLITIQUE & INTERNATIONAL*\n"
        "   - *NATIONAL*\n"
        "   - *SPORTS*\n"
        "   - *TECH & INNOVATION*\n"
        "   - *CULTURE & MUSIQUE*\n"
        "3. Supprime les doublons en fusionnant les infos similaires.\n"
        "4. Utilise le format Markdown de Telegram : utilise de simples astérisques pour le gras (ex: *Mon Titre*), pas de crochets [], pas de double astérisques **. Va droit au but."
    )
    
    modeles_a_tenter = ['gemini-2.5-flash', 'gemini-1.5-flash']
    
    for nom_modele in modeles_a_tenter:
        for essai in range(3):
            try:
                response = client.models.generate_content(
                    model=nom_modele,
                    contents=f"{prompt_instructions}\n\nVoici les articles bruts :\n\n{texte_brut}"
                )
                return response.text
            except Exception as e:
                if "503" in str(e) and essai < 2:
                    print(f"⚠️ Serveur surchargé (Essai {essai + 1}/3). Nouvelle tentative dans 5 secondes...")
                    time.sleep(5)
                else:
                    print(f"❌ Échec avec le modèle {nom_modele}: {e}")
                    break
                    
    return "❌ Erreur Gemini : Les serveurs de Google étaient indisponibles après plusieurs tentatives sur différents modèles."

# --- ÉTAPE 4 : ENVOI TELEGRAM ---
def envoyer_a_telegram(texte):
    print("🚀 Envoi du journal sur Telegram...")
    date_str = datetime.now().strftime('%d/%m/%Y')
    message_complet = f"📰 *VOTRE JOURNAL DU {date_str} (48h)*\n\n{texte}"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message_complet,
        'parse_mode': 'Markdown'
    }
    
    data = urllib.parse.urlencode(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    
    try:
        with urllib.request.urlopen(req) as response:
            print("✅ Journal reçu sur Telegram !")
    except Exception as e:
        print(f"❌ Erreur d'envoi Telegram : {e}")

# --- LANCEMENT ---
if __name__ == "__main__":
    data_brute = collecter_actualites()
    journal = generer_synthese(data_brute)
    envoyer_a_telegram(journal)
