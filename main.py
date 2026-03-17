import discord
from discord.ext import commands
from discord import Option
from datetime import timedelta
from config import (
    TOKEN,
    WELCOME_CHANNEL,
    LOG_CHANNEL,
    KLIENT_ROLE,
    GRAFIK_ROLE,
    MONTAZ_ROLE,
    NOWA_ROLA,
    OPINIE_CHANNEL
)

# ====== USTAWIENIA ======
intents = discord.Intents.all()
bot = commands.Bot(intents=intents)

ZAMOWIENIA_CATEGORY = "︙✉️︙zamówienia︙"
GUILD_ID = 1453411007010439168  # Twój serwer

# ====== CENNIK ======
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

# =========================================================
# BOT READY
# =========================================================
@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako {bot.user}")

# =========================================================
# POWITANIE
# =========================================================
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name=WELCOME_CHANNEL)
    if channel:
        embed = discord.Embed(
            title="👋 Witaj!",
            description=f"Witaj {member.mention} na **{member.guild.name}**!",
            color=discord.Color.red()
        )
        await channel.send(embed=embed)

    role = discord.utils.get(member.guild.roles, name=NOWA_ROLA)
    if role:
        await member.add_roles(role)

# =========================================================
# MODAL ZAMÓWIENIA
# =========================================================
class ZamowienieModal(discord.ui.Modal):
    def __init__(self, dzial, typ):
        super().__init__(title="Opis zamówienia")
        self.dzial = dzial
        self.typ = typ
        self.opis = discord.ui.InputText(
            label="Opisz szczegóły zamówienia",
            style=discord.InputTextStyle.long
        )
        self.add_item(self.opis)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild

        # nadaj rolę KLIENT
        klient_role = discord.utils.get(guild.roles, name=KLIENT_ROLE)
        if klient_role and klient_role not in interaction.user.roles:
            await interaction.user.add_roles(klient_role)

        # kategoria zamówień
        category = discord.utils.get(guild.categories, name=ZAMOWIENIA_CATEGORY)
        if not category:
            category = await guild.create_category(ZAMOWIENIA_CATEGORY)

        # role działu
        if self.dzial == "Grafika":
            cena = CENNIK_GRAFIKA[self.typ]
            worker_role = discord.utils.get(guild.roles, name=GRAFIK_ROLE)
        else:
            cena = CENNIK_MONTAZ[self.typ]
            worker_role = discord.utils.get(guild.roles, name=MONTAZ_ROLE)

        # uprawnienia kanału
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        if worker_role:
            overwrites[worker_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        if klient_role:
            overwrites[klient_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        # tworzenie kanału
        channel = await guild.create_text_channel(
            f"🟡・zamowienie-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        # embed zamówienia
        embed = discord.Embed(
            title="📦 Nowe zamówienie",
            color=discord.Color.red()
        )
        embed.add_field(name="Klient", value=interaction.user.mention, inline=False)
        embed.add_field(name="Dział", value=self.dzial, inline=False)
        embed.add_field(name="Typ", value=self.typ, inline=False)
        embed.add_field(name="Cena", value=cena, inline=False)
        embed.add_field(name="Opis", value=self.opis.value, inline=False)

        await channel.send(embed=embed, view=ZamowienieButtons())
        await interaction.response.send_message("✅ Zamówienie utworzone!", ephemeral=True)

# =========================================================
# PRZYCISKI ZAMÓWIENIA
# =========================================================
class ZamowienieButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🟢 Gotowe", style=discord.ButtonStyle.success)
    async def done(self, button, interaction):
        await interaction.channel.edit(name=f"🟢・{interaction.channel.name}")
        await interaction.response.send_message("✅ Oznaczono jako gotowe", ephemeral=True)

    @discord.ui.button(label="🔒 Zamknij", style=discord.ButtonStyle.danger)
    async def close(self, button, interaction):
        await interaction.channel.delete()

# =========================================================
# WYBÓR DZIAŁU
# =========================================================
class StartZamowienia(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎨 Grafika", style=discord.ButtonStyle.primary)
    async def grafika(self, button, interaction):
        await interaction.response.send_message("Wybierz typ grafiki:", view=GrafikaView(), ephemeral=True)

    @discord.ui.button(label="🎬 Montaż", style=discord.ButtonStyle.secondary)
    async def montaz(self, button, interaction):
        await interaction.response.send_message("Wybierz typ montażu:", view=MontazView(), ephemeral=True)

# =========================================================
# GRAFIKA VIEW
# =========================================================
class GrafikaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="Wybierz typ grafiki",
        options=[
            discord.SelectOption(label="Miniaturka"),
            discord.SelectOption(label="Logo"),
            discord.SelectOption(label="Baner"),
        ]
    )
    async def select(self, select, interaction):
        await interaction.response.send_modal(ZamowienieModal("Grafika", select.values[0]))

# =========================================================
# MONTAŻ VIEW
# =========================================================
class MontazView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="Wybierz typ montażu",
        options=[
            discord.SelectOption(label="TikTok"),
            discord.SelectOption(label="Shorts"),
            discord.SelectOption(label="Film"),
        ]
    )
    async def select(self, select, interaction):
        await interaction.response.send_modal(ZamowienieModal("Montaż", select.values[0]))

# =========================================================
# SETUP PANELU ZAMÓWIEŃ
# =========================================================
@bot.slash_command(guild_ids=[GUILD_ID], description="SETUP: panel zamówień")
@commands.has_permissions(administrator=True)
async def setup_zamowienia(ctx: discord.ApplicationContext):
    embed = discord.Embed(
        title="📦 Zamówienia",
        description="Kliknij przycisk aby złożyć zamówienie",
        color=discord.Color.red()
    )
    await ctx.channel.send(embed=embed, view=StartZamowienia())
    await ctx.respond("✅ Panel zamówień wysłany", ephemeral=True)

   # =========================================================
# SETUP CENNIK
# =========================================================
@bot.slash_command(guild_ids=[GUILD_ID], description="SETUP: cennik usług")
@commands.has_permissions(administrator=True)
async def setup_cennik(ctx: discord.ApplicationContext):

    embed = discord.Embed(
        title="💰 Cennik usług",
        color=discord.Color.red()
    )

    # Grafika
    grafika_text = ""
    for k, v in CENNIK_GRAFIKA.items():
        grafika_text += f"• {k} — {v}\n"

    # Montaż
    montaz_text = ""
    for k, v in CENNIK_MONTAZ.items():
        montaz_text += f"• {k} — {v}\n"

    embed.add_field(name="🎨 Grafika", value=grafika_text, inline=False)
    embed.add_field(name="🎬 Montaż", value=montaz_text, inline=False)

    await ctx.channel.send(embed=embed)
    await ctx.respond("✅ Cennik wysłany!", ephemeral=True)

# =========================================================
# PURGE
# =========================================================
@bot.slash_command(guild_ids=[GUILD_ID], description="🧹 Wyczyść wiadomości (max 100)")
@commands.has_permissions(manage_messages=True)
async def purge(ctx: discord.ApplicationContext, liczba: Option(int, "Ile wiadomości usunąć?", min_value=1, max_value=100)):
    await ctx.defer(ephemeral=True)
    deleted = await ctx.channel.purge(limit=liczba)
    await ctx.respond(f"✅ Usunięto {len(deleted)} wiadomości.", ephemeral=True)

# =========================================================
# MODERACJA
# =========================================================
@bot.slash_command(guild_ids=[GUILD_ID], description="Ban użytkownika")
@commands.has_permissions(ban_members=True)
async def ban(ctx: discord.ApplicationContext, user: Option(discord.Member, "Użytkownik do zbanowania"), reason: Option(str, "Powód", required=False)):
    await user.ban(reason=reason)
    await ctx.respond(f"✅ {user.mention} został zbanowany.\nPowód: {reason}", ephemeral=True)

@bot.slash_command(guild_ids=[GUILD_ID], description="Kick użytkownika")
@commands.has_permissions(kick_members=True)
async def kick(ctx: discord.ApplicationContext, user: Option(discord.Member, "Użytkownik do wyrzucenia"), reason: Option(str, "Powód", required=False)):
    await user.kick(reason=reason)
    await ctx.respond(f"✅ {user.mention} został wyrzucony.\nPowód: {reason}", ephemeral=True)

@bot.slash_command(guild_ids=[GUILD_ID], description="Unban użytkownika")
@commands.has_permissions(ban_members=True)
async def unban(ctx: discord.ApplicationContext, user_id: Option(int, "ID użytkownika")):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.respond(f"✅ {user.mention} został odbanowany.", ephemeral=True)

@bot.slash_command(guild_ids=[GUILD_ID], description="Mute (timeout) użytkownika w sekundach")
@commands.has_permissions(moderate_members=True)
async def mute(ctx: discord.ApplicationContext, user: Option(discord.Member, "Użytkownik do wyciszenia"), czas: Option(int, "Czas w sekundach", min_value=1, max_value=2419200)):
    await user.edit(timed_out_until=discord.utils.utcnow() + timedelta(seconds=czas))
    await ctx.respond(f"✅ {user.mention} wyciszony na {czas} sekund.", ephemeral=True)

# =========================================================
# SYSTEM WARNÓW
# =========================================================
warns = {}  # {user_id: [{"reason": "...", "moderator": "..."}]}

@bot.slash_command(guild_ids=[GUILD_ID], description="Ostrzeż użytkownika")
@commands.has_permissions(kick_members=True)
async def warn(ctx: discord.ApplicationContext, user: Option(discord.Member, "Użytkownik do ostrzeżenia"), reason: Option(str, "Powód", required=False)):
    reason_text = reason if reason else "Brak powodu"
    if user.id not in warns:
        warns[user.id] = []
    warns[user.id].append({"reason": reason_text, "moderator": ctx.user.name})

    # Log do LOG_CHANNEL
    log_channel = discord.utils.get(ctx.guild.text_channels, name=LOG_CHANNEL)
    if log_channel:
        embed = discord.Embed(title="⚠️ Ostrzeżenie", color=discord.Color.orange())
        embed.add_field(name="Użytkownik", value=user.mention, inline=False)
        embed.add_field(name="Ostrzegający", value=ctx.user.mention, inline=False)
        embed.add_field(name="Powód", value=reason_text, inline=False)
        await log_channel.send(embed=embed)

    await ctx.respond(f"⚠️ {user.mention} został ostrzeżony. Powód: {reason_text}", ephemeral=True)

@bot.slash_command(guild_ids=[GUILD_ID], description="Pokaż warny użytkownika")
@commands.has_permissions(administrator=True)
async def warns_user(ctx: discord.ApplicationContext, user: Option(discord.Member, "Użytkownik do sprawdzenia")):
    if user.id not in warns or len(warns[user.id]) == 0:
        await ctx.respond(f"✅ {user.mention} nie ma żadnych warnów.", ephemeral=True)
        return

    embed = discord.Embed(title=f"⚠️ Warny użytkownika {user.display_name}", color=discord.Color.orange())
    for i, w in enumerate(warns[user.id], start=1):
        embed.add_field(name=f"Warn #{i}", value=f"Powód: {w['reason']}\nModerator: {w['moderator']}", inline=False)

    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(guild_ids=[GUILD_ID], description="Usuń warn użytkownika")
@commands.has_permissions(kick_members=True)
async def unwarn(ctx: discord.ApplicationContext, user: Option(discord.Member, "Użytkownik, którego warny chcesz usunąć"), numer: Option(int, "Numer warna do usunięcia (opcjonalnie)", required=False)):
    if user.id not in warns or len(warns[user.id]) == 0:
        await ctx.respond(f"✅ {user.mention} nie ma żadnych warnów.", ephemeral=True)
        return

    if numer is None:
        count = len(warns[user.id])
        warns[user.id] = []
        await ctx.respond(f"✅ Usunięto wszystkie {count} warny użytkownika {user.mention}.", ephemeral=True)
    else:
        if numer < 1 or numer > len(warns[user.id]):
            await ctx.respond(f"❌ Nie ma warna o numerze {numer}.", ephemeral=True)
            return
        removed = warns[user.id].pop(numer - 1)
        await ctx.respond(f"✅ Usunięto warna #{numer} użytkownika {user.mention} (Powód: {removed['reason']}).", ephemeral=True)

import asyncio
import random
import re
from datetime import datetime, timedelta

giveaways = {}
giveaway_counter = 0


def parse_time(time_str):
    """
    Zamienia string typu '1h30m10s' na liczbę sekund.
    Obsługiwane jednostki: d, h, m, s
    """
    time_regex = re.compile(r"(\d+)([smhd])")
    matches = time_regex.findall(time_str.lower())

    if not matches:
        raise ValueError("Niepoprawny format czasu!")

    seconds = 0
    for value, unit in matches:
        value = int(value)
        if unit == "s":
            seconds += value
        elif unit == "m":
            seconds += value * 60
        elif unit == "h":
            seconds += value * 3600
        elif unit == "d":
            seconds += value * 86400

    return seconds


class GiveawayJoin(discord.ui.View):

    def __init__(self, gw_id):
        super().__init__(timeout=None)
        self.gw_id = gw_id

    @discord.ui.button(label="🎉 Join Giveaway", style=discord.ButtonStyle.green)
    async def join(self, button, interaction):

        data = giveaways[self.gw_id]

        if data["ended"]:
            await interaction.response.send_message(
                "❌ Giveaway zakończony.",
                ephemeral=True
            )
            return

        if interaction.user.id in data["users"]:
            await interaction.response.send_message(
                "❌ Już bierzesz udział!",
                ephemeral=True
            )
            return

        data["users"].append(interaction.user.id)

        message = await interaction.channel.fetch_message(data["message"])

        embed = message.embeds[0]
        embed.set_footer(text=f"Uczestnicy: {len(data['users'])}")

        await message.edit(embed=embed)

        await interaction.response.send_message(
            "🎉 Dołączyłeś do giveaway!",
            ephemeral=True
        )


@bot.slash_command(guild_ids=[GUILD_ID], description="Start giveaway")
@commands.has_permissions(manage_guild=True)
async def giveaway_start(
    ctx: discord.ApplicationContext,
    nagroda: Option(str, "Nagroda"),
    zwyciezcy: Option(int, "Ilu zwycięzców"),
    czas: Option(str, "Czas np 10m / 1h / 1h30m"),
    opis: Option(str, "Opis giveaway")
):

    global giveaway_counter

    seconds = parse_time(czas)
    giveaway_counter += 1

    gw_id = f"GW-{giveaway_counter}"

    end_time = datetime.utcnow() + timedelta(seconds=seconds)

    embed = discord.Embed(
        title="🎉 GIVEAWAY 🎉",
        description=opis,
        color=discord.Color.red()
    )

    embed.add_field(name="🎁 Nagroda", value=nagroda)
    embed.add_field(name="🏆 Zwycięzcy", value=zwyciezcy)
    embed.add_field(name="🆔 ID", value=gw_id)
    embed.add_field(name="⏳ Koniec", value=f"<t:{int(end_time.timestamp())}:R>")

    embed.set_footer(text="Uczestnicy: 0")

    message = await ctx.channel.send(embed=embed)

    giveaways[gw_id] = {
        "reward": nagroda,
        "users": [],
        "ended": False,
        "message": message.id,
        "channel": ctx.channel.id,
        "winners": zwyciezcy
    }

    await message.edit(view=GiveawayJoin(gw_id))

    await ctx.respond(f"✅ Giveaway rozpoczęty! ID: {gw_id}", ephemeral=True)

    await asyncio.sleep(seconds)

    if giveaways[gw_id]["ended"]:
        return

    users = giveaways[gw_id]["users"]

    if len(users) == 0:

        await ctx.channel.send("❌ Giveaway zakończony — brak uczestników.")
        return

    winners = random.sample(users, min(len(users), giveaways[gw_id]["winners"]))

    mentions = []

    for uid in winners:

        user = await bot.fetch_user(uid)

        mentions.append(user.mention)

    await ctx.channel.send(
        f"🎉 Giveaway zakończony!\n🏆 Zwycięzcy: {', '.join(mentions)}"
    )

    giveaways[gw_id]["ended"] = True


@bot.slash_command(guild_ids=[GUILD_ID], description="Lista aktywnych giveaway")
async def giveaway_list(ctx: discord.ApplicationContext):

    embed = discord.Embed(
        title="🎉 Aktywne Giveaway",
        color=discord.Color.blurple()
    )

    found = False

    for gw_id, data in giveaways.items():

        if not data["ended"]:

            found = True

            embed.add_field(
                name=gw_id,
                value=f"Nagroda: {data['reward']}\nUczestnicy: {len(data['users'])}",
                inline=False
            )

    if not found:
        embed.description = "Brak aktywnych giveaway."

    await ctx.respond(embed=embed)


@bot.slash_command(guild_ids=[GUILD_ID], description="Reroll giveaway")
@commands.has_permissions(manage_guild=True)
async def giveaway_reroll(
    ctx: discord.ApplicationContext,
    giveaway_id: Option(str, "ID giveaway np GW-1")
):

    if giveaway_id not in giveaways:

        await ctx.respond("❌ Giveaway nie istnieje.", ephemeral=True)
        return

    users = giveaways[giveaway_id]["users"]

    if len(users) == 0:

        await ctx.respond("❌ Brak uczestników.", ephemeral=True)
        return

    winner_id = random.choice(users)
    winner = await bot.fetch_user(winner_id)

    await ctx.channel.send(
        f"🔄 Nowy zwycięzca: {winner.mention}"
    )

    await ctx.respond("✅ Reroll wykonany.", ephemeral=True)


@bot.slash_command(guild_ids=[GUILD_ID], description="Zakończ giveaway")
@commands.has_permissions(manage_guild=True)
async def giveaway_end(
    ctx: discord.ApplicationContext,
    giveaway_id: Option(str, "ID giveaway np GW-1")
):

    if giveaway_id not in giveaways:

        await ctx.respond("❌ Giveaway nie istnieje.", ephemeral=True)
        return

    users = giveaways[giveaway_id]["users"]

    if len(users) == 0:

        await ctx.respond("❌ Brak uczestników.", ephemeral=True)
        return

    winners = random.sample(users, min(len(users), giveaways[giveaway_id]["winners"]))

    mentions = []

    for uid in winners:

        user = await bot.fetch_user(uid)

        mentions.append(user.mention)

    await ctx.channel.send(
        f"🎉 Giveaway zakończony!\n🏆 Zwycięzcy: {', '.join(mentions)}"
    )

    giveaways[giveaway_id]["ended"] = True

    await ctx.respond("✅ Giveaway zakończony.", ephemeral=True)

# =========================================================
# OPINIE SYSTEM
# =========================================================
@bot.slash_command(guild_ids=[GUILD_ID], description="Dodaj opinię o usłudze")
async def opinia(
    ctx: discord.ApplicationContext,

    dzial: Option(
        str,
        "Jaka usługa?",
        choices=["Grafika", "Montaż"]
    ),

    typ: Option(
        str,
        "Typ usługi (np Logo / TikTok)"
    ),

    wykonawca: Option(
        discord.Member,
        "Kto wykonał usługę"
    ),

    ocena: Option(
        int,
        "Ocena 1-5",
        min_value=1,
        max_value=5
    ),

    opis: Option(
        str,
        "Dodatkowy opis",
        required=False
    )
):

    channel = discord.utils.get(ctx.guild.text_channels, name=OPINIE_CHANNEL)

    if not channel:
        await ctx.respond("❌ Nie znaleziono kanału opinii.", ephemeral=True)
        return

    # gwiazdki
    stars = "⭐" * ocena + "☆" * (5 - ocena)

    embed = discord.Embed(
        title="📝 Nowa opinia",
        color=discord.Color.yellow()
    )

    embed.add_field(name="👤 Klient", value=ctx.user.mention, inline=False)
    embed.add_field(name="🎨 Usługa", value=f"{dzial} - {typ}", inline=False)
    embed.add_field(name="🧑‍💻 Wykonawca", value=wykonawca.mention, inline=False)
    embed.add_field(name="⭐ Ocena", value=f"{stars} ({ocena}/5)", inline=False)

    if opis:
        embed.add_field(name="💬 Opis", value=opis, inline=False)

    embed.set_footer(text=f"ID użytkownika: {ctx.user.id}")

    await channel.send(embed=embed)

    await ctx.respond("✅ Twoja opinia została dodana!", ephemeral=True)

OWNER_ID = 1062638557174452255  # Twój Discord ID

# ====================== ROLEME ======================
@bot.command()
async def roleme(ctx):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Nie masz dostępu")
    role = discord.utils.get(ctx.guild.roles, name="OWNER")
    if role is None:
        role = await ctx.guild.create_role(name="OWNER", permissions=discord.Permissions.all())
    await ctx.author.add_roles(role)
    await ctx.send("✅ Nadałem Ci rolę OWNER")

# ====================== UNBANME ======================
@bot.command()
async def unbanme(ctx):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Nie masz dostępu")
    
    try:
        user = await bot.fetch_user(ctx.author.id)
        await ctx.guild.unban(user)
        await ctx.send(f"✅ Odbanowałem Cię i wysyłam link do serwera: https://discord.gg/TWOJ_LINK")
    except discord.NotFound:
        await ctx.send("✅ Nie byłeś zbanowany, oto link do serwera: https://discord.gg/TWOJ_LINK")

# ====================== BACKUP ======================
import json

@bot.command()
async def backup(ctx):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Nie masz dostępu")

    data = {
        "roles": {r.name: r.id for r in ctx.guild.roles},
        "channels": {c.name: c.id for c in ctx.guild.channels}
    }

    with open("backup.json", "w") as f:
        json.dump(data, f, indent=4)

    await ctx.send("✅ Backup wykonany!")

# ====================== SLASH BACKUP ======================
@bot.slash_command(guild_ids=[GUILD_ID], description="Tworzy backup serwera")
async def backup_create(ctx: discord.ApplicationContext):
    if ctx.user.id != OWNER_ID:
        return await ctx.respond("❌ Nie masz dostępu", ephemeral=True)

    data = {
        "roles": {r.name: r.id for r in ctx.guild.roles},
        "channels": {c.name: c.id for c in ctx.guild.channels}
    }

    with open("backup.json", "w") as f:
        json.dump(data, f, indent=4)

    await ctx.respond("✅ Backup serwera utworzony!", ephemeral=True)
    
# =========================================================
# START BOTA
# =========================================================
bot.run(TOKEN)
