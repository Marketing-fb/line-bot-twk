from flask import Flask, request, abort, url_for, send_from_directory
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    FlexMessage,
    FlexCarousel,
    FlexBubble,
    FlexImage,
    FlexBox,
    FlexButton,
    MessageAction,
    TextMessage,
    QuickReply,
    QuickReplyItem
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
import os
import requests
from datetime import datetime, timedelta

os.environ["FLASK_SKIP_DOTENV"] = "1"
app = Flask(__name__, static_folder='.', static_url_path='/static')
user_states = {}

CHANNEL_ACCESS_TOKEN_1 = "4eAH59oxrR3UUYIYGQE/1ihGOouS/IbhDIJkbUOJ9C/VBM1UjOhd++hWVBE0lVqN/wq39d6XYdmbdR3lVF3/4zhw0Kr3WSfkSW4fSbK5YbfLHyg+tnrJmab3sGvDIfNMXd6q8A86v/KDmeKz5O95hgdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET_1 = "f3eebeda19446c4e7287d54d1b6f1ef6"
SCRIPT_URL_1 = "https://script.google.com/macros/s/AKfycbxuFIUFZ8LBbcdz9-fGSOeY9kD1qVxLhVTvxy1DKeOjeOh5mV1CD5Bt0PqXKSc4p10T/exec"

CHANNEL_ACCESS_TOKEN_2 = "MlnDvQQGSC2nZ1znCwZUlyzxLq+WmLGM/aPRYDGFk8K9g0WbniDGTzsjVdyOODt8H5sg4wACyTFd9sjAc8y2d0Hc+DZCwqGz3ntxqb9GXmudBWSOJJLRYGuLsaq41lMu84XbmV74OYqcl0RnwwCs6AdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET_2 = "817aaffc5346eacdfdb06f390ef9372b"
SCRIPT_URL_2 = "https://script.google.com/macros/s/AKfycbyNTEXRHgWrxtmCuHLnI6eIHLz9zfPYlp31oaILOOyx7Nwc2oumC9tI-ovhJUuhte9UjQ/exec"

configuration_1 = Configuration(access_token=CHANNEL_ACCESS_TOKEN_1)
handler_1 = WebhookHandler(CHANNEL_SECRET_1)

configuration_2 = Configuration(access_token=CHANNEL_ACCESS_TOKEN_2)
handler_2 = WebhookHandler(CHANNEL_SECRET_2)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler_1.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@app.route("/callback2", methods=['POST'])
def callback2():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler_2.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@app.route("/")
def index():
    return "Webhook is running for both accounts!"

def process_message(event, config, script_url):
    text = event.message.text
    user_id = event.source.user_id
    
    import re
    tracking_number = text.strip().upper()
    
    # ตรวจสอบว่าข้อความมีตัวเลขติดกัน 5 หลักขึ้นไปหรือไม่ (รับรู้ทันทีโดยไม่ต้องรอสถานะ)
    if re.search(r"\d{5,}", tracking_number):
        if user_id in user_states:
            del user_states[user_id]
            
        now = datetime.utcnow() + timedelta(hours=7)
        date_str = now.strftime("%d/%m/%Y")
        time_str = now.strftime("%H:%M")
        
        payload = {
            "tracking": tracking_number,
            "date": date_str,
            "time": time_str,
            "status": "รอดำเนินการ"
        }
        
        reply_text = f"ขอบคุณค่ะ 🙏 บันทึกข้อมูลเลข {tracking_number} เรียบร้อยแล้ว ทีมงานจะรีบดำเนินการให้นะคะ"
        with ApiClient(config) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
            
        def send_to_sheets():
            import requests
            try:
                requests.post(script_url, json=payload)
            except Exception as e:
                app.logger.error(f"Error saving to sheets: {e}")
                
        import threading
        threading.Thread(target=send_to_sheets).start()
        return True
    return False

@handler_1.add(MessageEvent, message=TextMessageContent)
def handle_message_1(event):
    if process_message(event, configuration_1, SCRIPT_URL_1): return
    handle_common_menu(event, configuration_1)

@handler_2.add(MessageEvent, message=TextMessageContent)
def handle_message_2(event):
    if process_message(event, configuration_2, SCRIPT_URL_2): return
    handle_common_menu(event, configuration_2)

def handle_common_menu(event, configuration):
    text = event.message.text
        
    if text == "แจ้ง Tracking":
        reply_text = "ลูกค้าสามารถแจ้งเลข Tracking โดยพิมพ์ \"โค้ดลูกค้า\" และใส่ขีด - ด้วยและ \"เลข Tracking\" ต่อกันในข้อความเดียว โดยไม่ต้องเว้นวรรคได้เลยครับ\nตัวอย่าง\nTWK-OPPA-AIR6778366197549\nหรือ\nTWK-OPPA-SHIP6778366197559"
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
            
    elif text in ["กฎและเงื่อนไข", "กฏและเงื่อนไข"]:
        host_url = request.host_url.replace("http://", "https://")
        
        bubbles = []
        for i in range(1, 6):
            img_url = f"{host_url}static/rule{i}.jpg"
            bubbles.append(
                FlexBubble(
                    body=FlexBox(
                        layout='vertical',
                        paddingAll='0px',
                        contents=[
                            FlexImage(
                                url=img_url,
                                size='full',
                                aspectMode='cover',
                                aspectRatio='2:3'
                            )
                        ]
                    )
                )
            )
            
        carousel = FlexCarousel(contents=bubbles)
        flex_message = FlexMessage(alt_text="สไลด์กฎและเงื่อนไข", contents=carousel)
            
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[flex_message]
                )
            )
            
    elif text == "ราคาแพ็คเกจ":
        host_url = request.host_url.replace("http://", "https://")
        
        bubbles = []
        for i in range(1, 3):
            img_url = f"{host_url}static/price{i}.jpg"
            bubbles.append(
                FlexBubble(
                    body=FlexBox(
                        layout='vertical',
                        paddingAll='0px',
                        contents=[
                            FlexImage(
                                url=img_url,
                                size='full',
                                aspectMode='cover',
                                aspectRatio='1:1'
                            )
                        ]
                    ),
                    footer=FlexBox(
                        layout='vertical',
                        spacing='sm',
                        contents=[
                            FlexButton(
                                style='primary',
                                color='#122346', # TWK Navy Blue
                                action=MessageAction(
                                    label='สอบถามราคาเหมา',
                                    text='ติดต่อแอดมิน'
                                )
                            )
                        ]
                    )
                )
            )
            
        carousel = FlexCarousel(contents=bubbles)
        flex_message = FlexMessage(alt_text="สไลด์ราคาแพ็คเกจ", contents=carousel)
            
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[flex_message]
                )
            )
            

    elif text == "ติดต่อแอดมิน":
        quick_reply = QuickReply(
            items=[
                QuickReplyItem(
                    action=MessageAction(label="💸 แจ้งชำระเงิน", text="แจ้งชำระเงิน")
                ),
                QuickReplyItem(
                    action=MessageAction(label="❓ สนใจสั่งสินค้า", text="สนใจสั่งสินค้า")
                ),
                QuickReplyItem(
                    action=MessageAction(label="👨‍💻 ติดต่อแอดมิน", text="คุยกับแอดมิน")
                )
            ]
        )
        
        text_message = TextMessage(
            text="รบกวนคุณลูกค้าเลือกหัวข้อที่ต้องการติดต่อแอดมิน จากปุ่มด้านล่างนี้ได้เลยครับ 👇",
            quick_reply=quick_reply
        )
        
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[text_message]
                )
            )
            
    elif text in ["แจ้งชำระเงิน", "สนใจสั่งสินค้า", "คุยกับแอดมิน"]:
        text_message = TextMessage(
            text="ระบบได้แจ้งเตือนแอดมินเรียบร้อยแล้วครับ รบกวนพิมพ์รายละเอียดทิ้งไว้ได้เลย แอดมินจะรีบเข้ามาตอบกลับโดยเร็วที่สุดครับ 🙏"
        )
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[text_message]
                )
            )

if __name__ == "__main__":
    app.run(port=5000, debug=True)
