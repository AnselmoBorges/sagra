-- Tabela de Pacientes (Atletas)
CREATE TABLE pacientes (
    id INTEGER PRIMARY KEY,
    nome VARCHAR NOT NULL UNIQUE,
    data_nascimento DATE,
    posicao VARCHAR,
    clube VARCHAR,
    data_cirurgia DATE
);

-- Tabela de Lesões
CREATE TABLE lesoes (
    id INTEGER PRIMARY KEY,
    paciente_id INTEGER NOT NULL,
    tipo_lesao VARCHAR NOT NULL,
    data_lesao DATE,
    data_cirurgia DATE,
    observacoes TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

-- Tabela de Fases de Reabilitação
CREATE TABLE fases_reabilitacao (
    id INTEGER PRIMARY KEY,
    fase VARCHAR NOT NULL,
    periodo_aproximado VARCHAR NOT NULL,
    atividades_liberadas TEXT,
    testes_especificos TEXT,
    tratamentos TEXT,
    preparacao_fisica TEXT,
    tecnicas_rugby TEXT
);

-- Tabela de Progresso
CREATE TABLE progresso (
    id INTEGER PRIMARY KEY,
    paciente_id INTEGER NOT NULL,
    fase VARCHAR NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE,
    status VARCHAR DEFAULT 'Em andamento',
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    UNIQUE(paciente_id, fase, data_inicio)
);

-- Inserir fases padrão de reabilitação
INSERT INTO fases_reabilitacao (id, fase, periodo_aproximado, atividades_liberadas, testes_especificos, tratamentos, preparacao_fisica, tecnicas_rugby) VALUES
(1, 'Fase 1', '1 a 14 dias', 'Mobilização passiva, Exercícios isométricos', 'Avaliação de edema, Avaliação de ADM', 'Crioterapia,Eletroterapia,Exercícios de mobilização passiva', 'Isometria de quadríceps (Progressão),Exercícios de ADM (Progressão)', 'Tackle:1,Passe:1,Scrum:1,Ruck:1,Treino em campo:1'),
(2, 'Fase 2', '15 a 28 dias', 'Exercícios em CCA, Bicicleta estacionária', 'Teste de força muscular, Avaliação de marcha', 'Exercícios ativos,Treino de marcha,Fortalecimento', 'Leg Press (Progressão),Agachamento (Restrição),Bicicleta (Completo)', 'Tackle:1,Passe:2,Scrum:1,Ruck:1,Treino em campo:1'),
(3, 'Fase 3', '29 a 90 dias', 'Exercícios em CCF, Corrida em linha reta', 'Teste de agilidade, Avaliação funcional', 'Exercícios pliométricos,Treino de corrida,Core', 'Agachamento (Progressão),Corrida (Progressão),Pliometria (Restrição)', 'Tackle:1,Passe:3,Scrum:2,Ruck:2,Treino em campo:2'),
(4, 'Fase 4', '91 a 180 dias', 'Exercícios específicos do rugby, Treino com bola', 'Teste de salto, Y-Balance Test', 'Treino específico,Agilidade,Potência', 'Pliometria (Progressão),Agilidade (Progressão),Potência (Progressão)', 'Tackle:2,Passe:3,Scrum:2,Ruck:2,Treino em campo:3'),
(5, 'Fase 5', '181 a 240 dias', 'Retorno gradual ao treino com equipe', 'Testes específicos do rugby', 'Treino com equipe,Contato gradual,Jogo simulado', 'Treino completo (Progressão),Contato (Progressão)', 'Tackle:2,Passe:3,Scrum:3,Ruck:3,Treino em campo:3'),
(6, 'Alta', 'após 240 dias', 'Retorno completo às atividades', '-', 'Manutenção,Prevenção', 'Treino completo (Completo)', 'Tackle:3,Passe:3,Scrum:3,Ruck:3,Treino em campo:3'); 