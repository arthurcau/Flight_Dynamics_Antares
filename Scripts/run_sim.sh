#!/bin/bash
# Script de conveniência para rodar as simulações do Antares Flight Dynamics

if [ -z "$1" ]; then
    echo "ERRO: Você precisa informar o caminho do script de simulação que deseja rodar."
    echo ""
    echo "Uso correto:"
    echo "  ./Scripts/run_sim.sh <caminho_do_script>"
    echo ""
    echo "Exemplo:"
    echo "  ./Scripts/run_sim.sh Projects/00_Copy_This/simulations/nominal.py"
    exit 1
fi

# Exporta a pasta Source para que os módulos do antares_fd sejam encontrados
export PYTHONPATH="Source"

# Executa o script
python3 "$1"
