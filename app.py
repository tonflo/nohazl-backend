from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app, resources={r"/chat": {"origins": "*"}})  # Tillåter frontend att anropa denna endpoint

# OpenAI API-konfiguration
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")

    if not user_message:
        return jsonify({"reply": "Jag behöver en fråga eller ett ämne för att hjälpa dig!"}), 400

    # 🛑 Bättre prompt för att få bättre DIY-svar
    prompt = f"""
    Du är No Hazl Assistant, en hjälpsam AI som ger praktiska DIY-tips.
    När användaren frågar något, ge alltid ett konkret tips de kan testa hemma.
    Om det behövs mer info, ställ en specifik följdfråga.

    Användarens fråga: {user_message}
    """

    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        print("❌ OpenAI API-fel:", e)
        return jsonify({"reply": "⚠️ Jag kunde inte hämta ett svar just nu. Försök igen senare."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # 🔄 Ändrat från 10000 till standard
    app.run(host="0.0.0.0", port=port)
