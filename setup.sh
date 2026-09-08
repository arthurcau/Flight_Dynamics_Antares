#!/bin/bash
# Script de configuração do ambiente (Antares Flight Dynamics)

echo "========================================================"
echo " Configurando o ambiente do Antares Flight Dynamics..."
echo "========================================================"

# Verifica se o Python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERRO: python3 não encontrado. Por favor, instale o Python 3."
    exit 1
fi

echo "[1/3] Preparando Ambiente Virtual Python (.venv)..."
if [ ! -d ".venv" ]; then
    if ! python3 -m venv .venv; then
        echo "====================================================================="
        echo "ERRO: O seu sistema não possui o pacote 'venv' nativo instalado."
        echo "No Ubuntu/Debian, você precisa instalá-lo rodando:"
        echo "  sudo apt install python3-venv"
        echo ""
        echo "Após a instalação, rode o ./setup.sh novamente!"
        echo "====================================================================="
        exit 1
    fi
    echo "-> Ambiente virtual '.venv' criado com sucesso."
else
    echo "-> Ambiente virtual '.venv' já existe. Reaproveitando..."
fi

echo "[2/3] Atualizando o instalador (pip) interno..."
./.venv/bin/python -m pip install --upgrade pip > /dev/null 2>&1

echo "[3/3] Instalando bibliotecas obrigatórias (RocketPy, PyYAML, Staticmap)..."
if ./.venv/bin/pip install -r requirements.txt; then
    echo ""
    echo "========================================================"
    echo " TUDO PRONTO! O ambiente foi configurado com sucesso."
    echo "========================================================"
    echo ""
    echo "Se você estiver usando uma IDE (VS Code, PyCharm), ela provavelmente"
    echo "já selecionou o interpretador correto automaticamente (.venv)."
    echo ""
    echo "Se for rodar pelo terminal cru, você pode ativar o ambiente com:"
    echo "  source .venv/bin/activate"
    echo ""
    echo "E então rodar suas simulações normalmente:"
    echo "  python3 Projects/Neblina/simulations/nominal.py"
    echo ""
else
    echo ""
    echo "ERRO: Falha ao tentar baixar e instalar as dependências."
    exit 1
fi
