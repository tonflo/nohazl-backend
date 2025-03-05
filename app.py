from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import smtplib
from email.mime.text import MIMEText
import os
import threading
import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

openai.api_key = os.getenv("OPENAI_API_KEY")

# 🛑 Spara användarens språk och meddelanderäkning
user_data = {}

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    user_id = request.remote_addr  # 🛑 Identifiera användaren via IP-adress

    if user_id not in user_data:
        user_data[user_id] = {"language": None, "message_count": 0}

    # 🛑 Identifiera språk vid första meddelandet
    if user_data[user_id]["language"] is None:
        client = openai.OpenAI()
        lang_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Identifiera språket i detta meddelande och svara endast med språknamnet: {user_message}"}]
        )
        detected_language = lang_response.choices[0].message.content.strip()
        user_data[user_id]["language"] = detected_language

    # 🛑 Sätt språk i systempromten
    system_prompt = f"Du är en AI-assistent och ska svara på {user_data[user_id]['language']} hela konversationen."

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

    # 🛑 Efter 5 meddelanden, erbjud sammanfattning
    if user_data[user_id]["message_count"] == 5:
        reply += "\n\n📌 Vill du ha en sammanfattning skickad? Tryck på knappen nedan!"

    # 🛑 Om AI:n identifierar att det handlar om företag, fråga om registrering
    if "företag" in user_message.lower() or "business" in user_message.lower():
        reply += "\n\n🏢 Är du företagare? Vi kan registrera ditt företag i vårt lokalregister. Vill du veta mer?"

    return jsonify({"reply": reply})

# 🛑 Lista för att spara e-postadresser för uppföljning
saved_emails = []

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
        return jsonify({"error": "Missing email or summary"}), 400

    saved_emails.append(email)

    msg = MIMEText(f"Here is your chat summary:\n\n{summary}")
    msg["Subject"] = "Your Chat Summary from No Hazl AI Chat"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, email, msg.as_string())

        return jsonify({"message": "Summary sent successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
