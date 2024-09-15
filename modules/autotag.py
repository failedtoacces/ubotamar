from telethon import events
import json
import os
from .afk import check_afk_status
from .utils import restricted_to_authorized

TAG_MESSAGE_FILE = 'tag_message_{}.json'

def load_tag_message(user_id):
    file_name = TAG_MESSAGE_FILE.format(user_id)
    if os.path.exists(file_name):
        with open(file_name, 'r') as f:
            return json.load(f)
    return {}

def save_tag_message(user_id, tag_message):
    file_name = TAG_MESSAGE_FILE.format(user_id)
    with open(file_name, 'w') as f:
        json.dump(tag_message, f)

def load(client):
    @client.on(events.NewMessage(pattern=r'\.settag (.+)'))
    @restricted_to_authorized
    async def set_tag_message(event):
        message = event.pattern_match.group(1)
        user_id = str(event.sender_id)
        tag_message = load_tag_message(user_id)
        tag_message[user_id] = message
        save_tag_message(user_id, tag_message)
        await event.edit(f"Pesan tag otomatis telah diatur: {message}")

    @client.on(events.NewMessage(pattern=r'\.cleartag'))
    @restricted_to_authorized
    async def clear_tag_message(event):
        user_id = str(event.sender_id)
        tag_message = load_tag_message(user_id)
        if user_id in tag_message:
            del tag_message[user_id]
            save_tag_message(user_id, tag_message)
            await event.edit("Pesan tag otomatis telah dihapus.")
        else:
            await event.edit("Anda tidak memiliki pesan tag yang diatur.")

    @client.on(events.NewMessage(incoming=True))
    async def handle_tag(event):
        if event.mentioned:
            me = await event.client.get_me()
            is_afk, _ = check_afk_status(me.id)
            if not is_afk:
                user_id = str(me.id)
                tag_message = load_tag_message(user_id)
                if user_id in tag_message:
                    await event.reply(tag_message[user_id])

def add_commands(add_command):
    add_command('.settag <pesan>', 'Mengatur pesan otomatis saat di-tag')
    add_command('.cleartag', 'Menghapus pesan otomatis saat di-tag')