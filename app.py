from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Hämta din OpenAI API-nyckel från miljövariabler
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/healthz", methods=["GET"])
def health_check():
    """ Används för att kolla om backend är uppe (Render Health Check) """
    return jsonify({"status": "ok"}), 200

@app.route("/chat", methods=["POST"])
def chat():
    """
    Mjuk ton: Ställer följdfrågor, ger DIY-tips, erbjuder vidare hjälp om det passar.
    """
    data = request.get_json(force=True)
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Jag behöver en fråga eller ett ämne för att hjälpa dig!"}), 400

    # Systemprompt i vanlig sträng (ej f-string) för att undvika backslash-problem
    system_prompt = (
        "Du är No Hazl Assistant, en vänlig och empatisk AI.\n"
        " - Hälsa alltid användaren varmt.\n"
        " - Ge korta, konkreta DIY-tips.\n"
        " - Ställ följdfrågor först, innan du levererar en längre lösning.\n"
        " - Efter att du gett ett tips, erbjud gärna att No Hazl kan hjälpa dem mer personligt.\n"
        " - Håll konversationen på ett mjukt, vänligt språk.\n"
        "Exempel: \"Har du fler detaljer?\" \"Behöver du mer hjälp?\" \"Vi kan gärna hjälpa dig vidare!\"\n"
    )

    # Bygger upp meddelanden till AI
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    try:
        # Anropa OpenAI (du nämnde gpt-4o-mini)
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


@app.route("/summary", methods=["POST"])
def summarize():
    """
    Tar hela chathistoriken + e-post från frontend.
    Skickar sammanfattningen via e-post i HTML-format.
    """
    data = request.json
    chat_history = data.get("chat", "")
    user_email = data.get("email", "")

    if not chat_history or not user_email:
        return jsonify({"error": "Chat eller e-postadress saknas!"}), 400

    # Sammanfattnings-prompt
    summary_prompt = (
        "Här är en konversation mellan en användare och en AI.\n"
        "Sammanfatta det viktigaste på ett vänligt och lättsamt sätt.\n"
        "Korta ner men behåll huvudpunkterna.\n\n"
        f"Konversation:\n{chat_history}"
    )

    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": summary_prompt}]
        )
        summary = response.choices[0].message.content

        # Skicka sammanfattningen via HTML-mejl
        send_email(user_email, summary)
        return jsonify({"message": "Sammanfattning skickad!"})

    except Exception as e:
        print("❌ Fel vid sammanfattning:", e)
        return jsonify({"error": "Kunde inte skapa sammanfattning."}), 500


def send_email(to_email, summary):
    """ Skickar ett HTML-e-postmeddelande med chattsammanfattningen via Strato (e.likn.) """
    sender_email = os.getenv("EMAIL_USERNAME")  # Ex: chat@nohazl.com
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.strato.de")
    smtp_port = int(os.getenv("SMTP_PORT", 465))

    if not sender_email or not sender_password:
        print("❌ E-postkonfiguration saknas! Lägg till EMAIL_USERNAME och EMAIL_PASSWORD.")
        return

    try:
        # Skapa ett HTML-mail via MIMEMultipart
        message = MIMEMultipart("alternative")
        message["Subject"] = "Din sammanfattning från No Hazl Assistant"
        message["From"] = sender_email
        message["To"] = to_email

        # Bygg HTML-del – ingen f-string med backslash
        html_body = (
            "<html>\n"
            "  <body>\n"
            "    <h2>Din sammanfattning</h2>\n"
            f"    <p>{summary.replace('\n', '<br>')}</p>\n"
            "    <hr>\n"
            '    <p style="font-size:0.9em;">\n'
            "      Tack för att du använder No Hazl Assistant!<br>\n"
            "      Om du har fler frågor, tveka inte att höra av dig.\n"
            "    </p>\n"
            "  </body>\n"
            "</html>\n"
        )
        message.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())

        print(f"✅ E-post skickad till {to_email}")

    except Exception as e:
        print("❌ Fel vid e-postutskick:", e)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
