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
    await ctx.respond(embed=embed, ephemeral=True)

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
    await ctx.respond(embed=embed, view=ZamowieniaStart(), ephemeral=True)

bot.run(os.getenv("TOKEN"))


