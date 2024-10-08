from telethon import events, functions, types
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors import RPCError
from .utils import restricted_to_authorized
import asyncio
from datetime import datetime, timedelta
import pytz

# Mendapatkan zona waktu Jakarta
jakarta_tz = pytz.timezone('Asia/Jakarta')

async def invite_members(client, target_group_id, source_group_id, limit):
    try:
        # Mendapatkan anggota dari grup sumber
        members = await client.get_participants(source_group_id, limit=limit)
        members_to_invite = [member.id for member in members if not member.bot]

        if len(members_to_invite) == 0:
            print("Tidak ada anggota yang ditemukan untuk diundang.")
            return

        # Mendapatkan anggota yang sudah ada di grup target
        existing_members = await client.get_participants(target_group_id)
        existing_member_ids = [member.id for member in existing_members]

        for i in range(0, len(members_to_invite), 1):  # Mengundang satu per satu
            if members_to_invite[i] not in existing_member_ids:
                try:
                    await client(InviteToChannelRequest(target_group_id, [members_to_invite[i]]))
                    print(f"✅ Berhasil mengundang anggota dengan ID {members_to_invite[i]}.")
                except RPCError as e:
                    print(f"❌ Terjadi kesalahan saat mengundang anggota dengan ID {members_to_invite[i]}: {str(e)}")
            else:
                print(f"🔍 Anggota dengan ID {members_to_invite[i]} sudah berada di grup target.")

            if i < len(members_to_invite) - 1:
                # Hitung waktu undangan berikutnya dalam zona waktu Jakarta
                next_invite_time = datetime.now(jakarta_tz) + timedelta(seconds=15)
                next_invite_time_str = next_invite_time.strftime("%H:%M:%S")
                
                print(f"⏳ Menunggu 15 Detik sebelum mengundang anggota berikutnya... (perkiraan waktu undangan berikutnya: {next_invite_time_str})")
                await asyncio.sleep(15)  # Delay 15 detik

    except RPCError as e:
        print(f"Terjadi kesalahan: {str(e)}")

def load(client):
    @client.on(events.NewMessage(pattern=r'\.culik (\d+) (\d+) (\d+)'))
    @restricted_to_authorized
    async def invite(event):
        if not event.is_group:
            await event.reply("❌ Perintah ini hanya dapat digunakan di grup.")
            return

        try:
            # Parse the command arguments
            args = event.pattern_match.groups()
            limit = int(args[0])
            source_group_id = int(args[1])
            target_group_id = int(args[2])
            
            # Informasikan pengguna tentang proses dan delay
            await event.reply(
                f"🔄 Mulai mengundang hingga {limit} \n anggota dari grup {source_group_id} \n ke grup {target_group_id}.\n\n"
                f"Proses ini akan memakan waktu karena ada delay 15 detik antara setiap undangan.\n\n"
                f"Perkiraan waktu undangan berikutnya akan diumumkan setelah setiap undangan."
            )
            
            await invite_members(client, target_group_id, source_group_id, limit)
        except ValueError:
            await event.reply("⚠️ Argumen tidak valid. Gunakan `.culik <jumlah> <idgroup target> <idgroup kita>`.")
        except Exception as e:
            await event.reply(f"❌ Terjadi kesalahan: {str(e)}")

def add_commands(add_command):
    add_command('.culik', '🔗 Undang anggota dari satu grup ke grup lain dengan delay 15 detik antara setiap undangan. Anggota yang sudah ada di grup target tidak akan diundang.')
