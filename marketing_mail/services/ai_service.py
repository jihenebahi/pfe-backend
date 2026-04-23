import re
import google.generativeai as genai

# config API
genai.configure(api_key="AIzaSyC60KBetzX6I5pG-ta1GCCQ4Ieo4a9zPNQ")

def generate_with_gemini(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")

    response = model.generate_content(prompt)

    text = response.text.strip()

    # nettoyage si json retourné
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    return text.strip()