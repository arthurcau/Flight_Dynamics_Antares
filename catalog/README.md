# Catálogo institucional de evidências

`datasets.yaml` guarda identificador, tipo, projeto, origem documental,
responsável institucional, caminho local, tamanho, SHA-256 e data de registro.
Não há evidências cadastradas de forma presumida. O catálogo pode estar vazio.

Registre um arquivo existente, sem modificá-lo:

```bash
antares-fd datasets add ensaio_motor_2026_01 data/motor_tests/ensaio_original.csv \
  --kind motor_test --owner "Antares / Propulsão" \
  --source "Relatório de ensaio: identificador e data" --project neblina_1
antares-fd datasets verify
```

O exemplo não representa um ensaio existente. Troque os campos por registros
reais. Outros tipos: `openrocket`, `mass_properties`, `calibration`, `telemetry`,
`atmosphere`, `campaign`, `other`. Cada ID é único: uma aquisição nova usa novo
ID. O registro não movimenta nem altera a fonte. Alterações posteriores são
classificadas como `CHANGED`; indisponibilidade local como `MISSING`.

Arquivos brutos ficam em `data/`, ignorado pelo Git, ou nas fontes versionadas
do projeto quando pequenos. Preserve-os em armazenamento institucional com
controle de acesso e segunda cópia. O repositório registra a referência desse
armazenamento no campo `source`; o caminho `path` continua relativo à cópia
local. Download e sincronização não são automáticos. Antes de analisar, confira
os hashes. Nunca substitua uma aquisição bruta por uma versão tratada; preserve
tratamentos, unidades, calibrações e scripts como derivados identificáveis.

Na troca de gestão, o responsável entrega acesso às duas cópias, inventário,
retenção e instruções de recuperação. Execute `datasets verify` após recuperar
uma cópia em outro computador. Não coloque credenciais no catálogo.
