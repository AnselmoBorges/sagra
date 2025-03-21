# SAGRA - Sistema de Acompanhamento e Gerenciamento de Reabilitação de Atletas
# Autor: Anselmo Borges, Pedro Bala Pascal, Luis Eduardo dos Santos
# Data: 16/03/2025
# Descrição: Sistema para acompanhamento e gerenciamento da reabilitação de atletas
#            de rugby após cirurgia de reconstrução do LCA.

# Importação das bibliotecas necessárias
import streamlit as st
import duckdb
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import os
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import bcrypt
import pandas as pd

# Configuração da página Streamlit (deve ser a primeira chamada Streamlit)
st.set_page_config(
    page_title="SAGRA - Reabilitação LCA",
    page_icon="🏉",
    layout="wide"
)

# Função auxiliar para extrair número de dias do período
def extrair_dias(periodo):
    """
    Extrai o número de dias de um período especificado no formato 'X a Y dias' ou 'após X dias'
    Args:
        periodo (str): String contendo o período
    Returns:
        int: Número de dias do período
    """
    if 'após' in periodo:
        return int(periodo.split(' ')[1])
    else:
        dias = periodo.split(' a ')
        return int(dias[-1].split(' ')[0])

# Carrega as configurações de autenticação
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Cria o autenticador
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Inicializa o status de autenticação
name, authentication_status, username = authenticator.login('Login', 'main')

# Função de inicialização do banco de dados
def init_database():
    """Inicializa a conexão com o banco de dados DuckDB e cria as tabelas se necessário"""
    try:
        # Tenta primeiro uma conexão exclusiva
        conn = duckdb.connect('SAGRA.db')
        
        # Cria as sequências para os IDs
        conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS seq_pacientes START 1;
            CREATE SEQUENCE IF NOT EXISTS seq_lesoes START 1;
            CREATE SEQUENCE IF NOT EXISTS seq_fases START 1;
            CREATE SEQUENCE IF NOT EXISTS seq_progresso START 1;
        """)
        
        # Cria as tabelas se não existirem
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_pacientes'),
                nome VARCHAR UNIQUE NOT NULL,
                data_nascimento DATE,
                posicao VARCHAR,
                clube VARCHAR,
                data_cirurgia DATE
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lesoes (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_lesoes'),
                paciente_id INTEGER NOT NULL,
                tipo_lesao VARCHAR NOT NULL,
                data_lesao DATE,
                data_cirurgia DATE,
                observacoes TEXT,
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fases_reabilitacao (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_fases'),
                fase VARCHAR NOT NULL,
                periodo_aproximado VARCHAR NOT NULL,
                atividades_liberadas TEXT,
                testes_especificos TEXT,
                tratamentos TEXT,
                preparacao_fisica TEXT,
                tecnicas_rugby TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS progresso (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_progresso'),
                paciente_id INTEGER NOT NULL,
                fase VARCHAR NOT NULL,
                data_inicio DATE NOT NULL,
                data_fim DATE,
                status VARCHAR DEFAULT 'Em andamento',
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
                UNIQUE(paciente_id, fase, data_inicio)
            )
        """)
        
        # Insere as fases padrão se a tabela estiver vazia
        if conn.execute("SELECT COUNT(*) FROM fases_reabilitacao").fetchone()[0] == 0:
            conn.execute("""
                INSERT INTO fases_reabilitacao (fase, periodo_aproximado, atividades_liberadas, testes_especificos, tratamentos, preparacao_fisica, tecnicas_rugby) VALUES
                ('Fase 1', '1 a 14 dias', 'Mobilização passiva, Exercícios isométricos', 'Avaliação de edema, Avaliação de ADM', 'Crioterapia,Eletroterapia,Exercícios de mobilização passiva', 'Isometria de quadríceps (Progressão),Exercícios de ADM (Progressão)', 'Tackle:1,Passe:1,Scrum:1,Ruck:1,Treino em campo:1'),
                ('Fase 2', '15 a 28 dias', 'Exercícios em CCA, Bicicleta estacionária', 'Teste de força muscular, Avaliação de marcha', 'Exercícios ativos,Treino de marcha,Fortalecimento', 'Leg Press (Progressão),Agachamento (Restrição),Bicicleta (Completo)', 'Tackle:1,Passe:2,Scrum:1,Ruck:1,Treino em campo:1'),
                ('Fase 3', '29 a 90 dias', 'Exercícios em CCF, Corrida em linha reta', 'Teste de agilidade, Avaliação funcional', 'Exercícios pliométricos,Treino de corrida,Core', 'Agachamento (Progressão),Corrida (Progressão),Pliometria (Restrição)', 'Tackle:1,Passe:3,Scrum:2,Ruck:2,Treino em campo:2'),
                ('Fase 4', '91 a 180 dias', 'Exercícios específicos do rugby, Treino com bola', 'Teste de salto, Y-Balance Test', 'Treino específico,Agilidade,Potência', 'Pliometria (Progressão),Agilidade (Progressão),Potência (Progressão)', 'Tackle:2,Passe:3,Scrum:2,Ruck:2,Treino em campo:3'),
                ('Fase 5', '181 a 240 dias', 'Retorno gradual ao treino com equipe', 'Testes específicos do rugby', 'Treino com equipe,Contato gradual,Jogo simulado', 'Treino completo (Progressão),Contato (Progressão)', 'Tackle:2,Passe:3,Scrum:3,Ruck:3,Treino em campo:3'),
                ('Alta', 'após 240 dias', 'Retorno completo às atividades', '-', 'Manutenção,Prevenção', 'Treino completo (Completo)', 'Tackle:3,Passe:3,Scrum:3,Ruck:3,Treino em campo:3')
            """)
        
        # Insere dados mocados se a tabela de pacientes estiver vazia
        if conn.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0] == 0:
            # Lista de nomes fictícios de atletas
            atletas_mock = [
                ("João Silva", "Pilar", "Bandeirantes Rugby"),
                ("Pedro Santos", "Hooker", "São José Rugby"),
                ("Lucas Oliveira", "Segunda Linha", "Pasteur Athletique"),
                ("Matheus Souza", "Terceira Linha", "Jacareí Rugby"),
                ("Gabriel Costa", "Scrum-half", "São Paulo Athletic Club"),
                ("Rafael Pereira", "Fly-half", "Curitiba Rugby"),
                ("Thiago Lima", "Centro", "Niterói Rugby"),
                ("Bruno Fernandes", "Ponta", "Desterro Rugby"),
                ("Diego Alves", "Fullback", "Charrua Rugby"),
                ("Marcelo Rocha", "Pilar", "BH Rugby"),
                ("Felipe Santos", "Hooker", "Guanabara Rugby"),
                ("André Costa", "Segunda Linha", "Albatroz Rugby"),
                ("Ricardo Oliveira", "Terceira Linha", "Rio Branco Rugby"),
                ("Gustavo Silva", "Scrum-half", "Urutu Rugby"),
                ("Henrique Lima", "Fly-half", "Templários Rugby"),
                ("Carlos Eduardo", "Centro", "Vitória Rugby"),
                ("Paulo Roberto", "Ponta", "Recife Rugby"),
                ("Fernando Souza", "Fullback", "Goianos Rugby"),
                ("Roberto Carlos", "Pilar", "Brasília Rugby"),
                ("José Antonio", "Hooker", "Cuiabá Rugby"),
                ("Miguel Santos", "Segunda Linha", "Londrina Rugby"),
                ("Daniel Costa", "Terceira Linha", "Maringá Rugby"),
                ("Alexandre Lima", "Scrum-half", "Cascavel Rugby"),
                ("Marcos Paulo", "Fly-half", "Blumenau Rugby"),
                ("Victor Hugo", "Centro", "Floripa Rugby"),
                ("Leonardo Silva", "Ponta", "Porto Alegre Rugby"),
                ("Eduardo Santos", "Fullback", "Pelotas Rugby"),
                ("Rodrigo Costa", "Pilar", "Santa Maria Rugby"),
                ("Fábio Lima", "Hooker", "Caxias Rugby"),
                ("Guilherme Souza", "Segunda Linha", "Bento Rugby"),
                ("Renato Silva", "Terceira Linha", "Farrapos Rugby"),
                ("Maurício Santos", "Scrum-half", "Serra Rugby"),
                ("Augusto Lima", "Fly-half", "Universitário Rugby"),
                ("Caio Costa", "Centro", "ABC Rugby"),
                ("Igor Santos", "Ponta", "Natal Rugby"),
                ("Leandro Silva", "Fullback", "Maceió Rugby"),
                ("Júlio César", "Pilar", "Aracaju Rugby"),
                ("Márcio Lima", "Hooker", "Salvador Rugby"),
                ("Nelson Costa", "Segunda Linha", "Vitória Rugby"),
                ("Otávio Santos", "Terceira Linha", "Vila Velha Rugby"),
                ("Pablo Silva", "Scrum-half", "Espírito Santo Rugby"),
                ("Quintino Lima", "Fly-half", "Juiz de Fora Rugby"),
                ("Rogério Costa", "Centro", "Uberlândia Rugby"),
                ("Sérgio Santos", "Ponta", "Uberaba Rugby"),
                ("Tiago Silva", "Fullback", "Montes Claros Rugby"),
                ("Ulisses Lima", "Pilar", "Ouro Preto Rugby"),
                ("Vitor Costa", "Hooker", "Lavras Rugby"),
                ("Wagner Santos", "Segunda Linha", "Pouso Alegre Rugby"),
                ("Xavier Silva", "Terceira Linha", "Poços Rugby"),
                ("Yuri Lima", "Scrum-half", "Varginha Rugby")
            ]

            # Insere os atletas
            for nome, posicao, clube in atletas_mock:
                # Gera uma data de nascimento aleatória entre 1990 e 2000
                ano = int(conn.execute("SELECT 1990 + abs(random() % 10)").fetchone()[0])
                mes = int(conn.execute("SELECT 1 + abs(random() % 12)").fetchone()[0])
                dia = int(conn.execute("SELECT 1 + abs(random() % 28)").fetchone()[0])
                data_nascimento = datetime(ano, mes, dia).date()
                
                # Insere o atleta
                conn.execute("""
                    INSERT INTO pacientes (nome, data_nascimento, posicao, clube)
                    VALUES (?, ?, ?, ?)
                """, [nome, data_nascimento, posicao, clube])
                
                # Obtém o ID do atleta inserido
                atleta_id = conn.execute("SELECT id FROM pacientes WHERE nome = ?", [nome]).fetchone()[0]
                
                # Define aleatoriamente se o atleta terá lesão (70% de chance)
                if int(conn.execute("SELECT abs(random() % 100)").fetchone()[0]) < 70:
                    # Tipos de lesão possíveis
                    tipos_lesao = [
                        "LCA", "LCP", "Menisco", "Ligamento Colateral", "Tendinite Patelar",
                        "Luxação de Ombro", "Ruptura de Manguito Rotador", "Lesão de Labrum",
                        "Fratura de Clavícula", "Entorse de Tornozelo"
                    ]
                    tipo_lesao = tipos_lesao[int(conn.execute("SELECT abs(random() % 10)").fetchone()[0])]
                    
                    # Gera uma data de lesão nos últimos 2 anos
                    dias_atras_lesao = int(conn.execute("SELECT 1 + abs(random() % 730)").fetchone()[0])
                    data_lesao = datetime.now().date() - timedelta(days=dias_atras_lesao)
                    
                    # Data da cirurgia alguns dias após a lesão
                    dias_ate_cirurgia = int(conn.execute("SELECT 3 + abs(random() % 30)").fetchone()[0])
                    data_cirurgia = data_lesao + timedelta(days=dias_ate_cirurgia)
                    
                    # Insere a lesão
                    conn.execute("""
                        INSERT INTO lesoes (paciente_id, tipo_lesao, data_lesao, data_cirurgia, observacoes)
                        VALUES (?, ?, ?, ?, ?)
                    """, [atleta_id, tipo_lesao, data_lesao, data_cirurgia, "Lesão durante partida oficial"])
                    
                    # Atualiza a data da cirurgia no paciente
                    conn.execute("""
                        UPDATE pacientes 
                        SET data_cirurgia = ? 
                        WHERE id = ?
                    """, [data_cirurgia, atleta_id])
                    
                    # Calcula em qual fase o atleta está baseado na data da cirurgia
                    dias_desde_cirurgia = (datetime.now().date() - data_cirurgia).days
                    
                    # Define a fase atual
                    fase_atual = None
                    if dias_desde_cirurgia <= 14:
                        fase_atual = "Fase 1"
                    elif dias_desde_cirurgia <= 28:
                        fase_atual = "Fase 2"
                    elif dias_desde_cirurgia <= 90:
                        fase_atual = "Fase 3"
                    elif dias_desde_cirurgia <= 180:
                        fase_atual = "Fase 4"
                    elif dias_desde_cirurgia <= 240:
                        fase_atual = "Fase 5"
                    else:
                        fase_atual = "Alta"
                    
                    # Registra o progresso
                    if fase_atual:
                        conn.execute("""
                            INSERT INTO progresso (paciente_id, fase, data_inicio, data_fim, status)
                            VALUES (?, ?, ?, ?, 'Em andamento')
                        """, [atleta_id, fase_atual, data_cirurgia, None])

        return conn
    except Exception as e:
        if "Conflicting lock" in str(e):
            # Se falhar por causa do lock, tenta em modo read-only
            st.warning("Banco de dados aberto em modo somente leitura devido a outro processo estar usando-o.")
            return duckdb.connect('SAGRA.db', read_only=True)
        else:
            # Se for outro erro, mostra o erro e para
            st.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        st.stop()

# Container centralizado para o login
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("logo_sagra.png", use_container_width=True)
    st.title("SAGRA")
    st.caption("Sistema de Acompanhamento e Gerenciamento de Reabilitação de Atletas")
    
    if authentication_status == False:
        st.error('❌ Usuário ou senha incorretos')
    elif authentication_status == None:
        st.info('👋 Por favor, faça login para continuar')

# Se autenticado, mostra o conteúdo principal
if authentication_status:
    try:
        # Inicializa a conexão com o banco de dados
        conn = init_database()

        # Mostra o menu de logout e boas-vindas na sidebar
        with st.sidebar:
            st.title("🏉 SAGRA")
            st.write(f'Bem-vindo *{name}*')
            authenticator.logout('Logout', 'main')
            st.divider()
            
            # Menu de Navegação
            st.subheader("Menu de Navegação")
            menu_option = st.radio(
                "Selecione uma opção:",
                ["📊 Dashboard",
                 "👥 Cadastro de Atletas",
                 "🏥 Cadastro de Lesões",
                 "🔍 Busca e Relatórios"]
            )
            
            # Filtros específicos para busca
            if menu_option == "🔍 Busca e Relatórios":
                st.subheader("Filtros")
                busca_tipo = st.selectbox(
                    "Tipo de Busca",
                    ["Por Atleta", "Por Lesão", "Por Período"]
                )
                
                if busca_tipo == "Por Atleta":
                    # Busca todos os atletas no banco
                    atletas = conn.execute("SELECT DISTINCT nome FROM pacientes ORDER BY nome").df()
                    atleta_selecionado = st.selectbox("Selecione o Atleta", atletas['nome'].tolist())
                elif busca_tipo == "Por Lesão":
                    lesoes = conn.execute("SELECT DISTINCT tipo_lesao FROM lesoes ORDER BY tipo_lesao").df()
                    lesao_selecionada = st.selectbox("Tipo de Lesão", lesoes['tipo_lesao'].tolist())
                elif busca_tipo == "Por Período":
                    data_inicio = st.date_input("Data Inicial")
                    data_fim = st.date_input("Data Final")
            
            st.divider()

        # Conteúdo principal baseado na seleção do menu
        if menu_option == "📊 Dashboard":
            st.title("Dashboard - Visão Geral")
            
            # Estatísticas gerais em cards do Streamlit
            col1, col2, col3 = st.columns(3)
            with col1:
                total_atletas = conn.execute("SELECT COUNT(DISTINCT nome) as total FROM pacientes").df()['total'][0]
                st.metric("Total de Atletas", total_atletas)
            with col2:
                atletas_ativos = conn.execute("""
                    SELECT COUNT(DISTINCT p.nome) as total 
                    FROM pacientes p 
                    WHERE EXISTS (
                        SELECT 1 FROM progresso pr 
                        WHERE pr.paciente_id = p.id 
                        AND pr.status = 'Em andamento'
                    )
                """).df()['total'][0]
                st.metric("Atletas em Tratamento", atletas_ativos)
            with col3:
                total_lesoes = conn.execute("SELECT COUNT(DISTINCT tipo_lesao) as total FROM lesoes").df()['total'][0]
                st.metric("Tipos de Lesões", total_lesoes)
            
            # Lista dos últimos atletas cadastrados
            st.subheader("Últimos Atletas Cadastrados")
            ultimos_atletas = conn.execute("""
                SELECT 
                    p.nome, 
                    p.data_cirurgia,
                    (SELECT tipo_lesao 
                     FROM lesoes l 
                     WHERE l.paciente_id = p.id 
                     ORDER BY l.data_lesao DESC 
                     LIMIT 1) as lesao
                FROM pacientes p
                ORDER BY data_cirurgia DESC
                LIMIT 5
            """).df()
            st.dataframe(ultimos_atletas, hide_index=True, use_container_width=True)

            # Container para o formulário de novo paciente
            with st.container():
                st.subheader("Novo Acompanhamento")
                
                # Campos do formulário em colunas
                col1, col2 = st.columns([2, 1])
                with col1:
                    nome_atleta = st.text_input('Nome do Atleta')
                with col2:
                    data_cirurgia = st.date_input(
                        "Data da Cirurgia",
                        value=(datetime.now().date() - timedelta(days=140)),
                        min_value=datetime(2023, 1, 1).date(),
                        max_value=datetime.now().date()
                    )

                # Processamento do formulário
                if nome_atleta and data_cirurgia:
                    try:
                        # Registra ou atualiza o paciente
                        conn.execute("""
                            INSERT INTO pacientes (nome, data_cirurgia)
                            VALUES (?, ?)
                            ON CONFLICT (nome) DO UPDATE SET
                                data_cirurgia = excluded.data_cirurgia;
                        """, [nome_atleta, data_cirurgia])
                        
                        # Obtém o ID do paciente
                        paciente_id = conn.execute("""
                            SELECT id FROM pacientes WHERE nome = ?
                        """, [nome_atleta]).fetchone()[0]
                    
                        # Busca as fases do banco de dados
                        fases_df = conn.execute("""
                            SELECT 
                                id,
                                fase::VARCHAR as fase,
                                periodo_aproximado::VARCHAR as periodo_aproximado,
                                atividades_liberadas::VARCHAR as atividades_liberadas,
                                testes_especificos::VARCHAR as testes_especificos,
                                tratamentos::VARCHAR as tratamentos,
                                preparacao_fisica::VARCHAR as preparacao_fisica,
                                tecnicas_rugby::VARCHAR as tecnicas_rugby
                            FROM fases_reabilitacao
                            ORDER BY id
                        """).df()
                        
                        # Cálculo das datas de cada fase
                        dados_fases = []
                        data_atual = data_cirurgia
                        
                        # Processamento de cada fase
                        for _, row in fases_df.iterrows():
                            dias = extrair_dias(row['periodo_aproximado'])
                            
                            # Cálculo das datas de início e fim de cada fase
                            if row['fase'] == 'Fase 1':
                                data_inicio = data_atual
                                data_fim = data_inicio + timedelta(days=dias)
                            elif row['fase'] == 'Alta':
                                data_inicio = data_cirurgia + timedelta(days=240)
                                data_fim = data_inicio + timedelta(days=30)
                            else:
                                data_inicio = data_atual + timedelta(days=1)
                                data_fim = data_inicio + timedelta(days=dias - 1)
                            
                            # Processamento dos tratamentos
                            tratamentos = row['tratamentos'].split(',') if row['tratamentos'] else []
                            
                            # Montagem do dicionário de dados da fase
                            dados_fases.append({
                                'Fase': str(row['fase']),
                                'Data Início': data_inicio.strftime('%d/%m/%Y'),
                                'Data Fim': data_fim.strftime('%d/%m/%Y'),
                                'Duração (dias)': str(dias) if row['fase'] != 'Alta' else 'Contínuo',
                                'Atividades': str(row['atividades_liberadas']),
                                'Testes': str(row['testes_especificos']),
                                'Tratamentos': tratamentos,
                                'Preparacao_Fisica': str(row['preparacao_fisica']),
                                'tecnicas_rugby': str(row['tecnicas_rugby'])
                            })
                            data_atual = data_fim
                        
                        # Exibição das informações do paciente
                        st.subheader(f'Cronograma de Reabilitação para: {nome_atleta}')
                        
                        # Datas importantes
                        data_alta = data_cirurgia + timedelta(days=240)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f'**Data da Cirurgia:** {data_cirurgia.strftime("%d/%m/%Y")}')
                        with col2:
                            st.info(f'**Previsão de Alta:** {data_alta.strftime("%d/%m/%Y")}')
                        
                        # Cronograma detalhado
                        st.subheader('Cronograma Detalhado')
                        st.dataframe(
                            dados_fases,
                            column_config={
                                "Fase": st.column_config.TextColumn("Fase"),
                                "Data Início": st.column_config.TextColumn("Início"),
                                "Data Fim": st.column_config.TextColumn("Fim"),
                                "Duração (dias)": st.column_config.TextColumn("Dias"),
                                "Atividades": st.column_config.TextColumn("Atividades Liberadas", width="large"),
                                "Testes": st.column_config.TextColumn("Testes Específicos", width="medium")
                            },
                            hide_index=True,
                            use_container_width=True
                        )
                        
                        # Detalhamento das fases
                        st.subheader('Detalhamento das Fases')
                        for fase in dados_fases:
                            with st.expander(f"{fase['Fase']} ({fase['Data Início']} a {fase['Data Fim']})"):
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.write("**Atividades Liberadas:**")
                                    st.write(fase['Atividades'])
                                    st.write("**Testes Específicos:**")
                                    st.write(fase['Testes'] if fase['Testes'] != '-' else "Nenhum teste específico nesta fase")
                                
                                with col2:
                                    st.write("**Tratamentos e Exercícios:**")
                                    for tratamento in fase['Tratamentos']:
                                        st.write(f"- {tratamento.strip()}")
                                
                                with col3:
                                    st.write("**Preparação Física:**")
                                    for exercicio in fase['Preparacao_Fisica'].split(','):
                                        status = exercicio.strip()
                                        if '(Completo)' in status:
                                            st.success(f"- {status}")
                                        elif '(Restrição)' in status:
                                            st.error(f"- {status}")
                                        elif '(Progressão)' in status:
                                            st.warning(f"- {status}")
                                        else:
                                            st.write(f"- {status}")
                        
                        # Progresso do tratamento
                        st.subheader('Progresso do Tratamento')
                        dias_desde_cirurgia = (datetime.now().date() - data_cirurgia).days
                        progresso = min(100, max(0, (dias_desde_cirurgia / 240) * 100))
                        
                        # Barra de progresso (valor entre 0 e 1)
                        st.progress(max(0, min(1, progresso / 100)))
                        st.write(f"Progresso Total: {progresso:.1f}% ({dias_desde_cirurgia} dias desde a cirurgia)")
                        
                        # Identificação e registro da fase atual
                        fase_atual = None
                        for fase in dados_fases:
                            data_inicio = datetime.strptime(fase['Data Início'], '%d/%m/%Y').date()
                            data_fim = datetime.strptime(fase['Data Fim'], '%d/%m/%Y').date()
                            if data_inicio <= datetime.now().date() <= data_fim:
                                fase_atual = fase
                                st.success(f"**Fase Atual:** {fase['Fase']}")
                                
                                # Registra progresso
                                conn.execute("""
                                    INSERT INTO progresso (paciente_id, fase, data_inicio, data_fim, status)
                                    VALUES (?, ?, ?, ?, 'Em andamento')
                                    ON CONFLICT (paciente_id, fase, data_inicio) DO UPDATE
                                    SET status = 'Em andamento',
                                        data_fim = excluded.data_fim
                                """, [paciente_id, fase['Fase'], data_inicio, data_fim])
                                break

                        # Métricas do progresso
                        semana_atual = dias_desde_cirurgia // 7
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Semana Atual", f"{semana_atual}ª semana")
                        with col2:
                            st.metric("Dias Pós-Cirurgia", f"{dias_desde_cirurgia} dias")
                        with col3:
                            st.metric("Progresso Total", f"{progresso:.1f}%")
                        
                        if fase_atual:
                            # Resumo das atividades atuais
                            st.subheader('Resumo das Atividades Atuais')
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write("**🏃 Atividades Liberadas**")
                                st.info(fase_atual['Atividades'])
                                st.write("**🎯 Objetivos da Fase**")
                                st.success(f"- Fase: {fase_atual['Fase']}\n- Duração: {fase_atual['Duração (dias)']} dias")
                            with col2:
                                st.write("**📊 Testes e Avaliações**")
                                st.warning(fase_atual['Testes'] if fase_atual['Testes'] != '-' else "Nenhum teste específico nesta fase")
                                
                                # Análise dos exercícios
                                st.subheader('Status dos Exercícios')
                                exercicios = fase_atual['Preparacao_Fisica'].split(',')
                                status_exercicios = {
                                    'Completo': len([ex for ex in exercicios if '(Completo)' in ex]),
                                    'Em Progressão': len([ex for ex in exercicios if '(Progressão)' in ex]),
                                    'Com Restrição': len([ex for ex in exercicios if '(Restrição)' in ex])
                                }
                                
                                fig_pizza = px.pie(
                                    values=list(status_exercicios.values()),
                                    names=list(status_exercicios.keys()),
                                    title='Distribuição dos Exercícios por Status',
                                    color_discrete_map={
                                        'Completo': 'green',
                                        'Em Progressão': 'orange',
                                        'Com Restrição': 'red'
                                    }
                                )
                                st.plotly_chart(fig_pizza, use_container_width=True)
                                
                                # Recomendações
                                st.subheader('Recomendações e Próximos Passos')
                                st.write("""
                                **Pontos de Atenção:**
                                - Continue seguindo rigorosamente o protocolo de exercícios
                                - Mantenha o acompanhamento regular com a equipe de reabilitação
                                - Observe qualquer sinal de dor ou desconforto anormal
                                
                                **Próximos Objetivos:**
                                - Progredir nos exercícios marcados como 'Em Progressão'
                                - Preparar-se para os próximos testes e avaliações
                                - Manter o fortalecimento muscular e ganho de resistência
                                """)
                                
                    except Exception as e:
                        st.error(f"Erro ao processar dados: {str(e)}")

        elif menu_option == "👥 Cadastro de Atletas":
            st.title("Cadastro de Atletas")
            # Interface para cadastro de novo atleta
            with st.form("cadastro_atleta"):
                nome_atleta = st.text_input("Nome do Atleta")
                data_nascimento = st.date_input("Data de Nascimento")
                posicao = st.selectbox("Posição", ["Pilar", "Hooker", "Segunda Linha", "Terceira Linha", "Scrum-half", "Fly-half", "Centro", "Ponta", "Fullback"])
                clube = st.text_input("Clube")
                submitted = st.form_submit_button("Cadastrar Atleta")
                
                if submitted:
                    try:
                        conn.execute("""
                            INSERT INTO pacientes (nome, data_nascimento, posicao, clube)
                            VALUES (?, ?, ?, ?)
                        """, [nome_atleta, data_nascimento, posicao, clube])
                        st.success("Atleta cadastrado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar atleta: {str(e)}")

        elif menu_option == "🏥 Cadastro de Lesões":
            st.title("Cadastro de Lesões")
            # Interface para cadastro de lesão
            with st.form("cadastro_lesao"):
                # Busca atletas cadastrados
                atletas = conn.execute("SELECT id, nome FROM pacientes ORDER BY nome").df()
                atleta_selecionado = st.selectbox("Atleta", atletas['nome'].tolist())
                
                tipo_lesao = st.selectbox("Tipo de Lesão", [
                    "LCA", "LCP", "Menisco", "Ligamento Colateral", "Tendinite Patelar",
                    "Luxação de Ombro", "Ruptura de Manguito Rotador", "Lesão de Labrum",
                    "Fratura de Clavícula", "Entorse de Tornozelo"
                ])
                data_lesao = st.date_input("Data da Lesão")
                data_cirurgia = st.date_input("Data da Cirurgia")
                observacoes = st.text_area("Observações")
                submitted = st.form_submit_button("Cadastrar Lesão")
                
                if submitted:
                    try:
                        # Obtém o ID do atleta
                        atleta_id = conn.execute("SELECT id FROM pacientes WHERE nome = ?", [atleta_selecionado]).fetchone()[0]
                        
                        conn.execute("""
                            INSERT INTO lesoes (paciente_id, tipo_lesao, data_lesao, data_cirurgia, observacoes)
                            VALUES (?, ?, ?, ?, ?)
                        """, [atleta_id, tipo_lesao, data_lesao, data_cirurgia, observacoes])
                        st.success("Lesão cadastrada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar lesão: {str(e)}")

        elif menu_option == "🔍 Busca e Relatórios":
            st.title("Busca e Relatórios")
            if busca_tipo == "Por Atleta":
                if atleta_selecionado:
                    # Exibe informações do atleta
                    info_atleta = conn.execute("""
                        SELECT 
                            p.*,
                            l.tipo_lesao,
                            CAST(l.data_lesao AS DATE) as data_lesao,
                            CAST(l.data_cirurgia AS DATE) as data_cirurgia,
                            l.observacoes as obs_lesao,
                            pr.fase as fase_atual,
                            CAST(pr.data_inicio AS DATE) as inicio_fase,
                            pr.status,
                            CASE 
                                WHEN l.data_cirurgia IS NOT NULL THEN 
                                    (CURRENT_DATE - CAST(l.data_cirurgia AS DATE))
                                ELSE 0 
                            END as dias_desde_cirurgia,
                            CASE 
                                WHEN l.data_cirurgia IS NOT NULL THEN 
                                    (CAST(l.data_cirurgia AS DATE) + 240 - CURRENT_DATE)
                                ELSE NULL 
                            END as dias_ate_alta,
                            CASE 
                                WHEN l.data_cirurgia IS NOT NULL THEN 
                                    LEAST(100, GREATEST(0, CAST((CURRENT_DATE - CAST(l.data_cirurgia AS DATE)) AS FLOAT) / 240 * 100))
                                ELSE 0 
                            END as progresso
                        FROM pacientes p
                        LEFT JOIN lesoes l ON l.paciente_id = p.id
                        LEFT JOIN progresso pr ON pr.paciente_id = p.id
                        WHERE p.nome = ?
                        ORDER BY pr.data_inicio DESC
                        LIMIT 1
                    """, [atleta_selecionado]).df()
                    
                    st.subheader(f"Relatório de Evolução - {atleta_selecionado}")
                    
                    # Informações básicas em cards
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"**🏃 Posição:** {info_atleta['posicao'][0]}")
                    with col2:
                        st.info(f"**🏉 Clube:** {info_atleta['clube'][0]}")
                    with col3:
                        st.info(f"**🏥 Tipo de Lesão:** {info_atleta['tipo_lesao'][0]}")

                    # Timeline do tratamento
                    st.subheader("📅 Timeline do Tratamento")
                    data_lesao = info_atleta['data_lesao'][0]
                    data_cirurgia = info_atleta['data_cirurgia'][0]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Data da Lesão", 
                                 data_lesao.strftime("%d/%m/%Y") if pd.notna(data_lesao) else "N/A")
                    with col2:
                        st.metric("Data da Cirurgia", 
                                 data_cirurgia.strftime("%d/%m/%Y") if pd.notna(data_cirurgia) else "N/A")
                    with col3:
                        dias_tratamento = info_atleta['dias_desde_cirurgia'][0] if pd.notna(info_atleta['dias_desde_cirurgia'][0]) else 0
                        st.metric("Dias em Tratamento", f"{dias_tratamento} dias")
                    with col4:
                        dias_alta = info_atleta['dias_ate_alta'][0] if pd.notna(info_atleta['dias_ate_alta'][0]) else None
                        st.metric("Dias até Alta Prevista", 
                                 f"{dias_alta} dias" if dias_alta is not None else "N/A")

                    # Progresso do tratamento
                    if pd.notna(data_cirurgia):
                        st.subheader("📊 Progresso do Tratamento")
                        progresso = float(info_atleta['progresso'][0])  # Converte para float padrão
                        
                        # Barra de progresso (valor entre 0 e 1)
                        st.progress(float(progresso) / 100.0)  # Garante que seja float
                        st.write(f"Progresso Total: {progresso:.1f}%")
                        
                        # Histórico de fases
                        historico_fases = conn.execute("""
                            SELECT 
                                fase,
                                data_inicio,
                                data_fim,
                                status,
                                julian(COALESCE(data_fim, CURRENT_DATE)) - julian(data_inicio) as dias_fase
                            FROM progresso
                            WHERE paciente_id = (SELECT id FROM pacientes WHERE nome = ?)
                            ORDER BY data_inicio
                        """, [atleta_selecionado]).df()
                        
                        # Gráfico de evolução por fases
                        if not historico_fases.empty:
                            fig_fases = go.Figure()
                            
                            for idx, fase in historico_fases.iterrows():
                                fig_fases.add_trace(go.Bar(
                                    name=fase['fase'],
                                    x=[fase['fase']],
                                    y=[fase['dias_fase']],
                                    text=f"{fase['dias_fase']:.0f} dias",
                                    textposition='auto',
                                ))
                            
                            fig_fases.update_layout(
                                title="Duração de Cada Fase (em dias)",
                                xaxis_title="Fases",
                                yaxis_title="Dias",
                                showlegend=False
                            )
                            
                            st.plotly_chart(fig_fases, use_container_width=True)
                        
                        # Busca detalhes da fase atual
                        fase_atual = info_atleta['fase_atual'][0] if 'fase_atual' in info_atleta else None
                        if fase_atual:
                            detalhes_fase = conn.execute("""
                                SELECT *
                                FROM fases_reabilitacao
                                WHERE fase = ?
                            """, [fase_atual]).df()
                            
                            if not detalhes_fase.empty:
                                st.subheader(f"📋 Detalhes da Fase Atual: {fase_atual}")
                                
                                # Atividades e restrições
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write("**🏃 Atividades Liberadas**")
                                    for atividade in detalhes_fase['atividades_liberadas'][0].split(','):
                                        st.success(f"✓ {atividade.strip()}")
                                    
                                    st.write("**🎯 Testes Específicos**")
                                    for teste in detalhes_fase['testes_especificos'][0].split(','):
                                        st.info(f"• {teste.strip()}")
                                
                                with col2:
                                    st.write("**💪 Preparação Física**")
                                    for prep in detalhes_fase['preparacao_fisica'][0].split(','):
                                        status = prep.strip()
                                        if '(Completo)' in status:
                                            st.success(f"✓ {status}")
                                        elif '(Restrição)' in status:
                                            st.error(f"⚠ {status}")
                                        else:
                                            st.warning(f"↗ {status}")
                        
                        # Análise de Risco e Recomendações
                        st.subheader("🎯 Análise de Risco e Recomendações")
                        
                        # Calcula o nível de risco baseado no progresso
                        nivel_risco = "Alto" if progresso < 33 else "Médio" if progresso < 66 else "Baixo"
                        cor_risco = "red" if nivel_risco == "Alto" else "orange" if nivel_risco == "Médio" else "green"
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Nível de Risco para Retorno**")
                            st.markdown(f"<p style='color: {cor_risco}; font-size: 24px;'>{nivel_risco}</p>", unsafe_allow_html=True)
                            
                            st.write("**Fatores de Risco:**")
                            if nivel_risco == "Alto":
                                st.error("• Fase inicial de recuperação")
                                st.error("• Tecido em cicatrização")
                                st.error("• Força muscular reduzida")
                            elif nivel_risco == "Médio":
                                st.warning("• Força muscular em desenvolvimento")
                                st.warning("• Coordenação em adaptação")
                                st.warning("• Condicionamento parcial")
                            else:
                                st.success("• Boa evolução no tratamento")
                                st.success("• Força muscular adequada")
                                st.success("• Baixo risco de recidiva")
                        
                        with col2:
                            st.write("**Recomendações para Retorno:**")
                            if nivel_risco == "Alto":
                                st.write("""
                                - Seguir estritamente o protocolo de reabilitação
                                - Evitar qualquer atividade não autorizada
                                - Manter repouso e proteção da área afetada
                                - Realizar exercícios apenas sob supervisão
                                """)
                            elif nivel_risco == "Médio":
                                st.write("""
                                - Progredir gradualmente nas atividades
                                - Monitorar sinais de fadiga ou dor
                                - Realizar exercícios específicos de fortalecimento
                                - Iniciar atividades técnicas básicas
                                """)
                            else:
                                st.write("""
                                - Manter rotina de exercícios preventivos
                                - Retorno gradual aos treinos com equipe
                                - Monitorar carga de treino
                                - Realizar aquecimento adequado
                                """)
                            
                            # Previsão de retorno
                            st.write("**⏱ Previsão de Retorno às Atividades:**")
                            if info_atleta['dias_desde_cirurgia'][0] <= 90:
                                st.error("Retorno total previsto em 6-8 meses")
                            elif info_atleta['dias_desde_cirurgia'][0] <= 180:
                                st.warning("Retorno total previsto em 2-4 meses")
                            else:
                                st.success("Retorno total previsto em breve")
            
            elif busca_tipo == "Por Lesão":
                if lesao_selecionada:
                    # Lista atletas com a lesão selecionada
                    atletas_lesao = conn.execute("""
                        SELECT p.nome, p.data_cirurgia, pr.status
                        FROM pacientes p
                        JOIN lesoes l ON l.paciente_id = p.id
                        LEFT JOIN progresso pr ON pr.paciente_id = p.id
                        WHERE l.tipo_lesao = ?
                        ORDER BY p.data_cirurgia DESC
                    """, [lesao_selecionada]).df()
                    
                    st.subheader(f"Atletas com {lesao_selecionada}")
                    st.dataframe(atletas_lesao, hide_index=True)
            
            elif busca_tipo == "Por Período":
                if data_inicio and data_fim:
                    # Lista atletas que iniciaram tratamento no período
                    atletas_periodo = conn.execute("""
                        SELECT p.nome, l.tipo_lesao, p.data_cirurgia, pr.status
                        FROM pacientes p
                        JOIN lesoes l ON l.paciente_id = p.id
                        LEFT JOIN progresso pr ON pr.paciente_id = p.id
                        WHERE p.data_cirurgia BETWEEN ? AND ?
                        ORDER BY p.data_cirurgia
                    """, [data_inicio, data_fim]).df()
                    
                    st.subheader(f"Atletas no Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
                    st.dataframe(atletas_periodo, hide_index=True)

    except Exception as e:
        st.error(f"Erro ao inicializar o sistema: {str(e)}")
        st.stop() 