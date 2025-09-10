#!/bin/bash
# start.sh

echo "🚀 Iniciando TechSuppliers Backend..."
echo "📊 Conectando ao banco de dados..."

# Criar tabelas se não existirem
python -c "
import app
app.criar_tabelas()
print('✅ Tabelas verificadas/criadas')
"

# Iniciar o servidor
gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120 app:app
