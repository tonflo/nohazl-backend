from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Tillåter alla domäner att anropa backend

# OpenAI API-konfiguration
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")

    if not user_message:
        return jsonify({"reply": "Jag behöver en fråga eller ett ämne för att hjälpa dig!"})

    # 🛑 Förbättrad prompt för att undvika generiska svar
    prompt = f"""
    Du är No Hazl Assistant, en hjälpsam AI-assistent.
    Ge konkreta och relevanta svar baserat på användarens fråga.
    Om det är en bred fråga, ge en snabb sammanfattning men följ alltid upp med en specifik fråga.
    Håll svaren korta och relevanta, men undvik att bara säga "kan du specificera mer?".

    Användarens fråga: {user_message}
    """

    # Skapa klient och skicka förfrågan till OpenAI
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    reply = response.choices[0].message.content
    return jsonify({"reply": reply})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
