# bot.py
import os
import discord
import datetime
import os

with open("secret.txt", "r", encoding='utf-8') as f:
    TOKEN = f.readlines()[0].strip()

GUILD = 'test'
STATE_FILE = 'state.tsv'
WINDOW = (datetime.timedelta(hours=12), datetime.timedelta(hours=21))


class BossNotFound(Exception):
    pass

class ToDInFuture(Exception):
    pass

client = discord.Client()

@client.event
async def on_ready():
    guild = discord.utils.find(lambda g: g.name == GUILD, client.guilds)
    print(guild)
    global state
    state = get_state()

def check(tod):
    start = tod + WINDOW[0]
    end = tod + WINDOW[1]
    now = datetime.datetime.now()
    if start <= now <= end:
        return "**On Window**"
    if now < start:
        delta = start - now
        h, m = delta.seconds // 3600, (delta.seconds // 60) % 60
        return "Window starts in {} hours and {} minutes".format(h, m)
    if now > end:
        return "Window ended {} ago, we probably didn't register the last ToD".format(now - end)
    

def get_supported_bosses():
    return list(state.keys())

def str2date(s, format='%Y-%m-%d %H:%M:%S'):
    print("converting", s)
    return datetime.datetime.strptime(s, format)

def get_state():
    with open(STATE_FILE, "r", encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]
        state = {line.split("\t")[0]: str2date(line.split("\t")[1]) for line in lines}
    return state

def troll(name):
    return "**The 9000 IQ supreme leader {} has spoken, all shall listen to his infinite wisdom.**".format(name)

def set_state(state):
    os.remove(STATE_FILE)
    with open(STATE_FILE, "w", encoding='utf-8') as f:
        for k, v in state.items():
            print(v)
            f.write("{}\t{}\n".format(k, v))


def register(name, time, date=None):
    if name not in state and not force:
        raise BossNotFound()
        
    # Update the state
    now = datetime.datetime.now()
    try:
        if date is None:
            full_date = False
            hour, minute = time.split(":")
            hour, minute = int(hour), int(minute)
            tod = datetime.datetime(year=now.year, month=now.month, day=now.day, hour=hour, minute=minute)
        else:
            tod = str2date(date + " " + time)
    except ValueError:
        examples = [
            "\t1. Only current hour:minute in which case I assume it died at that time today. E.g. '!register Golgoda 13:05'",
            "\t2. Full datetime in this format: 'YYYY-mm-dd hh:mm'. For example '2022-02-16 13:01'"
        ]
        msg = "Time format is wrong"
        msg = msg + "\n" + examples[0] + "\n" + examples[1]
        raise ValueError(msg)
    if tod > now:
        raise ToDInFuture()
    
    state[name] = tod
    set_state(state)

@client.event
async def on_message(message):
    if message.author == client.user or not message.content.startswith("!"):
        return
    if str(message.channel) != "bots":
        return

    if message.content == '!check':
        response = "I was called"
        for name in get_supported_bosses():
            tod = state[name]
            status = check(tod)
            await message.channel.send("{}: {}".format(name, status))
     
    elif message.content == "!sb":
        await message.channel.send(get_supported_bosses())

    elif message.content.startswith("!register"):
       parts = message.content.split()
       try:
           if len(parts) == 3:
               name, time = parts[1], parts[2]
               register(name, time, date=None)
               await message.channel.send("You entered only time, not date. I am assuming date is today.")
           elif len(parts) == 4:
               name, date, time = parts[1], parts[2], parts[3]
               register(name, time, date=date)

       except BossNotFound:
           await message.channel.send("Boss {} unknown, use !sb to check which bosses are currently supported".format(name))
           await message.channel.send("If you wish to register a new boss, repeat the same command but using !fregister instead of !register")
       except ToDInFuture:
           msg = "ToD cannot lie in the future silly. Are you sure you are using CET timezone?"
           await message.channel.send(msg)
       except ValueError as e:
           await message.channel.send(str(e))

client.run(TOKEN)