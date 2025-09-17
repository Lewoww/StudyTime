import discord
from discord.ext import commands
import time
import asyncio 
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

async def update_study_time(member_id, guild_id, nome, tempo):
    try:
        conn = get_connection()
    except psycopg2.OperationalError:
        print("DB não disponível, dados não serão salvos")
        return
    
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ranking (discord_id, guild_id, user_name, total_time)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (discord_id, guild_id) 
        DO UPDATE SET total_time = ranking.total_time + EXCLUDED.total_time;
    """, (member_id, guild_id, nome, tempo))
    conn.commit()
    cur.close()
    conn.close()

intents = discord.Intents.all()
tempos_de_estudo = {}
ranking = {}
bot = commands.Bot(".", intents=intents)

def format_tempo(segundos_total):
    segundos = segundos_total
    minutos = segundos // 60
    segundos = segundos % 60
    horas = minutos // 60
    minutos = minutos % 60

    partes = []
    if horas > 0:
        partes.append(f"{horas}h")
    if minutos > 0:
        partes.append(f"{minutos}m")
    if segundos > 0 or not partes:
        partes.append(f"{segundos}s")

    return " ".join(partes)

@bot.event
async def on_voice_state_update(member, before, after):
    voice_channel = discord.utils.get(member.guild.voice_channels, name="studytime")
    text_channel = discord.utils.get(member.guild.text_channels, name="studytime")

    if voice_channel is None or text_channel is None:
        return
    
    guild_id = member.guild.id
    
    # Entrou no canal studytime
    if after.channel == voice_channel and (before.channel != voice_channel):
        tempos_de_estudo[member.id] = time.time()
        await text_channel.send(f"{member.display_name} começou a estudar!")

    # Saiu do canal studytime
    if before.channel == voice_channel and (after.channel != voice_channel):
        if member.id in tempos_de_estudo:
            start = tempos_de_estudo.pop(member.id)
            finish = time.time()
            total_study_time = int(finish - start)
            ranking[member.id] = ranking.get(member.id, 0) + total_study_time

            await text_channel.send(
                f"⏳ {member.display_name} estudou por {format_tempo(total_study_time)}!"
            )
            await update_study_time(member.id, guild_id ,member.display_name, total_study_time)




@bot.command()
async def points(ctx: commands.Context):
    user_id = ctx.author.id
    total = ranking.get(user_id, 0)

    segundos = total
    minutos = segundos // 60
    segundos = segundos % 60

    horas = minutos // 60
    minutos = minutos % 60

    dias = horas // 24
    horas = horas % 24

    meses = dias // 30
    dias = dias % 30

    anos = meses // 12
    meses = meses % 12

    decadas = anos // 10
    anos = anos % 10

    seculos = decadas // 10
    decadas = decadas % 10

    milenios = seculos // 10
    seculos = seculos % 10
    msg = f"{ctx.author.display_name}, você estudou por "

    partes = []
    if milenios > 0:
        partes.append(f"{milenios} milênios")
    if seculos > 0:
        partes.append(f"{seculos} séculos")
    if decadas > 0:
        partes.append(f"{decadas} décadas")
    if anos > 0:
        partes.append(f"{anos} anos")
    if meses > 0:
        partes.append(f"{meses} meses")
    if dias > 0:
        partes.append(f"{dias} dias")
    if horas > 0:
        partes.append(f"{horas} horas")
    if minutos > 0:
        partes.append(f"{minutos} minutos")
    if segundos > 0 or not partes:
        partes.append(f"{segundos} segundos")

    msg += ", ".join(partes) + "!"
    await ctx.send(msg)

@bot.command()
async def leaderboard(ctx: commands.Context):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Busca top 5 ordenado por tempo
        cur.execute("""
            SELECT discord_id, total_time
            FROM ranking
            WHERE guild_id = %s
            ORDER BY total_time DESC
            LIMIT 5;
        """, (ctx.guild.id,))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            await ctx.send("Ainda não há pontuações registradas.")
            return

        msg = "**🏆 Melhores Estudantes**\n"

        for i, row in enumerate(rows, start=1):
            user = await bot.fetch_user(row["discord_id"])
            total = row["total_time"]

            segundos = total
            minutos = segundos // 60
            segundos = segundos % 60
            horas = minutos // 60
            minutos = minutos % 60

            msg += f"{i}. {user.display_name} — {horas}h {minutos}m {segundos}s\n"

        await ctx.send(msg)

    except Exception as e:
        await ctx.send(f"⚠️ Erro ao acessar o banco: {e}")

@bot.command()
async def addtime(ctx, member: discord.Member, segundos: int):
    # adiciona segundos ao ranking
    ranking[member.id] = ranking.get(member.id, 0) + segundos
    await ctx.send(f"✅ {segundos} segundos adicionados a {member.display_name}. Total agora: {ranking[member.id]} s")

bot.run(TOKEN)