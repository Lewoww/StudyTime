# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

import discord
from discord.ext import commands
import time
import asyncio
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

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


# Teste inicial de conexão
try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT NOW();")
    print("✅ Banco conectado com sucesso:", cur.fetchone())
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Falha ao conectar: {e}")

# Discord setup
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

# Atualizar tempo de estudo no banco
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
        print(f"✅ Tempo atualizado para {nome} ({tempo}s)")
    except Exception as e:
        print(f"⚠️ Erro ao atualizar tempo: {e}")

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
        await text_channel.send(f"{member.display_name} começou a estudar! 📚")

    # Saiu do canal studytime
    if before.channel == voice_channel and (after.channel != voice_channel):
        total_study_time = 0

        # Se o membro estava estudando (não pausado)
        if member.id in tempos_de_estudo:
            start = tempos_de_estudo.pop(member.id)
            finish = time.time()
            total_study_time += int(finish - start)

        # Se o membro estava pausado (mas tinha tempo acumulado)
        if member.id in tempos_pausados:
            total_study_time += tempos_pausados.pop(member.id)

        # Se houver tempo a registrar
        if total_study_time > 0:
            ranking[member.id] = ranking.get(member.id, 0) + total_study_time
            await text_channel.send(
                f"⏳ {member.display_name} estudou por {format_tempo(total_study_time)}!"
            )
            await update_study_time(member.id, guild_id, member.display_name, total_study_time)


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

        msg = "**🏆 Melhores Estudantes**\n"
        for i, row in enumerate(rows, start=1):
            nome = row["user_name"]
            total = row["total_time"]
            horas = total // 3600
            minutos = (total % 3600) // 60
            segundos = total % 60
            msg += f"{i}. {nome} — {horas}h {minutos}m {segundos}s\n"

        await ctx.send(msg)

    except Exception as e:
        await ctx.send(f"⚠️ Erro ao acessar o banco: {e}")

tempos_de_estudo = {}
tempos_pausados = {}


@bot.command()
async def pause(ctx):
    member = ctx.author
    if member.id in tempos_de_estudo:
        start = tempos_de_estudo.pop(member.id)
        elapsed = int(time.time() - start)
        tempos_pausados[member.id] = tempos_pausados.get(member.id, 0) + elapsed
        await ctx.send(f"⏸️ {member.display_name} pausou o estudo ({format_tempo(elapsed)} acumulado).")
    else:
        await ctx.send("⚠️ Você não está estudando agora.")

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

bot.run(TOKEN)
