from telethon import events, functions, types
import json
import os
import asyncio  # Untuk menambahkan delay
from telethon.errors import RPCError
from .utils import restricted_to_authorized

# Lokasi file untuk menyimpan blacklist
BLACKLIST_FILE = 'blacklist.json'

# Muat daftar blacklist group
def load_blacklist():
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, 'w') as f:
        json.dump(list(blacklist), f, indent=2)

def load(client):
    blacklist = load_blacklist()

    @client.on(events.NewMessage(pattern=r'\.addbl'))
    @restricted_to_authorized
    async def add_blacklist(event):
        if event.is_group:
            group_id = event.chat_id
            if group_id in blacklist:
                await event.edit(f"⚠️ Grup ini sudah ada di blacklist.")
            else:
                blacklist.add(group_id)
                save_blacklist(blacklist)
                await event.edit(f"✅ Grup ini telah ditambahkan ke blacklist.")
        else:
            await event.edit("❌ Perintah ini hanya bisa digunakan di grup.")

    @client.on(events.NewMessage(pattern=r'\.rmbl'))
    @restricted_to_authorized
    async def remove_blacklist(event):
        if event.is_group:
            group_id = event.chat_id
            if group_id not in blacklist:
                await event.edit(f"⚠️ Grup ini tidak ada di blacklist.")
            else:
                blacklist.remove(group_id)
                save_blacklist(blacklist)
                await event.edit(f"✅ Grup ini telah dihapus dari blacklist.")
        else:
            await event.edit("❌ Perintah ini hanya bisa digunakan di grup.")

    @client.on(events.NewMessage(pattern=r'\.gc(?: (.+))?'))
    @restricted_to_authorized
    async def broadcast_message(event):
        message = event.pattern_match.group(1)
        if message is None and event.is_reply:
            message = (await event.get_reply_message()).text

        if message is None:
            await event.edit("❌ Harap berikan pesan atau balas pesan untuk broadcast.")
            return

        dialogs = await client.get_dialogs()
        success_count = 0
        fail_count = 0
        total_groups = len([d for d in dialogs if d.is_group and d.id not in blacklist])

        # Mulai broadcast
        progress_message = await event.reply(f"📢 Memulai broadcast ke {total_groups} grup...")

        for idx, dialog in enumerate(dialogs):
            if dialog.is_group and dialog.id not in blacklist:
                try:
                    await client.send_message(dialog.id, message)
                    success_count += 1
                except RPCError:
                    fail_count += 1

                # Tambahkan delay 0,5 detik
                await asyncio.sleep(0.5)

            # Update status setiap 5 grup
            if (idx + 1) % 5 == 0:
                await progress_message.edit(
                    f"📢 Broadcast sedang berlangsung...\n"
                    f"✅ Berhasil: {success_count}\n"
                    f"❌ Gagal: {fail_count}\n"
                    f"🔄 Grup tersisa: {total_groups - (success_count + fail_count)}"
                )

        # Kirim laporan ke Pesan Tersimpan
        saved_messages_id = '777000'
        report_message = (
            f"📢 **Laporan Broadcast**\n\n"
            f"✅ Berhasil dikirim ke {success_count} grup.\n"
            f"❌ Gagal dikirim ke {fail_count} grup."
        )
        await client.send_message(saved_messages_id, report_message)

        await progress_message.edit(f"✅ Broadcast selesai!\n"
                                    f"Berhasil: {success_count} grup.\n"
                                    f"Gagal: {fail_count} grup.\n"
                                    f"📄 Laporan dikirim ke Pesan Tersimpan.")

def add_commands(add_command):
    add_command('.addbl', '🛑 Menambahkan grup ini ke blacklist')
    add_command('.rmbl', '🗑️ Menghapus grup ini dari blacklist')
    add_command('.gc <pesan> atau reply pesan', '📢 Mengirimkan pesan broadcast ke semua grup kecuali yang ada di blacklist')
