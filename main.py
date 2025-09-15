import discord
from discord.ext import commands
import time
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")


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

@bot.command
async def show_rank(ctx):
    await ctx.send("O ranking de tempos:")

@bot.event
async def on_voice_state_update(member, before, after):

    if before.channel is None and after.channel is not None:
        tempos_de_estudo[member.id] = time.time()
        text_channel = discord.utils.get(member.guild.text_channels, name="geral")

        if text_channel:
            await text_channel.send(f"{member.display_name} começou a estudar!")

    elif before.channel is not None and after.channel is None:
        if member.id in tempos_de_estudo:
            start = tempos_de_estudo.pop(member.id) 
            finish = time.time()
            total_study_time = int(finish - start)

            ranking[member.id] = ranking.get(member.id, 0) + total_study_time

            text_channel = discord.utils.get(member.guild.text_channels, name="geral")

        if text_channel:
            await text_channel.send(
                f"⏳ {member.display_name} estudou por {format_tempo(total_study_time)}!"
            )

@bot.command()
async def points(ctx: commands.Context):
    user_id = ctx.author.id
    total = ranking.get(user_id, 0)  # total em segundos

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
    if not ranking:
        await ctx.send("Ainda não há pontuações registradas.")
        return

    # Ordena o ranking do maior para o menor tempo
    top5 = sorted(ranking.items(), key=lambda x: x[1], reverse=True)[:5]

    msg = "**🏆 Melhores Estudantes**\n"

    for i, (user_id, total) in enumerate(top5, start=1):
        user = await bot.fetch_user(user_id)  # pega o objeto do usuário pelo ID

        # Converte segundos em horas, minutos e segundos
        segundos = total
        minutos = segundos // 60
        segundos = segundos % 60
        horas = minutos // 60
        minutos = minutos % 60

        msg += f"{i}. {user.display_name} — {horas}h {minutos}m {segundos}s\n"

    await ctx.send(msg)

@bot.command()
async def addtime(ctx, member: discord.Member, segundos: int):
    # adiciona segundos ao ranking
    ranking[member.id] = ranking.get(member.id, 0) + segundos
    await ctx.send(f"✅ {segundos} segundos adicionados a {member.display_name}. Total agora: {ranking[member.id]} s")

bot.run(TOKEN)