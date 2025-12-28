import discord
from discord.ext import commands
from discord import Option
from datetime import timedelta
from config import *

intents = discord.Intents.all()
bot = commands.Bot(intents=intents)

ZAMOWIENIA_CATEGORY = "︙✉️︙zamówienia︙"

CENNIK = {
    "Miniaturka": "10 PLN",
    "Logo": "20 PLN",
    "Baner": "20 PLN"
}

# ================= BOT READY =================
@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako {bot.user}")

# ================= POWITANIE =================
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

# ================= MODAL =================
class ZamowienieModal(discord.ui.Modal):
    def __init__(self, typ):
        super().__init__(title=f"Zamówienie: {typ}")
        self.typ = typ
        self.opis = discord.ui.InputText(
            label="Opis zamówienia",
            style=discord.InputTextStyle.long,
            placeholder="Opisz szczegóły zamówienia"
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

        grafik_role = discord.utils.get(guild.roles, name=GRAFIK_ROLE)

        embed = discord.Embed(title="📦 Nowe zamówienie", color=discord.Color.orange())
        embed.add_field(name="Klient", value=interaction.user.mention, inline=False)
        embed.add_field(name="Typ", value=self.typ, inline=False)
        embed.add_field(name="Cena", value=CENNIK[self.typ], inline=False)
        embed.add_field(name="Opis", value=self.opis.value, inline=False)

        await channel.send(
            content=grafik_role.mention if grafik_role else None,
            embed=embed
        )

        await interaction.response.send_message("✅ Zamówienie utworzone!", ephemeral=True)

# ================= PRZYCISK =================
class ZamowienieView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📦 Złóż zamówienie", style=discord.ButtonStyle.primary)
    async def zamowienie(self, button, interaction):
        await interaction.response.send_message(
            "Wybierz typ zamówienia:",
            view=TypView(),
            ephemeral=True
        )

class TypView(discord.ui.View):
    @discord.ui.select(
        placeholder="Wybierz typ",
        options=[
            discord.SelectOption(label="Miniaturka"),
            discord.SelectOption(label="Logo"),
            discord.SelectOption(label="Baner"),
        ]
    )
    async def select(self, select, interaction):
        await interaction.response.send_modal(ZamowienieModal(select.values[0]))

# ================= KOMENDA ADMIN – ZAMÓWIENIA =================
@bot.slash_command(name="zamowienia_setup", description="Wyślij panel zamówień")
@commands.has_permissions(administrator=True)
async def zamowienia_setup(ctx):
    channel = discord.utils.get(ctx.guild.text_channels, name=ZAMOWIENIA_CHANNEL)
    if not channel:
        return await ctx.respond("❌ Brak kanału zamówień", ephemeral=True)

    embed = discord.Embed(
        title="📦 Zamówienia",
        description="Kliknij przycisk, aby złożyć zamówienie",
        color=discord.Color.blurple()
    )
    await channel.send(embed=embed, view=ZamowienieView())
    await ctx.respond("✅ Panel zamówień wysłany", ephemeral=True)

# ================= KOMENDA ADMIN – CENNIK =================
@bot.slash_command(name="cennik", description="Wyślij cennik")
@commands.has_permissions(administrator=True)
async def cennik(ctx):
    channel = discord.utils.get(ctx.guild.text_channels, name=CENNIK_CHANNEL)
    if not channel:
        return await ctx.respond("❌ Brak kanału cennik", ephemeral=True)

    embed = discord.Embed(title="💰 Cennik – VexSync", color=discord.Color.blue())
    for k, v in CENNIK.items():
        embed.add_field(name=k, value=v, inline=False)

    await channel.send(embed=embed)
    await ctx.respond("✅ Cennik wysłany", ephemeral=True)

# ================= OPINIA =================
@bot.slash_command(name="opinia", description="Dodaj opinię")
async def opinia(ctx, tekst: Option(str, "Twoja opinia")):
    channel = discord.utils.get(ctx.guild.text_channels, name=OPINIE_CHANNEL)
    embed = discord.Embed(title="⭐ Opinia", description=tekst, color=discord.Color.gold())
    embed.set_footer(text=f"{ctx.author}")
    await channel.send(embed=embed)
    await ctx.respond("✅ Opinia dodana", ephemeral=True)

# ================= MODERACJA =================
@bot.slash_command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, reason: str = "Brak powodu"):
    await member.ban(reason=reason)
    await ctx.respond("🔨 Zbanowano")

@bot.slash_command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, reason: str = "Brak powodu"):
    await member.kick(reason=reason)
    await ctx.respond("👢 Wyrzucono")

@bot.slash_command(name="timeout")
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, minutes: int):
    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(until)
    await ctx.respond("⏱️ Timeout nadany")

# ================= START =================
bot.run(TOKEN)


