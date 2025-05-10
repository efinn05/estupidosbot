import os
import requests
import cv2
from telegram.ext import Updater, MessageHandler, Filters

# 🔐 Tus claves
TELEGRAM_TOKEN = '7621542899:AAGWYg0xjACU7G693oLzjUgZ_olBh-Da4sU'
SIGHTENGINE_USER = '1999824564'
SIGHTENGINE_SECRET = 'DuFcmKiRjw6gLdu5DFN7WwqF922bohVN'

# 📷 Revisar imágenes
def revisar_imagen(update, context):
    mensaje = update.message
    if not mensaje.photo:
        return

    archivo = mensaje.photo[-1].get_file()
    ruta = 'imagen.jpg'
    archivo.download(ruta)

    analizar_y_banear(ruta, mensaje, context)

# 🎥 Revisar videos
def revisar_video(update, context):
    mensaje = update.message
    if not mensaje.video:
        return

    archivo = mensaje.video.get_file()
    ruta_video = 'video.mp4'
    ruta_frame = 'frame.jpg'
    archivo.download(ruta_video)

    video = cv2.VideoCapture(ruta_video)
    success, frame = video.read()
    if success:
        cv2.imwrite(ruta_frame, frame)
    video.release()
    os.remove(ruta_video)

    analizar_y_banear(ruta_frame, mensaje, context)

# 📦 Revisar GIFs y stickers animados (como archivos/documentos)
def revisar_documento(update, context):
    mensaje = update.message
    if not mensaje.document:
        return

    archivo = mensaje.document.get_file()
    ruta = 'archivo.gif'
    archivo.download(ruta)

    # Extraer primer frame del gif
    video = cv2.VideoCapture(ruta)
    success, frame = video.read()
    if success:
        ruta_frame = 'gif_frame.jpg'
        cv2.imwrite(ruta_frame, frame)
        video.release()
        os.remove(ruta)
        analizar_y_banear(ruta_frame, mensaje, context)
    else:
        os.remove(ruta)

# 🧠 Analizar la imagen y tomar acción
def analizar_y_banear(ruta_imagen, mensaje, context):
    with open(ruta_imagen, 'rb') as img:
        r = requests.post(
            'https://api.sightengine.com/1.0/check.json',
            files={'media': img},
            data={'models': 'nudity,wad,offensive,gore', 'api_user': SIGHTENGINE_USER, 'api_secret': SIGHTENGINE_SECRET}
        )
        resultado = r.json()

    os.remove(ruta_imagen)

    if (
        resultado.get('nudity', {}).get('raw', 0) > 0.7 or
        resultado.get('weapon', 0) > 0.5 or
        resultado.get('gore', 0) > 0.5 or
        resultado.get('drugs', 0) > 0.5
    ):
        try:
            mensaje.delete()
            context.bot.kick_chat_member(chat_id=mensaje.chat_id, user_id=mensaje.from_user.id)
            mensaje.reply_text("🚫 Contenido inapropiado detectado. Usuario expulsado.")
        except Exception as e:
            print("Error al borrar o expulsar:", e)
            mensaje.reply_text("⚠️ No tengo permisos suficientes para borrar o expulsar.")

# 🚀 Iniciar el bot
def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.photo, revisar_imagen))
    dp.add_handler(MessageHandler(Filters.video, revisar_video))
    dp.add_handler(MessageHandler(Filters.document.category("video"), revisar_documento))
    dp.add_handler(MessageHandler(Filters.sticker, revisar_documento))

    updater.start_polling()
    print("✅ Bot moderador en funcionamiento.")
    updater.idle()

if __name__ == '__main__':
    main()
