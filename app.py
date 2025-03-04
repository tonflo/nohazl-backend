from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

# Ange din OpenAI API-nyckel här
openai.api_key = "DIN_OPENAI_API_NYCKEL"

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
    app.run(host="0.0.0.0", port=10000)
