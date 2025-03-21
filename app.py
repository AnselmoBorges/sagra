import streamlit as st
import duckdb
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import os
import streamlit_authenticator as stauth
import bcrypt
import pandas as pd

# Configuração da página Streamlit
st.set_page_config(
    page_title="SAGRA - Reabilitação LCA",
    page_icon="🏉",
    layout="wide"
)

# Autenticação manual
credentials = {
    "usernames": {
        "admin": {
            "name": "Administrador",
            "password": "$2b$12$qOMhXS8nxqHWOvhQpkWxCuqwQqPgfWm6VVKZPJDcg3DfNqT6Ry3Uy"  # admin123
        }
    }
}

cookie_name = "sagra_cookie"
cookie_key = "sagra_cookie_key"
cookie_expiry_days = 30

# Cria o autenticador diretamente com valores literais
authenticator = stauth.Authenticate(
    credentials,
    cookie_name,
    cookie_key,
    cookie_expiry_days
)

# Container centralizado para o login
st.image("logo_sagra.png", use_container_width=True)
st.title("SAGRA")
st.caption("Sistema de Acompanhamento e Gerenciamento de Reabilitação de Atletas")

# Inicializa o status de autenticação
try:
    name, authentication_status, username = authenticator.login('Login')
except Exception as e:
    st.error(f"Erro na autenticação: {str(e)}")
    st.stop()

# Verifica o status da autenticação
if authentication_status == False:
    st.error('❌ Usuário ou senha incorretos')
    st.stop()
elif authentication_status == None:
    st.info('👋 Por favor, faça login para continuar')
    st.stop()

# Conteúdo principal se autenticado
st.success(f"Bem-vindo, {name}!")
st.write("Aplicação SAGRA - Versão Simplificada para Teste")

# Mostra o menu de logout
with st.sidebar:
    st.title("🏉 SAGRA")
    st.write(f'Bem-vindo *{name}*')
    authenticator.logout('Logout', 'main') 