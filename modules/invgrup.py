from telethon import events, errors
from telethon.tl.functions.channels import EditTitleRequest, EditPhotoRequest
from telethon.tl.functions.messages import EditChatTitleRequest
from telethon.tl.types import InputChatUploadedPhoto, ChatPhotoEmpty
from .utils import restricted_to_authorized
import io

def load(client):
    @client.on(events.NewMessage(pattern=r'\.setgpic'))
    @restricted_to_authorized
    async def set_group_pic(event):
        if event.is_reply:
            replied_message = await event.get_reply_message()
            try:
                if replied_message.photo:
                    photo = await client.download_media(replied_message.photo)
                    await client(EditPhotoRequest(
                        event.chat_id,
                        InputChatUploadedPhoto(await client.upload_file(photo))
                    ))
                    await event.reply("✅ Foto grup berhasil diubah.")
                else:
                    await event.reply("❌ Silakan balas ke sebuah foto.")
            except Exception as e:
                await event.reply(f"❌ Terjadi kesalahan: {str(e)}")
        else:
            await event.reply("❌ Silakan balas ke sebuah foto.")

    @client.on(events.NewMessage(pattern=r'\.setgtitle (.+)'))
    @restricted_to_authorized
    async def set_group_title(event):
        new_title = event.pattern_match.group(1)
        try:
            if event.is_group:
                await client(EditTitleRequest(event.chat_id, new_title))
            else:
                await client(EditChatTitleRequest(event.chat_id, new_title))
            await event.reply(f"✅ Judul grup berhasil diubah menjadi: {new_title}")
        except Exception as e:
            await event.reply(f"❌ Terjadi kesalahan: {str(e)}")

    @client.on(events.NewMessage(pattern=r'\.setgdesc (.+)'))
    @restricted_to_authorized
    async def set_group_desc(event):
        new_desc = event.pattern_match.group(1)
        try:
            await client.edit_message(event.chat_id, message=new_desc, edit_hide=True)
            await event.reply(f"✅ Deskripsi grup berhasil diubah.")
        except Exception as e:
            await event.reply(f"❌ Terjadi kesalahan: {str(e)}")

    @client.on(events.NewMessage(pattern=r'\.addgemoji (.+)'))
    @restricted_to_authorized
    async def add_group_emoji(event):
        emoji = event.pattern_match.group(1)
        try:
            group = await event.get_chat()
            if not group.title:
                await event.reply("❌ Grup ini tidak memiliki judul.")
                return
            new_title = f"{emoji} {group.title}"
            if event.is_group:
                await client(EditTitleRequest(event.chat_id, new_title))
            else:
                await client(EditChatTitleRequest(event.chat_id, new_title))
            await event.reply(f"✅ Emoji {emoji} berhasil ditambahkan ke judul grup.")
        except Exception as e:
            await event.reply(f"❌ Terjadi kesalahan: {str(e)}")

    @client.on(events.NewMessage(pattern=r'\.gpinfo'))
    @restricted_to_authorized
    async def group_info(event):
        try:
            group = await event.get_chat()
            if not group.username:
                username = "Tidak ada"
            else:
                username = f"@{group.username}"
            info = f"ℹ️ Informasi Grup:\n\n"
            info += f"🆔 ID: `{group.id}`\n"
            info += f"📝 Judul: `{group.title}`\n"
            info += f"🔗 Username: {username}\n"
            if hasattr(group, 'participants_count'):
                info += f"👥 Jumlah Anggota: {group.participants_count}\n"
            if hasattr(group, 'about'):
                info += f"ℹ️ Deskripsi: {group.about}\n"
            await event.reply(info)
        except Exception as e:
            await event.reply(f"❌ Terjadi kesalahan: {str(e)}")

def add_commands(add_command):
    add_command('.setgpic', 'Mengubah foto profil grup (balas ke sebuah foto)')
    add_command('.setgtitle [judul baru]', 'Mengubah judul grup')
    add_command('.setgdesc [deskripsi baru]', 'Mengubah deskripsi grup')
    add_command('.addgemoji [emoji]', 'Menambahkan emoji ke judul grup')
    add_command('.gpinfo', 'Menampilkan informasi tentang grup')