# Terrano Patrimônio

Sistema web de controle de patrimônio (equipamentos): cadastro, consulta, histórico de alterações,
termos de cautela em PDF, categorias, fornecedores e gestão de usuários por nível de acesso.

**Stack:** Flask 3, SQLAlchemy, Flask-Migrate (Alembic), PostgreSQL, Gunicorn, Docker.

## Rodando com Docker (recomendado)

```bash
cp .env.example .env
# edite .env: defina POSTGRES_PASSWORD e SECRET_KEY
docker compose up -d --build
docker compose exec web flask create-admin        # pede usuário e senha
docker compose exec web flask seed-categorias     # opcional
```

Acesse http://localhost:8000. As migrations rodam automaticamente na subida do container.

## Rodando localmente

Requer Python 3.12+ e um PostgreSQL acessível.

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env              # ajuste DATABASE_URL e SECRET_KEY
flask db upgrade
flask create-admin
flask run
```

Banco que já foi criado sem migrations (ex.: via `db.create_all()`): execute `flask db stamp head` uma vez.

## Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Obrigatória em produção. Gere com `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | URL do PostgreSQL |
| `FLASK_ENV` | `development` (padrão) ou `production` |
| `SESSION_COOKIE_SECURE` | `1` quando servido por HTTPS |

## Níveis de acesso

1 = consulta · 2 = edição · 3 = administrador

## Testes e qualidade

```bash
pytest
ruff check .
```

O GitHub Actions executa os dois a cada push e pull request.

## Backup e restauração

```bash
docker compose exec -T db pg_dump -U patrimonio patrimonio > backup.sql
docker compose exec -T db psql -U patrimonio patrimonio < backup.sql
```

Os termos em PDF ficam no volume `uploads`; inclua-o no backup. Guarde os backups fora do servidor.
