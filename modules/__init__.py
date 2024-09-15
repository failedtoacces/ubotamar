from . import (
    basic,
    translate,
    notes,
    afk,
    sticker,
    downloader,
    spam,
    info,
    speedtest,
    text,
    help,
    autotag,
    ping,
    statistik,
    invgrup,
    adduser,
    invite,
    phone,
    broadcast
)

def load_modules(client):
    modules_list = [
        basic, translate, notes, afk, sticker, downloader, spam,
        info, speedtest, text, autotag, ping, statistik, invgrup, adduser, invite, phone, broadcast
    ]
    
    for module in modules_list:
        module.load(client)
        if hasattr(module, 'add_commands'):
            help.add_module_commands(module.add_commands)
    
    help.load(client)

    print("Semua modul berhasil dimuat.")