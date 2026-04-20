import re
import os
from google import genai

# Récupérer la clé API depuis les variables d'environnement
API_KEY = os.environ.get('GCP_API_KEY')

if not API_KEY:
    raise ValueError("❌ La variable d'environnement GCP_API_KEY n'est pas définie")

client = genai.Client(api_key=API_KEY)

def generate_with_gemini(prompt):
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt
    )
    text = response.text.strip()
    # Gemini retourne parfois ```json ... ``` → on nettoie
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()