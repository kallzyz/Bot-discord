import os
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True

CONFIGS_SERVIDOR = {}

class MeuBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands sincronizados globalmente!")
        bot.loop.create_task(start_web_server())

bot = MeuBot()

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="estermanagement.gg"))

# Comando manual para forçar sincronização caso sumam
@bot.tree.command(name="sync", description="Sincroniza os comandos slash do bot (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def sync_commands(interaction: discord.Interaction):
    await bot.tree.sync()
    await interaction.response.send_message("✅ Comandos sincronizados com sucesso!", ephemeral=True)

# ==========================================
# REACTION ROLES (CARGOS POR REAÇÃO)
# ==========================================
@bot.event
async def on_raw_reaction_add(payload):
    if payload.member and payload.member.bot:
        return
    guild_id = str(payload.guild_id)
    config = CONFIGS_SERVIDOR.get(guild_id, {})
    reaction_rules = config.get("reaction_roles", [])
    
    for rule in reaction_rules:
        if str(rule.get("message_id")) == str(payload.message_id):
            emoji_str = str(payload.emoji)
            if emoji_str == rule.get("emoji"):
                guild = bot.get_guild(payload.guild_id)
                if guild:
                    role = guild.get_role(int(rule.get("role_id")))
                    member = guild.get_member(payload.user_id)
                    if role and member:
                        try:
                            await member.add_roles(role, reason="Cargo por Reação")
                        except Exception as e:
                            print(f"Erro ao dar cargo por reação: {e}")

@bot.event
async def on_raw_reaction_remove(payload):
    guild_id = str(payload.guild_id)
    config = CONFIGS_SERVIDOR.get(guild_id, {})
    reaction_rules = config.get("reaction_roles", [])
    
    for rule in reaction_rules:
        if str(rule.get("message_id")) == str(payload.message_id):
            emoji_str = str(payload.emoji)
            if emoji_str == rule.get("emoji"):
                guild = bot.get_guild(payload.guild_id)
                if guild:
                    role = guild.get_role(int(rule.get("role_id")))
                    member = guild.get_member(payload.user_id)
                    if role and member:
                        try:
                            await member.remove_roles(role, reason="Remoção de Cargo por Reação")
                        except Exception as e:
                            print(f"Erro ao remover cargo por reação: {e}")

# ==========================================
# EVENTOS DE ENTRADA E SAÍDA
# ==========================================
def substituir_variaveis(texto, member):
    if not texto: return ""
    return (texto.replace("{user}", member.mention)
                 .replace("{username}", member.name)
                 .replace("{server}", member.guild.name)
                 .replace("{member_count}", str(member.guild.member_count)))

@bot.event
async def on_member_join(member):
    config = CONFIGS_SERVIDOR.get(str(member.guild.id), {})
    if not config.get("welcome_ativo", False): return
    canal = member.guild.get_channel(int(config.get("welcome_canal", 0) or 0))
    if not canal: return

    titulo = substituir_variaveis(config.get("welcome_titulo", ""), member)
    descricao = substituir_variaveis(config.get("welcome_descricao", ""), member)
    embed = discord.Embed(title=titulo if titulo else None, description=descricao)
    if config.get("welcome_cor"):
        try: embed.color = discord.Color(int(config.get("welcome_cor").replace("#", ""), 16))
        except: embed.color = discord.Color.green()
    if config.get("welcome_thumb"): embed.set_thumbnail(url=substituir_variaveis(config.get("welcome_thumb"), member))
    if config.get("welcome_imagem"): embed.set_image(url=substituir_variaveis(config.get("welcome_imagem"), member))
    if config.get("welcome_rodape"): embed.set_footer(text=substituir_variaveis(config.get("welcome_rodape"), member))
    
    try: await canal.send(content=substituir_variaveis(config.get("welcome_mensagem", ""), member) or None, embed=embed)
    except Exception as e: print(f"Erro welcome: {e}")

@bot.event
async def on_member_remove(member):
    config = CONFIGS_SERVIDOR.get(str(member.guild.id), {})
    if not config.get("leave_ativo", False): return
    canal = member.guild.get_channel(int(config.get("leave_canal", 0) or 0))
    if not canal: return

    titulo = substituir_variaveis(config.get("leave_titulo", ""), member)
    descricao = substituir_variaveis(config.get("leave_descricao", ""), member)
    embed = discord.Embed(title=titulo if titulo else None, description=descricao)
    if config.get("leave_cor"):
        try: embed.color = discord.Color(int(config.get("leave_cor").replace("#", ""), 16))
        except: embed.color = discord.Color.red()
    if config.get("leave_thumb"): embed.set_thumbnail(url=substituir_variaveis(config.get("leave_thumb"), member))
    if config.get("leave_imagem"): embed.set_image(url=substituir_variaveis(config.get("leave_imagem"), member))
    if config.get("leave_rodape"): embed.set_footer(text=substituir_variaveis(config.get("leave_rodape"), member))
    
    try: await canal.send(content=substituir_variaveis(config.get("leave_mensagem", ""), member) or None, embed=embed)
    except Exception as e: print(f"Erro leave: {e}")

# ==========================================
# API INTERNA AIOHTTP
# ==========================================
async def handle_get_guildas(request):
    user_guild_ids = request.query.getall('guilds[]', [])
    dados_guildas = []
    for guild in bot.guilds:
        guild_id = str(guild.id)
        if user_guild_ids and guild_id not in user_guild_ids: continue

        canais = [{"id": str(c.id), "nome": c.name} for c in guild.text_channels]
        cargos = [{"id": str(r.id), "nome": r.name} for r in guild.roles if not r.is_default()]
        
        if guild_id not in CONFIGS_SERVIDOR:
            CONFIGS_SERVIDOR[guild_id] = {
                "cargos_permitidos": [], "usuarios_permitidos": [], "canais_proibidos": [],
                "armadilha_canal": "", "armadilha_acao": "nenhuma", "armadilha_tempo": 10,
                "welcome_ativo": False, "welcome_canal": "", "welcome_mensagem": "", "welcome_titulo": "", "welcome_descricao": "", "welcome_cor": "5865F2", "welcome_thumb": "", "welcome_imagem": "", "welcome_rodape": "",
                "leave_ativo": False, "leave_canal": "", "leave_mensagem": "", "leave_titulo": "", "leave_descricao": "", "leave_cor": "da373c", "leave_thumb": "", "leave_imagem": "", "leave_rodape": "",
                "reaction_roles": []
            }

        dados_guildas.append({
            "id": guild_id, "nome": guild.name,
            "icone": str(guild.icon.url) if guild.icon else "https://cdn.discordapp.com/embed/avatars/0.png",
            "canais": canais, "cargos": cargos, "config": CONFIGS_SERVIDOR[guild_id]
        })
    return web.json_response(dados_guildas)

async def handle_salvar_config(request):
    data = await request.json()
    guild_id = data.get("guild_id")
    if guild_id in CONFIGS_SERVIDOR:
        CONFIGS_SERVIDOR[guild_id].update(data)
        return web.json_response({"status": "sucesso"})
    return web.json_response({"status": "erro"}, status=400)

async def handle_web_embed(request):
    data = await request.json()
    canal = bot.get_channel(int(data.get("canal_id"))) or await bot.fetch_channel(int(data.get("canal_id")))
    if not canal: return web.json_response({"status": "erro", "mensagem": "Canal não encontrado."}, status=400)

    embed = discord.Embed(title=data.get("titulo"), description=data.get("descricao").replace("\\n", "\n"))
    if data.get("cor_hex"):
        try: embed.color = discord.Color(int(data.get("cor_hex").replace("#", ""), 16))
        except: embed.color = discord.Color.blue()
    if data.get("titulo_url"): embed.url = data.get("titulo_url")
    if data.get("autor_nome"): embed.set_author(name=data.get("autor_nome"), icon_url=data.get("autor_icone") or None)
    if data.get("thumbnail"): embed.set_thumbnail(url=data.get("thumbnail"))
    if data.get("imagem_grande"): embed.set_image(url=data.get("imagem_grande"))
    embed.set_footer(text=data.get("rodape") or "Delaware Manager", icon_url=data.get("footer_icon") or None)
    if data.get("modo_data") == "atual": embed.timestamp = datetime.datetime.now()

    sent_msg = await canal.send(embed=embed)
    
    if data.get("rr_emoji") and data.get("rr_role_id"):
        guild_id = str(canal.guild.id)
        await sent_msg.add_reaction(data.get("rr_emoji"))
        if guild_id in CONFIGS_SERVIDOR:
            CONFIGS_SERVIDOR[guild_id]["reaction_roles"].append({
                "message_id": str(sent_msg.id),
                "emoji": data.get("rr_emoji"),
                "role_id": data.get("rr_role_id")
            })

    return web.json_response({"status": "sucesso"})

async def start_web_server():
    app = web.Application()
    app.router.add_get('/api/guildas', handle_get_guildas)
    app.router.add_post('/api/salvar-config', handle_salvar_config)
    app.router.add_post('/enviar-embed', handle_web_embed)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 8080)
    await site.start()

bot.run(TOKEN)