import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
from datetime import datetime

# --- Configurações do Banco de Dados ---
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "sistema_vendas" # Alterado para o novo sistema

# --- Funções do Banco de Dados ---
def conectar_db():
    """Conecta ao banco de dados MySQL."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
            # Database é conectado após verificar/criar
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn.database = DB_NAME
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao MySQL: {err}")
        return None

def criar_tabelas(conn):
    """Cria as tabelas no banco de dados se não existirem."""
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                cpf VARCHAR(14) UNIQUE,
                telefone VARCHAR(20),
                email VARCHAR(255)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                descricao TEXT,
                preco DECIMAL(10, 2) NOT NULL,
                estoque INT DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cliente_id INT NOT NULL,
                data_pedido DATETIME DEFAULT CURRENT_TIMESTAMP,
                valor_total DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS itens_pedido (
                id INT AUTO_INCREMENT PRIMARY KEY,
                pedido_id INT NOT NULL,
                produto_id INT NOT NULL,
                quantidade INT NOT NULL,
                preco_unitario DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE,
                FOREIGN KEY (produto_id) REFERENCES produtos(id)
            )
        """)
        conn.commit()
    except mysql.connector.Error as err:
        messagebox.showerror("Erro ao Criar Tabelas", f"Erro: {err}")
    finally:
        cursor.close()

# --- Classe Principal da Aplicação ---
class SistemaVendasApp:
    def __init__(self, root_tk):
        self.root = root_tk
        self.root.title("Sistema de Gestão de Vendas")
        self.root.geometry("900x700")

        # Conectar e criar tabelas
        self.conn = conectar_db()
        if self.conn:
            criar_tabelas(self.conn)
        else:
            self.root.quit() # Sai se não puder conectar
            return

        # Variáveis para o formulário de pedido
        self.itens_pedido_atual = [] # Lista para armazenar {produto_id, nome_produto, quantidade, preco_unitario, subtotal}
        self.cliente_selecionado_pedido = None
        self.total_pedido_atual = tk.DoubleVar(value=0.0)

        self.criar_menu()
        self.container_principal = tk.Frame(self.root)
        self.container_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tela inicial (pode ser um dashboard ou a primeira tela de cadastro)
        self.mostrar_tela_clientes()

    def criar_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu Cadastros
        menu_cadastros = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Cadastros", menu=menu_cadastros)
        menu_cadastros.add_command(label="Clientes", command=self.mostrar_tela_clientes)
        menu_cadastros.add_command(label="Produtos", command=self.mostrar_tela_produtos)
        menu_cadastros.add_command(label="Pedidos", command=self.mostrar_tela_pedidos)
        menu_cadastros.add_separator()
        menu_cadastros.add_command(label="Sair", command=self.root.quit)

        # Menu Ajuda
        menu_ajuda = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=menu_ajuda)
        menu_ajuda.add_command(label="Sobre", command=self.mostrar_sobre)

    def limpar_container_principal(self):
        for widget in self.container_principal.winfo_children():
            widget.destroy()

    def mostrar_sobre(self):
        messagebox.showinfo(
            "Sobre o Sistema de Vendas",
            "Nome do Proprietário: João Pedro Prosini Ramos\n"
            "Título do Projeto: Sistema de Gestão de Vendas\n"
            "Descrição: Aplicação para gerenciar clientes, produtos e pedidos, "
            "facilitando o controle de vendas de um pequeno negócio."
        )

    # --- Gerenciamento de Clientes ---
    def mostrar_tela_clientes(self):
        self.limpar_container_principal()
        frame_clientes = ttk.LabelFrame(self.container_principal, text="Gerenciamento de Clientes", padding=10)
        frame_clientes.pack(fill=tk.BOTH, expand=True)

        # Formulário
        form_frame = ttk.Frame(frame_clientes, padding=10)
        form_frame.pack(fill=tk.X, pady=5)

        ttk.Label(form_frame, text="Nome:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_cliente_nome = ttk.Entry(form_frame, width=40)
        self.entry_cliente_nome.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form_frame, text="CPF:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_cliente_cpf = ttk.Entry(form_frame, width=40)
        self.entry_cliente_cpf.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Telefone:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_cliente_telefone = ttk.Entry(form_frame, width=40)
        self.entry_cliente_telefone.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(form_frame, text="Email:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.entry_cliente_email = ttk.Entry(form_frame, width=40)
        self.entry_cliente_email.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        form_frame.columnconfigure(1, weight=1) # Faz o entry expandir

        btn_adicionar_cliente = ttk.Button(form_frame, text="Adicionar Cliente", command=self.adicionar_cliente)
        btn_adicionar_cliente.grid(row=4, column=0, columnspan=2, pady=10)

        # Treeview para listar clientes
        cols_clientes = ("ID", "Nome", "CPF", "Telefone", "Email")
        self.tree_clientes = ttk.Treeview(frame_clientes, columns=cols_clientes, show="headings", height=10)
        for col in cols_clientes:
            self.tree_clientes.heading(col, text=col)
            self.tree_clientes.column(col, width=150 if col !="ID" else 50, anchor="w")
        self.tree_clientes.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbar para Treeview
        scrollbar_clientes = ttk.Scrollbar(self.tree_clientes, orient="vertical", command=self.tree_clientes.yview)
        self.tree_clientes.configure(yscrollcommand=scrollbar_clientes.set)
        scrollbar_clientes.pack(side="right", fill="y")

        self.listar_clientes()

    def adicionar_cliente(self):
        nome = self.entry_cliente_nome.get()
        cpf = self.entry_cliente_cpf.get()
        telefone = self.entry_cliente_telefone.get()
        email = self.entry_cliente_email.get()

        if not nome or not cpf:
            messagebox.showwarning("Campo Obrigatório", "Nome e CPF são obrigatórios!")
            return

        try:
            cursor = self.conn.cursor()
            sql = "INSERT INTO clientes (nome, cpf, telefone, email) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (nome, cpf, telefone, email))
            self.conn.commit()
            messagebox.showinfo("Sucesso", "Cliente adicionado com sucesso!")
            self.entry_cliente_nome.delete(0, tk.END)
            self.entry_cliente_cpf.delete(0, tk.END)
            self.entry_cliente_telefone.delete(0, tk.END)
            self.entry_cliente_email.delete(0, tk.END)
            self.listar_clientes()
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao adicionar cliente: {err}")
        finally:
            if cursor:
                cursor.close()
    
    def listar_clientes(self):
        for i in self.tree_clientes.get_children():
            self.tree_clientes.delete(i)
        try:
            cursor = self.conn.cursor(dictionary=True) # dictionary=True para pegar por nome da coluna
            cursor.execute("SELECT id, nome, cpf, telefone, email FROM clientes ORDER BY nome")
            clientes = cursor.fetchall()
            for cliente in clientes:
                self.tree_clientes.insert("", "end", values=(cliente['id'], cliente['nome'], cliente['cpf'], cliente['telefone'], cliente['email']))
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao listar clientes: {err}")
        finally:
            if cursor:
                cursor.close()

    # --- Gerenciamento de Produtos ---
    def mostrar_tela_produtos(self):
        self.limpar_container_principal()
        frame_produtos = ttk.LabelFrame(self.container_principal, text="Gerenciamento de Produtos", padding=10)
        frame_produtos.pack(fill=tk.BOTH, expand=True)

        # Formulário
        form_frame = ttk.Frame(frame_produtos, padding=10)
        form_frame.pack(fill=tk.X, pady=5)

        ttk.Label(form_frame, text="Nome:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_produto_nome = ttk.Entry(form_frame, width=40)
        self.entry_produto_nome.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Descrição:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_produto_descricao = tk.Text(form_frame, width=40, height=3) # Usando tk.Text para descrição
        self.entry_produto_descricao.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Preço (R$):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_produto_preco = ttk.Entry(form_frame, width=40)
        self.entry_produto_preco.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Estoque:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.entry_produto_estoque = ttk.Entry(form_frame, width=40)
        self.entry_produto_estoque.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        form_frame.columnconfigure(1, weight=1)

        btn_adicionar_produto = ttk.Button(form_frame, text="Adicionar Produto", command=self.adicionar_produto)
        btn_adicionar_produto.grid(row=4, column=0, columnspan=2, pady=10)

        # Treeview para listar produtos
        cols_produtos = ("ID", "Nome", "Preço (R$)", "Estoque", "Descrição")
        self.tree_produtos = ttk.Treeview(frame_produtos, columns=cols_produtos, show="headings", height=10)
        for col in cols_produtos:
            self.tree_produtos.heading(col, text=col)
            self.tree_produtos.column(col, width=120 if col not in ["ID", "Descrição"] else (50 if col == "ID" else 200) , anchor="w")
        self.tree_produtos.pack(fill=tk.BOTH, expand=True, pady=10)

        scrollbar_produtos = ttk.Scrollbar(self.tree_produtos, orient="vertical", command=self.tree_produtos.yview)
        self.tree_produtos.configure(yscrollcommand=scrollbar_produtos.set)
        scrollbar_produtos.pack(side="right", fill="y")

        self.listar_produtos()

    def adicionar_produto(self):
        nome = self.entry_produto_nome.get()
        descricao = self.entry_produto_descricao.get("1.0", tk.END).strip() # Pega todo o texto
        preco_str = self.entry_produto_preco.get()
        estoque_str = self.entry_produto_estoque.get()

        if not nome or not preco_str:
            messagebox.showwarning("Campo Obrigatório", "Nome e Preço são obrigatórios!")
            return
        try:
            preco = float(preco_str.replace(",", "."))
            estoque = int(estoque_str) if estoque_str else 0
        except ValueError:
            messagebox.showwarning("Dado Inválido", "Preço e Estoque devem ser números válidos.")
            return

        try:
            cursor = self.conn.cursor()
            sql = "INSERT INTO produtos (nome, descricao, preco, estoque) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (nome, descricao, preco, estoque))
            self.conn.commit()
            messagebox.showinfo("Sucesso", "Produto adicionado com sucesso!")
            self.entry_produto_nome.delete(0, tk.END)
            self.entry_produto_descricao.delete("1.0", tk.END)
            self.entry_produto_preco.delete(0, tk.END)
            self.entry_produto_estoque.delete(0, tk.END)
            self.listar_produtos()
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao adicionar produto: {err}")
        finally:
            if cursor:
                cursor.close()

    def listar_produtos(self):
        for i in self.tree_produtos.get_children():
            self.tree_produtos.delete(i)
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute("SELECT id, nome, preco, estoque, descricao FROM produtos ORDER BY nome")
            produtos = cursor.fetchall()
            for prod in produtos:
                self.tree_produtos.insert("", "end", values=(prod['id'], prod['nome'], f"{prod['preco']:.2f}", prod['estoque'], prod['descricao']))
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao listar produtos: {err}")
        finally:
            if cursor:
                cursor.close()

    # --- Gerenciamento de Pedidos ---
    def mostrar_tela_pedidos(self):
        self.limpar_container_principal()
        frame_pedidos = ttk.LabelFrame(self.container_principal, text="Gerenciamento de Pedidos", padding=10)
        frame_pedidos.pack(fill=tk.BOTH, expand=True)

        # --- Seção Novo Pedido ---
        novo_pedido_frame = ttk.LabelFrame(frame_pedidos, text="Novo Pedido", padding=10)
        novo_pedido_frame.pack(fill=tk.X, pady=10)

        # Selecionar Cliente
        ttk.Label(novo_pedido_frame, text="Cliente:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.combo_cliente_pedido = ttk.Combobox(novo_pedido_frame, state="readonly", width=37)
        self.combo_cliente_pedido.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.combo_cliente_pedido.bind("<<ComboboxSelected>>", self.selecionar_cliente_para_pedido)
        self.carregar_clientes_combobox()

        # Adicionar Produto ao Pedido
        produto_add_frame = ttk.Frame(novo_pedido_frame)
        produto_add_frame.grid(row=1, column=0, columnspan=4, pady=10, sticky="ew")

        ttk.Label(produto_add_frame, text="Produto:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.combo_produto_pedido = ttk.Combobox(produto_add_frame, state="readonly", width=30)
        self.combo_produto_pedido.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.carregar_produtos_combobox()

        ttk.Label(produto_add_frame, text="Qtd:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.entry_qtd_produto_pedido = ttk.Entry(produto_add_frame, width=5)
        self.entry_qtd_produto_pedido.grid(row=0, column=3, padx=5, pady=2, sticky="w")
        self.entry_qtd_produto_pedido.insert(0, "1") # Default quantity

        btn_add_item_pedido = ttk.Button(produto_add_frame, text="Adicionar Item", command=self.adicionar_item_ao_pedido_atual)
        btn_add_item_pedido.grid(row=0, column=4, padx=10, pady=2)
        
        novo_pedido_frame.columnconfigure(1, weight=1)
        produto_add_frame.columnconfigure(1, weight=1)

        # Treeview para itens do pedido atual
        cols_itens_pedido_atual = ("Produto", "Qtd", "Preço Unit.", "Subtotal")
        self.tree_itens_pedido_atual = ttk.Treeview(novo_pedido_frame, columns=cols_itens_pedido_atual, show="headings", height=5)
        for col in cols_itens_pedido_atual:
            self.tree_itens_pedido_atual.heading(col, text=col)
            self.tree_itens_pedido_atual.column(col, width=100, anchor="center")
        self.tree_itens_pedido_atual.column("Produto", width=200, anchor="w")
        self.tree_itens_pedido_atual.grid(row=2, column=0, columnspan=4, sticky="ew", pady=10, padx=5)
        
        scrollbar_itens_pedido = ttk.Scrollbar(self.tree_itens_pedido_atual, orient="vertical", command=self.tree_itens_pedido_atual.yview)
        self.tree_itens_pedido_atual.configure(yscrollcommand=scrollbar_itens_pedido.set)
        # Não empacotar scrollbar aqui, pois treeview está no grid. Posicionar ao lado se necessário.

        # Total e Botão Finalizar
        total_frame = ttk.Frame(novo_pedido_frame)
        total_frame.grid(row=3, column=0, columnspan=4, pady=10, sticky="e")
        ttk.Label(total_frame, text="Total do Pedido: R$", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Label(total_frame, textvariable=self.total_pedido_atual, font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        btn_finalizar_pedido = ttk.Button(novo_pedido_frame, text="Finalizar Pedido", command=self.finalizar_pedido, style="Accent.TButton")
        btn_finalizar_pedido.grid(row=4, column=0, columnspan=4, pady=10)
        ttk.Style().configure("Accent.TButton", font=("Arial", 10, "bold"), padding=5)


        # --- Seção Listar Pedidos ---
        listar_pedidos_frame = ttk.LabelFrame(frame_pedidos, text="Histórico de Pedidos", padding=10)
        listar_pedidos_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        cols_pedidos = ("ID Pedido", "Cliente", "Data", "Valor Total (R$)")
        self.tree_pedidos = ttk.Treeview(listar_pedidos_frame, columns=cols_pedidos, show="headings", height=8)
        for col in cols_pedidos:
            self.tree_pedidos.heading(col, text=col)
            self.tree_pedidos.column(col, width=150, anchor="w")
        self.tree_pedidos.column("ID Pedido", width=80, anchor="center")
        self.tree_pedidos.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar_pedidos = ttk.Scrollbar(self.tree_pedidos, orient="vertical", command=self.tree_pedidos.yview)
        self.tree_pedidos.configure(yscrollcommand=scrollbar_pedidos.set)
        scrollbar_pedidos.pack(side="right", fill="y")

        self.listar_pedidos_registrados()
        self.resetar_novo_pedido_form() # Garante que o form de novo pedido está limpo

    def carregar_clientes_combobox(self):
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute("SELECT id, nome FROM clientes ORDER BY nome")
            clientes = cursor.fetchall()
            self.clientes_map = {f"{c['nome']} (ID: {c['id']})": c['id'] for c in clientes} # Mapa para pegar ID
            self.combo_cliente_pedido['values'] = list(self.clientes_map.keys())
        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao carregar clientes: {err}")
        finally:
            if cursor: cursor.close()

    def selecionar_cliente_para_pedido(self, event=None):
        selected_display_name = self.combo_cliente_pedido.get()
        if selected_display_name in self.clientes_map:
            self.cliente_selecionado_pedido = self.clientes_map[selected_display_name]
        else:
            self.cliente_selecionado_pedido = None

    def carregar_produtos_combobox(self):
        try:
            cursor = self.conn.cursor(dictionary=True)
            # Mostrar apenas produtos com estoque > 0 (ou remover essa condição se quiser vender sem estoque)
            cursor.execute("SELECT id, nome, preco FROM produtos WHERE estoque > 0 ORDER BY nome") 
            produtos = cursor.fetchall()
            self.produtos_map = {f"{p['nome']} (R$ {p['preco']:.2f})": {'id': p['id'], 'preco': p['preco']} for p in produtos}
            self.combo_produto_pedido['values'] = list(self.produtos_map.keys())
        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao carregar produtos: {err}")
        finally:
            if cursor: cursor.close()

    def adicionar_item_ao_pedido_atual(self):
        produto_display_name = self.combo_produto_pedido.get()
        qtd_str = self.entry_qtd_produto_pedido.get()

        if not produto_display_name:
            messagebox.showwarning("Seleção Necessária", "Selecione um produto.")
            return
        if not qtd_str:
            messagebox.showwarning("Quantidade Necessária", "Informe a quantidade.")
            return
        
        try:
            quantidade = int(qtd_str)
            if quantidade <= 0:
                messagebox.showwarning("Quantidade Inválida", "A quantidade deve ser maior que zero.")
                return
        except ValueError:
            messagebox.showwarning("Quantidade Inválida", "A quantidade deve ser um número inteiro.")
            return

        produto_info = self.produtos_map.get(produto_display_name)
        if not produto_info:
            messagebox.showerror("Erro", "Produto selecionado não encontrado no mapa.")
            return

        produto_id = produto_info['id']
        preco_unitario = produto_info['preco']
        nome_produto = produto_display_name.split(" (R$")[0] # Extrai nome
        subtotal = quantidade * preco_unitario

        # Verificar se o produto já está na lista para evitar duplicidade ou somar quantidades
        # Por simplicidade, vamos permitir adicionar o mesmo produto múltiplas vezes como itens separados.
        # Para agrupar, seria necessário verificar se produto_id já existe em self.itens_pedido_atual e atualizar a quantidade.

        self.itens_pedido_atual.append({
            'produto_id': produto_id,
            'nome_produto': nome_produto,
            'quantidade': quantidade,
            'preco_unitario': preco_unitario,
            'subtotal': subtotal
        })
        self.atualizar_tree_itens_pedido_atual()
        self.calcular_total_pedido_atual()

    def atualizar_tree_itens_pedido_atual(self):
        for i in self.tree_itens_pedido_atual.get_children():
            self.tree_itens_pedido_atual.delete(i)
        
        for item in self.itens_pedido_atual:
            self.tree_itens_pedido_atual.insert("", "end", values=(
                item['nome_produto'], 
                item['quantidade'], 
                f"{item['preco_unitario']:.2f}",
                f"{item['subtotal']:.2f}"
            ))

    def calcular_total_pedido_atual(self):
        total = sum(item['subtotal'] for item in self.itens_pedido_atual)
        self.total_pedido_atual.set(f"{total:.2f}")


    def finalizar_pedido(self):
        if not self.cliente_selecionado_pedido:
            messagebox.showwarning("Cliente Necessário", "Selecione um cliente para o pedido.")
            return
        if not self.itens_pedido_atual:
            messagebox.showwarning("Itens Necessários", "Adicione pelo menos um item ao pedido.")
            return

        valor_total_pedido = float(self.total_pedido_atual.get())
        cursor = None # Inicializar cursor
        try:
            cursor = self.conn.cursor()
            # Inserir na tabela pedidos
            sql_pedido = "INSERT INTO pedidos (cliente_id, valor_total, data_pedido) VALUES (%s, %s, %s)"
            data_agora = datetime.now()
            cursor.execute(sql_pedido, (self.cliente_selecionado_pedido, valor_total_pedido, data_agora))
            pedido_id = cursor.lastrowid # Pega o ID do pedido inserido

            # Inserir na tabela itens_pedido e atualizar estoque
            sql_item_pedido = "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (%s, %s, %s, %s)"
            sql_update_estoque = "UPDATE produtos SET estoque = estoque - %s WHERE id = %s"

            for item in self.itens_pedido_atual:
                cursor.execute(sql_item_pedido, (pedido_id, item['produto_id'], item['quantidade'], item['preco_unitario']))
                cursor.execute(sql_update_estoque, (item['quantidade'], item['produto_id']))
            
            self.conn.commit()
            messagebox.showinfo("Sucesso", f"Pedido Nº {pedido_id} finalizado com sucesso!")
            self.resetar_novo_pedido_form()
            self.listar_pedidos_registrados()
            self.carregar_produtos_combobox() # Recarregar produtos pois o estoque mudou
        
        except mysql.connector.Error as err:
            self.conn.rollback() # Desfaz transação em caso de erro
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao finalizar pedido: {err}")
        finally:
            if cursor:
                cursor.close()

    def resetar_novo_pedido_form(self):
        self.itens_pedido_atual.clear()
        self.atualizar_tree_itens_pedido_atual()
        self.total_pedido_atual.set(0.0)
        self.combo_cliente_pedido.set('')
        self.combo_produto_pedido.set('')
        self.entry_qtd_produto_pedido.delete(0, tk.END)
        self.entry_qtd_produto_pedido.insert(0, "1")
        self.cliente_selecionado_pedido = None


    def listar_pedidos_registrados(self):
        for i in self.tree_pedidos.get_children():
            self.tree_pedidos.delete(i)
        try:
            cursor = self.conn.cursor(dictionary=True)
            sql = """
                SELECT p.id, c.nome as nome_cliente, p.data_pedido, p.valor_total
                FROM pedidos p
                JOIN clientes c ON p.cliente_id = c.id
                ORDER BY p.data_pedido DESC
            """
            cursor.execute(sql)
            pedidos = cursor.fetchall()
            for pedido in pedidos:
                data_formatada = pedido['data_pedido'].strftime("%d/%m/%Y %H:%M") if pedido['data_pedido'] else "N/A"
                self.tree_pedidos.insert("", "end", values=(
                    pedido['id'], 
                    pedido['nome_cliente'], 
                    data_formatada,
                    f"{pedido['valor_total']:.2f}"
                ))
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao listar pedidos: {err}")
        finally:
            if cursor:
                cursor.close()

    def __del__(self):
        """Fecha a conexão com o banco ao destruir o objeto."""
        if hasattr(self, 'conn') and self.conn and self.conn.is_connected():
            self.conn.close()


# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    root_tk = tk.Tk()
    app = SistemaVendasApp(root_tk)
    root_tk.mainloop()