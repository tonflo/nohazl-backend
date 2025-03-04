import os
from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

# Hämta API-nyckeln från miljövariabler
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_message}]
    )

    reply = response["choices"][0]["message"]["content"]
    return jsonify({"reply": reply})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Render använder PORT-variabeln
    app.run(host="0.0.0.0", port=port)
