import os
import sys
import asyncio
import json
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from modules.utils import add_authorized_user

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Konfigurasi file
CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return []

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def add_user_to_config(api_id, api_hash, phone, string_session):
    configs = load_config()
    new_config = {
        "api_id": api_id,
        "api_hash": api_hash,
        "telepon": phone,
        "string_sesi": string_session
    }
    configs.append(new_config)
    save_config(configs)
    logger.info(f"New user {phone} added to config.")

async def start_client(session, api_id, api_hash):
    client = TelegramClient(StringSession(session), api_id, api_hash)
    try:
        await client.start()
        return client
    except Exception as e:
        logger.error(f"Error starting client: {str(e)}")
        return None

async def setup_new_client():
    print("Tidak ada konfigurasi yang ditemukan. Mari setup akun baru.")
    api_id = input("Masukkan API ID: ")
    api_hash = input("Masukkan API Hash: ")
    phone = input("Masukkan nomor telepon (format: +62xxxxxxxxxx): ")

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start()

    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Masukkan kode OTP: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password 2FA diperlukan: '))

    string_session = client.session.save()
    add_user_to_config(api_id, api_hash, phone, string_session)
    logger.info("Akun baru berhasil ditambahkan.")
    return client

async def main():
    configs = load_config()
    clients = []

    if not configs:
        client = await setup_new_client()
        clients.append(client)
        add_authorized_user(await client.get_me())
    else:
        for config in configs:
            client = await start_client(config['string_sesi'], config['api_id'], config['api_hash'])
            if client:
                clients.append(client)
                add_authorized_user(await client.get_me())
                logger.info(f"Client for {config['telepon']} started successfully.")

    if clients:
        # Load modules for each client
        from modules import load_modules
        for client in clients:
            load_modules(client)
            logger.info(f"Modules loaded for client {(await client.get_me()).first_name}")

        logger.info(f"Userbot running for {len(clients)} account(s).")

        # Keep the script running
        await asyncio.gather(*(client.run_until_disconnected() for client in clients))
    else:
        logger.error("No clients could be started. Please check your configuration.")

async def start_new_client(api_id, api_hash, string_session):
    client = await start_client(string_session, api_id, api_hash)
    if client:
        from modules import load_modules
        load_modules(client)
        add_authorized_user(await client.get_me())
        logger.info(f"New client started and modules loaded.")
        await client.run_until_disconnected()

def exception_handler(loop, context):
    exception = context.get('exception')
    logger.error(f"Unhandled exception: {str(exception)}")
    logger.error(f"Exception details: {context}")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
