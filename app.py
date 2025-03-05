from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import smtplib
from email.mime.text import MIMEText
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 🛑 OpenAI API-nyckel
openai.api_key = os.getenv("OPENAI_API_KEY")

# 🛑 Spara användardata (språk, historik, meddelanderäkning)
user_data = {}

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    user_id = request.remote_addr

    if user_id not in user_data:
        user_data[user_id] = {"language": None, "message_count": 0, "history": []}

    # 🛑 Lägg till senaste meddelandet i historiken
    user_data[user_id]["history"].append({"role": "user", "content": user_message})
    if len(user_data[user_id]["history"]) > 10:
        user_data[user_id]["history"].pop(0)  # Håll max 10 meddelanden

    # 🛑 Språkdetektering vid första meddelandet
    if user_data[user_id]["language"] is None:
        client = openai.OpenAI()
        lang_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Identifiera språket i detta meddelande: {user_message}. Svara endast med språknamnet."}]
        )
        user_data[user_id]["language"] = lang_response.choices[0].message.content.strip()

    # 🛑 Avgör om AI:n ska ställa följdfrågor istället för att ge en lång lista direkt
    client = openai.OpenAI()
    context_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Analysera följande fråga och avgör om den är för bred. Om den är för bred, svara endast med 'BRED'. Om den är tydlig, svara 'TYDLIG'."},
            {"role": "user", "content": user_message}
        ]
    )

    question_type = context_response.choices[0].message.content.strip()

    if question_type == "BRED":
        reply = "Det låter som att du vill veta mer om ett brett ämne. Kan du specificera lite mer? Till exempel, är du intresserad av verktyg, tekniker eller något annat specifikt?"
    else:
        # 🛑 AI ger svar baserat på tidigare konversation
        system_prompt = f"Du är en AI-assistent och ska svara på {user_data[user_id]['language']}. Håll dig till ämnet och använd sammanhanget från tidigare konversation."
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}] + user_data[user_id]["history"]
        )
        reply = response.choices[0].message.content

    user_data[user_id]["history"].append({"role": "assistant", "content": reply})
    user_data[user_id]["message_count"] += 1

    return jsonify({"reply": reply})

# 🛑 E-postkonfiguration
EMAIL_ADDRESS = "chat@nohazl.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.strato.de"
SMTP_PORT = 465

@app.route('/send-summary', methods=['POST'])
def send_summary():
    data = request.json
    email = data.get("email")
    summary = data.get("summary")

    if not email or not summary:
        return jsonify({"error": "❌ Missing email or summary"}), 400

    msg = MIMEText(f"Here is your chat summary:\n\n{summary}")
    msg["Subject"] = "Your Chat Summary"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, email, msg.as_string())

        return jsonify({"message": "✅ Summary sent successfully!"})
    except Exception as e:
        return jsonify({"error": f"❌ {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
