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

# Define as variáveis de autenticação
names = ["Administrador"]
usernames = ["admin"]
# Gera o hash da senha admin123
hashed = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt())
passwords = [hashed.decode()]

# Cria o autenticador
authenticator = stauth.Authenticate(names, usernames, passwords, 'sagra_cookie', 'sagra_cookie_key', cookie_expiry_days=30)

# Inicializa o status de autenticação
name, authentication_status, username = authenticator.login('', 'main')

# Função de inicialização do banco de dados
def init_database():
    """Inicializa a conexão com o banco de dados DuckDB e cria as tabelas se necessário"""
    try:
        # Tenta primeiro uma conexão exclusiva
        conn = duckdb.connect('SAGRA.db')
        
        # Cria as tabelas se não existirem
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY,
                nome VARCHAR UNIQUE NOT NULL,
                data_nascimento DATE,
                posicao VARCHAR,
                clube VARCHAR,
                data_cirurgia DATE
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lesoes (
                id INTEGER PRIMARY KEY,
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
                id INTEGER PRIMARY KEY,
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
                id INTEGER PRIMARY KEY,
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

if not authentication_status:
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
else:
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
            SELECT nome, data_cirurgia, 
                   (SELECT tipo_lesao FROM lesoes l WHERE l.paciente_id = p.id) as lesao
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
                data_cirurgia = excluded.data_cirurgia
            RETURNING id
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
    progresso = min(100, (dias_desde_cirurgia / 240) * 100)
    
    st.progress(progresso / 100)
    st.write(f"Progresso: {progresso:.1f}% ({dias_desde_cirurgia} dias desde a cirurgia)")
    
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
            
            tipo_lesao = st.selectbox("Tipo de Lesão", ["LCA", "LCP", "Menisco", "Ligamento Colateral", "Tendinite Patelar"])
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
                    SELECT p.*, l.tipo_lesao, l.data_lesao
                    FROM pacientes p
                    LEFT JOIN lesoes l ON l.paciente_id = p.id
                    WHERE p.nome = ?
                """, [atleta_selecionado]).df()
                
                st.subheader(f"Informações do Atleta: {atleta_selecionado}")
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Dados Pessoais**")
                    st.write(f"Nome: {info_atleta['nome'][0]}")
                    st.write(f"Posição: {info_atleta['posicao'][0]}")
                    st.write(f"Clube: {info_atleta['clube'][0]}")
                with col2:
                    st.write("**Informações da Lesão**")
                    st.write(f"Tipo: {info_atleta['tipo_lesao'][0]}")
                    st.write(f"Data da Lesão: {info_atleta['data_lesao'][0]}")
                    st.write(f"Data da Cirurgia: {info_atleta['data_cirurgia'][0]}")
        
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