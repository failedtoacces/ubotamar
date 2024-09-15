from telethon import events, TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from telethon.sessions import StringSession
import asyncio
from .utils import add_authorized_user, restricted_to_authorized

# Variabel global untuk menyimpan status proses
pending_requests = {}

async def tambah_pengguna(api_id, api_hash, telepon):
    try:
        client = TelegramClient(StringSession(), api_id, api_hash)
        await client.connect()

        if not await client.is_user_authorized():
            await client.send_code_request(telepon)
            return client, "OTP_NEEDED"

        string_sesi = StringSession.save(client.session)
        return client, string_sesi
    except Exception as e:
        return None, str(e)

async def verifikasi_otp(client, telepon, kode_otp):
    try:
        await client.sign_in(telepon, kode_otp)
        string_sesi = StringSession.save(client.session)
        return string_sesi, None
    except PhoneCodeInvalidError:
        return None, "Kode OTP tidak valid. Silakan coba lagi."
    except SessionPasswordNeededError:
        return "2FA_NEEDED", None
    except Exception as e:
        return None, str(e)

async def verifikasi_2fa(client, kata_sandi):
    try:
        await client.sign_in(password=kata_sandi)
        string_sesi = StringSession.save(client.session)
        return string_sesi, None
    except Exception as e:
        return None, str(e)

async def interactive_add_user(event, client):
    chat = event.chat_id
    sender = event.sender_id

    # Set status proses untuk membatalkan
    pending_requests[chat] = True

    async def get_reply(message):
        prompt = await client.send_message(chat, message)
        while pending_requests.get(chat, False):
            try:
                response = await client.get_messages(chat, limit=1)
                if response and response[0].sender_id == sender and response[0].id > prompt.id:
                    return response[0].text
            except Exception as e:
                print(f"Error in get_reply: {e}")
            await asyncio.sleep(1)
        return None

    try:
        await client.send_message(chat, "Proses penambahan akun baru dimulai. Silakan ikuti langkah-langkah berikut:")

        api_id = await get_reply("Balas pesan ini dengan API ID:")
        if api_id is None: return await client.send_message(chat, "Proses dibatalkan.")
        api_hash = await get_reply("Balas pesan ini dengan API Hash:")
        if api_hash is None: return await client.send_message(chat, "Proses dibatalkan.")
        telepon = await get_reply("Balas pesan ini dengan nomor telepon (format: +62xxxxxxxxxx):")
        if telepon is None: return await client.send_message(chat, "Proses dibatalkan.")

        await client.send_message(chat, "Memproses... Mengirim kode OTP.")
        new_client, result = await tambah_pengguna(api_id, api_hash, telepon)

        if result == "OTP_NEEDED":
            otp = await get_reply("Balas pesan ini dengan kode OTP yang telah dikirim ke nomor Anda:")
            if otp is None: return await client.send_message(chat, "Proses dibatalkan.")

            string_sesi, error = await verifikasi_otp(new_client, telepon, otp)
            if error:
                await client.send_message(chat, f"Error: {error}")
                return
            elif string_sesi == "2FA_NEEDED":
                pwd = await get_reply("Akun ini menggunakan 2FA. Balas pesan ini dengan kata sandi 2FA:")
                if pwd is None: return await client.send_message(chat, "Proses dibatalkan.")

                string_sesi, error = await verifikasi_2fa(new_client, pwd)
                if error:
                    await client.send_message(chat, f"Error: {error}")
                    return
        elif isinstance(result, str) and result.startswith("Error"):
            await client.send_message(chat, f"Terjadi kesalahan: {result}")
            return
        else:
            string_sesi = result

        # Tambahkan user baru ke konfigurasi
        add_user_to_config(api_id, api_hash, telepon, string_sesi)

        # Tambahkan user baru ke daftar user yang diotorisasi
        me = await new_client.get_me()
        add_authorized_user(me)

        # Mulai client baru untuk user yang baru ditambahkan
        asyncio.create_task(start_new_client(api_id, api_hash, string_sesi))

        await client.send_message(chat, "Akun baru berhasil ditambahkan dan diaktifkan! Anda sekarang dapat menggunakan semua perintah modul.")
    except Exception as e:
        await client.send_message(chat, f"Terjadi kesalahan: {str(e)}")
        print(f"Error in interactive_add_user: {e}")
    finally:
        # Hapus status proses
        pending_requests.pop(chat, None)

async def cancel_process(event, client):
    chat = event.chat_id
    if chat in pending_requests:
        pending_requests[chat] = False
        await client.send_message(chat, "Proses penambahan akun dibatalkan.")
    else:
        await client.send_message(chat, "Tidak ada proses penambahan akun yang sedang berlangsung.")

def load(client):
    global add_user_to_config, start_new_client
    from main import add_user_to_config, start_new_client

    @client.on(events.NewMessage(pattern=r'\.adduser'))
    @restricted_to_authorized
    async def handle_adduser(event):
        await interactive_add_user(event, client)

    @client.on(events.NewMessage(pattern=r'\.cancel'))
    @restricted_to_authorized
    async def handle_cancel(event):
        await cancel_process(event, client)

def add_commands(add_command):
    add_command('.adduser', 'Menambahkan akun Telegram baru ke userbot')
    add_command('.cancel', 'Membatalkan proses penambahan akun yang sedang berlangsung')
