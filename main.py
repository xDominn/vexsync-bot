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

        # Role
        if self.dzial == "Grafika":
            cena = CENNIK_GRAFIKA[self.typ]
            worker_role = discord.utils.get(guild.roles, name=GRAFIK_ROLE)
        else:
            cena = CENNIK_MONTAZ[self.typ]
            worker_role = discord.utils.get(guild.roles, name=MONTAZ_ROLE)

        # Nadanie roli KLIENT dopiero przy zamówieniu
        klient_role = discord.utils.get(guild.roles, name=KLIENT_ROLE)
        if klient_role:
            await interaction.user.add_roles(klient_role)

        # Kategoria
        category = discord.utils.get(guild.categories, name=ZAMOWIENIA_CATEGORY)
        if not category:
            category = await guild.create_category(ZAMOWIENIA_CATEGORY)

        # Permisje - tylko użytkownik i dział widzą kanał
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        if worker_role:
            overwrites[worker_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        # Tworzenie kanału
        channel = await guild.create_text_channel(
            f"🟡・zamowienie-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        # Embed zamówienia
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

        await interaction.response.send_message(
            "✅ Zamówienie utworzone! Masz dostęp tylko do swojego kanału.",
            ephemeral=True
        )

# =========================================================
# PRZYCISKI ZAMÓWIENIA
# =========================================================
class ZamowienieButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🟢 Gotowe", style=discord.ButtonStyle.success)
    async def done(self, button, interaction):
        await interaction.channel.edit(name=f"🟢・{interaction.channel.name}")
        await interaction.response.send_message(
            "✅ Oznaczono jako gotowe",
            ephemeral=True
        )

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
