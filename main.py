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
    MONTAZ_ROLE
)

# ====== USTAWIENIA ======
intents = discord.Intents.all()
bot = commands.Bot(intents=intents)

ZAMOWIENIA_CATEGORY = "︙✉️︙zamówienia︙"
NOWA_ROLA = "CZŁONEK"

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
# ======================= BOT READY =======================
# =========================================================
@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako {bot.user}")

# =========================================================
# ====================== POWITANIE ========================
# =========================================================
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name=WELCOME_CHANNEL)
    if channel:
        embed = discord.Embed(
            title="👋 Witaj!",
            description=f"Witaj {member.mention} na **VexSync**!",
            color=discord.Color.green()
        )
        await channel.send(embed=embed)

    role = discord.utils.get(member.guild.roles, name=NOWA_ROLA)
    if role:
        await member.add_roles(role)

# =========================================================
# ===================== MODAL OPIS ========================
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

        category = discord.utils.get(guild.categories, name=ZAMOWIENIA_CATEGORY)
        if not category:
            category = await guild.create_category(ZAMOWIENIA_CATEGORY)

        channel = await guild.create_text_channel(
            f"🟡・zamowienie-{interaction.user.name}",
            category=category
        )

        if self.dzial == "Grafika":
            cena = CENNIK_GRAFIKA[self.typ]
            role_ping = discord.utils.get(guild.roles, name=GRAFIK_ROLE)
        else:
            cena = CENNIK_MONTAZ[self.typ]
            role_ping = discord.utils.get(guild.roles, name=MONTAZ_ROLE)

        embed = discord.Embed(title="📦 Nowe zamówienie", color=discord.Color.orange())
        embed.add_field(name="Klient", value=interaction.user.mention, inline=False)
        embed.add_field(name="Dział", value=self.dzial, inline=False)
        embed.add_field(name="Typ", value=self.typ, inline=False)
        embed.add_field(name="Cena", value=cena, inline=False)
        embed.add_field(name="Opis", value=self.opis.value, inline=False)

        await channel.send(
            content=role_ping.mention if role_ping else None,
            embed=embed,
            view=ZamowienieButtons()
        )

        await interaction.response.send_message("✅ Zamówienie utworzone!", ephemeral=True)

# =========================================================
# ===================== PRZYCISKI =========================
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
# ================== WYBÓR DZIAŁU =========================
# =========================================================
class StartZamowienia(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎨 Grafika", style=discord.ButtonStyle.primary)
    async def grafika(self, button, interaction):
        await interaction.response.send_message(
            "Wybierz typ grafiki:",
            view=GrafikaView(),
            ephemeral=True
        )

    @discord.ui.button(label="🎬 Montaż", style=discord.ButtonStyle.secondary)
    async def montaz(self, button, interaction):
        await interaction.response.send_message(
            "Wybierz typ montażu:",
            view=MontazView(),
            ephemeral=True
        )

# =========================================================
# =================== GRAFIKA VIEW ========================
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
        await interaction.response.send_modal(
            ZamowienieModal("Grafika", select.values[0])
        )

# =========================================================
# =================== MONTAŻ VIEW =========================
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
        await interaction.response.send_modal(
            ZamowienieModal("Montaż", select.values[0])
        )

# =========================================================
# ================== SETUP ZAMÓWIEŃ =======================
# =========================================================
@bot.slash_command(description="SETUP: panel zamówień")
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
# ================== SETUP CENNIK =========================
# =========================================================
@bot.slash_command(description="SETUP: cennik")
@commands.has_permissions(administrator=True)
async def setup_cennik(ctx: discord.ApplicationContext):
    embed = discord.Embed(title="💰 Cennik – VexSync", color=discord.Color.gold())

    for k, v in CENNIK_GRAFIKA.items():
        embed.add_field(name=f"🎨 {k}", value=v, inline=False)

    for k, v in CENNIK_MONTAZ.items():
        embed.add_field(name=f"🎬 {k}", value=v, inline=False)

        # Dodanie pola informacyjnego o płatności
    embed.add_field(
        name="ℹ️ Informacja",
        value="💳 Płatność tylko Paysafecard",
        inline=False
    )

    await ctx.channel.send(embed=embed)
    await ctx.respond("✅ Cennik wysłany", ephemeral=True)

# =========================================================
# ======================= OPINIA ==========================
# =========================================================
@bot.slash_command(description="Dodaj opinię")
async def opinia(
    ctx: discord.ApplicationContext,
    dzial: Option(str, choices=["Grafika", "Montaż"]),
    tekst: Option(str, description="Treść opinii")
):
    channel = discord.utils.get(ctx.guild.text_channels, name="︙✅︙opinie︙")
    if not channel:
        return await ctx.respond("❌ Brak kanału opinii", ephemeral=True)

    embed = discord.Embed(
        title="⭐ Opinia",
        description=tekst,
        color=discord.Color.green()
    )
    embed.add_field(name="Dział", value=dzial)
    embed.set_footer(text=f"Autor: {ctx.author}")

    await channel.send(embed=embed)
    await ctx.respond("✅ Opinia dodana", ephemeral=True)

# =========================================================
# ====================== MODERACJA ========================
# =========================================================
@bot.slash_command(description="Ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, reason: str = "Brak powodu"):
    await member.ban(reason=reason)
    await ctx.respond(f"🔨 Zbanowano {member.mention}")

@bot.slash_command(description="Kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, reason: str = "Brak powodu"):
    await member.kick(reason=reason)
    await ctx.respond(f"👢 Wyrzucono {member.mention}")

@bot.slash_command(description="Timeout")
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, minutes: int):
    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(until)
    await ctx.respond(f"⏱️ Timeout {member.mention} na {minutes} min")

# =========================================================
# ======================== START ==========================
# =========================================================
bot.run(TOKEN)

