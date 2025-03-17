import asyncio
import datetime
import csv
import os
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
import nest_asyncio

# Permitir bucles de eventos anidados
nest_asyncio.apply()

# ---------------- CONFIGURACIÓN ----------------
api_id = '21317979'
api_hash = '7604702a9e4f4d172d5f138ef465c9aa'
group_title = 'https://t.me/alquileres_cubanos_habana'
limit_msg = 100
session_string = '1AZWarzwBuyL9wQ-U2DGzRO2rfOzoKL8anyjwXNC1sDraygOV5YR2xJNUxNy2H6sDd3k2IiGpXFe4sqlqFwCAwn0Bsk6tRurtDa0ue503sU1jguycEW1LkqiXsXGoDS6PRiKyplYKUaTx4AvPme3tbaa0G7Qz4cm2sgqvLYzcZnluJNIsqQEeir5obRL8FI8Y7hvQEGRCislSIPQeLD_Guwhdr6C93mG2Qv2e_SPBnvek21hOZ_UzziUl4qPJJs8_tCO3LYIx8QKYJWmd9z4U6DJeqUwl9eAzm2fq3wS0nkFhvEh_NK4dyLuU5hhV0u9icpoKArjfHCSo1tvT6V11joHbzwj2kGA='

repeat_number = 1000        # Ciclos externos (se puede ajustar según necesidad)
default_datetime_before = datetime.datetime(2025, 2, 19, 23, 6, 3, tzinfo=datetime.timezone.utc)

csv_file_name = "results.csv"      # Archivo CSV donde se guardarán los mensajes
checkpoint_file = "checkpoint.txt" # Archivo para almacenar el último timestamp procesado

# Directorio para guardar imágenes
media_save_path = "downloaded_media"
os.makedirs(media_save_path, exist_ok=True)
# ------------------------------------------------

def load_checkpoint():
    """
    Carga el checkpoint (timestamp) desde el archivo, si existe.
    Si no existe o hay error, se usa default_datetime_before.
    """
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            ts_str = f.read().strip()
            try:
                ts_float = float(ts_str)
                dt = datetime.datetime.fromtimestamp(ts_float, tz=datetime.timezone.utc)
                return dt
            except Exception as e:
                print(f"Error al leer checkpoint: {e}")
                return default_datetime_before
    else:
        return default_datetime_before

def save_checkpoint(dt):
    """
    Guarda el timestamp del último mensaje procesado en el archivo de checkpoint.
    """
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        f.write(str(dt.timestamp()))

async def get_messages(client, timestamp_before):
    """
    Extrae mensajes del grupo a partir de un timestamp dado,
    obteniendo el id, la fecha, el mensaje y descargando la imagen (si existe).
    """
    all_messages = []
    try:
        group = await client.get_entity(group_title)
        posts = await client(GetHistoryRequest(
            peer=group,
            limit=limit_msg,
            offset_date=timestamp_before,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))
        for message in posts.messages:
            if message.from_id:
                try:
                    message_data = {
                        'id': message.id,
                        'date': message.date,
                        'message': message.message,
                        'image': None  # Por defecto, sin imagen
                    }
                    # Si el mensaje tiene media, intentar descargarla
                    if message.media:
                        file_path = await client.download_media(message, file=media_save_path)
                        message_data['image'] = file_path
                        print(f"Downloaded media: {file_path}")
                    all_messages.append(message_data)
                except FloodWaitError as e:
                    print(f"FloodWaitError: Esperando {e.seconds} segundos")
                    await asyncio.sleep(e.seconds)
    except Exception as e:
        print(f"Ha ocurrido un error en get_messages: {e}")
    return all_messages

async def main():
    # Cargar el último checkpoint o usar el valor por defecto
    datetime_before = load_checkpoint()
    print(f"Reanudando desde checkpoint: {datetime_before}")

    # Abrir (o crear) el archivo CSV en modo append
    file_exists = os.path.exists(csv_file_name)
    csv_file = open(csv_file_name, "a", newline="", encoding="utf-8-sig")
    writer = csv.DictWriter(csv_file, fieldnames=['id', 'date', 'message', 'image'], restval='')
    if not file_exists:
        writer.writeheader()

    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        for repeat_index in range(repeat_number):
            loop_number = 50  # Número de iteraciones internas en cada ciclo
            for iteration in range(loop_number):
                try:
                    messages = await get_messages(client, datetime_before)
                    if not messages:
                        print("No se encontraron más mensajes. Finalizando descarga.")
                        csv_file.close()
                        return

                    # Guardar inmediatamente los mensajes (y rutas de imágenes) en el CSV
                    writer.writerows(messages)
                    csv_file.flush()

                    # Actualizar checkpoint usando la fecha del último mensaje descargado
                    datetime_before = messages[-1]['date']
                    save_checkpoint(datetime_before)
                    print(f"Ciclo {repeat_index} - Iteración {iteration}: {len(messages)} mensajes guardados. Nuevo checkpoint: {datetime_before}")

                    # Actualizar timestamp_before para la siguiente iteración
                    await asyncio.sleep(1)
                except FloodWaitError as e:
                    print(f"FloodWaitError en iteración {iteration}: Esperando {e.seconds} segundos")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    print(f"Error en iteración {iteration}: {e}")

    csv_file.close()

if __name__ == "__main__":
    asyncio.run(main())