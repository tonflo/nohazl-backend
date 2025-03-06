from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/healthz", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    print("🔍 Inkommande data:", data)

    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"reply": "Jag behöver en fråga eller ett ämne för att hjälpa dig!"}), 400

    messages = [
        {"role": "system", "content": "Du är en hjälpsam AI-assistent."},
        {"role": "user", "content": user_message}
    ]

    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        print("❌ OpenAI API-fel:", e)
        return jsonify({"reply": "⚠️ Jag kunde inte hämta ett svar just nu. Försök igen senare."}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
