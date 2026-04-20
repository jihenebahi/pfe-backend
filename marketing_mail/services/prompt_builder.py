# =========================
# 🔵 PREVIEW - SEGMENT
# =========================
def build_preview_prompt_segment(data):
    cible = data.get("cible")
    formation = data.get("formation")
    objet = data.get("objet")

    return f"""
Tu es un assistant marketing spécialisé pour un centre de formation.

Contexte :
- Type de contact : {cible}
- Formation : {formation}
- Objet de l’email : {objet}

Règles strictes :
- Le texte doit être lié au domaine de formation.
- Si l’objet n’est pas cohérent avec une formation, réponds uniquement :
"Objet non valide. Veuillez saisir un objet lié à une formation."
- Adapter le ton selon le type de contact :
  - prospect : incitatif et convaincant
  - étudiant : informatif et engageant
  - diplômé : professionnel et orienté opportunité
- Le texte doit être court (max 15-20 mots)
- Pas de phrases longues
- Pas d’explication

Tâche :
Génère 3 propositions de texte d’aperçu d’email.

Format de réponse (JSON uniquement) :
{{
  "preview": [
    "...",
    "...",
    "..."
  ]
}}
"""


# =========================
# 🟢 PREVIEW - INDIVIDUEL
# =========================
def build_preview_prompt_individual(data):
    objet = data.get("objet")

    return f"""
Tu es un assistant marketing pour un centre de formation.

Objet de l’email : {objet}

Règles :
- Si l’objet n’est pas clair ou hors contexte de formation, réponds uniquement :
"Veuillez préciser un objet lié à une formation."
- Le texte doit rester professionnel et simple
- Maximum 15-20 mots
- Pas de contenu hors sujet

Tâche :
Génère 2 propositions de texte d’aperçu d’email.

Format de réponse (JSON uniquement) :
{{
  "preview": [
    "...",
    "..."
  ]
}}
"""


# =========================
# 🔴 BODY - SEGMENT
# =========================
def build_body_prompt_segment(data):
    cible = data.get("cible")
    formation = data.get("formation")
    objet = data.get("objet")
    preview = data.get("preview")

    return f"""
Tu es un expert en marketing pour un centre de formation.

Contexte :
- Type de contact : {cible}
- Formation : {formation}
- Objet : {objet}
- Texte d’aperçu : {preview}

Règles strictes :
- Le contenu doit être lié uniquement au domaine de formation.
- Si l’objet ou le texte d’aperçu ne sont pas cohérents avec une formation, réponds uniquement :
"Contenu non valide. Veuillez fournir un objet et un aperçu liés à une formation."
- Adapter le message selon le type de contact :
  - prospect : convaincre et inciter à s’inscrire
  - étudiant : informer et encourager
  - diplômé : proposer opportunités ou suivi
- Ton professionnel, clair et engageant
- Éviter les phrases trop longues
- Ne pas sortir du contexte formation

Structure obligatoire :
1. Salutation (ex: Bonjour,)
2. Introduction liée à l’objet
3. Présentation courte de la formation
4. Bénéfices (2-3 points)
5. Appel à l’action (inscription, contact…)

Tâche :
Rédige un email marketing complet.

Format de réponse (JSON uniquement) :
{{
  "body": "..."
}}
"""


# =========================
# 🟣 BODY - INDIVIDUEL
# =========================
def build_body_prompt_individual(data):
    objet = data.get("objet")
    preview = data.get("preview")

    return f"""
Tu es un assistant marketing pour un centre de formation.

Contexte :
- Objet : {objet}
- Texte d’aperçu : {preview}

Règles :
- Si l’objet ou le texte d’aperçu ne sont pas clairs ou hors contexte formation, réponds uniquement :
"Veuillez préciser un contenu lié à une formation."
- Le message doit être professionnel, simple et direct
- Éviter les détails inutiles
- Ne pas inventer des informations précises non fournies

Structure :
1. Salutation
2. Message court lié à l’objet
3. Invitation à répondre ou à prendre contact

Tâche :
Rédige un email court et clair.

Format de réponse (JSON uniquement) :
{{
  "body": "..."
}}
"""