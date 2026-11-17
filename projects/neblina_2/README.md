# Neblina 2 — projeto preliminar

Derivado do modelo atual de Neblina 1; não representa uma montagem construída.

- Motor: comprimento ×2 e diâmetro ×0,70; valores absolutos aguardam revisão do .ork.
- Payload: 4 kg, transferido do nariz ao alojamento anterior da eletrônica.
- Eletrônica/gaiola: deslocada ao alojamento anterior do payload.
- Estruturas (incluindo acopladores, bulkheads, gaiola e ejeção): fator de massa 0,95, aplicado por componente quando sua massa for conhecida.
- Payload e eletrônica não recebem redução global de 5%.

`config/design.yaml` preserva os valores de referência e as hipóteses.
`config/components.yaml` é um inventário parcial, com desconhecidos em null.
O .ork ainda não foi fornecido. A GUI permite importá-lo e conferir lacunas.

A curva do motor antigo, presente apenas como referência herdada em motors/, não é usada como curva do motor novo: thrust_source permanece null.
Massa agregada, CG, inércia, montagem do motor e data de lançamento também aguardam dados.
A validação deve indicar essas pendências e impedir uma simulação enganosa.

```bash
python -m antares_fd.cli --repo-root . validate neblina_2
python -m antares_fd.cli --repo-root . gui
```

Não se multiplica impulso por comprimento ou volume do envelope. A geometria interna, o propelente e o bocal exigem definição própria.
