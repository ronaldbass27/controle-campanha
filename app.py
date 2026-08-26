from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'chave_secreta_campanha_2026'

def inicializar_banco():
    conexao = sqlite3.connect('estoque.db')
    cursor = conexao.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            tipo TEXT NOT NULL,
            material TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            responsavel TEXT NOT NULL,
            lote_id TEXT
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE movimentacoes ADD COLUMN lote_id TEXT")
        conexao.commit()
    except sqlite3.OperationalError:
        pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materiais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL
        )
    ''')
    
    cursor.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (username, senha, tipo) VALUES (?, ?, ?)", 
                       ('admin', 'controle2026', 'admin'))
        conexao.commit()
        
    conexao.close()

inicializar_banco()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['username']
        senha = request.form['senha']
        
        conexao = sqlite3.connect('estoque.db')
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE username = ? AND senha = ?", (usuario, senha))
        user = cursor.fetchone()
        conexao.close()
        
        if user:
            session['usuario'] = user[1]
            session['tipo'] = user[3]
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos!')
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    busca = request.args.get('busca', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Quantidade de itens por página
    offset = (page - 1) * per_page
    
    conexao = sqlite3.connect('estoque.db')
    cursor = conexao.cursor()
    
    cursor.execute("SELECT nome FROM materiais")
    materiais = [row[0] for row in cursor.fetchall()]
    
    # Contagem total para a paginação
    if busca:
        cursor.execute("SELECT COUNT(*) FROM movimentacoes WHERE responsavel LIKE ? OR material LIKE ?", 
                       ('%' + busca + '%', '%' + busca + '%'))
    else:
        cursor.execute("SELECT COUNT(*) FROM movimentacoes")
    total_itens = cursor.fetchone()[0]
    total_pages = (total_itens + per_page - 1) // per_page if total_itens > 0 else 1
    
    # Busca paginada
    if busca:
        cursor.execute("SELECT * FROM movimentacoes WHERE responsavel LIKE ? OR material LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?", 
                       ('%' + busca + '%', '%' + busca + '%', per_page, offset))
    else:
        cursor.execute("SELECT * FROM movimentacoes ORDER BY id DESC LIMIT ? OFFSET ?", (per_page, offset))
    movimentos = cursor.fetchall()
    
    # Saldos
    saldos = {mat: 0 for mat in materiais}
    cursor.execute("SELECT tipo, material, quantidade FROM movimentacoes")
    todas_movs = cursor.fetchall()
    for tipo, mat, qtd in todas_movs:
        if mat in saldos:
            if tipo == 'Entrada' or tipo == 'Devolução':
                saldos[mat] += qtd
            elif tipo == 'Saída':
                saldos[mat] -= qtd
                
    conexao.close()
    
    return render_template('dashboard.html', 
                           materiais=materiais, 
                           movimentos=movimentos, 
                           saldos=saldos, 
                           busca=busca,
                           page=page,
                           total_pages=total_pages)

@app.route('/add', methods=['POST'])
def add():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    tipo = request.form['tipo']
    responsavel = request.form['responsavel']
    data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
    lote_id = datetime.now().strftime('%Y%m%d%H%M%S') if tipo == 'Saída' else None
    
    conexao = sqlite3.connect('estoque.db')
    cursor = conexao.cursor()
    
    materiais = request.form.getlist('material[]')
    quantidades = request.form.getlist('quantidade[]')
    
    if materiais and quantidades:
        for mat, qtd in zip(materiais, quantidades):
            if qtd and int(qtd) > 0:
                cursor.execute(
                    "INSERT INTO movimentacoes (data, tipo, material, quantidade, responsavel, lote_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (data_atual, tipo, mat, int(qtd), responsavel, lote_id)
                )
    else:
        material = request.form.get('material')
        quantidade = request.form.get('quantidade')
        if material and quantidade:
            cursor.execute(
                "INSERT INTO movimentacoes (data, tipo, material, quantidade, responsavel, lote_id) VALUES (?, ?, ?, ?, ?, ?)",
                (data_atual, tipo, material, int(quantidade), responsavel, lote_id)
            )
            
    conexao.commit()
    conexao.close()
    
    return redirect(url_for('dashboard'))

@app.route('/add_material', methods=['POST'])
def add_material():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    novo_material = request.form['novo_material']
    
    conexao = sqlite3.connect('estoque.db')
    cursor = conexao.cursor()
    try:
        cursor.execute("INSERT INTO materiais (nome) VALUES (?)", (novo_material,))
        conexao.commit()
    except:
        pass
    conexao.close()
    
    return redirect(url_for('dashboard'))

@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    if 'usuario' not in session or session.get('tipo') != 'admin':
        return redirect(url_for('login'))
        
    novo_user = request.form['novo_username']
    nova_senha = request.form['nova_senha']
    tipo_user = request.form['tipo_usuario']
    
    conexao = sqlite3.connect('estoque.db')
    cursor = conexao.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (username, senha, tipo) VALUES (?, ?, ?)", 
                       (novo_user, nova_senha, tipo_user))
        conexao.commit()
    except:
        pass
    conexao.close()
    
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:id>')
def delete(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    conexao = sqlite3.connect('estoque.db')
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM movimentacoes WHERE id = ?", (id,))
    conexao.commit()
    conexao.close()
    
    return redirect(url_for('dashboard'))

@app.route('/recibo/<int:id>')
def recibo(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    conexao = sqlite3.connect('estoque.db')
    cursor = conexao.cursor()
    
    cursor.execute("SELECT * FROM movimentacoes WHERE id = ?", (id,))
    mov_base = cursor.fetchone()
    
    if not mov_base:
        conexao.close()
        return "Movimentação não encontrada.", 404
        
    lote_id = mov_base[6]
    
    if lote_id:
        cursor.execute("SELECT * FROM movimentacoes WHERE lote_id = ?", (lote_id,))
        itens = cursor.fetchall()
    else:
        itens = [mov_base]
        
    conexao.close()
    
    responsavel = mov_base[5]
    data_mov = mov_base[1]
    
    tabela_itens = ""
    for item in itens:
        tabela_itens += f"<tr><td>{item[3]}</td><td style='text-align: center;'><strong>{item[4]}</strong></td></tr>"
    
    html_recibo = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Termo de Recebimento de Materiais</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; color: #333; max-width: 700px; margin: 0 auto; }}
            .cabecalho {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 15px; margin-bottom: 25px; }}
            .conteudo {{ font-size: 15px; line-height: 1.6; margin-bottom: 30px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #333; padding: 10px; text-align: left; font-size: 14px; }}
            th {{ background: #f4f4f4; }}
            .assinatura {{ margin-top: 70px; text-align: center; }}
            .linha-assinatura {{ border-top: 1px solid #333; width: 60%; margin: 0 auto 10px auto; }}
            @media print {{
                .nao-imprimir {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="cabecalho">
            <h2>TERMO DE RESPONSABILIDADE E RECEBIMENTO DE MATERIAIS</h2>
            <p>Controle de Campanha 2026</p>
        </div>
        <div class="conteudo">
            <p>Declaro para os devidos fins que recebi nesta data (<strong>{data_mov}</strong>), os seguintes materiais abaixo relacionados para uso exclusivo nas atividades autorizadas da campanha:</p>
            
            <table>
                <tr>
                    <th>Material / Item</th>
                    <th style="text-align: center; width: 120px;">Quantidade</th>
                </tr>
                {tabela_itens}
            </table>
            
            <p><strong>Responsável pelo recebimento:</strong> {responsavel}</p>
        </div>
        <div class="assinatura">
            <div class="linha-assinatura"></div>
            <p>{responsavel}<br>Assinatura do Responsável</p>
        </div>
        <br>
        <div style="text-align: center;" class="nao-imprimir">
            <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">Imprimir Termo</button>
            <br><br>
            <a href="/dashboard">Voltar ao Painel</a>
        </div>
    </body>
    </html>
    """
    return html_recibo

@app.route('/relatorio_estoque')
def relatorio_estoque():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    conexao = sqlite3.connect('estoque.db')
    cursor = conexao.cursor()
    cursor.execute("SELECT nome FROM materiais")
    materiais = [row[0] for row in cursor.fetchall()]
    
    saldos = {mat: 0 for mat in materiais}
    cursor.execute("SELECT tipo, material, quantidade FROM movimentacoes")
    todas_movs = cursor.fetchall()
    conexao.close()
    
    for tipo, mat, qtd in todas_movs:
        if mat in saldos:
            if tipo == 'Entrada' or tipo == 'Devolução':
                saldos[mat] += qtd
            elif tipo == 'Saída':
                saldos[mat] -= qtd
                
    html = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Relatório de Estoque Atual</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 30px; max-width: 700px; margin: 0 auto; color: #333; }
            h2 { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            th { background: #f4f4f4; }
            @media print { .nao-imprimir { display: none; } }
        </style>
    </head>
    <body>
        <h2>Relatório de Saldo Atual do Estoque</h2>
        <p>Data de emissão: """ + datetime.now().strftime('%d/%m/%Y %H:%M') + """</p>
        <table>
            <tr><th>Material</th><th>Quantidade em Estoque</th></tr>
    """
    for mat, qtd in saldos.items():
        html += f"<tr><td>{mat}</td><td><strong>{qtd}</strong></td></tr>"
        
    html += """
        </table>
        <br><br>
        <div style="text-align: center;" class="nao-imprimir">
            <button onclick="window.print()" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">Imprimir Relatório</button>
            <br><br>
            <a href="/dashboard">Voltar ao Painel</a>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/relatorio_movimentacoes')
def relatorio_movimentacoes():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    conexao = sqlite3.connect('estoque.db')
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM movimentacoes ORDER BY id DESC")
    movimentos = cursor.fetchall()
    conexao.close()
    
    html = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Relatório Completo de Movimentações</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 30px; max-width: 900px; margin: 0 auto; color: #333; }
            h2 { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 13px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background: #f4f4f4; }
            @media print { .nao-imprimir { display: none; } }
        </style>
    </head>
    <body>
        <h2>Relatório Completo de Movimentações</h2>
        <p>Data de emissão: """ + datetime.now().strftime('%d/%m/%Y %H:%M') + """</p>
        <table>
            <tr><th>Data/Hora</th><th>Tipo</th><th>Material</th><th>Qtd</th><th>Responsável / Destino</th></tr>
    """
    for mov in movimentos:
        html += f"<tr><td>{mov[1]}</td><td>{mov[2]}</td><td>{mov[3]}</td><td>{mov[4]}</td><td>{mov[5]}</td></tr>"
        
    html += """
        </table>
        <br><br>
        <div style="text-align: center;" class="nao-imprimir">
            <button onclick="window.print()" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">Imprimir Relatório</button>
            <br><br>
            <a href="/dashboard">Voltar ao Painel</a>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)