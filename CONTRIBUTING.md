# Contribuir com o Antares Flight Dynamics

Leia [o onboarding](docs/ONBOARDING.md), [a arquitetura](docs/decisions/0001-plataforma.md)
e [o fluxo de manutenção](docs/MANUTENCAO.md). Dados de um foguete ficam em
`projects/<id>/`; regras reutilizáveis ficam em `source/antares_fd/`. Use a GUI
e a CLI como clientes dos serviços de `application/`.

1. Crie uma branch de trabalho e descreva o problema com um exemplo reproduzível.
2. Identifique se a mudança afeta software, modelo físico ou evidência experimental.
3. Preserve a origem dos números, unidades SI, referencial, hipóteses e ausências.
4. Modifique o menor conjunto coerente de arquivos. Não replique o motor em projetos.
5. Rode os testes pertinentes, a análise estática e a checagem da referência.
6. Abra uma PR com comportamento resultante, validação e limitações físicas.
7. Solicite revisão aos responsáveis de software e, se aplicável, do subsistema físico.

Preparação e verificações, com Python 3.14:

```bash
python -m pip install --require-hashes -r requirements-py314.lock
python -m pip install --no-deps --no-build-isolation -e .
python -m ruff check source MAGI projects scripts tests setup.py
python scripts/generate_function_reference.py
python scripts/generate_function_reference.py --check
MPLBACKEND=Agg python -m pytest tests MAGI/tests -m "not gui"
```

No PowerShell, configure `$env:MPLBACKEND="Agg"` antes do pytest. Para Python
3.12 use o lock correspondente. O teste de navegador é descrito em
[GUI.md](docs/GUI.md); Playwright é dependência de teste opcional.

Funções públicas documentam objetivo, entradas, unidades, retorno, mecanismo,
efeitos e falhas relevantes. Mantenha invariantes verificáveis, fluxo simples,
limites explícitos, erros específicos e dados ausentes visíveis. Os princípios
de previsibilidade e rastreabilidade são inspirados em software crítico;
**este projeto não é software certificado pela NASA**. Python/RocketPy e análise
exploratória não cumprem automaticamente normas de software embarcado crítico.

Inclua regressões para defeitos e mudanças físicas; evite testes que apenas
repitam uma fórmula implementada. Use casos analíticos independentes e o modelo
offline congelado. Uma mudança legítima de apogeu exige investigar entradas,
integrador e convenções; não atualize o baseline só para fazer o teste passar.

Alterações incompatíveis de YAML exigem nova versão e migração explícita.
Registre decisões duradouras em `docs/decisions/`. Edite a fonte da referência
de funções, depois regenere os documentos; não corrija apenas a saída gerada.
Dados de voo e resultados não podem ser rotulados como validados sem evidência
experimental e definição de incerteza correspondentes.
