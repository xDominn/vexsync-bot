import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
from config import TOKEN

# ========= USTAWIENIA =========
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

ZAMOWIENIA_CHANNEL = "︙✉️︙zamówienia︙"
CENNIK_CHANNEL = "︙💸︙cennik︙"
OPINIE_CHANNEL = "︙✅︙opinie︙"
LOG_CHANNEL = "︙📝︙logi︙"

ROLE_CZLONEK = "CZŁONEK"
ROLE_GRAFIK = "GRAFIK"
ROLE_MONTAZ = "MONTAŻYSTA"
ROLE_KLIENT = "KLIENT"

# ========= CENNIK =========
CENNIK = {
    "Miniaturka": "10 PLN",
    "Logo": "20 PLN",
    "Baner": "20 PLN",
    "TikTok": "15 PLN",
    "Shorts": "15 PLN",
    "Film": "30 PLN"
}

# ========= READY =========
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Zalogowano jako {bot.user}")

# ========= AUTO ROLA =========
@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name=ROLE_CZLONEK)
    if role:
        await member.add_roles(role)

# ========= MODAL =========
class ZamowienieModal(discord.ui.Modal):
    def __init__(self, dzial, typ):
        super().__init__(title=f"Zamówienie – {typ}")
        self.dzial = dzial
        self.typ = typ

        self.opis = discord.ui.TextInput(
            label="Opis zamówienia",
            style=discord.TextStyle.long,
            required=True,
            placeholder="Opisz dokładnie czego potrzebujesz"
        )
        self.add_item(self.opis)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild

        # role
        await interaction.user.add_roles(
            discord.utils.get(guild.roles, name=ROLE_KLIENT)
        )

        # kanał
        category = discord.utils.get(guild.categories, name="ZAMÓWIENIA")
        if not category:
            category = await guild.create_category("ZAMÓWIENIA")

        channel = await guild.create_text_channel(
            f"zamowienie-{interaction.user.name}",
            category=category
        )

        ping_role = ROLE_GRAFIK if self.dzial == "Grafika" else ROLE_MONTAZ
        role = discord.utils.get(guild.roles, name=ping_role)

        embed = discord.Embed(
            title="📦 Nowe zamówienie",
            color=discord.Color.orange()
        )
        embed.add_field(name="Klient", value=interaction.user.mention)
        embed.add_field(name="Dział", value=self.dzial)
        embed.add_field(name="Typ", value=self.typ)
        embed.add_field(name="Cena", value=CENNIK.get(self.typ))
        embed.add_field(name="Opis", value=self.opis.value, inline=False)

        await channel.send(
            content=role.mention if role else None,
            embed=embed
        )

        await interaction.response.send_message(
            "✅ Zamówienie utworzone!",
            ephemeral=True
        )

# ========= WYBÓR TYPU =========
class TypView(discord.ui.View):
    def __init__(self, dzial):
        super().__init__(timeout=None)
        self.dzial = dzial

        if dzial == "Grafika":
            self.add_item(TypButton("Miniaturka", dzial))
            self.add_item(TypButton("Logo", dzial))
            self.add_item(TypButton("Baner", dzial))
        else:
            self.add_item(TypButton("TikTok", dzial))
            self.add_item(TypButton("Shorts", dzial))
            self.add_item(TypButton("Film", dzial))

class TypButton(discord.ui.Button):
    def __init__(self, label, dzial):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.typ = label
        self.dzial = dzial

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            ZamowienieModal(self.dzial, self.typ)
        )

# ========= WYBÓR DZIAŁU =========
class ZamowienieView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎨 Grafika", style=discord.ButtonStyle.success)
    async def grafika(self, interaction: discord.Interaction, _):
        await interaction.response.send_message(
            "Wybierz typ grafiki:",
            view=TypView("Grafika"),
            ephemeral=True
        )

    @discord.ui.button(label="🎬 Montaż", style=discord.ButtonStyle.primary)
    async def montaz(self, interaction: discord.Interaction, _):
        await interaction.response.send_message(
            "Wybierz typ montażu:",
            view=TypView("Montaż"),
            ephemeral=True
        )

# ========= KOMENDA ADMIN – ZAMÓWIENIA =========
@bot.tree.command(name="wyslij_zamowienia")
@app_commands.checks.has_permissions(administrator=True)
async def wyslij_zamowienia(interaction: discord.Interaction):
    channel = discord.utils.get(interaction.guild.text_channels, name=ZAMOWIENIA_CHANNEL)
    embed = discord.Embed(
        title="📦 Zamówienia",
        description="Kliknij przycisk aby złożyć zamówienie",
        color=discord.Color.green()
    )
    await channel.send(embed=embed, view=ZamowienieView())
    await interaction.response.send_message("✅ Wysłano", ephemeral=True)

# ========= KOMENDA ADMIN – CENNIK =========
@bot.tree.command(name="wyslij_cennik")
@app_commands.checks.has_permissions(administrator=True)
async def wyslij_cennik(interaction: discord.Interaction):
    channel = discord.utils.get(interaction.guild.text_channels, name=CENNIK_CHANNEL)

    embed = discord.Embed(
        title="💰 Cennik usług",
        color=discord.Color.blue()
    )
    for k, v in CENNIK.items():
        embed.add_field(name=k, value=v, inline=False)

    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Cennik wysłany", ephemeral=True)

# ========= OPINIA =========
@bot.tree.command(name="opinia")
async def opinia(interaction: discord.Interaction, dzial: str, tresc: str):
    channel = discord.utils.get(interaction.guild.text_channels, name=OPINIE_CHANNEL)

    embed = discord.Embed(
        title="⭐ Opinia",
        description=tresc,
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"{dzial} | {interaction.user}")

    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Dodano opinię", ephemeral=True)

# ========= MODERACJA =========
@bot.tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Brak powodu"):
    await member.ban(reason=reason)
    await interaction.response.send_message("🔨 Zbanowano")

@bot.tree.command(name="kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member):
    await member.kick()
    await interaction.response.send_message("👢 Wyrzucono")

@bot.tree.command(name="timeout")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int):
    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(until)
    await interaction.response.send_message("⏱️ Timeout nadany")

# ========= START =========
bot.run(TOKEN)
