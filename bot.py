import re
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction, FlexSendMessage, ImageSendMessage
)
import requests

LINE_CHANNEL_ACCESS_TOKEN = "pOeuYts3fBz7/7EKuLM/MbtWuwwafC8j3PEt7aO5BYiSYN6ktoeCTdY/9hioytXloOlymxzh0Q7mYgtjt5bkkR/xoz33wJIhu+ZAvZ0SKISMJaVrSxQdu7ue6aZJXZt2HdLNpQIzFvNsupbHK5qwPgdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "a97292ce3ac2827d0ac77ab4deac0ea8"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

PREDICTION_API_URL = "https://bot-api-hxi2.onrender.com/predict"

user_sessions = {}

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Line Chatbot for Penguin Prediction is Running."

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text.strip().lower()

    if user_input in ["help", "ช่วยเหลือ", "วิธีใช้", "สอบถาม"]:
        reply_text = (
            "🔹 วิธีใช้ระบบพยากรณ์เบาหวาน\n"
            "1️⃣ พิมพ์ 'Prediction' เพื่อเริ่มต้น\n"
            "2️⃣ บอทจะถามค่าที่ต้องกรอกทีละข้อ\n"
            "3️⃣ ตอบค่าต่างๆ ตามที่ระบบขอ\n"
            "4️⃣ หลังจากกรอกครบ ระบบจะทำการพยากรณ์ผล\n"
            "🔸 หากต้องการเริ่มใหม่ ให้พิมพ์ 'ยกเลิก'"
        )
        
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    if user_input in ["prediction", "พยากรณ์", "ทำนาย", "predict", "predictions"]:
        user_sessions[user_id] = {"step": 1, "data": {}}
        reply_text = "กรุณากรอกค่า Glucose (mg/dL) เช่น 120"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    if user_input in ["ถูกต้อง", "ยืนยันข้อมูล"]:
        if user_id not in user_sessions or "data" not in user_sessions[user_id]:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ไม่พบข้อมูล กรุณาเริ่มใหม่"))
            return

        user_data = user_sessions[user_id]["data"]

        response = requests.post(PREDICTION_API_URL, json=user_data)
        result = response.json()

        if "prediction" in result:
            reply_text = f"ผลลัพธ์: {result['prediction']}"
        else:
            reply_text = f"Error: {result.get('error', 'ไม่สามารถพยากรณ์ได้')}"

        del user_sessions[user_id]  
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    if user_input == "ยกเลิก":
        del user_sessions[user_id]  
        reply_text = "ข้อมูลถูกยกเลิก กรุณาเริ่มใหม่"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    if user_id in user_sessions:
        session = user_sessions[user_id]
        step = session["step"]

        try:
            if step in [1, 2, 3]:  
                if not re.match(r'^\d+(\.\d+)?$', user_input):
                    reply_text = "กรุณากรอกเฉพาะค่าตัวเลขที่เป็นบวก เช่น 120"
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
                    return

                value = float(user_input)

                if step == 1:
                    session["data"]["Glucose"] = value
                    reply_text = "กรุณากรอกค่า Insulin (μU/mL) เช่น 80"
                elif step == 2:
                    session["data"]["Insulin"] = value
                    reply_text = "กรุณากรอกค่า BMI เช่น 25.5"
                elif step == 3:
                    session["data"]["BMI"] = value
                    summary_flex = create_summary_flex(session["data"])
                    line_bot_api.reply_message(event.reply_token, summary_flex)
                    return

                session["step"] += 1
        
        except ValueError:
            reply_text = "กรุณากรอกค่าตัวเลขที่ถูกต้อง"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
            return

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return


def create_summary_flex(user_data):
    flex_message = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#E3F2FD", 
            "cornerRadius": "md",
            "paddingAll": "lg",
            "contents": [
                {
                    "type": "text",
                    "text": "ข้อมูลของคุณ",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#1976D2",  
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "sm",
                    "color": "#B0BEC5"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "sm",
                    "spacing": "xs",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"Bill Length: {user_data['bill_length_mm']} mm",
                            "size": "md",
                            "color": "#37474F"
                        },
                        {
                            "type": "text",
                            "text": f"Bill Depth: {user_data['bill_depth_mm']} mm",
                            "size": "md",
                            "color": "#37474F"
                        },
                        {
                            "type": "text",
                            "text": f"Flipper Length: {user_data['flipper_length_mm']} mm",
                            "size": "md",
                            "color": "#37474F"
                        },
                        {
                            "type": "text",
                            "text": f"Body Mass: {user_data['body_mass_g']} g",
                            "size": "md",
                            "color": "#37474F"
                        },
                        {
                            "type": "text",
                            "text": f"Sex: {user_data['sex']}",
                            "size": "md",
                            "color": "#37474F"
                        }
                    ]
                },
                {
                    "type": "separator",
                    "margin": "sm",
                    "color": "#B0BEC5"
                },
                {
                    "type": "text",
                    "text": "ข้อมูลของคุณถูกต้องหรือไม่?",
                    "margin": "sm",
                    "size": "md",
                    "color": "#1976D2",
                    "align": "center",
                    "weight": "bold"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#BBDEFB",  
            "cornerRadius": "md",
            "paddingAll": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#42A5F5",
                    "action": {
                        "type": "message",
                        "label": "ถูกต้อง",
                        "text": "ยืนยันข้อมูล"
                    },
                    "height": "sm",
                    "margin": "none"
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "color": "#90A4AE",
                    "action": {
                        "type": "message",
                        "label": "ยกเลิก",
                        "text": "ยกเลิก"
                    },
                    "height": "sm",
                    "margin": "md"
                }
            ]
        }
    }
    return FlexSendMessage(alt_text="สรุปข้อมูลของคุณ", contents=flex_message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
