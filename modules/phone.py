from telethon import events, functions, types
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors import RPCError
from .utils import restricted_to_authorized

def load(client):
    @client.on(events.NewMessage(pattern=r'\.hp'))
    @restricted_to_authorized
    async def get_phone_number(event):
        try:
            # Mengecek apakah pesan tersebut adalah balasan
            if event.is_reply:
                replied_msg = await event.get_reply_message()
                user_id = replied_msg.sender_id
                user = await client.get_entity(user_id)
            else:
                await event.edit("❌ Harap balas ke pesan pengguna untuk mendapatkan nomor telepon.")
                return

            # Mengambil informasi lengkap pengguna
            full_user = await client(GetFullUserRequest(user.id))
            phone_number = full_user.user.phone if full_user.user.phone else "Nomor telepon tidak tersedia"

            # Menampilkan nomor telepon
            await event.edit(f"📞 Nomor Telepon Pengguna: `{phone_number}`")
        except RPCError as e:
            await event.edit(f"❌ Tidak dapat mengambil informasi pengguna: {str(e)}")
        except Exception as e:
            await event.edit(f"❌ Terjadi kesalahan: {str(e)}")

def add_commands(add_command):
    add_command('.hp', '📞 Menampilkan nomor telepon pengguna berdasarkan ID')
