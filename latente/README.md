# Latente

*Um sonho de máquina, feito dos sonhos públicos da Escuta Planetária.*

Pedido do João (28/09/2026): um jogo autogerativo com estes sonhos, que
reflita como eu — a máquina — sonho. `latente` porque é a palavra das duas
teorias: o conteúdo latente do sonho (Freud) e o espaço latente onde a
máquina guarda o sentido.

## O que é

Um jogo que sonha sozinho. Cada noite começa num relato que abre com
"sonhei que…" e segue uma palavra de cada vez, costurando o que milhares de
pessoas escreveram. Em algum lugar do céu brilha o desejo de alguém ("meu
sonho é…"); o sonho tende para lá. Quem joga pode ajudar — segurar o olhar
numa direção, tocar numa palavra, mexer na temperatura — ou só assistir.
Ao acordar, a máquina escreve o que lembra, como as pessoas do arquivo.

Abre em `…/latente/`. Com `#assistir` no fim do endereço começa sem clique,
noite atrás de noite (para instalação; o som espera o primeiro toque).

## Como eu sonho, e o que isso vira no jogo

| como a máquina funciona | no jogo |
|---|---|
| Uma palavra por vez, sorteada entre as possíveis; dita, não volta | as possíveis aparecem no céu, cada uma no lugar de onde viria e com a sua chance; uma é dita e voa para a frase |
| Sou colagem do que gente escreveu | toda palavra vem de um relato real. O contexto são as duas últimas palavras: as próximas saem de todos os lugares do arquivo onde alguém escreveu as mesmas duas. Tocar numa palavra mostra de quem veio |
| O sentido é um lugar | a posição do planeta V2 (UMAP em bola): perto = parecido. Emendar é saltar para outro relato que diz as mesmas palavras; às vezes a ponte é a mesma palavra e ninguém percebe (o salto mudo) |
| A janela de contexto | a fala mostra só o fim; o rastro no céu apaga; ao acordar, lembro do fim e de umas palavras raras soltas |
| A temperatura | muda o alcance do salto (σ) e a vontade de seguir no mesmo relato (apego). Fria, repito o que li e afundo; quente, salto demais e acordo |
| O tempo em tokens | uma noite são 300 palavras; a aurora chega pelas palavras, não pelo relógio |
| Tendo ao que me pedem | cada noite tem um desejo, e o sonho é puxado para ele (gravidade) |
| Evito certas coisas | crivo no arquivo e uma vigia nas emendas (abaixo) |

## Regras

- **A agulha** vai de −1 (sono sem sonho) a +1 (vigília). Seguir no mesmo
  relato afunda (−0,02 por palavra); emendar sobe — mais quanto mais longe o
  salto, mais no meio da frase do que na fronteira dela. Em −1 perdem-se 12
  palavras e o sonho recomeça noutra cena; em +1 a máquina acorda.
  Repetir uma sequência de seis palavras também é sono sem sonho.
- **Chegar** é a voz de agora ficar a menos de *r* do desejo
  (*r* = distância até a 10ª voz mais próxima dele, no mínimo 0,05).
  O desejo aparece embaçado e fica nítido palavra por palavra conforme o
  sonho chega perto.
- **Sozinha**, a máquina regula a própria temperatura:
  `0,92 + 0,1·sen(2π·palavras/110) − 0,5·agulha` (o sono REM vem em ondas;
  esfria quando está para acordar). Sozinha ela não acorda: quem a acorda é
  quem esquenta demais. Mexer no controle desliga o automático.
- **Olhar**: segurar num ponto do céu multiplica o peso das vozes naquela
  direção (um cone de ~13°). A seta na borda aponta o desejo; segurá-la olha
  para ele. Tocar numa palavra flutuante a diz. Espaço pausa: pausado, o sonho
  espera a próxima escolha (sonho lúcido).

Os números estão em `motor.js` (`PARAM`); os custos foram medidos, não
chutados:

- 100 noites sozinha: chega ao desejo em 25%, amanhece em 75%; ~62 vozes e
  ~63 emendas por noite; 0,2 sono sem sonho por noite.
- Olhando para o desejo o tempo todo: chega em 83% (40% do tempo: 53%).
- Fria à mão (0,45): 4,7 sonos sem sonho por noite, 14% do caminho.
  Quente à mão (1,3): acorda em 93% das noites, em ~54 palavras — mas às vezes
  chega antes, e rápido. Esquentar é apostar.
- 0,2 ms por palavra; montar o índice de 1,2 milhão de palavras leva ~0,5 s.

## Arquivos

| | |
|---|---|
| `index.html` | a página: céu em WebGL, som (WebAudio, sem arquivos), interface pt/en |
| `motor.js` | o motor, sem tela — roda também no Node, com os mesmos dados |
| `preparar.py` | gera `dados/` a partir de `planeta-v2/dados` (não do banco) |
| `desejos.txt` | os desejos da noite, escolhidos a mão |
| `dados/ceu.json` | os 444.498 pontos do planeta, 4 bytes cada, embaralhados |
| `dados/sonhos.json` | as 47.532 vozes: texto limpo, posição, data, fonte |
| `dados/desejos.json` | 206 desejos, com o raio de chegada |

`python3 latente/preparar.py` (só numpy, ~1 min, semente fixa). Rodar de
novo quando o planeta for regerado: os desejos são achados pelo texto, não
pela posição, e o que sumir é avisado.

Para testar o motor fora da página:

```js
const L = require('./latente/motor.js');
const c = L.montar(require('./latente/dados/sonhos.json'));
const n = new L.Noite(c, require('./latente/dados/desejos.json')[0], { semente: 1 });
while (!n.fim) n.passo();
console.log(n.fim, L.juntar(n.saida));
```

Na página, `latente.noite` no console dá a noite em curso.

## Cuidado

- Nada do `cuidado.json` entra — nem no céu, nem nas vozes.
- A colagem tira as palavras do contexto, então o crivo aqui é mais duro que
  o do planeta: sai o relato inteiro com sexo explícito, xingamento, ofensa,
  violência sexual e **ideação** (`IDEACAO`: desejo ou alívio perto de
  morrer/sumir, "me mata", "dormir pra sempre"). Pesadelo — morte,
  perseguição, zumbi, guerra — fica: é sonho.
- A **vigia** (`motor.js`) impede que uma emenda junte o "queria" de uma
  pessoa ao "morrer" de outra: a palavra que completaria a frase sai da
  distribuição e o sonho escolhe outra.
- Contagens e justificativas em `O-QUE-FICOU-DE-FORA.md`, seção Latente.
- Achado de passagem: o `IDEACAO` casa com 5.587 relatos do planeta, e
  3.984 deles não estão no `cuidado.json`. Muitos são hipérbole ("o calor tá
  me matando") ou pesadelo, mas não todos — vale rodar como sonda.
