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

GUILD_ID = 1453411007010439168
OWNER_ID = 1062638557174452255
ROLE_OWNER = "OWNER"
ZAMOWIENIA_CATEGORY = "︙✉️︙zamówienia︙"

giveaways = {}

# =========================================================
# READY
# =========================================================
@bot.event
async def on_ready():
    print(f"✅ {bot.user}")

# =========================================================
# ON MESSAGE (NAPRAWIONE)
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

@bot.slash_command(guild_ids=[GUILD_ID])
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
# ZAMÓWIENIA (FULL PANEL + VIEW + MODAL)
# =========================================================
class ZamowienieModal(discord.ui.Modal):
    def __init__(self, dzial, typ):
        super().__init__(title=f"Zamówienie - {typ}")
        self.dzial = dzial
        self.typ = typ

        self.opis = discord.ui.InputText(
            label="Opisz zamówienie",
            style=discord.InputTextStyle.long
        )
        self.add_item(self.opis)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild

        category = discord.utils.get(guild.categories, name=ZAMOWIENIA_CATEGORY)
        if not category:
            category = await guild.create_category(ZAMOWIENIA_CATEGORY)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True)
        }

        role = discord.utils.get(guild.roles, name=GRAFIK_ROLE if self.dzial=="Grafika" else MONTAZ_ROLE)
        if role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True)

        channel = await guild.create_text_channel(
            name=f"zam-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        cena = CENNIK_GRAFIKA.get(self.typ) if self.dzial=="Grafika" else CENNIK_MONTAZ.get(self.typ)

        embed = discord.Embed(title="📦 Zamówienie", color=discord.Color.red())
        embed.add_field(name="👤 Klient", value=interaction.user.mention, inline=False)
        embed.add_field(name="🎨 Typ", value=self.typ, inline=False)
        embed.add_field(name="💰 Cena", value=cena, inline=False)
        embed.add_field(name="📝 Opis", value=self.opis.value, inline=False)

        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Zamówienie utworzone!", ephemeral=True)

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
    async def grafika(self, b, i):
        await i.response.send_message("Wybierz usługę:", view=GrafikaView(), ephemeral=True)

    @discord.ui.button(label="🎬 Montaż")
    async def montaz(self, b, i):
        await i.response.send_message("Wybierz usługę:", view=MontazView(), ephemeral=True)

@bot.slash_command(guild_ids=[GUILD_ID])
async def setup_zamowienia(ctx):
    embed = discord.Embed(
        title="📦 Zamówienia",
        description="Kliknij przycisk poniżej aby złożyć zamówienie",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed, view=ZamowieniaStart())
    await ctx.respond("✅ Panel zamówień gotowy", ephemeral=True)
# =========================================================
# MODERACJA
# =========================================================
warns = {}

@bot.slash_command(guild_ids=[GUILD_ID])
async def purge(ctx, liczba:int):
    await ctx.channel.purge(limit=liczba)
    await ctx.respond("✅", ephemeral=True)

@bot.slash_command(guild_ids=[GUILD_ID])
async def ban(ctx, user:discord.Member, powod:str="Brak"):
    await user.ban(reason=powod)
    await ctx.respond("✅", ephemeral=True)

@bot.slash_command(guild_ids=[GUILD_ID])
async def kick(ctx, user:discord.Member):
    await user.kick()
    await ctx.respond("✅", ephemeral=True)

@bot.slash_command(guild_ids=[GUILD_ID])
async def warn(ctx, user:discord.Member, powod:str):
    warns.setdefault(user.id, []).append(powod)
    await ctx.respond("⚠️ Warn dodany", ephemeral=True)

@bot.slash_command(guild_ids=[GUILD_ID])
async def warns_cmd(ctx, user:discord.Member):
    lista = warns.get(user.id, [])
    embed = discord.Embed(title="Warny", color=discord.Color.red())
    embed.description = "\n".join(lista) if lista else "Brak"
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(guild_ids=[GUILD_ID])
async def unwarn(ctx, user:discord.Member, index:int):
    if user.id in warns and len(warns[user.id]) >= index:
        warns[user.id].pop(index-1)
    await ctx.respond("✅", ephemeral=True)

# =========================================================
# GIVEAWAY (FULL)
# =========================================================
def parse_time(t):
    matches = re.findall(r"(\d+)([smhd])", t)
    sec = 0
    for v,u in matches:
        v=int(v)
        if u=="s": sec+=v
        if u=="m": sec+=v*60
        if u=="h": sec+=v*3600
        if u=="d": sec+=v*86400
    return sec

@bot.slash_command(guild_ids=[GUILD_ID])
async def giveaway(ctx, nagroda:str, winners:int, czas:str):
    sec = parse_time(czas)
    end = int((datetime.utcnow()+timedelta(seconds=sec)).timestamp())

    embed = discord.Embed(title="🎉 GIVEAWAY", color=discord.Color.red())
    embed.add_field(name="Nagroda", value=nagroda)
    embed.add_field(name="Wygrani", value=winners)
    embed.add_field(name="Koniec", value=f"<t:{end}:R>")

    msg = await ctx.send(embed=embed)
    giveaways[msg.id] = {"users":[], "winners":winners}

    await ctx.respond("✅", ephemeral=True)

    await asyncio.sleep(sec)

    users = giveaways[msg.id]["users"]
    if users:
        win = random.sample(users, min(len(users), winners))
        await ctx.send("🏆 " + ", ".join([f"<@{u}>" for u in win]))

# =========================================================
# OPINIE
# =========================================================
@bot.slash_command(guild_ids=[GUILD_ID])
async def opinia(ctx, dzial:str, typ:str, wykonawca:discord.Member, ocena:int):
    ch = discord.utils.get(ctx.guild.text_channels, name=OPINIE_CHANNEL)
    stars = "⭐"*ocena + "☆"*(5-ocena)

    embed = discord.Embed(title="📝 Opinia", color=discord.Color.red())
    embed.add_field(name="User", value=ctx.user.mention)
    embed.add_field(name="Usługa", value=f"{dzial}-{typ}")
    embed.add_field(name="Wykonawca", value=wykonawca.mention)
    embed.add_field(name="Ocena", value=stars)

    await ch.send(embed=embed)
    await ctx.respond("✅", ephemeral=True)

# =========================================================
# DM KOMENDY
# =========================================================
@bot.command()
async def roleme(ctx):
    if not isinstance(ctx.channel, discord.DMChannel): return
    if ctx.author.id != OWNER_ID: return

    guild = bot.get_guild(GUILD_ID)
    role = discord.utils.get(guild.roles, name=ROLE_OWNER) or await guild.create_role(name=ROLE_OWNER)

    await guild.get_member(ctx.author.id).add_roles(role)
    await ctx.send(embed=discord.Embed(title="Rola nadana", color=discord.Color.red()))

@bot.command()
async def unbanme(ctx):
    if not isinstance(ctx.channel, discord.DMChannel): return
    if ctx.author.id != OWNER_ID: return

    guild = bot.get_guild(GUILD_ID)
    bans = await guild.bans()

    for b in bans:
        if b.user.id == OWNER_ID:
            await guild.unban(b.user)
            await ctx.send(embed=discord.Embed(title="Unban", color=discord.Color.red()))

@bot.command()
async def backup(ctx, arg=None):
    if not isinstance(ctx.channel, discord.DMChannel): return
    if ctx.author.id != OWNER_ID: return

    guild = bot.get_guild(GUILD_ID)

    if arg=="create":
        data = {
            "roles":[r.name for r in guild.roles],
            "channels":[c.name for c in guild.channels]
        }
        with open("backup.json","w") as f:
            json.dump(data,f)

        await ctx.send(embed=discord.Embed(title="Backup zapisany", color=discord.Color.red()))

# =========================================================
# START (RAILWAY)
# =========================================================
bot.run(os.getenv("TOKEN"))
