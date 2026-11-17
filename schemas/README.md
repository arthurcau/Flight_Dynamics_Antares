# Contratos de dados v1

Os JSON Schemas nesta pasta descrevem o inventário de componentes e os
metadados novos de modelo. YAMLs são convertidos para os mesmos tipos JSON.
Campos físicos legados continuam definidos pelos arquivos do template e pelos
validadores em `config/`, `builders/` e `application/validation.py`; não há um
schema único que prometa cobrir toda a física do RocketPy.

`components-v1.schema.json` permite desconhecidos `null` durante edição. Somente
o validador físico calcula completude, positividade do tensor, desigualdade
triangular dos momentos principais, CG e soma de componentes. Um documento que
passa pelo schema ainda pode ser fisicamente inválido. `coverage: COMPLETE`
é uma declaração a verificar, não uma substituição das medições faltantes.

`model-v1.schema.json` define estados documentais. Campos extras são preservados
para metadados/proveniência; recursos que o builder não suporta são rejeitados
pelo diagnóstico antes de integrar. Evoluções incompatíveis exigem versão nova
e migração explícita. O runtime usa validadores Python, sem download de schemas.
