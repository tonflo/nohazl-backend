from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

openai.api_key = os.getenv("OPENAI_API_KEY")

user_data = {}

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    user_id = request.remote_addr

    if user_id not in user_data:
        user_data[user_id] = {"language": None, "message_count": 0}

    if user_data[user_id]["language"] is None:
        client = openai.OpenAI()
        lang_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Identifiera språket i detta meddelande: {user_message}. Svara endast med språknamnet."}]
        )
        detected_language = lang_response.choices[0].message.content.strip()
        user_data[user_id]["language"] = detected_language

    system_prompt = f"Du är en AI-assistent som alltid svarar på {user_data[user_id]['language']}. Håll dig konsekvent till detta språk."

    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    reply = response.choices[0].message.content
    user_data[user_id]["message_count"] += 1

    if user_data[user_id]["message_count"] == 5:
        reply += "\n\n📩 Klicka på ikonen bredvid detta meddelande för en sammanfattning!"

    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
