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
            description=f"Witaj {member.mention} na **VexSync**!",
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

        # kategoria
        category = discord.utils.get(guild.categories, name=ZAMOWIENIA_CATEGORY)
        if not category:
            category = await guild.create_category(ZAMOWIENIA_CATEGORY)

        # role
        klient_role = discord.utils.get(guild.roles, name=KLIENT_ROLE)
        if self.dzial == "Grafika":
            cena = CENNIK_GRAFIKA[self.typ]
            worker_role = discord.utils.get(guild.roles, name=GRAFIK_ROLE)
        else:
            cena = CENNIK_MONTAZ[self.typ]
            worker_role = discord.utils.get(guild.roles, name=MONTAZ_ROLE)

        # PERMISJE
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        if klient_role:
            overwrites[klient_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        if worker_role:
            overwrites[worker_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        # tworzenie kanału
        channel = await guild.create_text_channel(
            f"🟡・zamowienie-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        # wymuszenie permisji (discord czasem ignoruje przy kategorii)
        if klient_role:
            await channel.set_permissions(klient_role, view_channel=True, send_messages=True)
        if worker_role:
            await channel.set_permissions(worker_role, view_channel=True, send_messages=True)

        # embed
        embed = discord.Embed(
            title="📦 Nowe zamówienie",
            color=discord.Color.orange()
        )
        embed.add_field(name="Klient", value=interaction.user.mention, inline=False)
        embed.add_field(name="Dział", value=self.dzial, inline=False)
        embed.add_field(name="Typ", value=self.typ, inline=False)
        embed.add_field(name="Cena", value=cena, inline=False)
        embed.add_field(name="Opis", value=self.opis.value, inline=False)

        # przyciski z dostępem
        await channel.send(embed=embed, view=ZamowienieButtons(worker_role))

        await interaction.response.send_message(
            "✅ Zamówienie utworzone!",
            ephemeral=True
        )

# =========================================================
# PRZYCISKI ZAMÓWIENIA
# =========================================================
class ZamowienieButtons(discord.ui.View):
    def __init__(self, worker_role: discord.Role):
        super().__init__(timeout=None)
        self.worker_role = worker_role
        self.assigned_member = None

    @discord.ui.button(label="📌 Przyjmuję zamówienie", style=discord.ButtonStyle.primary)
    async def assign(self, button, interaction: discord.Interaction):
        # sprawdzenie roli
        if not self.worker_role or self.worker_role not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ Nie masz roli do przyjęcia tego zamówienia.",
                ephemeral=True
            )
            return

        # przypisanie
        self.assigned_member = interaction.user
        button.disabled = True
        await interaction.response.edit_message(view=self)

        # zaktualizowanie uprawnień kanału – tylko osoba przypisana może pisać
        overwrites = interaction.channel.overwrites
        for r, perm in overwrites.items():
            if isinstance(r, discord.Member):
                # klient dalej może pisać
                continue
            elif isinstance(r, discord.Role):
                # rola działu widzi ale nie pisze
                await interaction.channel.set_permissions(r, send_messages=False, view_channel=True)
        await interaction.channel.set_permissions(self.assigned_member, send_messages=True, view_channel=True)

        await interaction.channel.send(f"📌 Zamówienie przyjął: {interaction.user.mention}")

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
        await interaction.response.send_modal(
            ZamowienieModal("Grafika", select.values[0])
        )

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
        await interaction.response.send_modal(
            ZamowienieModal("Montaż", select.values[0])
        )

# =========================================================
# SETUP PANELU ZAMÓWIEŃ
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
# START BOTA
# =========================================================
bot.run(TOKEN)
