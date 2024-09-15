from telethon import events
from googletrans import Translator, LANGUAGES
import emoji
from .utils import restricted_to_authorized

translator = Translator()

def remove_emoji(text):
    return emoji.replace_emoji(text, replace='')

def load(client):
    @client.on(events.NewMessage(pattern=r'\.tr(?: |$)(.*)'))
    @restricted_to_authorized
    async def translate_handler(event):
        if event.is_reply:
            replied = await event.get_reply_message()
            text = replied.text
        else:
            text = event.pattern_match.group(1)
        
        if not text:
            await event.edit("🔍 Mohon berikan teks untuk diterjemahkan atau balas ke pesan yang ingin diterjemahkan.")
            return

        args = text.split(maxsplit=1)
        if len(args) == 2:
            dest_lang = args[0]
            text_to_translate = args[1]
        else:
            dest_lang = 'id'  
            text_to_translate = text

        try:
            detected = translator.detect(remove_emoji(text_to_translate))
            src_lang = detected.lang
          
            translation = translator.translate(text_to_translate, dest=dest_lang, src=src_lang)
            
            result = f"🔤 **Dari:** {LANGUAGES.get(src_lang, 'Unknown').title()} ({src_lang})\n"
            result += f"🔤 **Ke:** {LANGUAGES.get(dest_lang, 'Unknown').title()} ({dest_lang})\n\n"
            result += f"📝 **Teks Asli:**\n{text_to_translate}\n\n"
            result += f"🔄 **Terjemahan:**\n{translation.text}"
            
            await event.edit(result)
        except ValueError as e:
            if "invalid destination language" in str(e):
                await event.edit(f"❌ Kode bahasa '{dest_lang}' tidak valid. Gunakan kode bahasa yang benar (contoh: 'en' untuk Inggris, 'id' untuk Indonesia).")
            else:
                await event.edit(f"❌ Terjadi kesalahan: {str(e)}")
        except Exception as e:
            await event.edit(f"❌ Gagal menerjemahkan: {str(e)}")

    @client.on(events.NewMessage(pattern=r'\.lang(?: |$)(.*)'))
    @restricted_to_authorized
    async def language_list(event):
        search = event.pattern_match.group(1)
        if search:
            search = search.lower()
            langs = {code: name for code, name in LANGUAGES.items() if search in name.lower() or search in code.lower()}
        else:
            langs = LANGUAGES

        if not langs:
            await event.edit("❌ Tidak ada bahasa yang cocok dengan pencarian Anda.")
            return

        lang_list = "🌐 **Daftar Kode Bahasa:**\n\n"
        for code, name in sorted(langs.items(), key=lambda x: x[1]):
            lang_list += f"`{code}` - {name.title()}\n"

        if len(lang_list) > 4096:
            parts = [lang_list[i:i+4096] for i in range(0, len(lang_list), 4096)]
            for part in parts:
                await event.reply(part)
        else:
            await event.edit(lang_list)

def add_commands(add_command):
    add_command('.tr [kode_bahasa] <teks>', '🔄 Menerjemahkan teks ke bahasa yang ditentukan (default: id)')
    add_command('.lang [pencarian]', '🌐 Menampilkan daftar kode bahasa yang tersedia')