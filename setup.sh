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

# Verifica se o pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "ERRO: pip3 não encontrado. Por favor, instale o pip para Python 3."
    exit 1
fi

echo "[1/2] Instalando bibliotecas obrigatórias (RocketPy, PyYAML, Pytest)..."

# Tenta instalar as dependências. Em sistemas Linux modernos (Debian/Ubuntu),
# o pip bloqueia instalações globais exigindo um ambiente virtual. 
# O parâmetro --break-system-packages é usado aqui como fallback de conveniência
# caso o usuário não queira usar/não tenha acesso ao venv, instalando na pasta ~/.local do usuário.

if pip3 install -r requirements.txt --user --break-system-packages &> /dev/null; then
    pip3 install -r requirements.txt --user --break-system-packages
else
    # Fallback normal para Windows/Mac ou distribuições mais antigas
    pip3 install -r requirements.txt
fi

echo ""
echo "========================================================"
echo " TUDO PRONTO! O ambiente foi configurado com sucesso."
echo "========================================================"
echo ""
echo "Para rodar a sua primeira simulação de teste, execute:"
echo "  ./Scripts/run_sim.sh Projects/00_Copy_This/simulations/nominal.py"
echo ""
