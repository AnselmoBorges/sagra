# SAGRA - Sistema de Acompanhamento e Gerenciamento de Reabilitação de Atletas 🏉

## Descrição
Sistema desenvolvido para acompanhamento e gerenciamento da reabilitação de atletas de rugby após cirurgia de reconstrução do Ligamento Cruzado Anterior (LCA). O sistema utiliza DuckDB para gerenciamento dos dados e oferece uma interface web interativa para visualização do progresso e recomendações.

## Características Principais
- Interface web interativa usando Streamlit
- Gerenciamento de dados com DuckDB
- Visualização do progresso de reabilitação
- Cronograma detalhado das fases
- Gráficos e métricas de acompanhamento
- Recomendações específicas por fase

## Arquitetura do Sistema
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Interface     │     │  Processamento    │     │     Dados       │
│   (Streamlit)   │     │   (Python)       │     │    (DuckDB)     │
├─────────────────┤     ├──────────────────┤     ├─────────────────┤
│- Input dados    │     │- Cálculo fases   │     │- Database SAGRA │
│- Visualização   │◄───►│- Análise status  │◄───►│- Tabelas        │
│- Gráficos       │     │- Recomendações   │     │- Histórico      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

O sistema segue uma arquitetura em três camadas:
1. **Interface (Streamlit)**: Responsável pela interação com o usuário, entrada de dados e visualização
2. **Processamento (Python)**: Gerencia a lógica de negócio, cálculos e análises
3. **Dados (DuckDB)**: Armazena e gerencia os dados do protocolo, pacientes e progresso

## Estrutura do Sistema

### Arquivos
- `sagra.py`: Aplicação principal com a interface e lógica do sistema
- `SAGRA.db`: Banco de dados DuckDB com as informações do protocolo e pacientes

### Estrutura do Banco de Dados
O sistema utiliza um banco de dados DuckDB com as seguintes tabelas:

1. `fases_reabilitacao`
   - Armazena o protocolo de reabilitação
   - Campos: id, fase, periodo_aproximado, atividades_liberadas, testes_especificos, tratamentos, preparacao_fisica, tecnicas_rugby

2. `pacientes`
   - Registro dos pacientes em tratamento
   - Campos: id, nome, data_cirurgia, data_cadastro

3. `progresso`
   - Acompanhamento do progresso dos pacientes
   - Campos: id, paciente_id, fase, data_inicio, data_fim, status, observacoes

## Requisitos
```
streamlit>=1.31.0
duckdb>=0.9.2
plotly>=5.18.0
python-dateutil>=2.8.2
```

## Instalação e Uso

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITORIO]
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute a aplicação:
```bash
streamlit run sagra.py
```

## Funcionalidades

### Registro e Acompanhamento
- Cadastro de pacientes
- Registro da data da cirurgia
- Acompanhamento automático das fases
- Visualização do progresso

### Visualização de Dados
- Cronograma detalhado das fases
- Gráficos de progresso
- Status das atividades
- Recomendações específicas

### Monitoramento
- Progresso por fase
- Status dos exercícios
- Evolução das técnicas de rugby
- Métricas de acompanhamento

## Contribuição
Para contribuir com o projeto:
1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Envie um pull request

## Autores
- Anselmo Borges
- Pedro Bala Pascal
- Luis Eduardo dos Santos

## Licença
Este projeto está sob a licença [INSERIR_LICENÇA].

## Agradecimentos
- Equipe médica
- Preparadores físicos
- Técnicos de rugby 