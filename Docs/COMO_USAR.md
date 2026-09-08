# Guia Rápido: Como Usar o Repositório

Este guia é um passo a passo prático para novos membros da equipe rodarem suas simulações de voo rapidamente.

## 1. Configurando o seu computador
Antes de rodar qualquer coisa pela primeira vez, você precisa instalar as dependências (RocketPy, etc).
Abra o terminal na pasta raiz do repositório e rode:
```bash
./setup.sh
```
*(Se você usar Windows, apenas rode `pip install -r requirements.txt`).*

---

## 2. Criando um Novo Foguete
Nunca altere ou trabalhe diretamente na pasta `00_Copy_This`. Ela é um *template* (molde).

Para simular o seu foguete:
1. Copie a pasta `Projects/00_Copy_This`.
2. Cole e renomeie para o nome do seu projeto (exemplo: `Projects/Meu_Foguete`).

---

## 3. Preenchendo os Parâmetros (A Engenharia)
Na sua nova pasta `Projects/Meu_Foguete/config/`, você encontrará os arquivos `.yaml`. 
Abra-os e preencha os dados físicos do seu foguete real.

* **`launch.yaml`**: Local de lançamento, tamanho do trilho e ângulo.
* **`motor.yaml`**: Massa do motor, curva de empuxo (aponte para o seu arquivo `.eng` na pasta `motors/`).
* **`recovery.yaml`**: Tamanho dos paraquedas (Cd*S) e altitudes de acionamento.
* **`vehicle.yaml`**: Geometria do foguete, massa (sem motor), inércia e dimensões das aletas.

> **Regra de Ouro**: O sistema de unidades é **sempre SI** (metros, quilogramas, segundos). O referencial de posição é **Sempre do Bico para a Cauda** (Nose-to-Tail), sendo o bico o ponto `0.0`.

---

## 4. Rodando a Simulação
Com os dados preenchidos, basta pedir para o Python rodar o script principal do seu projeto. 
Se estiver usando um terminal comum, ative o ambiente virtual antes:

```bash
source .venv/bin/activate
python3 Projects/Meu_Foguete/simulations/nominal.py
```

*Nota: Graças à nossa arquitetura, se você usa IDE (VS Code, PyCharm), você pode simplesmente abrir o arquivo `nominal.py` e clicar no botão "Play", pois a IDE detecta o `.venv` automaticamente.*

---

## 5. Analisando os Resultados
Se tudo der certo, o terminal vai imprimir o **FLIGHT SUMMARY** (Resumo de Voo) mostrando o Apogeu, Velocidade Máxima, Mach e os tempos de abertura dos paraquedas.

Além disso, a simulação vai salvar automaticamente um arquivo **`trajectory.kml`** dentro da pasta do seu projeto. 
* Pegue esse arquivo `.kml`.
* Arraste para dentro da tela do **Google Earth** (pode ser a versão de navegador web).
* Você verá a trajetória 3D exata do seu foguete renderizada sobre o mapa do local de lançamento!
