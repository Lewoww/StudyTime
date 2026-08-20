from keep_alive import keep_alive
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

import discord
from discord.ext import commands
from discord import Embed
import time
import asyncio
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

channel_participants = {}
pomodoro_tasks = {}
tempos_de_estudo = {}
tempos_pausados = {}

load_dotenv()

mode = os.getenv("MODE")

if mode == "local":
    load_dotenv(".env.local")
else:
    load_dotenv(".env.prod")
    
DATABASE_URL = os.getenv("DATABASE_URL")
TOKEN = os.getenv("TOKEN")

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT NOW();")
    print("✅ Banco conectado com sucesso:", cur.fetchone())
    cur.close()
    conn.close()
except Exception as e:
    print(f"Falha ao conectar: {e}")

intents = discord.Intents.all()
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

async def update_study_time(member_id, guild_id, nome, tempo):
    try:
        conn = get_connection()
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
        print(f"Tempo atualizado para {nome} ({tempo}s)")
    except Exception as e:
        print(f"Erro ao atualizar tempo: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    voice_channel = discord.utils.get(member.guild.voice_channels, name="studytime")
    text_channel = discord.utils.get(member.guild.text_channels, name="studytime")
    
    if voice_channel is None or text_channel is None:
        return

    guild_id = member.guild.id
    if guild_id not in channel_participants:
        channel_participants[guild_id] = set()

    # entra na call
    if after.channel == voice_channel and before.channel != voice_channel:
        if member.id not in channel_participants[guild_id]:
            tempos_de_estudo[member.id] = time.time()
            channel_participants[guild_id].add(member.id)
            await text_channel.send(f"{member.display_name} começou a estudar! 📚")

    # sai da call
    if before.channel == voice_channel and after.channel != voice_channel:
        total_study_time = 0
        channel_participants[guild_id].discard(member.id)

        if member.id in tempos_de_estudo:
            start = tempos_de_estudo.pop(member.id)
            finish = time.time()
            total_study_time += int(finish - start)

        if member.id in tempos_pausados:
            total_study_time += tempos_pausados.pop(member.id)

        if total_study_time > 0:
            ranking[member.id] = ranking.get(member.id, 0) + total_study_time
            await text_channel.send(
                f"⏳ {member.display_name} estudou por {format_tempo(total_study_time)}!"
            )
            await update_study_time(member.id, guild_id, member.display_name, total_study_time)

        if len(channel_participants[guild_id]) == 0:
            if guild_id in pomodoro_tasks:
                pomodoro_tasks[guild_id].cancel()
                del pomodoro_tasks[guild_id]
                await text_channel.send("Pomodoro cancelado! A sala esvaziou.")

@bot.command()
async def comandos(ctx):
    await ctx.send("Lista de comandos:\n"
            ".leaderboard:      Retorna mensagem com o ranking de tempo estudado\n"
            ".points:           Exibe suas horas estudadas totais.\n"
            ".pause:            Pausa o tempo de seus estudos. Beba água.\n"
            ".continuar:        Continue o tempo da onde tinha parado.\n"
            ".pomodoro X Y:     Adicione o tempo de estudo em minutos e o tempo de descanso após o comando, respectivamente.\n")

@bot.command()
async def points(ctx: commands.Context):
    user_id = ctx.author.id
    total = ranking.get(user_id, 0)

    segundos = total
    minutos = segundos // 60
    segundos = segundos % 60
    horas = minutos // 60
    minutos = minutos % 60

    msg = f"{ctx.author.display_name}, você estudou por {horas}h {minutos}m {segundos}s!"
    await ctx.send(msg)

@bot.command()
async def leaderboard(ctx: commands.Context):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT discord_id, user_name, total_time
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

        msg = "**🏆 Painel de Estudos**\n"
        for i, row in enumerate(rows, start=1):
            nome = row["user_name"]
            total = row["total_time"]
            horas = total // 3600
            minutos = (total % 3600) // 60
            segundos = total % 60
            msg += f"{i}. {nome} — {horas}h {minutos}m {segundos}s\n"

        await ctx.send(msg)

    except Exception as e:
        await ctx.send(f"Erro ao acessar o banco: {e}")



@bot.command()
async def pause(ctx):
    member = ctx.author
    if member.id in tempos_de_estudo:
        start = tempos_de_estudo.pop(member.id)
        elapsed = int(time.time() - start)
        tempos_pausados[member.id] = tempos_pausados.get(member.id, 0) + elapsed
        await ctx.send(f"{member.display_name} pausou o estudo ({format_tempo(elapsed)} acumulado).")
    else:
        await ctx.send("Você não está estudando agora.")

@bot.command()
async def continuar(ctx):
    member = ctx.author

    if member.id not in tempos_pausados:
        await ctx.send("⚠️ Você não tem uma sessão pausada para continuar.")
        return

    if member.id in tempos_de_estudo:
        await ctx.send("⚠️ Você já está estudando no momento.")
        return

    tempos_de_estudo[member.id] = time.time()
    await ctx.send(f"▶️ {member.display_name} retomou o estudo!")

@bot.command()
async def addtime(ctx, member: discord.Member, segundos: int):
    ranking[member.id] = ranking.get(member.id, 0) + segundos
    await ctx.send(f"✅ {segundos} segundos adicionados a {member.display_name}. Total agora: {ranking[member.id]} s")

@bot.command()
async def pomodoro(ctx, estudo:int, descanso:int):
    member = ctx.author
    guild_id = ctx.guild.id

    if member.id in tempos_de_estudo:
        if guild_id in pomodoro_tasks:
            await ctx.send("Já existe um pomodoro rolando.")
            return

        task = asyncio.create_task(run_pomodoro(ctx, estudo, descanso))
        pomodoro_tasks[guild_id] = task
        await ctx.send(f"Pomodoro iniciado: {estudo}m estudo / {descanso}m descanso!")
        await asyncio.sleep(1)

    else:
        await ctx.send("Você precisa estar estudando para iniciar um pomodoro, entre na chamada de estudos e tente novamente.")


async def run_pomodoro(ctx, estudo, descanso):
    pomodoros_round = 1

    guild_id = ctx.guild.id


    try:
        while guild_id in pomodoro_tasks:
            embed = Embed(
                title=f"📚 Rodada {pomodoros_round}",  # título do card
                description=f"Hora de focar! ⏳",  # descrição opcional
                color=0x00ff00  # cor verde
            )
            embed.add_field(name="Estudo", value=f"{estudo} minutos", inline=True)
            await ctx.send(embed=embed)

            await asyncio.sleep(estudo*1)
            await ctx.send(f"Parabéns, a rodada {pomodoros_round} acabou! Descanse por {descanso} minutos!")
            embed2 = Embed(
                title=f"Descanse!",
                description="Hora da Pausa",
                color=0xff0000
            )
            embed2.add_field(name="Descanso", value=f"{descanso} minutos", inline=True)
            await ctx.send(embed=embed2)
            await asyncio.sleep(descanso*1)
            await ctx.send("Intervalo acabou! Vamos voltar aos estudos!")
            
            pomodoros_round = pomodoros_round + 1

    finally:
        pomodoro_tasks.pop(guild_id, None)

# Inicia o servidor web em segundo plano
keep_alive()

bot.run(TOKEN)