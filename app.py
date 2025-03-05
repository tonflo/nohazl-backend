from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import smtplib

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Tillåter alla domäner att anropa backend

# OpenAI API-konfiguration
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    """ Hanterar chattförfrågningar och skickar dem till OpenAI """
    print("🔍 Request JSON:", request.json)  # Debug-logg
    user_message = request.get_json(force=True).get("message")

    if not user_message:
        return jsonify({"reply": "Jag behöver en fråga eller ett ämne för att hjälpa dig!"}), 400

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

@app.route('/summary', methods=['POST'])
def summarize():
    """ Skapar en sammanfattning av chatten och skickar den via e-post """
    data = request.json
    chat_history = data.get("chat", "")
    user_email = data.get("email", "")

    if not chat_history or not user_email:
        return jsonify({"error": "Chat eller e-postadress saknas!"}), 400

    summary_prompt = f"""
    Här är en chatt mellan en användare och en AI-assistent.
    Sammanfatta det viktigaste och ge en kort sammanfattning.

    Chatt:
    {chat_history}
    """

    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": summary_prompt}]
        )
        summary = response.choices[0].message.content

        # 🔥 Skicka sammanfattningen via e-post
        send_email(user_email, summary)
        return jsonify({"message": "Sammanfattning skickad!"})

    except Exception as e:
        print("❌ Fel vid sammanfattning:", e)
        return jsonify({"error": "Kunde inte skapa sammanfattning."}), 500

def send_email(to_email, summary):
    """ Skickar ett e-postmeddelande med chattsammanfattningen """
    sender_email = os.getenv("EMAIL_USERNAME")
    sender_password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not sender_password:
        print("❌ E-postkonfiguration saknas! Lägg till miljövariablerna EMAIL_USERNAME och EMAIL_PASSWORD.")
        return

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, f"Subject: Din chattsammanfattning\n\n{summary}")
        print(f"✅ E-post skickad till {to_email}")

    except Exception as e:
        print("❌ Fel vid e-postutskick:", e)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # 🚀 Render tilldelar PORT dynamiskt
    app.run(host="0.0.0.0", port=port)
