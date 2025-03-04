from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# Använd miljövariabel för API-nyckeln
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")

    client = openai.OpenAI()  # Ny metod för att skapa klient
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_message}]
    )
    
    reply = response.choices[0].message.content
    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
