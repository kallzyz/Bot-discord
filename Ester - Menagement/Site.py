import os
from flask import Flask, render_template_string, request, redirect, session, url_for
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "chave_secreta_padrao_super_segura")

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:5000/callback"
API_ENDPOINT = "https://discord.com/api/v10"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Painel de Controle • Delaware Bot</title>
    <style>
        :root {
            --bg-base: #0b0c10;
            --bg-sidebar: rgba(20, 21, 26, 0.65);
            --bg-card: rgba(26, 28, 36, 0.55);
            --bg-card-hover: rgba(32, 35, 45, 0.65);
            --bg-input: rgba(15, 16, 20, 0.5);
            --border-glass: rgba(255, 255, 255, 0.08);
            --border-glass-focus: rgba(88, 101, 242, 0.5);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --accent: #5865F2;
            --accent-hover: #4752c4;
            --shadow-subtle: 0 10px 30px 0 rgba(0, 0, 0, 0.4);
            --shadow-floating: 0 20px 40px rgba(0, 0, 0, 0.5);
        }

        /* SCROLLBAR CUSTOMIZADA (TRANSLÚCIDA COM INDICADOR ROXO) */
        * {
            scrollbar-width: thin;
            scrollbar-color: rgba(138, 43, 226, 0.6) rgba(255, 255, 255, 0.02);
        }
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.02);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(138, 43, 226, 0.6);
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(138, 43, 226, 0.9);
        }

        body { 
            background: var(--bg-base); 
            color: var(--text-main); 
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, sans-serif; 
            margin: 0; 
            display: flex; 
            height: 100vh; 
            overflow: hidden; 
            -webkit-font-smoothing: antialiased;
            position: relative;
            box-sizing: border-box;
            padding: 20px;
            gap: 20px;
        }

        /* GLOW ROXO NO CENTRO INFERIOR */
        body::before {
            content: '';
            position: absolute;
            bottom: -150px;
            left: 50%;
            transform: translateX(-50%);
            width: 700px;
            height: 350px;
            background: radial-gradient(circle, rgba(138, 43, 226, 0.25) 0%, rgba(88, 101, 242, 0.08) 50%, transparent 80%);
            filter: blur(80px);
            z-index: 0;
            pointer-events: none;
        }
        
        .sidebar { 
            width: 270px; 
            background: var(--bg-sidebar); 
            backdrop-filter: blur(25px); 
            -webkit-backdrop-filter: blur(25px);
            display: flex; 
            flex-direction: column; 
            border: 1px solid var(--border-glass); 
            border-radius: 20px;
            z-index: 10;
            box-shadow: var(--shadow-floating);
            overflow: hidden;
        }

        /* SELETOR DE SERVIDOR INTEGRADO AO HEADER */
        .sidebar-header-wrapper {
            position: relative;
            border-bottom: 1px solid var(--border-glass);
            background: rgba(255, 255, 255, 0.02);
        }
        .sidebar-header { 
            padding: 18px 16px; 
            font-weight: 600; 
            font-size: 14px; 
            color: #fff; 
            display: flex; 
            align-items: center; 
            gap: 10px; 
            cursor: pointer;
            user-select: none;
            transition: background 0.2s;
        }
        .sidebar-header:hover {
            background: rgba(255, 255, 255, 0.04);
        }
        .sidebar-header img { width: 34px; height: 34px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
        .sidebar-header .server-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
        .sidebar-header .arrow-icon { font-size: 11px; color: var(--text-muted); transition: transform 0.2s; }
        .sidebar-header.open .arrow-icon { transform: rotate(180deg); }

        /* MENU SUSPENSO DE SERVIDORES */
        .server-dropdown-menu {
            position: absolute;
            top: 100%;
            left: 10px;
            right: 10px;
            background: rgba(20, 21, 26, 0.95);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--border-glass);
            border-radius: 14px;
            margin-top: 6px;
            box-shadow: var(--shadow-floating);
            display: none;
            flex-direction: column;
            gap: 4px;
            padding: 6px;
            z-index: 100;
            max-height: 260px;
            overflow-y: auto;
        }
        .server-dropdown-menu.active { display: flex; }
        .server-dropdown-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            border-radius: 10px;
            text-decoration: none;
            color: var(--text-muted);
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .server-dropdown-item:hover {
            background: rgba(255, 255, 255, 0.06);
            color: #fff;
        }
        .server-dropdown-item.active {
            background: var(--accent);
            color: #fff;
        }
        .server-dropdown-item img {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            object-fit: cover;
        }

        .sidebar-nav { flex: 1; padding: 16px 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; }
        .nav-section-title { font-size: 11px; font-weight: 700; color: #6b7280; padding: 10px 10px 6px 10px; text-transform: uppercase; letter-spacing: 0.8px; }
        .nav-item { display: flex; align-items: center; gap: 12px; padding: 11px 14px; color: var(--text-muted); text-decoration: none; border-radius: 12px; font-weight: 500; font-size: 14px; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); }
        .nav-item:hover { background: rgba(255, 255, 255, 0.05); color: var(--text-main); }
        .nav-item.active { background: var(--accent); color: #fff; box-shadow: 0 4px 14px rgba(88, 101, 242, 0.4); }

        .sidebar-footer { padding: 16px; background: rgba(15, 16, 20, 0.4); display: flex; align-items: center; justify-content: space-between; border-top: 1px solid var(--border-glass); }
        .user-mini { display: flex; align-items: center; gap: 10px; font-size: 13px; font-weight: 500; color: #fff; }
        .user-mini img { width: 34px; height: 34px; border-radius: 50%; object-fit: cover; }

        .main-content { 
            flex: 1; 
            display: flex; 
            background: var(--bg-sidebar); 
            backdrop-filter: blur(25px); 
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid var(--border-glass);
            border-radius: 20px;
            overflow: hidden;
            z-index: 10;
            box-shadow: var(--shadow-floating);
            position: relative;
        }
        .content-container { flex: 1; padding: 40px; padding-bottom: 90px; max-width: 920px; overflow-y: auto; box-sizing: border-box; z-index: 1; }
        
        .preview-pane { width: 380px; background: rgba(15, 16, 20, 0.4); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-left: 1px solid var(--border-glass); padding: 30px; box-sizing: border-box; display: none; z-index: 1; overflow-y: auto; }
        .preview-pane.active { display: block; }

        h2 { color: #ffffff; margin-top: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.5px; }
        p.subtitle { color: var(--text-muted); font-size: 14px; margin-bottom: 30px; line-height: 1.5; }
        
        label { display: block; margin-top: 20px; font-weight: 600; color: var(--text-main); font-size: 13px; letter-spacing: 0.2px; }
        .input-desc { font-size: 11px; color: var(--text-muted); margin-top: 3px; margin-bottom: 6px; line-height: 1.3; }

        input, textarea, select { width: 100%; padding: 12px 14px; margin-top: 4px; background: var(--bg-input); border: 1px solid var(--border-glass); color: #fff; border-radius: 12px; box-sizing: border-box; font-size: 14px; outline: none; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: inset 0 1px 2px rgba(0,0,0,0.2); }
        input:focus, textarea:focus, select:focus { border-color: var(--border-glass-focus); box-shadow: 0 0 0 3px rgba(88, 101, 242, 0.2), inset 0 1px 2px rgba(0,0,0,0.2); }
        textarea { resize: vertical; height: 100px; }

        .row { display: flex; gap: 16px; }
        .col { flex: 1; }
        .color-group { display: flex; gap: 10px; align-items: center; margin-top: 4px; }
        .color-group input[type="color"] { width: 48px; height: 46px; padding: 2px; border: 1px solid var(--border-glass); border-radius: 12px; cursor: pointer; background: var(--bg-input); }

        .msg-sucesso { background: rgba(46, 160, 67, 0.15); border: 1px solid rgba(46, 160, 67, 0.4); color: #3fb950; padding: 14px; text-align: center; border-radius: 12px; margin-bottom: 24px; font-weight: 600; backdrop-filter: blur(10px); }
        .msg-erro { background: rgba(248, 81, 73, 0.15); border: 1px solid rgba(248, 81, 73, 0.4); color: #f85149; padding: 14px; text-align: center; border-radius: 12px; margin-bottom: 24px; font-weight: 600; backdrop-filter: blur(10px); }
        
        .card-toggle { display: flex; align-items: center; justify-content: space-between; background: var(--bg-card); backdrop-filter: blur(10px); padding: 18px 22px; border-radius: 14px; margin-top: 16px; border: 1px solid var(--border-glass); box-shadow: var(--shadow-subtle); }
        .card-toggle span { font-weight: 600; color: #fff; font-size: 15px; }
        
        .switch { position: relative; display: inline-block; width: 50px; height: 28px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(255, 255, 255, 0.15); transition: .3s cubic-bezier(0.4, 0, 0.2, 1); border-radius: 28px; border: 1px solid var(--border-glass); }
        .slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 3px; bottom: 3px; background-color: white; transition: .3s cubic-bezier(0.4, 0, 0.2, 1); border-radius: 50%; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        input:checked + .slider { background-color: var(--accent); border-color: var(--accent); }
        input:checked + .slider:before { transform: translateX(22px); }

        /* CONTAINERS EXPANSÍVEIS (ACCORDION ESTILO iOS) */
        .accordion-container { background: var(--bg-card); backdrop-filter: blur(10px); border: 1px solid var(--border-glass); border-radius: 16px; margin-top: 18px; overflow: hidden; box-shadow: var(--shadow-subtle); transition: border-color 0.2s; }
        .accordion-container:hover { border-color: rgba(255, 255, 255, 0.12); }
        .accordion-header { padding: 18px 22px; font-weight: 600; color: #fff; font-size: 15px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; background: transparent; transition: background 0.2s; }
        .accordion-header:hover { background: rgba(255, 255, 255, 0.03); }
        .accordion-content { padding: 22px; border-top: 1px solid var(--border-glass); background: rgba(15, 16, 20, 0.3); display: none; }
        .accordion-content.open { display: block; }

        /* BALÕES DE CARGOS COM GLOW */
        .role-picker-container { margin-top: 10px; }
        .role-input-row { display: flex; gap: 12px; margin-bottom: 12px; }
        
        .role-badges-box { display: flex; flex-wrap: wrap; gap: 8px; min-height: 46px; background: var(--bg-input); border: 1px solid var(--border-glass); border-radius: 12px; padding: 12px; box-sizing: border-box; box-shadow: inset 0 1px 2px rgba(0,0,0,0.2); }
        .role-badge { 
            display: inline-flex; 
            align-items: center; 
            gap: 8px; 
            padding: 6px 14px; 
            border-radius: 20px; 
            font-size: 13px; 
            font-weight: 600; 
            background: rgba(24, 25, 28, 0.8); 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 4px 12px var(--badge-glow, rgba(88, 101, 242, 0.2));
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .role-badge:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px var(--badge-glow, rgba(88, 101, 242, 0.35));
        }
        .role-badge-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px currentColor; }
        .role-badge-remove { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 15px; font-weight: bold; padding: 0; display: flex; align-items: center; transition: color 0.2s; }
        .role-badge-remove:hover { color: #f85149; }

        .discord-message { display: flex; gap: 14px; margin-top: 20px; background: rgba(20, 21, 25, 0.4); padding: 16px; border-radius: 14px; border: 1px solid var(--border-glass); }
        .discord-avatar { width: 42px; height: 42px; border-radius: 50%; background: var(--accent); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; flex-shrink: 0; box-shadow: 0 4px 12px rgba(88, 101, 242, 0.4); }
        .discord-content { flex: 1; overflow: hidden; }
        .discord-username { color: #f3f4f6; font-weight: 600; font-size: 14px; display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
        .discord-bot-tag { background: var(--accent); color: white; font-size: 9px; padding: 2px 5px; border-radius: 4px; font-weight: 700; letter-spacing: 0.5px; }
        .discord-embed { display: flex; margin-top: 8px; max-width: 100%; border-radius: 8px; background: rgba(24, 25, 28, 0.7); border-left: 4px solid var(--accent); box-shadow: 0 4px 16px rgba(0,0,0,0.2); }
        .discord-embed-inner { padding: 12px 16px; width: 100%; box-sizing: border-box; }
        .embed-title { color: #f3f4f6; font-weight: 700; font-size: 15px; margin-bottom: 6px; display: block; text-decoration: none; }
        .embed-desc { color: #d1d5db; font-size: 13px; white-space: pre-wrap; word-break: break-word; line-height: 1.4; }

        .btn-login { background: var(--accent); color: white; padding: 14px 28px; border-radius: 14px; text-decoration: none; font-weight: 600; display: inline-block; box-shadow: 0 4px 14px rgba(88, 101, 242, 0.4); transition: all 0.2s; }
        .btn-login:hover { background: var(--accent-hover); transform: translateY(-1px); }
        .btn-logout { color: #f85149; text-decoration: none; font-weight: 600; font-size: 13px; transition: opacity 0.2s; }
        .btn-logout:hover { opacity: 0.8; }
        
        .variaveis-box { background: rgba(16, 17, 20, 0.5); padding: 14px; border-radius: 12px; margin-top: 18px; font-size: 12px; color: var(--text-muted); border: 1px dashed var(--border-glass); }
        .variaveis-box code { background: rgba(255, 255, 255, 0.08); color: #fff; padding: 3px 6px; border-radius: 6px; font-weight: 600; font-family: ui-monospace, monospace; }

        /* POPUP FLUTUANTE DE ALTERAÇÕES NÃO SALVAS */
        .save-bar-popup {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: rgba(20, 21, 26, 0.9);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid var(--border-glass);
            padding: 14px 24px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            gap: 24px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.6);
            z-index: 1000;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .save-bar-popup.visible {
            transform: translateX(-50%) translateY(0);
        }
        .save-bar-text {
            color: var(--text-main);
            font-size: 14px;
            font-weight: 500;
        }
        .save-bar-actions {
            display: flex;
            gap: 10px;
        }
        .btn-discard {
            background: rgba(255, 255, 255, 0.06);
            color: var(--text-muted);
            border: 1px solid var(--border-glass);
            padding: 8px 16px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-discard:hover {
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
        }
        .btn-popup-save {
            background: #2ea043;
            color: white;
            border: none;
            padding: 8px 18px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 4px 12px rgba(46, 160, 67, 0.3);
        }
        .btn-popup-save:hover {
            background: #238636;
        }
    </style>
</head>
<body>

    {% if not user %}
        <div style="display: flex; justify-content: center; align-items: center; width: 100%; height: 100vh; flex-direction: column; text-align: center; padding: 20px; z-index: 10;">
            <h2>Painel de Gerenciamento • Delaware Bot</h2>
            <p style="color: var(--text-muted); margin-bottom: 24px; max-width: 400px;">Faça login com sua conta do Discord para gerenciar os servidores com um painel moderno e fluido.</p>
            <a href="/login" class="btn-login">🔑 Entrar com Discord</a>
        </div>
    {% else %}
        <div class="sidebar">
            <div class="sidebar-header-wrapper">
                <div class="sidebar-header" id="server-header-toggle" onclick="toggleServerMenu(event)">
                    <img src="{{ guild_atual.icone if guild_atual else 'https://cdn.discordapp.com/embed/avatars/0.png' }}" alt="Ícone">
                    <span class="server-name">{{ guild_atual.nome if guild_atual else 'Selecionar' }}</span>
                    <span class="arrow-icon">▼</span>
                </div>

                <div class="server-dropdown-menu" id="server-dropdown">
                    {% for g in guildas %}
                        <a href="?guild={{ g.id }}&tab={{ tab }}" class="server-dropdown-item {% if g.id == guild_id_atual %}active{% endif %}">
                            <img src="{{ g.icone if g.icone else 'https://cdn.discordapp.com/embed/avatars/0.png' }}" alt="Ícone">
                            <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ g.nome }}</span>
                        </a>
                    {% endfor %}
                </div>
            </div>

            <div class="sidebar-nav">
                <div class="nav-section-title">Módulos</div>
                <a href="?guild={{ guild_id_atual }}&tab=embed" class="nav-item {% if tab == 'embed' %}active{% endif %}">🎨 Criador de Embed</a>
                <a href="?guild={{ guild_id_atual }}&tab=welcome_leave" class="nav-item {% if tab == 'welcome_leave' %}active{% endif %}">👋 Entradas/Saídas</a>
                <a href="?guild={{ guild_id_atual }}&tab=reaction_roles" class="nav-item {% if tab == 'reaction_roles' %}active{% endif %}">⭐ Cargos por Reação</a>
                <a href="?guild={{ guild_id_atual }}&tab=permissoes" class="nav-item {% if tab == 'permissoes' %}active{% endif %}">🔒 Permissões</a>
                <a href="?guild={{ guild_id_atual }}&tab=armadilha" class="nav-item {% if tab == 'armadilha' %}active{% endif %}">🪤 Canal Armadilha</a>
            </div>

            <div class="sidebar-footer">
                <div class="user-mini">
                    <img src="{{ user.avatar_url }}" alt="Avatar">
                    <span style="overflow: hidden; text-overflow: ellipsis; max-width: 130px;">{{ user.username }}</span>
                </div>
                <a href="/logout" class="btn-logout">Sair</a>
            </div>
        </div>

        <div class="main-content">
            <div class="content-container">

                {% if status == 'sucesso' %}
                    <div class="msg-sucesso">✅ Alterações salvas com sucesso!</div>
                {% elif status == 'erro' %}
                    <div class="msg-erro">❌ Erro ao processar requisição.</div>
                {% endif %}

                <form method="POST" id="main-config-form">
                    <input type="hidden" name="acao" id="form-acao-input" value="{% if tab == 'embed' %}embed{% elif tab == 'welcome_leave' %}welcome_leave{% elif tab == 'reaction_roles' %}reaction_roles{% elif tab == 'permissoes' %}config{% elif tab == 'armadilha' %}armadilha{% endif %}">

                    <!-- ABA 1: EMBED -->
                    {% if tab == 'embed' %}
                        <h2>Criador e Enviador de Embed</h2>
                        <p class="subtitle">Envie mensagens customizadas em formato Embed diretamente para os canais do seu servidor.</p>
                        
                        <label>Canal de Destino:</label>
                        <div class="input-desc">Canal onde o bot enviará a mensagem embed formatada.</div>
                        <select name="canal_id" required>
                            {% if guild_atual %}
                                {% for c in guild_atual.canais %}
                                    <option value="{{ c.id }}"># {{ c.nome }}</option>
                                {% endfor %}
                            {% endif %}
                        </select>

                        <div class="row">
                            <div class="col">
                                <label>Author Name:</label>
                                <div class="input-desc">Nome exibido no topo do embed.</div>
                                <input type="text" id="input-autor" name="autor_nome" oninput="atualizarPreviewGeneric()">
                            </div>
                            <div class="col">
                                <label>Author Icon URL:</label>
                                <div class="input-desc">URL da imagem ao lado do nome do autor.</div>
                                <input type="text" id="input-autor-icone" name="autor_icone" oninput="atualizarPreviewGeneric()">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col">
                                <label>Título:</label>
                                <div class="input-desc">Título principal da mensagem.</div>
                                <input type="text" id="input-titulo" name="titulo" oninput="atualizarPreviewGeneric()" required>
                            </div>
                            <div class="col">
                                <label>Título URL:</label>
                                <div class="input-desc">Transforma o título em um link clicable.</div>
                                <input type="text" id="input-titulo-url" name="titulo_url" oninput="atualizarPreviewGeneric()">
                            </div>
                        </div>

                        <label>Descrição:</label>
                        <div class="input-desc">Texto principal do embed. Suporta quebras de linha.</div>
                        <textarea id="input-desc" name="descricao" oninput="atualizarPreviewGeneric()" required></textarea>

                        <div class="row">
                            <div class="col">
                                <label>Cor Hex:</label>
                                <div class="input-desc">Cor da barra lateral do embed.</div>
                                <div class="color-group">
                                    <input type="color" id="color-picker" value="#5865F2" onchange="sincronizarHex(this.value)">
                                    <input type="text" id="cor-input" name="cor_hex" value="5865F2" oninput="sincronizarPicker(this.value)">
                                </div>
                            </div>
                            <div class="col">
                                <label>Thumbnail URL:</label>
                                <div class="input-desc">Imagem pequena exibida no canto superior direito.</div>
                                <input type="text" id="input-thumb" name="thumbnail" oninput="atualizarPreviewGeneric()">
                            </div>
                        </div>

                        <label>Imagem Grande:</label>
                        <div class="input-desc">Imagem em destaque exibida na parte inferior do embed.</div>
                        <input type="text" id="input-imagem" name="imagem_grande" oninput="atualizarPreviewGeneric()">

                        <div class="row">
                            <div class="col">
                                <label>Rodapé:</label>
                                <div class="input-desc">Texto pequeno exibido no rodapé do embed.</div>
                                <input type="text" id="input-rodape" name="rodape" oninput="atualizarPreviewGeneric()">
                            </div>
                            <div class="col">
                                <label>Ícone Rodapé:</label>
                                <div class="input-desc">Mini ícone exibido ao lado do texto do rodapé.</div>
                                <input type="text" id="input-footer-icon" name="footer_icon" oninput="atualizarPreviewGeneric()">
                            </div>
                        </div>

                        <label>Modo de Data:</label>
                        <div class="input-desc">Define se exibe o carimbo de data/hora atual no rodapé.</div>
                        <select name="modo_data"><option value="atual">Atual</option><option value="nenhuma">Nenhuma</option></select>

                    <!-- ABA 2: ENTRADAS / SAÍDAS -->
                    {% elif tab == 'welcome_leave' %}
                        <h2>Gerenciamento de Entradas e Saídas</h2>
                        <p class="subtitle">Configure mensagens automáticas de boas-vindas e despedidas em containers expansíveis.</p>
                        
                        <!-- CONTAINER 1: BOAS-VINDAS -->
                        <div class="accordion-container">
                            <div class="accordion-header" onclick="toggleAccordion(this)">
                                <span>👋 Mensagens de Boas-Vindas</span>
                                <span>▼</span>
                            </div>
                            <div class="accordion-content">
                                <div class="card-toggle" style="margin-top: 0;">
                                    <span>Ativar Boas-Vindas</span>
                                    <label class="switch">
                                        <input type="checkbox" name="welcome_ativo" value="1" {% if guild_atual and guild_atual.config.welcome_ativo %}checked{% endif %}>
                                        <span class="slider"></span>
                                    </label>
                                </div>

                                <label>Canal de Entrada:</label>
                                <div class="input-desc">Canal onde o aviso de boas-vindas será postado.</div>
                                <select name="welcome_canal">
                                    <option value="">Selecione um canal...</option>
                                    {% if guild_atual %}
                                        {% for c in guild_atual.canais %}
                                            <option value="{{ c.id }}" {% if guild_atual.config.welcome_canal == c.id %}selected{% endif %}># {{ c.nome }}</option>
                                        {% endfor %}
                                    {% endif %}
                                </select>

                                <label>Texto Simples:</label>
                                <div class="input-desc">Mensagem enviada fora do embed (ex: menção ao usuário).</div>
                                <input type="text" name="welcome_mensagem" id="input-welcome-msg" value="{{ guild_atual.config.welcome_mensagem if guild_atual else '' }}" oninput="atualizarPreviewGeneric()">

                                <div class="row">
                                    <div class="col">
                                        <label>Título do Embed:</label>
                                        <div class="input-desc">Título da caixa de boas-vindas.</div>
                                        <input type="text" name="welcome_titulo" id="input-welcome-titulo" value="{{ guild_atual.config.welcome_titulo if guild_atual else '' }}" oninput="atualizarPreviewGeneric()">
                                    </div>
                                    <div class="col">
                                        <label>Cor Hex:</label>
                                        <div class="input-desc">Cor lateral do embed.</div>
                                        <input type="text" name="welcome_cor" id="input-welcome-cor" value="{{ guild_atual.config.welcome_cor if guild_atual else '5865F2' }}" oninput="atualizarPreviewGeneric()">
                                    </div>
                                </div>

                                <label>Descrição do Embed:</label>
                                <div class="input-desc">Texto principal de boas-vindas dentro da caixa.</div>
                                <textarea name="welcome_descricao" id="input-welcome-desc" oninput="atualizarPreviewGeneric()">{{ guild_atual.config.welcome_descricao if guild_atual else '' }}</textarea>

                                <div class="row">
                                    <div class="col">
                                        <label>Thumbnail URL:</label>
                                        <div class="input-desc">Mini imagem no canto superior direito.</div>
                                        <input type="text" name="welcome_thumb" id="input-welcome-thumb" value="{{ guild_atual.config.welcome_thumb if guild_atual else '' }}">
                                    </div>
                                    <div class="col">
                                        <label>Imagem URL:</label>
                                        <div class="input-desc">Banner grande no rodapé do embed.</div>
                                        <input type="text" name="welcome_imagem" id="input-welcome-imagem" value="{{ guild_atual.config.welcome_imagem if guild_atual else '' }}">
                                    </div>
                                </div>

                                <label>Rodapé:</label>
                                <div class="input-desc">Texto informativo no rodapé.</div>
                                <input type="text" name="welcome_rodape" id="input-welcome-rodape" value="{{ guild_atual.config.welcome_rodape if guild_atual else '' }}">

                                <div class="variaveis-box">
                                    <b>Variáveis:</b> <code>{user}</code> • <code>{username}</code> • <code>{server}</code> • <code>{member_count}</code>
                                </div>
                            </div>
                        </div>

                        <!-- CONTAINER 2: DESPEDIDAS -->
                        <div class="accordion-container">
                            <div class="accordion-header" onclick="toggleAccordion(this)">
                                <span>📤 Mensagens de Despedida</span>
                                <span>▼</span>
                            </div>
                            <div class="accordion-content">
                                <div class="card-toggle" style="margin-top: 0;">
                                    <span>Ativar Despedidas</span>
                                    <label class="switch">
                                        <input type="checkbox" name="leave_ativo" value="1" {% if guild_atual and guild_atual.config.leave_ativo %}checked{% endif %}>
                                        <span class="slider"></span>
                                    </label>
                                </div>

                                <label>Canal de Saída:</label>
                                <div class="input-desc">Canal onde o aviso de saída será postado.</div>
                                <select name="leave_canal">
                                    <option value="">Selecione um canal...</option>
                                    {% if guild_atual %}
                                        {% for c in guild_atual.canais %}
                                            <option value="{{ c.id }}" {% if guild_atual.config.leave_canal == c.id %}selected{% endif %}># {{ c.nome }}</option>
                                        {% endfor %}
                                    {% endif %}
                                </select>

                                <label>Texto Simples:</label>
                                <div class="input-desc">Mensagem de texto simples enviada junto à saída.</div>
                                <input type="text" name="leave_mensagem" id="input-leave-msg" value="{{ guild_atual.config.leave_mensagem if guild_atual else '' }}" oninput="atualizarPreviewGeneric()">

                                <div class="row">
                                    <div class="col">
                                        <label>Título do Embed:</label>
                                        <div class="input-desc">Título da mensagem de despedida.</div>
                                        <input type="text" name="leave_titulo" id="input-leave-titulo" value="{{ guild_atual.config.leave_titulo if guild_atual else '' }}" oninput="atualizarPreviewGeneric()">
                                    </div>
                                    <div class="col">
                                        <label>Cor Hex:</label>
                                        <div class="input-desc">Cor lateral do embed de saída.</div>
                                        <input type="text" name="leave_cor" id="input-leave-cor" value="{{ guild_atual.config.leave_cor if guild_atual else 'da373c' }}" oninput="atualizarPreviewGeneric()">
                                    </div>
                                </div>

                                <label>Descrição do Embed:</label>
                                <div class="input-desc">Texto detalhado da saída do membro.</div>
                                <textarea name="leave_descricao" id="input-leave-desc" oninput="atualizarPreviewGeneric()">{{ guild_atual.config.leave_descricao if guild_atual else '' }}</textarea>

                                <div class="row">
                                    <div class="col">
                                        <label>Thumbnail URL:</label>
                                        <div class="input-desc">Mini imagem superior direita.</div>
                                        <input type="text" name="leave_thumb" id="input-leave-thumb" value="{{ guild_atual.config.leave_thumb if guild_atual else '' }}">
                                    </div>
                                    <div class="col">
                                        <label>Imagem URL:</label>
                                        <div class="input-desc">Banner grande inferior.</div>
                                        <input type="text" name="leave_imagem" id="input-leave-imagem" value="{{ guild_atual.config.leave_imagem if guild_atual else '' }}">
                                    </div>
                                </div>

                                <label>Rodapé:</label>
                                <div class="input-desc">Texto informativo no rodapé.</div>
                                <input type="text" name="leave_rodape" id="input-leave-rodape" value="{{ guild_atual.config.leave_rodape if guild_atual else '' }}">

                                <div class="variaveis-box">
                                    <b>Variáveis:</b> <code>{user}</code> • <code>{username}</code> • <code>{server}</code> • <code>{member_count}</code>
                                </div>
                            </div>
                        </div>

                    <!-- ABA 3: REACTION ROLES -->
                    {% elif tab == 'reaction_roles' %}
                        <h2>Cargos por Reação (Reaction Roles)</h2>
                        <p class="subtitle">Configure um embed completo de Reaction Roles selecionando cargos diretamente na lista.</p>
                        
                        <label>Canal onde o Bot enviará a Mensagem:</label>
                        <div class="input-desc">Canal onde o painel de reações ficará disponível.</div>
                        <select name="canal_id" required>
                            {% if guild_atual %}
                                {% for c in guild_atual.canais %}
                                    <option value="{{ c.id }}"># {{ c.nome }}</option>
                                {% endfor %}
                            {% endif %}
                        </select>

                        <div class="row" style="margin-top: 15px;">
                            <div class="col">
                                <label>Título do Embed:</label>
                                <div class="input-desc">Título principal do painel de cargos.</div>
                                <input type="text" name="titulo" id="input-rr-titulo" value="Escolha seus Cargos" oninput="atualizarPreviewGeneric()" required>
                            </div>
                            <div class="col">
                                <label>Cor Hex:</label>
                                <div class="input-desc">Cor da borda lateral.</div>
                                <input type="text" name="cor_hex" id="input-rr-cor" value="5865F2" oninput="atualizarPreviewGeneric()" required>
                            </div>
                        </div>

                        <label>Descrição do Embed:</label>
                        <div class="input-desc">Instruções exibidas aos membros no embed.</div>
                        <textarea name="descricao" id="input-rr-desc" oninput="atualizarPreviewGeneric()" required>Reaja abaixo para receber o cargo correspondente!</textarea>

                        <div class="row" style="margin-top: 10px;">
                            <div class="col">
                                <label>Thumbnail URL:</label>
                                <div class="input-desc">Mini imagem superior direita.</div>
                                <input type="text" name="thumbnail" id="input-rr-thumb" oninput="atualizarPreviewGeneric()">
                            </div>
                            <div class="col">
                                <label>Rodapé:</label>
                                <div class="input-desc">Texto do rodapé.</div>
                                <input type="text" name="rodape" id="input-rr-rodape" oninput="atualizarPreviewGeneric()">
                            </div>
                        </div>

                        <label style="margin-top: 20px;">Selecionar Cargo Disponível:</label>
                        <div class="input-desc">Associe um emoji a um cargo específico do servidor.</div>
                        <div class="role-picker-container">
                            <div class="role-input-row">
                                <input type="text" id="rr-emoji-input" placeholder="Emoji (Ex: 🔥 ou 👍)" style="flex: 1;">
                                <select id="rr-role-select" style="flex: 2;" onchange="adicionarCargoReactionDireto(this)">
                                    <option value="">Selecione um cargo para adicionar...</option>
                                    {% if guild_atual %}
                                        {% for r in guild_atual.cargos %}
                                            <option value="{{ r.id }}" data-name="{{ r.nome }}" data-color="{{ r.cor }}">@ {{ r.nome }}</option>
                                        {% endfor %}
                                    {% endif %}
                                </select>
                            </div>
                            <div class="role-badges-box" id="rr-badges-container">
                                <span style="color: var(--text-muted); font-size: 13px;" id="rr-empty-text">Nenhum cargo adicionado ainda.</span>
                            </div>
                            <input type="hidden" name="reaction_items_json" id="reaction_items_json" value="[]">
                        </div>

                    <!-- ABA 4: PERMISSÕES -->
                    {% elif tab == 'permissoes' %}
                        <h2>Permissões e Cargos Autorizados</h2>
                        <p class="subtitle">Gerencie quem tem autoridade selecionando diretamente na lista de cargos.</p>
                        
                        <label>Adicionar Cargo Autorizado:</label>
                        <div class="input-desc">Cargos que possuem permissão para gerenciar o bot no painel.</div>
                        <div class="role-picker-container">
                            <div class="role-input-row">
                                <select id="select-cargo-add" style="flex: 1;" onchange="adicionarCargoAutorizadoDireto(this)">
                                    <option value="">Selecione um cargo para adicionar...</option>
                                    {% if guild_atual %}
                                        {% for r in guild_atual.cargos %}
                                            <option value="{{ r.id }}" data-name="{{ r.nome }}" data-color="{{ r.cor }}">@ {{ r.nome }}</option>
                                        {% endfor %}
                                    {% endif %}
                                </select>
                            </div>
                            <div class="role-badges-box" id="box-cargos-autorizados">
                                {% if guild_atual and guild_atual.config.cargos_permitidos %}
                                    {% for rc_id in guild_atual.config.cargos_permitidos %}
                                        {% set cargo_obj = guild_atual.cargos | selectattr('id', 'equalto', rc_id) | first %}
                                        {% if cargo_obj %}
                                            {% set c_hex = cargo_obj.cor if cargo_obj.cor else '#99aab5' %}
                                            <div class="role-badge" data-id="{{ cargo_obj.id }}" style="--badge-glow: {{ c_hex }}50;">
                                                <span class="role-badge-dot" style="background-color: {{ c_hex }}; color: {{ c_hex }};"></span>
                                                <span>{{ cargo_obj.nome }}</span>
                                                <button type="button" class="role-badge-remove" onclick="removerBadgeAutorizado(this, '{{ cargo_obj.id }}', '{{ cargo_obj.nome }}', '{{ c_hex }}')">×</button>
                                                <input type="hidden" name="cargos_permitidos" value="{{ cargo_obj.id }}">
                                            </div>
                                        {% endif %}
                                    {% endfor %}
                                {% endif %}
                            </div>
                        </div>
                        
                        <label style="margin-top: 20px;">IDs de Usuários Específicos (separados por vírgula):</label>
                        <div class="input-desc">Usuários adicionais que terão acesso total independente do cargo.</div>
                        <input type="text" name="usuarios_permitidos" value="{{ ', '.join(guild_atual.config.usuarios_permitidos) if guild_atual else '' }}">
                        
                        <label style="margin-top: 20px;">Canais Proibidos (Blacklist):</label>
                        <div class="input-desc">Canais onde os comandos do bot serão ignorados.</div>
                        <select name="canais_proibidos" multiple style="height: 120px;">
                            {% if guild_atual %}
                                {% for c in guild_atual.canais %}
                                    <option value="{{ c.id }}" {% if c.id in guild_atual.config.canais_proibidos %}selected{% endif %}># {{ c.nome }}</option>
                                {% endfor %}
                            {% endif %}
                        </select>

                    <!-- ABA 5: ARMADILHA -->
                    {% elif tab == 'armadilha' %}
                        <h2>Canal Armadilha (Anti-Divulgação / Anti-Flood)</h2>
                        <p class="subtitle">Monitore um canal específico para punir automaticamente usuários que enviarem mensagens impróprias.</p>
                        
                        <label>Canal Armadilha:</label>
                        <div class="input-desc">Canal designado para capturar mensagens indesejadas.</div>
                        <select name="armadilha_canal">
                            <option value="">Desativado</option>
                            {% if guild_atual %}
                                {% for c in guild_atual.canais %}
                                    <option value="{{ c.id }}" {% if guild_atual.config.armadilha_canal == c.id %}selected{% endif %}># {{ c.nome }}</option>
                                {% endfor %}
                            {% endif %}
                        </select>

                        <label style="margin-top: 15px;">Ação Automática:</label>
                        <div class="input-desc">Punição aplicada ao infrator que postar no canal armadilha.</div>
                        <select name="armadilha_acao">
                            <option value="nenhuma" {% if guild_atual and guild_atual.config.armadilha_acao == 'nenhuma' %}selected{% endif %}>Apenas deletar mensagem</option>
                            <option value="warn" {% if guild_atual and guild_atual.config.armadilha_acao == 'warn' %}selected{% endif %}>Aviso privado</option>
                            <option value="kick" {% if guild_atual and guild_atual.config.armadilha_acao == 'kick' %}selected{% endif %}>Kick</option>
                            <option value="ban" {% if guild_atual and guild_atual.config.armadilha_acao == 'ban' %}selected{% endif %}>Ban</option>
                            <option value="mute" {% if guild_atual and guild_atual.config.armadilha_acao == 'mute' %}selected{% endif %}>Timeout (Mute)</option>
                        </select>

                        <label style="margin-top: 15px;">Duração do Timeout (Minutos):</label>
                        <div class="input-desc">Tempo de silenciamento caso a ação escolhida seja Timeout.</div>
                        <input type="number" name="armadilha_tempo" value="{{ guild_atual.config.armadilha_tempo if guild_atual else 10 }}">
                    {% endif %}

                </form>

            </div>

            <!-- PAINEL DE PREVIEW AO VIVO -->
            <div class="preview-pane {% if tab in ['embed', 'welcome_leave', 'reaction_roles'] %}active{% endif %}" id="preview-box">
                <h3 style="color: #fff; margin-top: 0; font-size: 15px; font-weight: 600;">Preview ao Vivo</h3>
                
                <div class="discord-message">
                    <div class="discord-avatar">E</div>
                    <div class="discord-content">
                        <div class="discord-username">Ester <span class="discord-bot-tag">BOT</span></div>
                        <div id="preview-text-simples" style="color: #d1d5db; font-size: 13px; margin-bottom: 6px; display: none;"></div>
                        <div class="discord-embed" id="preview-border">
                            <div class="discord-embed-inner">
                                <a id="preview-title" class="embed-title" href="#" style="display: none;">Título</a>
                                <div id="preview-desc" class="embed-desc">Aguardando preenchimento...</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- POPUP FLUTUANTE DE ALTERAÇÕES -->
            <div class="save-bar-popup" id="save-popup-bar">
                <span class="save-bar-text">⚠️ Você tem alterações não salvas.</span>
                <div class="save-bar-actions">
                    <button type="button" class="btn-discard" onclick="descartarAlteracoes()">Descartar</button>
                    <button type="button" class="btn-popup-save" onclick="salvarAlteracoes()">Salvar Alterações</button>
                </div>
            </div>
        </div>
    {% endif %}

    <script>
        let hasChanges = false;

        // DETECTAR ALTERAÇÕES NOS INPUTS
        document.addEventListener("DOMContentLoaded", () => {
            const form = document.getElementById("main-config-form");
            if (form) {
                form.addEventListener("input", () => marcarModificado());
                form.addEventListener("change", () => marcarModificado());
            }
        });

        function marcarModificado() {
            if (!hasChanges) {
                hasChanges = true;
                document.getElementById("save-popup-bar").classList.add("visible");
            }
        }

        function descartarAlteracoes() {
            window.location.reload();
        }

        function salvarAlteracoes() {
            const form = document.getElementById("main-config-form");
            if (form) form.submit();
        }

        // MENU SUSPENSO DE SERVIDORES
        function toggleServerMenu(event) {
            event.stopPropagation();
            let header = document.getElementById("server-header-toggle");
            let menu = document.getElementById("server-dropdown");
            header.classList.toggle("open");
            menu.classList.toggle("active");
        }

        window.addEventListener("click", function() {
            let header = document.getElementById("server-header-toggle");
            let menu = document.getElementById("server-dropdown");
            if (menu && menu.classList.contains("active")) {
                header.classList.remove("open");
                menu.classList.remove("active");
            }
        });

        function toggleAccordion(header) {
            let content = header.nextElementSibling;
            content.classList.toggle("open");
            let arrow = header.querySelector("span:last-child");
            arrow.textContent = content.classList.contains("open") ? "▲" : "▼";
        }

        function sincronizarHex(val) {
            document.getElementById("cor-input").value = val.replace("#", "").toUpperCase();
            atualizarPreviewGeneric();
        }

        function sincronizarPicker(val) {
            let limpo = val.replace("#", "").trim();
            if (/^[0-9A-Fa-f]{6}$/.test(limpo)) document.getElementById("color-picker").value = "#" + limpo;
            atualizarPreviewGeneric();
        }

        // GERENCIAMENTO DE CARGOS AUTORIZADOS VIA SELECT
        function adicionarCargoAutorizadoDireto(selectEl) {
            let opt = selectEl.options[selectEl.selectedIndex];
            if (!opt.value) return;

            let cargoId = opt.value;
            let cargoNome = opt.getAttribute("data-name");
            let cargoCor = opt.getAttribute("data-color") || "#99aab5";

            let box = document.getElementById("box-cargos-autorizados");
            if (box.querySelector(`input[value="${cargoId}"]`)) {
                selectEl.selectedIndex = 0;
                return;
            }

            let badge = document.createElement("div");
            badge.className = "role-badge";
            badge.setAttribute("data-id", cargoId);
            badge.style.setProperty("--badge-glow", cargoCor + "50");
            badge.innerHTML = `
                <span class="role-badge-dot" style="background-color: ${cargoCor}; color: ${cargoCor};"></span>
                <span>${cargoNome}</span>
                <button type="button" class="role-badge-remove" onclick="removerBadgeAutorizado(this, '${cargoId}', '${cargoNome}', '${cargoCor}')">×</button>
                <input type="hidden" name="cargos_permitidos" value="${cargoId}">
            `;
            box.appendChild(badge);

            opt.remove();
            selectEl.selectedIndex = 0;
            marcarModificado();
        }

        function removerBadgeAutorizado(btn, cargoId, cargoNome, cargoCor) {
            let select = document.getElementById("select-cargo-add");
            if (select) {
                let newOpt = document.createElement("option");
                newOpt.value = cargoId;
                newOpt.setAttribute("data-name", cargoNome);
                newOpt.setAttribute("data-color", cargoCor);
                newOpt.textContent = "@ " + cargoNome;
                select.appendChild(newOpt);
            }
            btn.parentElement.remove();
            marcarModificado();
        }

        // GERENCIAMENTO DE REACTION ROLES VIA SELECT
        let reactionItemsList = [];

        function adicionarCargoReactionDireto(selectEl) {
            let emojiInput = document.getElementById("rr-emoji-input");
            if (!emojiInput.value.trim()) {
                alert("Digite o emoji primeiro antes de selecionar o cargo!");
                selectEl.selectedIndex = 0;
                return;
            }

            let opt = selectEl.options[selectEl.selectedIndex];
            if (!opt.value) return;

            let item = {
                emoji: emojiInput.value.trim(),
                role_id: opt.value,
                role_name: opt.getAttribute("data-name"),
                role_color: opt.getAttribute("data-color") || "#99aab5"
            };

            reactionItemsList.push(item);
            renderReactionItems();

            emojiInput.value = "";
            opt.remove();
            selectEl.selectedIndex = 0;
            marcarModificado();
        }

        function removeReactionItem(index) {
            let removed = reactionItemsList.splice(index, 1)[0];
            renderReactionItems();

            let select = document.getElementById("rr-role-select");
            if (select && removed) {
                let newOpt = document.createElement("option");
                newOpt.value = removed.role_id;
                newOpt.setAttribute("data-name", removed.role_name);
                newOpt.setAttribute("data-color", removed.role_color);
                newOpt.textContent = "@ " + removed.role_name;
                select.appendChild(newOpt);
            }
            marcarModificado();
        }

        function renderReactionItems() {
            let container = document.getElementById("rr-badges-container");
            let hiddenInput = document.getElementById("reaction_items_json");
            hiddenInput.value = JSON.stringify(reactionItemsList);

            if (reactionItemsList.length === 0) {
                container.innerHTML = '<span style="color: var(--text-muted); font-size: 13px;" id="rr-empty-text">Nenhum cargo adicionado ainda.</span>';
                return;
            }

            container.innerHTML = "";
            reactionItemsList.forEach((item, index) => {
                let badge = document.createElement("div");
                badge.className = "role-badge";
                badge.style.setProperty("--badge-glow", item.role_color + "50");
                badge.innerHTML = `
                    <span>${item.emoji}</span>
                    <span class="role-badge-dot" style="background-color: ${item.role_color}; color: ${item.role_color};"></span>
                    <span>${item.role_name}</span>
                    <button type="button" class="role-badge-remove" onclick="removeReactionItem(${index})">×</button>
                `;
                container.appendChild(badge);
            });
        }

        function atualizarPreviewGeneric() {
            let tab = "{{ tab }}";
            let corHex = "5865F2";
            let titulo = "";
            let desc = "Aguardando preenchimento...";
            let txtSimples = "";

            if (tab === 'embed') {
                corHex = document.getElementById("cor-input") ? document.getElementById("cor-input").value : "5865F2";
                titulo = document.getElementById("input-titulo") ? document.getElementById("input-titulo").value : "";
                desc = document.getElementById("input-desc") ? document.getElementById("input-desc").value : "";
            } else if (tab === 'welcome_leave') {
                corHex = document.getElementById("input-welcome-cor") ? document.getElementById("input-welcome-cor").value : "5865F2";
                titulo = document.getElementById("input-welcome-titulo") ? document.getElementById("input-welcome-titulo").value : "";
                desc = document.getElementById("input-welcome-desc") ? document.getElementById("input-welcome-desc").value : "";
                txtSimples = document.getElementById("input-welcome-msg") ? document.getElementById("input-welcome-msg").value : "";
            } else if (tab === 'reaction_roles') {
                corHex = document.getElementById("input-rr-cor") ? document.getElementById("input-rr-cor").value : "5865F2";
                titulo = document.getElementById("input-rr-titulo") ? document.getElementById("input-rr-titulo").value : "";
                desc = document.getElementById("input-rr-desc") ? document.getElementById("input-rr-desc").value : "";
            }

            let limpoHex = corHex.trim().replace("#", "");
            if (/^[0-9A-Fa-f]{6}$/.test(limpoHex)) {
                document.getElementById("preview-border").style.borderLeftColor = "#" + limpoHex;
            }

            let titleEl = document.getElementById("preview-title");
            if (titulo) {
                titleEl.textContent = titulo;
                titleEl.style.display = "block";
            } else {
                titleEl.style.display = "none";
            }

            document.getElementById("preview-desc").textContent = desc || "Aguardando preenchimento...";

            let txtSimplesEl = document.getElementById("preview-text-simples");
            if (txtSimplesEl) {
                if (txtSimples) {
                    txtSimplesEl.textContent = txtSimples;
                    txtSimplesEl.style.display = "block";
                } else {
                    txtSimplesEl.style.display = "none";
                }
            }
        }

        window.onload = function() {
            atualizarPreviewGeneric();
        };
    </script>
</body>
</html>
"""

@app.route("/login")
def login():
    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds")

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code: return redirect(url_for("index"))
    
    resp = requests.post(f"{API_ENDPOINT}/oauth2/token", data={
        "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    
    if resp.status_code != 200: return "Falha na autenticação.", 400
    access_token = resp.json().get("access_token")
    session["access_token"] = access_token
    
    user_resp = requests.get(f"{API_ENDPOINT}/users/@me", headers={"Authorization": f"Bearer {access_token}"})
    if user_resp.status_code == 200:
        u_data = user_resp.json()
        avatar_hash = u_data.get("avatar")
        session["user"] = {
            "username": u_data.get("username"), "id": u_data.get("id"),
            "avatar_url": f"https://cdn.discordapp.com/avatars/{u_data['id']}/{avatar_hash}.png" if avatar_hash else "https://cdn.discordapp.com/embed/avatars/0.png"
        }
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/", methods=["GET", "POST"])
def index():
    status = None
    guildas = []
    user = session.get("user")
    tab = request.args.get("tab", "embed")
    guild_id_atual = request.args.get("guild")

    if user and "access_token" in session:
        g_resp = requests.get(f"{API_ENDPOINT}/users/@me/guilds", headers={"Authorization": f"Bearer {session['access_token']}"})
        if g_resp.status_code == 200:
            user_guild_ids = [g["id"] for g in g_resp.json() if (int(g["permissions"]) & 0x20) == 0x20 or g.get("owner")]
            try:
                resp = requests.get("http://127.0.0.1:8080/api/guildas", params=[('guilds[]', gid) for gid in user_guild_ids], timeout=3)
                if resp.status_code == 200: guildas = resp.json()
            except: pass

    if not guild_id_atual and guildas:
        guild_id_atual = guildas[0]["id"]

    guild_atual = next((g for g in guildas if g["id"] == guild_id_atual), guildas[0] if guildas else None)

    if request.method == "POST" and user:
        acao = request.form.get("acao")

        if acao == "embed":
            dados = {
                "canal_id": request.form.get("canal_id"), "titulo": request.form.get("titulo"),
                "titulo_url": request.form.get("titulo_url"), "descricao": request.form.get("descricao"),
                "cor_hex": request.form.get("cor_hex"), "autor_nome": request.form.get("autor_nome"),
                "autor_icone": request.form.get("autor_icone"), "thumbnail": request.form.get("thumbnail"),
                "imagem_grande": request.form.get("imagem_grande"), "rodape": request.form.get("rodape"),
                "footer_icon": request.form.get("footer_icon"), "modo_data": request.form.get("modo_data")
            }
            try:
                resposta = requests.post("http://127.0.0.1:8080/enviar-embed", json=dados, timeout=5)
                status = "sucesso" if resposta.status_code == 200 else "erro"
            except: status = "erro"
        elif acao == "reaction_roles":
            import json
            items_json = request.form.get("reaction_items_json", "[]")
            try:
                items = json.loads(items_json)
            except:
                items = []

            dados = {
                "canal_id": request.form.get("canal_id"),
                "titulo": request.form.get("titulo"),
                "descricao": request.form.get("descricao"),
                "cor_hex": request.form.get("cor_hex"),
                "thumbnail": request.form.get("thumbnail"),
                "rodape": request.form.get("rodape"),
                "modo_data": "nenhuma",
                "reaction_items": items
            }
            try:
                resposta = requests.post("http://127.0.0.1:8080/enviar-embed", json=dados, timeout=5)
                status = "sucesso" if resposta.status_code == 200 else "erro"
            except: status = "erro"
        else:
            try:
                current_config = guild_atual["config"] if guild_atual else {}

                if acao == "config":
                    current_config["cargos_permitidos"] = request.form.getlist("cargos_permitidos")
                    current_config["usuarios_permitidos"] = [u.strip() for u in request.form.get("usuarios_permitidos", "").split(",") if u.strip()]
                    current_config["canais_proibidos"] = request.form.getlist("canais_proibidos")
                elif acao == "armadilha":
                    current_config["armadilha_canal"] = request.form.get("armadilha_canal")
                    current_config["armadilha_acao"] = request.form.get("armadilha_acao")
                    current_config["armadilha_tempo"] = int(request.form.get("armadilha_tempo", 10))
                elif acao == "welcome_leave":
                    # Boas-Vindas
                    current_config["welcome_ativo"] = bool(request.form.get("welcome_ativo"))
                    current_config["welcome_canal"] = request.form.get("welcome_canal")
                    current_config["welcome_mensagem"] = request.form.get("welcome_mensagem")
                    current_config["welcome_titulo"] = request.form.get("welcome_titulo")
                    current_config["welcome_descricao"] = request.form.get("welcome_descricao")
                    current_config["welcome_cor"] = request.form.get("welcome_cor")
                    current_config["welcome_thumb"] = request.form.get("welcome_thumb")
                    current_config["welcome_imagem"] = request.form.get("welcome_imagem")
                    current_config["welcome_rodape"] = request.form.get("welcome_rodape")
                    # Despedidas
                    current_config["leave_ativo"] = bool(request.form.get("leave_ativo"))
                    current_config["leave_canal"] = request.form.get("leave_canal")
                    current_config["leave_mensagem"] = request.form.get("leave_mensagem")
                    current_config["leave_titulo"] = request.form.get("leave_titulo")
                    current_config["leave_descricao"] = request.form.get("leave_descricao")
                    current_config["leave_cor"] = request.form.get("leave_cor")
                    current_config["leave_thumb"] = request.form.get("leave_thumb")
                    current_config["leave_imagem"] = request.form.get("leave_imagem")
                    current_config["leave_rodape"] = request.form.get("leave_rodape")

                current_config["guild_id"] = guild_id_atual
                resp = requests.post("http://127.0.0.1:8080/api/salvar-config", json=current_config, timeout=5)
                if resp.status_code == 200: status = "sucesso"
            except: status = "erro"

        try:
            resp = requests.get("http://127.0.0.1:8080/api/guildas", params=[('guilds[]', gid) for gid in user_guild_ids], timeout=3)
            if resp.status_code == 200: 
                guildas = resp.json()
                guild_atual = next((g for g in guildas if g["id"] == guild_id_atual), guild_atual)
        except: pass

    return render_template_string(HTML_TEMPLATE, status=status, guildas=guildas, user=user, guild_atual=guild_atual, guild_id_atual=guild_id_atual, tab=tab)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)