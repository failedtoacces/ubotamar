from telethon import events, types
import time
import random
from .utils import restricted_to_authorized
import json
import os
import asyncio

AFK_FILE = 'afk_status_{}.json'

afk_responses = [
    "Halo! {name} lagi AFK nih. {reason}",
    "Yah, {name} lagi nggak ada. {reason}",
    "Sst, {name} lagi sibuk. {reason}",
    "Waduh, {name} lagi off dulu. {reason}",
    "Sorry ya, {name} lagi AFK. {reason}"
]

default_reasons = [
    "Mungkin lagi bobo cantik kali ya?",
    "Kayaknya sih lagi nonton Netflix.",
    "Bisa jadi lagi makan deh.",
    "Mungkin lagi main game kali ya?",
    "Sepertinya lagi asik sendiri nih."
]

def format_time(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours} jam {minutes} menit"
    elif minutes > 0:
        return f"{minutes} menit"
    else:
        return f"{seconds} detik"

def load_afk_status(user_id):
    file_name = AFK_FILE.format(user_id)
    if os.path.exists(file_name):
        with open(file_name, 'r') as f:
            return json.load(f)
    return None

def save_afk_status(user_id, status):
    file_name = AFK_FILE.format(user_id)
    with open(file_name, 'w') as f:
        json.dump(status, f)

def remove_afk_status(user_id):
    file_name = AFK_FILE.format(user_id)
    if os.path.exists(file_name):
        os.remove(file_name)

def check_afk_status(user_id):
    status = load_afk_status(user_id)
    if status:
        return True, status
    return False, None

def load(client):
    @client.on(events.NewMessage(pattern=r'(?i)^\.afk(?: (.*))?'))
    @restricted_to_authorized
    async def afk_handler(event):
        reason = event.pattern_match.group(1)
        user = await event.get_sender()
        user_id = user.id
        first_name = user.first_name if user.first_name else "Kamu"
        
        afk_status = {
            'time': time.time(),
            'reason': reason if reason else random.choice(default_reasons),
            'name': first_name
        }
        save_afk_status(user_id, afk_status)
        
        if reason:
            await event.edit(f"Oke deh, {first_name} AFK ya. Kalo ada yang nyariin, aku bilang: {reason}")
        else:
            await event.edit(f"Siap, {first_name} AFK mode: ON! 😎")

        # Penundaan agar perintah .afk tidak langsung dianggap sebagai aktivitas
        await asyncio.sleep(1)

    @client.on(events.NewMessage)
    async def afk_responder(event):
        sender = await event.get_sender()
        is_afk = False
        afk_status = None

        if sender:
            is_afk, afk_status = check_afk_status(sender.id)
            if is_afk:
                # Abaikan jika pesan adalah .afk
                if event.text and event.text.lower().startswith('.afk'):
                    return
                
                afk_time = time.time() - afk_status['time']
                time_str = format_time(afk_time)
                reason = afk_status['reason']
                name = afk_status['name']
                
                response = random.choice(afk_responses).format(name=name, reason=reason)
                response += f"\nUdah AFK {time_str} nih."
                
                await event.reply(response)

                # Hapus status AFK jika pengguna mengirim pesan selain .afk
                remove_afk_status(sender.id)
                
                messages = [
                    f"Halo semuanya! {name} balik lagi nih setelah AFK {time_str}! 🎉",
                    f"Guess who's back? {name} udah nggak AFK lagi setelah {time_str}! 😄",
                    f"Yuhuu, {name} udah online lagi nih. AFK {time_str} terasa cepet ya!",
                    f"Selamat datang kembali, {name}! Abis AFK {time_str}, pasti kangen sama chat ya? 😉"
                ]
                
                await event.respond(random.choice(messages))

def add_commands(add_command):
    add_command('.afk [alasan]', 'Ngasih tau yang lain kalo kamu lagi AFK')
