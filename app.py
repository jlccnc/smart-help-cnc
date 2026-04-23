from flask import Flask, request, render_template_string, url_for
import pandas as pd
import webbrowser
import threading
from datetime import datetime
import os
import sys

# ✅ ADICIONE AQUI
historico = []

app = Flask(__name__, static_folder="static")

ARQUIVO = "LOG_ALARMES.xlsx"
excel = pd.ExcelFile(ARQUIVO)
import os
import sys

def caminho_arquivo(nome):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, nome)
    return os.path.join(os.path.abspath("."), nome)

ARQUIVO = caminho_arquivo("LOG_ALARMES.xlsx")

app = Flask(__name__, static_folder=caminho_arquivo("static"))



# 🔍 BUSCA (Lógica preservada com a pequena correção de estabilidade do Pandas)

def buscar(codigo, aba):
    if not codigo:
        return None

    codigo = str(codigo).strip().upper()

    df = excel.parse(aba)
    df.columns = df.columns.str.strip().str.upper()

    # 🔍 coluna de código
    col_codigo = next((c for c in df.columns if "COD" in c), None)
    if not col_codigo:
        return None

    df[col_codigo] = df[col_codigo].astype(str).str.upper().str.replace(".0", "", regex=False)

    codigo_limpo = codigo.replace(" ", "").replace("-", "")
    df["_COD"] = df[col_codigo].str.replace(" ", "").str.replace("-", "")

    resultado = df[df["_COD"].str.contains(codigo_limpo, na=False)]
    if resultado.empty:
        return None

    linha = resultado.iloc[0]

    # 🔍 função pra achar coluna mesmo com nome diferente
    def get_col(nome):
        for c in df.columns:
            if nome in c:
                return c
        return None

    return {
        "codigo": str(linha.get(col_codigo, "")),
        "tag": str(linha.get(get_col("TAG") or "", "")),
        "ihm": str(linha.get(get_col("IHM") or "", "")),
        "descricao": str(linha.get(get_col("DESCRI") or "", "")),
        "causa": str(linha.get(get_col("CAUSA") or "", "")),
        "acao": str(linha.get(get_col("AÇÃO") or get_col("ACAO") or "", ""))
    }



# 🎨 CORES E ARQUIVOS DE IMAGEM
cores = {
    "FANUC": "#FFC107", "OKUMA": "#0284c7", "ROBO ABB": "#E31E24", 
    "ROBO KUKA": "#FF7900", "ROBO FANUC": "#28A745", "HAAS": "#6F42C1", 
    "MORI SEIKI": "#17A2B8", "PLC": "#1B365D"
}

icones_arquivos = {

    
    "FANUC": "fanuc.png",
    "OKUMA": "okuma.png",
    "ROBO ABB": "abb.png",
    "ROBO KUKA": "kuka.png",
    "ROBO FANUC": "robo_fanuc.png",
    "HAAS": "haas.png",
    "MORI SEIKI": "mori.png",
    "PLC": "plc.png"
}



# 🔷 CSS GLOBAL (REFINADO PARA IMAGENS REAIS)
CSS_ESTILO = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    :root { --bg-body: #f4f7fa; }
    body { margin: 0; font-family: 'Inter', sans-serif; background: var(--bg-body); color: #1e293b; }

    /* CABEÇALHO IGUAL À IMAGEM */
    .header-main { 
        background: linear-gradient(135deg, #000c1d 0%, #001e3c 100%);
        color: white; padding: 15px 50px; display: flex; justify-content: space-between; align-items: center;
        border-bottom: 3px solid #3b82f6;
    }
    .logo-container h1 { margin: 0; font-size: 24px; font-weight: 800; }
    .logo-container h1 span { color: #3b82f6; }
    .logo-container p { margin: 0; font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }

    .header-right { display: flex; gap: 30px; align-items: center; }
    .status-box { background: rgba(255,255,255,0.05); padding: 8px 15px; border-radius: 8px; display: flex; align-items: center; gap: 12px; border: 1px solid rgba(255,255,255,0.1); }
    .dot { width: 12px; height: 12px; background: #22c55e; border-radius: 50%; box-shadow: 0 0 10px #22c55e; }

    /* TITULOS */
    .main-title { text-align: center; margin: 40px 0; }
    .main-title h2 { font-size: 26px; font-weight: 800; text-transform: uppercase; margin-bottom: 10px; }
    .main-title .line { width: 40px; height: 4px; background: #3b82f6; margin: 0 auto 15px; }

    /* GRID DE CARDS */
    .card-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; padding: 0 40px; }
    .machine-card {
        background: white; width: 145px; height: 280px; border-radius: 10px; 
        border-left: 8px solid var(--cor); text-decoration: none; 
        display: flex; flex-direction: column; align-items: center; padding: 20px 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); transition: 0.3s;
    }
    .machine-card:hover { transform: translateY(-8px); box-shadow: 0 12px 25px rgba(0,0,0,0.1); }
    
    /* ESTILO PARA AS IMAGENS DA PASTA STATIC */
    .card-img-container { width: 100%; height: 90px; display: flex; align-items: center; justify-content: center; margin-bottom: 15px; }
    .card-img-container img { max-width: 85%; max-height: 100%; object-fit: contain; }

    .machine-card h3 { color: var(--cor); margin: 10px 0 5px; font-size: 15px; font-weight: 800; }
    .machine-card p { font-size: 10px; color: #94a3b8; text-align: center; font-weight: 600; line-height: 1.4; margin: 0; }

    .arrow-circle {
        width: 32px; height: 32px; border: 1.5px solid #e2e8f0; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        margin-top: auto; color: #94a3b8; font-size: 12px;
    }

    /* RODAPÉ E BOXES */
    .bottom-info { display: flex; justify-content: center; gap: 20px; margin: 50px auto; max-width: 900px; padding: 0 20px; }
    .info-item { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; flex: 1; display: flex; align-items: center; gap: 20px; }
    .footer-bar { background: #000814; color: #475569; padding: 20px 50px; display: flex; justify-content: space-between; font-size: 11px; }
</style>
"""

# 🔷 HOME
@app.route("/")
def home():
    
    descricoes = {
        "FANUC": "Centros CNC<br>Robôs e Comandos",
        "OKUMA": "Centros de Usinagem<br>Tornos e Comandos",
        "ROBO ABB": "Robôs Industriais<br>Controladores",
        "ROBO KUKA": "Robôs Industriais<br>Controladores",
        "ROBO FANUC": "Robôs FANUC<br>Sistemas Integrados",
        "HAAS": "Centros CNC<br>Tornos CNC",
        "MORI SEIKI": "Centros CNC<br>Tornos CNC",
        "PLC": "Automação<br>CLP e I/O"
    }

    cartoes_html = ""
    for nome, cor in cores.items():
        # Gera o caminho da imagem na pasta static
        img_url = url_for('static', filename=icones_arquivos.get(nome, "default.png"))
        
        cartoes_html += f'''
        <a href="/grupo/{nome}" class="machine-card" style="--cor:{cor}">
            <div class="card-img-container">
                <img src="{img_url}" alt="{nome}">
            </div>
            <h3>{nome}</h3>
            <p>{descricoes.get(nome, "")}</p>
            <div class="arrow-circle">➔</div>
        </a>
        '''

    return f"""
<html>
<head>
    <meta charset="UTF-8">
    {CSS_ESTILO}
</head>
<body>
    <header class="header-main">
        <div class="logo-container">
            <h1>SMART HELP CNC <span>PRO</span></h1>
            <p>Inteligência para manutenção industrial</p>
        </div>
        <div class="header-right">
            <div class="status-box">
                <div class="dot"></div>
                <div style="line-height:1.2">
                    <span style="font-weight:800; font-size:11px;">SISTEMA ONLINE</span><br>
                    <span style="font-size:9px; color:#94a3b8;">Todos os serviços operacionais</span>
                </div>
            </div>
            <div style="text-align:right; border-left: 1px solid rgba(255,255,255,0.2); padding-left:20px;">
                <span style="font-weight:800; font-size:15px;">{datetime.now().strftime('%H:%M:%S')}</span><br>
                <span style="color:#94a3b8; font-size:11px;">{datetime.now().strftime('%d/%m/%Y')}</span>
            </div>
        </div>
    </header>

    <div class="main-title">
        <h2>Selecione o Equipamento</h2>
        <div class="line"></div>
        <p>Escolha o grupo de máquinas para visualizar e pesquisar alarmes</p>
    </div>

    <div class="card-grid">{cartoes_html}</div>

    <div class="bottom-info">
        <div class="info-item">
            <div style="width:48px; height:48px; background:#1e3a8a; color:white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:20px;">💡</div>
            <div>
                <b style="display:block; font-size:13px; color:#1e3a8a;">Dica Rápida</b>
                <span style="font-size:12px; color:#64748b;">Selecione o equipamento desejado acima para buscar alarmes.</span>
            </div>
        </div>
        <div class="info-item">
            <div style="width:48px; height:48px; background:#1e3a8a; color:white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:20px;">📊</div>
            <div>
                <b style="display:block; font-size:13px; color:#1e3a8a;">Histórico Recente</b>
                <a href="/historico" style="color:#3b82f6; text-decoration:none; font-size:12px; font-weight:600;">
    Acessar histórico ›
</a>
            </div>
        </div>
    </div>

    <footer class="footer-bar">
        <div>© 2026 <b style="color:#3b82f6;">7 AUTOMAÇÃO INDUSTRIAL</b> | Todos os direitos reservados</div>
        <div>Suporte: <b>engenharia@7automacao.com.br</b></div>
    </footer>
</body>
</html>
"""

# Mantive as rotas /grupo e /maquina conforme o layout anterior, que já seguia o padrão visual.

@app.route("/grupo/<grupo>")
def grupo(grupo):
    abas = excel.sheet_names

    # 🔥 CORREÇÃO AQUI
    if grupo.upper().startswith("ROBO"):
        maquinas = [
            aba for aba in abas
            if aba.upper().startswith(grupo.upper().replace(" ", "_"))
        ]
    else:
        maquinas = [
            aba for aba in abas
            if aba.upper().startswith(grupo.upper() + "_")
        ]

    cor = cores.get(grupo, "#3b82f6")
    botoes = ""

    for m in maquinas:
        nome_exibicao = m.replace(grupo.upper()+"_", "").replace("_", " ")
        botoes += f'''<a href="/maquina/{grupo}/{m}" class="machine-card" style="--cor:{cor}; height:100px; width:200px;"><h3>{nome_exibicao}</h3><div class="arrow-circle">➔</div></a>'''

    return f"""<html><head><meta charset="UTF-8">{CSS_ESTILO}</head><body>
    <header class="header-main"><h1>{grupo}</h1><a href="/" style="color:white; font-size:12px;">VOLTAR</a></header>
    <div class="card-grid" style="margin-top:60px;">{botoes}</div></body></html>"""

@app.route("/maquina/<grupo>/<aba>", methods=["GET", "POST"])
def maquina(grupo, aba):
    resultado = None
    erro = None
    cor = cores.get(grupo, "#3b82f6")

    if request.method == "POST":
        codigo = request.form.get("codigo")
        resultado = buscar(codigo, aba)

        if resultado:
            historico.insert(0, {
                "grupo": grupo,
                "aba": aba,
                "codigo": resultado["codigo"],
                "descricao": resultado["descricao"],
                "data": datetime.now().strftime("%d/%m/%Y %H:%M")
            })

            # limitar histórico (últimos 10)
            historico[:] = historico[:10]

        else:
            erro = "Alarme não encontrado."

    return render_template_string(f"""
    <html><head><meta charset="UTF-8">{CSS_ESTILO}
    <style>
        .container-busca {{ max-width: 800px; margin: 40px auto; background: white; padding: 30px; border-radius: 12px; border-top: 5px solid {cor}; }}
        input {{ width: 70%; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
        button {{ background: {cor}; color: white; border: none; padding: 15px 30px; border-radius: 8px; font-weight: 800; cursor: pointer; }}
    </style>
    </head><body>
    <header class="header-main">
        <h1>{grupo} › {aba}</h1>
        <a href="/grupo/{grupo}" style="color:white; font-size:12px;">VOLTAR</a>
    </header>

    <div class="container-busca">
        <form method="POST">
            <input name="codigo" placeholder="Código do alarme..." required>
            <button>BUSCAR</button>
        </form>

        {{% if resultado %}}
        <div style="margin-top:20px; text-align:left;">
            <b>CÓDIGO:</b> {{{{ resultado.codigo }}}}<br>
            <b>TAG:</b> {{{{ resultado.tag }}}}<br>
            <b>IHM:</b> {{{{ resultado.ihm }}}}<br>
            <b>DESCRIÇÃO:</b> {{{{ resultado.descricao }}}}<br>
            <b>CAUSA:</b> {{{{ resultado.causa }}}}<br>
            <b>AÇÃO:</b> {{{{ resultado.acao }}}}
        </div>
        {{% endif %}}

        {{% if erro %}}
        <p style="color:red; margin-top:20px;">{{{{ erro }}}}</p>
        {{% endif %}}

    </div>
    </body></html>
    """, resultado=resultado, erro=erro)

@app.route("/historico")
def pagina_historico():
    itens = ""

    for h in historico:
        itens += f"""
        <div class="machine-card" style="--cor:#3b82f6; width:250px; height:180px;">
            <h3>{h['codigo']}</h3>
            <p><b>{h['grupo']}</b></p>
            <p style="font-size:11px;">{h['descricao'][:60]}...</p>
            <p style="font-size:10px; color:#64748b;">{h['data']}</p>
            <a href="/maquina/{h['grupo']}/{h['aba']}" style="margin-top:auto; font-size:11px;">ABRIR</a>
        </div>
        """

    return f"""
    <html><head><meta charset="UTF-8">{CSS_ESTILO}</head><body>

    <header class="header-main">
        <h1>HISTÓRICO</h1>
        <a href="/" style="color:white;">VOLTAR</a>
    </header>

    <div class="card-grid" style="margin-top:40px;">
        {itens if itens else "<p style='text-align:center'>Nenhuma busca ainda</p>"}
    </div>

    </body></html>
    """


if __name__ == "__main__":
    if "gunicorn" not in os.environ.get("SERVER_SOFTWARE", ""):
        import threading
        import webbrowser
        threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:3030")).start()

    app.run(port=3030, debug=True, use_reloader=False)
