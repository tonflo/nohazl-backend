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

# OpenAI API-konfiguration
openai.api_key = os.getenv("OPENAI_API_KEY")

# 🛑 Spara användarens språk i en dictionary (använd sessioner om du vill ha det per användare)
user_language = {}

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    user_id = request.remote_addr  # 🛑 Identifiera användaren via IP-adress (kan ändras till en bättre identifiering)

    if user_id not in user_language:
        # 🛑 Första meddelandet: Låt AI identifiera språket
        language_prompt = f"Identifiera vilket språk detta meddelande är skrivet på och svara endast med namnet på språket: {user_message}"
        client = openai.OpenAI()
        lang_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": language_prompt}]
        )
        detected_language = lang_response.choices[0].message.content.strip()
        user_language[user_id] = detected_language

    # 🛑 Sätt språk i systempromten
    system_prompt = f"Du är en AI-assistent som alltid svarar på {user_language[user_id]}. Håll konversationen på detta språk."

    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    reply = response.choices[0].message.content
    return jsonify({"reply": reply})

# Lista för att spara e-postadresser för uppföljning
saved_emails = []

# E-postkonfiguration (NoHazl-mail)
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

@app.route('/get-saved-emails', methods=['GET'])
def get_saved_emails():
    return jsonify({"saved_emails": saved_emails})

def follow_up_emails():
    while True:
        time.sleep(7 * 24 * 60 * 60)
        for email in saved_emails:
            try:
                msg = MIMEText("Hello! One week ago, you received AI-generated advice from No Hazl AI Chat. Did our suggestions help? Let us know if you need further assistance!")
                msg["Subject"] = "Follow-up from No Hazl AI Chat"
                msg["From"] = EMAIL_ADDRESS
                msg["To"] = email

                with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                    server.sendmail(EMAIL_ADDRESS, email, msg.as_string())

                print(f"Follow-up email sent to {email}")
            except Exception as e:
                print(f"Failed to send follow-up email to {email}: {str(e)}")

follow_up_thread = threading.Thread(target=follow_up_emails, daemon=True)
follow_up_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
