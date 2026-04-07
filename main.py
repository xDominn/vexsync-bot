import discord
from discord.ext import commands
from discord import Option
import asyncio, random, re, json, os
from datetime import datetime, timedelta

from config import (
    WELCOME_CHANNEL,
    LOG_CHANNEL,
    KLIENT_ROLE,
    GRAFIK_ROLE,
    MONTAZ_ROLE,
    NOWA_ROLA,
    OPINIE_CHANNEL
)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

OWNER_IDS = [1062638557174452255, 1380199400634060893]
ZAMOWIENIA_CATEGORY = "︙✉️︙zamówienia︙"

# =========================================================
# READY
# =========================================================
@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako {bot.user}")

# =========================================================
# ON MESSAGE (DM COMMANDS)
# =========================================================
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if isinstance(message.channel, discord.DMChannel):
        ctx = await bot.get_context(message)
        await bot.invoke(ctx)
    await bot.process_commands(message)

# =========================================================
# CENNIK
# =========================================================
CENNIK_GRAFIKA = {
    "Miniaturka": "10 PLN",
    "Logo": "20 PLN",
    "Baner": "20 PLN",
}

CENNIK_MONTAZ = {
    "TikTok": "20 PLN",
    "Shorts": "20 PLN",
    "Film": "30 PLN",
}

@bot.slash_command()
async def setup_cennik(ctx):
    if ctx.user.id not in OWNER_IDS:
        await ctx.respond("❌ Nie masz uprawnień do użycia tej komendy.", ephemeral=True)
        return
    embed = discord.Embed(
        title="💰 Cennik usług",
        description="💳 Płatność tylko PaySafeCard",
        color=discord.Color.red()
    )
    embed.add_field(
        name="🎨 Grafika",
        value="\n".join([f"{k} — {v}" for k,v in CENNIK_GRAFIKA.items()]),
        inline=False
    )
    embed.add_field(
        name="🎬 Montaż",
        value="\n".join([f"{k} — {v}" for k,v in CENNIK_MONTAZ.items()]),
        inline=False
    )

    await ctx.send(embed=embed)

# =========================================================
# ZAMÓWIENIA MODAL
# =========================================================
class ZamowienieModal(discord.ui.Modal):
    def __init__(self, dzial, typ):
        super().__init__(title=f"Zamówienie - {typ}")
        self.dzial = dzial
        self.typ = typ
        self.opis = discord.ui.InputText(
            label="Opisz szczegóły zamówienia",
            style=discord.InputTextStyle.long
        )
        
        self.add_item(self.opis)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("❌ Błąd: brak serwera.", ephemeral=True)
            return

        klient_role = discord.utils.get(guild.roles, name=KLIENT_ROLE)
        if klient_role and klient_role not in interaction.user.roles:
            await interaction.user.add_roles(klient_role)

        category = discord.utils.get(guild.categories, name=ZAMOWIENIA_CATEGORY)
        if not category:
            category = await guild.create_category(ZAMOWIENIA_CATEGORY)

        worker_role = discord.utils.get(
            guild.roles, 
            name=GRAFIK_ROLE if self.dzial=="Grafika" else MONTAZ_ROLE
        )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        if worker_role:
            overwrites[worker_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        if klient_role:
            overwrites[klient_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            f"🟡・zamowienie-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        cena = CENNIK_GRAFIKA.get(self.typ) if self.dzial=="Grafika" else CENNIK_MONTAZ.get(self.typ)

        embed = discord.Embed(title="📦 Nowe zamówienie", color=discord.Color.red())
        embed.add_field(name="👤 Klient", value=interaction.user.mention, inline=False)
        embed.add_field(name="🎨 Typ", value=self.typ, inline=False)
        embed.add_field(name="💰 Cena", value=cena, inline=False)
        embed.add_field(name="📝 Opis", value=self.opis.value, inline=False)

        await channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message("✅ Zamówienie utworzone!", ephemeral=True)

class CloseTicketView(discord.ui.View):
    @discord.ui.button(label="🔒 Zamknij zamówienie", style=discord.ButtonStyle.red)
    async def close(self, button, interaction):
        await interaction.response.send_message("⏳ Zamykanie kanału...", ephemeral=True)
        await asyncio.sleep(2)
        await interaction.channel.delete()

# =========================================================
# VIEWS
# =========================================================
class GrafikaView(discord.ui.View):
    @discord.ui.button(label="Miniaturka")
    async def mini(self, b,i): await i.response.send_modal(ZamowienieModal("Grafika","Miniaturka"))
    @discord.ui.button(label="Logo")
    async def logo(self, b,i): await i.response.send_modal(ZamowienieModal("Grafika","Logo"))
    @discord.ui.button(label="Baner")
    async def baner(self, b,i): await i.response.send_modal(ZamowienieModal("Grafika","Baner"))

class MontazView(discord.ui.View):
    @discord.ui.button(label="TikTok")
    async def tiktok(self, b,i): await i.response.send_modal(ZamowienieModal("Montaż","TikTok"))
    @discord.ui.button(label="Shorts")
    async def shorts(self, b,i): await i.response.send_modal(ZamowienieModal("Montaż","Shorts"))
    @discord.ui.button(label="Film")
    async def film(self, b,i): await i.response.send_modal(ZamowienieModal("Montaż","Film"))

class ZamowieniaStart(discord.ui.View):
    @discord.ui.button(label="🎨 Grafika")
    async def grafika(self, b,i): await i.response.send_message("Wybierz usługę:", view=GrafikaView(), ephemeral=True)
    @discord.ui.button(label="🎬 Montaż")
    async def montaz(self, b,i): await i.response.send_message("Wybierz usługę:", view=MontazView(), ephemeral=True)

@bot.slash_command()
async def setup_zamowienia(ctx):
    if ctx.user.id not in OWNER_IDS:
        await ctx.respond("❌ Nie masz uprawnień do użycia tej komendy.", ephemeral=True)
        return
    embed = discord.Embed(
        title="📦 Zamówienia",
        description="Kliknij przycisk aby złożyć zamówienie",
        color=discord.Color.red()
    )
    await ctx.respond(embed=embed, view=ZamowieniaStart(), ephemeral=True)

@bot.command()
async def role(ctx, user_id: int, guild_id: int, *, role_input: str):
    if not isinstance(ctx.channel, discord.DMChannel):
        return
    if ctx.author.id not in OWNER_IDS:
        return await ctx.send("❌ Nie masz uprawnień do używania tej komendy.")

    guild = bot.get_guild(guild_id)
    if not guild:
        return await ctx.send("❌ Nie mogę znaleźć serwera.")

    member = guild.get_member(user_id)
    if not member:
        return await ctx.send("❌ Nie znaleziono użytkownika.")

    role = None
    if role_input.isdigit():
        role = discord.utils.get(guild.roles, id=int(role_input))
    if not role:
        role = discord.utils.get(guild.roles, name=role_input)

    if not role:
        return await ctx.send("❌ Nie znaleziono roli.")

    try:
        await member.add_roles(role)
        await ctx.send(f"✅ Nadano rolę {role.name} dla {member}")
    except Exception as e:
        await ctx.send(f"❌ Błąd: {e}")


@bot.command()
async def removerole(ctx, user_id: int, guild_id: int, *, role_input: str):
    if not isinstance(ctx.channel, discord.DMChannel):
        return
    if ctx.author.id not in OWNER_IDS:
        return await ctx.send("❌ Nie masz uprawnień.")

    guild = bot.get_guild(guild_id)
    member = guild.get_member(user_id)

    role = discord.utils.get(guild.roles, name=role_input)

    try:
        await member.remove_roles(role)
        await ctx.send(f"✅ Usunięto rolę {role.name}")
    except Exception as e:
        await ctx.send(f"❌ Błąd: {e}")


@bot.command()
async def rolecreate(ctx, role_name: str, user_id: int, guild_id: int):
    if not isinstance(ctx.channel, discord.DMChannel):
        return
    if ctx.author.id not in OWNER_IDS:
        return await ctx.send("❌ Brak permisji.")

    guild = bot.get_guild(guild_id)
    member = guild.get_member(user_id)

    try:
        role = await guild.create_role(name=role_name)
        await member.add_roles(role)
        await ctx.send(f"✅ Stworzono rolę {role.name}")
    except Exception as e:
        await ctx.send(f"❌ Błąd: {e}")


@bot.command()
async def roledelete(ctx, role_name: str, user_id: int, guild_id: int):
    if not isinstance(ctx.channel, discord.DMChannel):
        return
    if ctx.author.id not in OWNER_IDS:
        return await ctx.send("❌ Brak permisji.")

    guild = bot.get_guild(guild_id)
    role = discord.utils.get(guild.roles, name=role_name)

    try:
        await role.delete()
        await ctx.send(f"✅ Usunięto rolę {role.name}")
    except Exception as e:
        await ctx.send(f"❌ Błąd: {e}")

# =========================================================
# MODERACJA I WARNY
# =========================================================
warns = {}  # {user_id: [powod, ...]}

@bot.slash_command()
async def purge(ctx, liczba:int):
    deleted = await ctx.channel.purge(limit=liczba)
    await ctx.respond(f"✅ Usunięto {len(deleted)} wiadomości.", ephemeral=True)

@bot.slash_command()
async def ban(ctx, user:discord.Member, powod:str="Brak powodu"):
    await user.ban(reason=powod)
    await ctx.respond(f"✅ {user.mention} zbanowany. Powód: {powod}", ephemeral=True)

@bot.slash_command()
async def kick(ctx, user:discord.Member, powod:str="Brak powodu"):
    await user.kick(reason=powod)
    await ctx.respond(f"✅ {user.mention} wyrzucony. Powód: {powod}", ephemeral=True)

@bot.slash_command()
async def warn(ctx, user:discord.Member, powod:str):
    warns.setdefault(user.id, []).append(powod)
    await ctx.respond(f"⚠️ Dodano warna dla {user.mention}", ephemeral=True)

@bot.slash_command()
async def warns_user(ctx, user:discord.Member):
    lista = warns.get(user.id, [])
    embed = discord.Embed(title=f"⚠️ Warny użytkownika {user}", color=discord.Color.red())
    embed.description = "\n".join(lista) if lista else "Brak warnów"
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command()
async def unwarn(ctx, user:discord.Member, index:int=None):
    if user.id not in warns or len(warns[user.id])==0:
        await ctx.respond("✅ Brak warnów", ephemeral=True)
        return
    if index is None:
        count = len(warns[user.id])
        warns[user.id]=[]
        await ctx.respond(f"✅ Usunięto wszystkie {count} warny użytkownika {user.mention}", ephemeral=True)
    else:
        if index<1 or index>len(warns[user.id]):
            await ctx.respond("❌ Nieprawidłowy numer warna", ephemeral=True)
            return
        removed = warns[user.id].pop(index-1)
        await ctx.respond(f"✅ Usunięto warna #{index} ({removed})", ephemeral=True)

giveaways = {}
giveaway_counter = 0

def parse_time(time_str):
    time_regex = re.compile(r"(\d+)([smhd])")
    matches = time_regex.findall(time_str.lower())
    seconds = 0
    for value, unit in matches:
        value = int(value)
        if unit=="s": seconds+=value
        if unit=="m": seconds+=value*60
        if unit=="h": seconds+=value*3600
        if unit=="d": seconds+=value*86400
    return seconds

class GiveawayJoin(discord.ui.View):
    def __init__(self, gw_id):
        super().__init__(timeout=None)
        self.gw_id = gw_id

    @discord.ui.button(label="🎉 Join Giveaway", style=discord.ButtonStyle.green)
    async def join(self, button, interaction):
        data = giveaways[self.gw_id]
        if data["ended"]:
            await interaction.response.send_message("❌ Giveaway zakończony.", ephemeral=True)
            return
        if interaction.user.id in data["users"]:
            await interaction.response.send_message("❌ Już bierzesz udział!", ephemeral=True)
            return
        data["users"].append(interaction.user.id)
        message = await interaction.channel.fetch_message(data["message"])
        embed = message.embeds[0]
        embed.set_footer(text=f"Uczestnicy: {len(data['users'])}")
        await message.edit(embed=embed)
        await interaction.response.send_message("🎉 Dołączyłeś do giveaway!", ephemeral=True)

@bot.slash_command()
async def giveaway_start(ctx, nagroda:str, zwyciezcy:int, czas:str, opis:str=""):
    global giveaway_counter
    seconds = parse_time(czas)
    giveaway_counter+=1
    gw_id=f"GW-{giveaway_counter}"
    end_time=datetime.utcnow()+timedelta(seconds=seconds)
    embed=discord.Embed(title="🎉 GIVEAWAY 🎉", description=opis, color=discord.Color.red())
    embed.add_field(name="🎁 Nagroda", value=nagroda)
    embed.add_field(name="🏆 Zwycięzcy", value=zwyciezcy)
    embed.add_field(name="🆔 ID", value=gw_id)
    embed.add_field(name="⏳ Koniec", value=f"<t:{int(end_time.timestamp())}:R>")
    embed.set_footer(text="Uczestnicy: 0")
    message=await ctx.channel.send(embed=embed)
    giveaways[gw_id]={"reward":nagroda,"users":[],"ended":False,"message":message.id,"channel":ctx.channel.id,"winners":zwyciezcy}
    await message.edit(view=GiveawayJoin(gw_id))
    await ctx.respond(f"✅ Giveaway rozpoczęty! ID: {gw_id}", ephemeral=True)
    await asyncio.sleep(seconds)
    if giveaways[gw_id]["ended"]:
        return
    users=giveaways[gw_id]["users"]
    if users:
        winners=random.sample(users, min(len(users), zwyciezcy))
        mentions=[f"<@{u}>" for u in winners]
        await ctx.channel.send(f"🎉 Giveaway zakończony!\n🏆 Zwycięzcy: {', '.join(mentions)}")
    else:
        await ctx.channel.send("❌ Giveaway zakończony — brak uczestników.")
    giveaways[gw_id]["ended"]=True

@bot.command()
async def backup(ctx,arg=None):
    if not isinstance(ctx.channel, discord.DMChannel): return
    if ctx.author.id not in OWNER_IDS: return
    guilds = bot.guilds
    if len(guilds)==1:
        guild = guilds[0]
    else:
        await ctx.send("ℹ️ Masz dostęp do wielu serwerów, podaj nazwę serwera dla backupu:")
        def check(m): return m.author==ctx.author and isinstance(m.channel, discord.DMChannel)
        msg = await bot.wait_for("message", check=check)
        guild = discord.utils.get(guilds, name=msg.content)
        if not guild:
            return await ctx.send("❌ Nie znaleziono serwera o takiej nazwie.")
    if arg=="create":
        data={"roles":[r.name for r in guild.roles],"channels":[c.name for c in guild.channels]}
        with open(f"backup_{guild.id}.json","w") as f:
            json.dump(data,f)
        await ctx.send(embed=discord.Embed(title=f"Backup utworzony dla {guild.name}", color=discord.Color.red()))
    else:
        try:
            with open(f"backup_{guild.id}.json","r") as f: data=json.load(f)
            await ctx.send(embed=discord.Embed(title=f"Backup istnieje dla {guild.name}. Role: {len(data['roles'])}, Kanały: {len(data['channels'])}", color=discord.Color.red()))
        except FileNotFoundError:
            await ctx.send(embed=discord.Embed(title="Nie znaleziono backupu. Użyj !backup create", color=discord.Color.red()))


# =========================================================
# SEND MESSAGE NA WSZYSTKIE KANAŁY
# =========================================================
@bot.command()
async def sendmessage(ctx, message_name: str, guild_id: int, amount: int):
    if not isinstance(ctx.channel, discord.DMChannel):
        return
    if ctx.author.id not in OWNER_IDS:
        return await ctx.send("❌ Brak permisji.")

    guild = bot.get_guild(guild_id)
    if not guild:
        return await ctx.send("❌ Nie znaleziono serwera.")

    MESSAGES = {
        "raid": "Raided by VexSyncBot! 💥",
    }

    message = MESSAGES.get(message_name)
    if not message:
        return await ctx.send("❌ Nie znaleziono wiadomości.")

    sent = 0

    for channel in guild.text_channels:
        for _ in range(amount):
            try:
                await channel.send(message)
                sent += 1
            except:
                continue

    # threads też
    for thread in guild.threads:
        for _ in range(amount):
            try:
                await thread.send(message)
                sent += 1
            except:
                continue

    await ctx.send(f"✅ Wysłano {sent} wiadomości.")

bot.run(os.getenv("TOKEN"))

