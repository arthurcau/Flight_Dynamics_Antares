# ADR 0001 — plataforma local, dados versionados e execução comum

Estado: implementada na versão 0.2.0. Data: 2026-11-17.

## Contexto

O uso por sucessivas gerações exige instalar um ambiente conhecido, entender
os dados de cada foguete, reproduzir uma execução e evoluir o software sem
copiar o motor em cada projeto. Massas agregadas não permitem trocar payload
e eletrônica com cálculo verificável de CG/inércia. Uma GUI que contenha
regras físicas próprias divergiria dos scripts existentes.

## Decisão

1. `application/` fornece criação/revisão, validação, execução, catálogo e
   consulta. CLI e HTTP chamam os mesmos serviços. `builders/` e `simulation/`
   continuam responsáveis pela construção e integração RocketPy.
2. `design/` guarda física de componentes e tradução conservadora OpenRocket.
   O inventário exclui motor/propelente da massa seca do veículo. Tensores
   locais são transportados ao CG por eixos paralelos. Componentes fora do
   eixo podem ser calculados, mas o builder rejeita CG radial não representável.
3. Estado do modelo é `DESIGN`, `AS_BUILT` ou `AS_FLOWN`. Essa etiqueta declara
   a condição documentada; não é certificação. Versão do software, revisão
   das entradas e identificador da evidência são conceitos independentes.
4. Cada edição pelo serviço preserva entradas anteriores, exige fingerprint
   esperado e serializa mutações com lock do sistema. Cada execução usa cópia
   congelada e hashes. Editar diretamente um YAML continua possível, porém só
   o Git registra esse histórico; o histórico local não observa edições externas.
5. A GUI é HTML/CSS/JavaScript sem framework, servida pelo Python em
   `127.0.0.1`. Host/origem, token efêmero, cookie estrito e caminhos contidos
   delimitam a estação. Não é um servidor multiusuário nem autenticação remota.
   Um único supervisor por workspace evita disputa sobre jobs recuperados.
6. A GUI inicia subprocessos da CLI, limita jobs simultâneos e cancela grupos.
   Estados terminais distinguem sucesso, falha, interrupção e cancelamento.
   Progresso indica fases; não promete estimativa linear do tempo restante.
7. Novas execuções Monte Carlo usam o motor com registro de falhas
   `simulation/monte_carlo_failure.py`. O controlador comum mantém população,
   seeds, cenários e restauração das variáveis de ambiente. Entradas antigas
   continuam disponíveis para compatibilidade; não devem receber novos motores.
8. Dependências são travadas com hashes; CI verifica software e um modelo
   offline congelado. Distribuições científicas podem variar numericamente
   entre CPUs, por isso a regressão tem tolerâncias explícitas.

## Limites e consequências

Python/RocketPy permitem evolução rápida; não fornecem execução em tempo real
com memória/tempo determinísticos nem certificação NASA. Há adaptadores para
a série RocketPy 1.13, inclusive APIs internas já usadas no repositório; subir
essa série exige revisar adaptadores e a regressão antes de liberar um lock.

OpenRocket e RocketPy têm representações diferentes de geometria, arrasto,
estabilidade, recuperação e motores. O importador preserva o `.ork`, extrai
campos reconhecidos e registra componentes não representados, overrides e
ausências. Exige revisão, curvas e dados de propulsão explícitos. Não fabrica
um motor novo a partir de fatores geométricos e não promete trajetória idêntica.

Referências de formato: [especificação oficial OpenRocket](https://openrocket.readthedocs.io/en/latest/dev_guide/file_specification.html)
e serializadores do projeto OpenRocket. O subconjunto inicial tem fixtures
controladas; outros componentes exigem ampliar o tradutor e seus casos de teste.

Histórico local e resultados ficam no disco. O responsável deve versionar os
dados pequenos e preservar artefatos/brutos em armazenamento institucional.
Não foram criados serviços de nuvem, contas, políticas remotas ou responsáveis
nominais. Uma futura API remota exigirá decisão própria sobre autenticação,
isolamento, filas, persistência e operação.
