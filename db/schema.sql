CREATE TABLE IF NOT EXISTS usuarios (
    id BIGINT PRIMARY KEY,
    nome VARCHAR(100),
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS produtos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    preco NUMERIC(10,2) NOT NULL,
    disponivel BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    usuario_id BIGINT REFERENCES usuarios(id),
    produto_id INT REFERENCES produtos(id),
    status VARCHAR(50) DEFAULT 'pendente',
    criado_em TIMESTAMP DEFAULT NOW()
);
