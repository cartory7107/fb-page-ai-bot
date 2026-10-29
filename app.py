import os
import requests
from flask import Flask, request

app = Flask(__name__)

# পরিবেশ থেকে সিক্রেট ভ্যারিয়েবল গ্রহণ
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_secret_math_token_123")
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")

# ১. মেটা ফেসবুকের Webhook ভেরিফিকেশন (GET Request)
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

# ২. মেসেঞ্জার থেকে ইনকামিং মেসেজ রিসিভ ও উত্তর পাঠানো (POST Request)
@app.route("/webhook", methods=["POST"])
def webhook_handler():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event.get("sender", {}).get("id")
                message = messaging_event.get("message", {})
                user_text = message.get("text")

                if sender_id and user_text:
                    reply_text = get_ai_answer(user_text)
                    send_messenger_message(sender_id, reply_text)
        return "EVENT_RECEIVED", 200
    return "Not Found", 404

def get_ai_answer(user_question):
    prompt = (
        "You are an inspiring Bangladeshi math teacher and helpful mentor. "
        "Answer the following student question in clear, encouraging Bengali (বাংলা ভাষায়). "
        "Keep the explanation simple, accurate, and easy to understand:\n\n"
        f"Question: {user_question}"
    )
    try:
        headers = {
            "Authorization": f"Bearer {OLLAMA_API_KEY.strip()}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gemma4:31b-cloud",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        res = requests.post("https://ollama.com/api/chat", headers=headers, json=payload, timeout=45)
        if res.status_code == 200:
            return res.json().get("message", {}).get("content")
    except Exception as e:
        print(f"Error from Ollama: {e}")
    return "দুঃখিত, এই মুহূর্তে উত্তর তৈরিতে কিছুটা সমস্যা হচ্ছে। অনুগ্রহ করে একটু পর আবার চেষ্টা করো।"

def send_messenger_message(recipient_id, text):
    url = "https://graph.facebook.com/v21.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
    }
    requests.post(url, params=params, json=payload)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
