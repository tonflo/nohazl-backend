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

# Lista för att spara e-postadresser för uppföljning
saved_emails = []

# E-postkonfiguration (NoHazl-mail)
EMAIL_ADDRESS = "chat@nohazl.com"  # NoHazl-mail
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # App-lösenord eller SMTP-lösenord
SMTP_SERVER = "smtp.strato.de"  # Strato SMTP-server
SMTP_PORT = 465  # SMTP-port

@app.route('/send-summary', methods=['POST'])
def send_summary():
    data = request.json
    email = data.get("email")
    summary = data.get("summary")
    
    if not email or not summary:
        return jsonify({"error": "Missing email or summary"}), 400
    
    # Spara e-postadressen för framtida uppföljning
    saved_emails.append(email)
    
    # Skapa e-postmeddelandet
    msg = MIMEText(f"Here is your chat summary:\n\n{summary}")
    msg["Subject"] = "Your Chat Summary from No Hazl AI Chat"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email
    
    try:
        # Skicka e-post
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        
        return jsonify({"message": "Summary sent successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-saved-emails', methods=['GET'])
def get_saved_emails():
    return jsonify({"saved_emails": saved_emails})

# Funktion för att skicka uppföljningsmejl efter en vecka
def follow_up_emails():
    while True:
        time.sleep(7 * 24 * 60 * 60)  # Vänta en vecka
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

# Starta uppföljningsfunktionen i en separat tråd
follow_up_thread = threading.Thread(target=follow_up_emails, daemon=True)
follow_up_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
