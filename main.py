import re
import telegram
import asyncio
import logging
import pg8000
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
import google.generativeai as generative_ai
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
import bcrypt

# Configuración de logging 
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)  # Inicializa el logger

# Reemplaza con tus credenciales
TOKEN = "TOKEN BOT" # REEMPLAZAR CON TOKEN DEL BOT
GOOGLE_API_KEY = "API GEMINI" # REEMPLAZAR CON API DE GOOGLE

# Inicializa la API de Gemini
generative_ai.configure(api_key=GOOGLE_API_KEY)
model = generative_ai.GenerativeModel("gemini-pro")


# Establece la conexión con base de datos utilizando pg8000
def get_db_connection():
    conn = pg8000.connect(
        user="USUARIO",  # Usuario de la base de datos
        password="CONTRASEÑA",  # Contraseña de la base de datos
        host="HOST",  # Dirección del host
        port="PUERTO",  # Puerto
        database="NOMBRE",  # Nombre de la base de datos
        ssl_context=True  # Usar SSL
    )
    return conn


# Función para guardar la consulta en la base de datos
def guardar_consulta(user_id, input_text, usuario):
    try:
        conn = get_db_connection()
        logger.info("Conexión a la base de datos establecida.")  # Registra la conexión exitosa
        cursor = conn.cursor()
        # Inserta la consulta en la tabla Consultas
        cursor.execute("INSERT INTO consultas (user_id, input, usuario) VALUES (%s, %s, %s)",
                       (user_id, input_text, usuario))
        conn.commit()
        logger.info(f"Consulta guardada: user_id={user_id}, input='{input_text}', usuario='{usuario}'")
    except Exception as e:
        logger.error(f"Error al guardar la consulta: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()
            logger.info("Conexión a la base de datos cerrada.")  # Registra el cierre de la conexión


###################SEGURIDAD###################
# La contraseña maestra hasheada
PASSWORD_HASH = "AQUI HABRÍA QUE PONER EL HASH EXTRAIDO DE HASH.PY"  # Password hasheada


# Función para verificar la contraseña
def verificar_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)
###################SEGURIDAD###################


# Función para manejar el comando /start
async def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    if 'authenticated' not in context.user_data or not context.user_data['authenticated']:  # Si el usuario no está autenticado
        await update.message.reply_text(f"¡Hola {user.first_name} 👋!\n"
                                        "Para usar este bot, por favor, introduce la contraseña:")
        context.user_data['waiting_for_password'] = True  # Marca que estamos esperando la contraseña
    else:
        await update.message.reply_text(f"¡Hola {user.first_name}👋!\n"
                                        "Bienvenido. ¿En qué puedo ayudarte?")


# Función para manejar el comando /help
async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Puedo responder preguntas, generar informes y mucho más. ¡Pregunta lo que necesites!")


# Función para manejar el comando /about
async def about_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Bot creado por hm.")


# Función para manejar mensajes de texto
async def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    user_id = update.message.from_user.id  # Obtener el ID del usuario
    usuario = update.message.from_user.first_name  # Obtener el nombre del usuario
    if 'waiting_for_password' in context.user_data and context.user_data['waiting_for_password']:  # Si estamos esperando la contraseña
        password = user_message
        if verificar_password(password, PASSWORD_HASH):  # Verifica la contraseña
            context.user_data['authenticated'] = True  # Marca al usuario como autenticado
            del context.user_data['waiting_for_password']  # Restablece la marca
            await update.message.reply_text("¡Contraseña correcta! Ahora puedes usar el bot.")
        else:
            await update.message.reply_text("Contraseña incorrecta. Por favor, inténtalo de nuevo.")
    elif 'authenticated' not in context.user_data or not context.user_data['authenticated']:  # Si no está autenticado, no permite usar el bot
        await update.message.reply_text("Para usar este bot, por favor, introduce la contraseña usando /start.")
    else:
        # Guarda la consulta en la base de datos
        guardar_consulta(user_id, user_message, usuario)
        try:
            response = model.generate_content(user_message)
            bot_reply = response.text if response.text else "Lo siento, no tengo una respuesta en este momento."
        except Exception as e:
            bot_reply = f"Error al procesar tu solicitud: {e}"
        try:
            await update.message.reply_text(bot_reply, parse_mode="Markdown")
        except Exception as e:
            f"Error al procesar tu solicitud:  {e}"


# Función principal
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot en ejecución...")
    application.run_polling()


if __name__ == '__main__':
    main()
