from flask import Flask, request, jsonify
from flask_cors import CORS  # Importera CORS
import openai
import os

app = Flask(__name__)

# Tillåt alla origins att anropa backend
CORS(app, resources={r"/*": {"origins": "*"}})

# Hämta OpenAI API-nyckeln från miljövariabler
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")

    client = openai.OpenAI()  # Skapa klient enligt nya OpenAI-biblioteket
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Ändrad modell
        messages=[{"role": "user", "content": user_message}]
    )

    reply = response.choices[0].message.content
    return jsonify({"reply": reply})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
