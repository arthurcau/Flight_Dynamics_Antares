# Guia rápido de uso

O [onboarding completo](ONBOARDING.md) reúne instalação em Linux/macOS e
Windows, mapa dos arquivos, criação de foguetes, campanhas, telemetria e
solução de problemas. Este documento mantém apenas o roteiro curto.

## Estação local e CLI compartilhada

Após instalar o ambiente, execute `antares-fd doctor` e `antares-fd gui`.
Consulte [GUI.md](GUI.md) para o fluxo atual e [MANUTENCAO.md](MANUTENCAO.md)
para instalação travada e treinamento offline. Os comandos de scripts abaixo
continuam disponíveis por compatibilidade.

## 1. Instalar

Na raiz do repositório, em Bash, com Python 3.12 ou superior:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -e ".[dev]"
source .venv/bin/activate
```

Para Windows e configuração da IDE, consulte o [onboarding](ONBOARDING.md).
Os comandos seguintes pressupõem o ambiente virtual ativado.

## 2. Verificar o ambiente

```bash
python -m antares_fd.cli --help
python -m pytest -q
```

## 3. Preparar o projeto

Para criar um foguete em Bash:

```bash
cp -R projects/00_Copy_This projects/meu_foguete
```

Use um destino novo. Revise os YAMLs em `projects/meu_foguete/config/`, a curva
em `motors/` e as tabelas em `aero/`. Substitua os valores do exemplo pelos dados
do veículo, inclusive os campos que já vêm preenchidos. Preserve informações
desconhecidas como `null` até obter os dados necessários.

Use unidades SI e posições do veículo medidas do bico para a cauda. Confira
as unidades angulares e a orientação própria declarada para o motor.

## 4. Executar o nominal

```bash
python projects/meu_foguete/simulations/nominal.py
```

O comando integra o voo e grava arquivos. Confira configuração meteorológica,
disponibilidade das entradas, resumo no terminal e mensagens de exportação.

## 5. Encontrar os resultados

O programa informa o diretório criado em `results/<projeto>/<identificador>/`.
Em um voo individual, procure `manifest.yaml`, `trajectory.kml` e, quando a
geração terminar, `reports/flight_dynamics_report.pdf` e
`reports/master_metrics.json`.

O KML representa a trajetória simulada. A existência de um PDF não garante que
toda a campanha terminou sem falhas; confira os manifestos e as mensagens.
As saídas são ignoradas pelo Git e precisam ser compartilhadas separadamente.

Para executar Monte Carlo, comparar cenários e auditar sensores, siga as
seções correspondentes do [onboarding](ONBOARDING.md).
