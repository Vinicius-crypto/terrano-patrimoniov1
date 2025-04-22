FROM python:3.12-slim

# Atualiza o pip antes de qualquer instalação
RUN pip install --upgrade pip

# Cria diretório do app
WORKDIR /app

# Copia primeiro os requirements e instala dependências
COPY requirements.txt .

# Instala as dependências do projeto
RUN pip install -r requirements.txt

# Copia o restante da aplicação
COPY . .

# Expõe a porta correta
EXPOSE 8000

# Executa a aplicação com Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]

