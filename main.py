import discord
from discord.ext import commands
from discord import Option
from datetime import timedelta
from config import TOKEN, WELCOME_CHANNEL, LOG_CHANNEL, KLIENT_ROLE, GRAFIK_ROLE

# ====== Ustawienia ======
intents = discord.Intents.all()
ZAMOWIENIA_CHANNEL = "︙✉️︙zamówienia︙"
NOWA_ROLA = "CZŁONEK"

# ====== CENNIK ======
CENNIK = {
    "Miniaturka": "10 PLN",
    "Logo": "20 PLN",
    "Baner": "20 PLN"
}

# ====== BOT ======
bot = commands.Bot(command_prefix="!", intents=intents)

# ====== BOT READY ======
@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako {bot.user}")

    guild = bot.guilds[0]  # bot tylko na jednym serwerze
    channel = discord.utils.get(guild.text_channels, name="︙💸︙cennik︙")
    if not channel:
        return

    # Sprawdzamy czy bot już coś wysłał na kanale
    async for msg in channel.history(limit=20):
        if msg.author == bot.user:
            return  # JUŻ JEST → nie wysyłamy drugi raz

    embed = discord.Embed(
        title="💰 Cennik usług graficznych – VexSync",
        color=discord.Color.blue()
    )
    embed.add_field(name="🖼️ Miniaturka", value="10 PLN", inline=False)
    embed.add_field(name="🎨 Logo", value="20 PLN", inline=False)
    embed.add_field(name="🖌️ Baner", value="20 PLN", inline=False)
    embed.set_footer(text="Ceny mogą ulec zmianie (płatność tylko paysafecard)")

    await channel.send(embed=embed)

    # Przyciski zamówienia na kanale
    zam_channel = discord.utils.get(guild.text_channels, name=ZAMOWIENIA_CHANNEL)
    if zam_channel:
        view = ZamowienieStartView()
        await zam_channel.send("Kliknij przycisk, aby złożyć zamówienie:", view=view)

# ====== POWITANIE ======
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name=WELCOME_CHANNEL)
    if channel:
        embed = discord.Embed(
            title="👋 Witaj na serwerze!",
            description=f"Witaj {member.mention} na **VexSync**!\nMiłej zabawy życzy administracja serwera!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

    role = discord.utils.get(member.guild.roles, name=NOWA_ROLA)
    if role:
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            print(f"❌ Nie udało się nadać roli {NOWA_ROLA} dla {member}")

# ====== MODAL ======
class ZamowienieModal(discord.ui.Modal):
    def __init__(self, typ):
        super().__init__(title=f"Zamówienie: {typ}")
        self.typ = typ
        self.opis = discord.ui.InputText(label="Opis zamówienia", style=discord.InputTextStyle.long)
        self.add_item(self.opis)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        klient_role = discord.utils.get(guild.roles, name=KLIENT_ROLE)
        if klient_role:
            try:
                await interaction.user.add_roles(klient_role)
            except discord.Forbidden:
                pass

        category = discord.utils.get(guild.categories, name="Zamówienia")
        if not category:
            category = await guild.create_category("Zamówienia")

        channel = await guild.create_text_channel(
            f"🟡・zamowienie-{interaction.user.name}",
            category=category
        )

        grafik_role = discord.utils.get(guild.roles, name=GRAFIK_ROLE)
        embed = discord.Embed(title="📦 Nowe zamówienie", color=discord.Color.orange())
        embed.add_field(name="Klient", value=interaction.user.mention, inline=False)
        embed.add_field(name="Typ", value=self.typ, inline=False)
        embed.add_field(name="Cena", value=CENNIK.get(self.typ, "Nieznana"), inline=False)
        embed.add_field(name="Opis", value=self.opis.value, inline=False)

        await channel.send(content=grafik_role.mention if grafik_role else None, embed=embed)
        log_channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL)
        if log_channel:
            await log_channel.send(f"📦 **Nowe zamówienie**: {interaction.user} → {channel.mention}")

        await interaction.response.send_message("✅ Zamówienie utworzone!", ephemeral=True)

# ====== PRZYCISK STARTOWY ======
class ZamowienieStartView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Złóż zamówienie", style=discord.ButtonStyle.primary)
    async def start_order(self, button, interaction: discord.Interaction):
        options = ["Miniaturka", "Logo", "Baner"]
        view = TypView(options)
        await interaction.response.send_message("Wybierz typ zamówienia:", view=view, ephemeral=True)

# ====== WYBÓR TYPU ======
class TypView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=None)
        for opt in options:
            self.add_item(TypButton(opt))

class TypButton(discord.ui.Button):
    def __init__(self, typ):
        super().__init__(label=typ, style=discord.ButtonStyle.secondary)
        self.typ = typ

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ZamowienieModal(self.typ))

# ====== OPINIA ======
@bot.slash_command(name="opinia", description="Dodaj opinię")
async def opinia(interaction: discord.Interaction, tekst: Option(str, "Twoja opinia")):
    channel = discord.utils.get(interaction.guild.text_channels, name="︙✅︙opinie︙")
    if not channel:
        return await interaction.response.send_message("❌ Brak kanału #opinie", ephemeral=True)

    embed = discord.Embed(title="⭐ Opinia klienta", description=tekst, color=discord.Color.gold())
    embed.set_footer(text=f"Autor: {interaction.user}")
    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Opinia dodana!", ephemeral=True)

# ====== MODERACJA ======
@bot.slash_command(name="ban", description="Zbanuj użytkownika")
@commands.has_permissions(ban_members=True)
async def ban(ctx: discord.Interaction, member: discord.Member, reason: str = "Brak powodu"):
    await member.ban(reason=reason)
    await ctx.response.send_message(f"🔨 Zbanowano {member.mention}")
    log_channel = discord.utils.get(ctx.guild.text_channels, name=LOG_CHANNEL)
    if log_channel:
        await log_channel.send(f"🔨 **BAN** | {member} | {ctx.user} | {reason}")

@bot.slash_command(name="kick", description="Wyrzuć użytkownika")
@commands.has_permissions(kick_members=True)
async def kick(ctx: discord.Interaction, member: discord.Member, reason: str = "Brak powodu"):
    await member.kick(reason=reason)
    await ctx.response.send_message(f"👢 Wyrzucono {member.mention}")
    log_channel = discord.utils.get(ctx.guild.text_channels, name=LOG_CHANNEL)
    if log_channel:
        await log_channel.send(f"👢 **KICK** | {member} | {ctx.user} | {reason}")

@bot.slash_command(name="timeout", description="Nadaj timeout")
@commands.has_permissions(moderate_members=True)
async def timeout(ctx: discord.Interaction, member: discord.Member, minutes: int):
    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(until)
    await ctx.response.send_message(f"⏱️ Timeout {member.mention} na {minutes} minut")
    log_channel = discord.utils.get(ctx.guild.text_channels, name=LOG_CHANNEL)
    if log_channel:
        await log_channel.send(f"⏱️ **TIMEOUT** | {member} | {minutes} min | {ctx.user}")

# ====== START ======
from config import TOKEN

bot.run(TOKEN)

