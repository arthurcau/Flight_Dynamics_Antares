# Manutenção, reprodução e transferência da plataforma

## Versões e contratos

Software: `antares_fd.__version__`, `setup.py` e `CHANGELOG.md` avançam juntos.
Modelo: `config/model.yaml` registra estado, origem e notas; fingerprint cobre
configurações, aerodinâmica, motores e fontes. Experimento: catálogo identifica
a aquisição pelo hash do original, responsável e origem. Não substitua uma
dessas referências por outra ao descrever um resultado.

`schema_version: 1` identifica os documentos novos. Documentos físicos legados
sem essa chave continuam aceitos como v1. Uma versão futura é rejeitada até
existir migração explícita. A migração atual adiciona metadados sem alterar
física:

```bash
antares-fd project migrate neblina_1
antares-fd project migrate neblina_1 --apply
```

O primeiro comando mostra o preview. O segundo preserva a revisão anterior.
Guias e contratos de campos: [GUI.md](GUI.md) e
[schemas](../schemas/README.md). Metadados desconhecidos são preservados;
isso não significa que sejam usados pelo integrador.

## Ambiente reproduzível

Locks `requirements-py312.lock` e `requirements-py314.lock` contêm versões exatas
e hashes das distribuições, resolvidos para os sistemas suportados. As versões
verificadas ficam em `requirements-tested.constraints`. Use ambiente virtual
novo; instalar o lock sobre um ambiente antigo não remove pacotes excedentes.

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-py314.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/antares-fd doctor
```

Para atualizar dependências, escolha versões, revise notas oficiais e altere
as constraints de forma explícita. Com `uv` instalado como ferramenta de
desenvolvimento, regenere os locks:

```bash
uv pip compile requirements-dev.in -c requirements-tested.constraints \
  --python-version 3.12 --universal --generate-hashes -o requirements-py312.lock
uv pip compile requirements-dev.in -c requirements-tested.constraints \
  --python-version 3.14 --universal --generate-hashes -o requirements-py314.lock
```

Confira diffs e rode testes nos dois intérpretes em CI. O ambiente local desta
entrega foi executado em Linux/Python 3.14; a configuração de CI inclui 3.12.
Não declare que uma plataforma foi testada apenas porque o solver gerou um lock.

## Exercício de passagem de conhecimento, sem meteorologia externa

Copie a fixture científica para um projeto de treinamento. Ela é derivada
das entradas históricas do Neblina 1, congelada com atmosfera padrão e sem
declaração de equivalência experimental. Não a use como configuração de voo.

```bash
cp -R tests/fixtures/reference_project projects/treinamento
antares-fd validate treinamento
antares-fd run treinamento --no-report
antares-fd results list treinamento
antares-fd gui
```

No PowerShell use `Copy-Item -Recurse tests/fixtures/reference_project
projects/treinamento`. Escolha um nome que ainda não exista. Pela GUI, altere
um parâmetro assumido, salve com motivo, confira histórico e restaure a revisão
anterior. Execute novamente, compare revisões e verifique integridade. Cadastre
uma evidência de treinamento com origem explícita. Registre versão, resultados
e quem realizou o exercício no registro da gestão, sem tratar números simulados
como medições. Mantenha alterações de treinamento fora de projetos de voo.

## Publicação e revisão

Antes de uma release, execute lint, referência de funções, testes offline e
fluxo do navegador. Revise o changelog, compatibilidade de configurações e
baseline físico com os responsáveis definidos em `MAINTAINERS.md`. Preserve
logs da CI e manifestos de uma execução representativa. Só então publique uma
tag e os artefatos pelo processo adotado pela equipe. Esta implementação não
publica tags, não faz push e não altera proteção de branches.

Os testes em `tests/fixtures/reference_project/expected.json` verificam
apogeu AGL, velocidade de saída, Mach, massa de burnout, impacto e impulso com
tolerâncias documentadas. São regressão de software, não validação de voo.
Outros testes verificam cilindros, soma de massas, CG e eixos paralelos contra
casos analíticos. A CI é uma barreira de regressão, não autorização de lançamento.

## Recuperação e limites operacionais

Resultados ficam em `results/<projeto>/<run_id>`. `execution.json` guarda estado;
`inputs/` guarda as entradas; `software_provenance.json` registra versões e
Git; `artifact_manifest.json` permite verificar integridade. Preserve a pasta
inteira para analisar uma execução em outro computador. Dependências e dados
meteorológicos externos não são baixados novamente pela consulta de resultados.

A atmosfera determinística utilizada é arquivada em `atmosphere_input.parquet`
com pressão, temperatura, vento, densidade e velocidade do som. Perfis MAGI
mantêm níveis e umidade quando disponíveis; atmosfera analítica é identificada
como amostrada. Campanhas mantêm snapshots e metadados próprios por caso/seed;
a aquisição meteorológica externa continua dependendo da disponibilidade dos
dados de origem. Nenhum manifesto garante igualdade bit a bit entre sistemas.

Fechar normalmente o servidor cancela workers ativos. Após encerramento abrupto,
estados gerenciados sem resultado terminal são marcados `INTERRUPTED` ao reiniciar.
Não se tenta matar um PID antigo, que pode ter sido reutilizado. Em caso de
queda forçada do processo servidor, confira processos remanescentes pelo sistema
operacional antes de reiniciar campanhas pesadas. A GUI aceita até dois jobs
simultâneos; `workers` controla paralelismo da campanha, não capacidade infinita.
