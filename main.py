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
    NOWA_ROLA
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
            color=discord.Color.green()
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
            color=discord.Color.orange()
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
        color=discord.Color.blurple()
    )
    await ctx.channel.send(embed=embed, view=StartZamowienia())
    await ctx.respond("✅ Panel zamówień wysłany", ephemeral=True)

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
async def warn(
    ctx: discord.ApplicationContext,
    user: Option(discord.Member, "Użytkownik do ostrzeżenia"),
    reason: Option(str, "Powód", required=False)
):
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
async def warns_user(
    ctx: discord.ApplicationContext,
    user: Option(discord.Member, "Użytkownik do sprawdzenia")
):
    if user.id not in warns or len(warns[user.id]) == 0:
        await ctx.respond(f"✅ {user.mention} nie ma żadnych warnów.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"⚠️ Warny użytkownika {user.display_name}",
        color=discord.Color.orange()
    )
    for i, w in enumerate(warns[user.id], start=1):
        embed.add_field(name=f"Warn #{i}", value=f"Powód: {w['reason']}\nModerator: {w['moderator']}", inline=False)

    await ctx.respond(embed=embed, ephemeral=True)

# =========================================================
# START BOTA
# =========================================================
bot.run(TOKEN)
