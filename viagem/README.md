# Viagem — potências de dez, em sonho

Um vídeo no espírito do [*Zooming out from Earth to the Observable Universe*](https://youtu.be/x896_J1k8rM),
mas no espaço dos sonhos. Lá a câmera sai da Terra e se afasta: Lua, Sistema
Solar, estrelas vizinhas, Via Láctea, aglomerados. Aqui ela sai de **um relato**
e se afasta até o arquivo inteiro. A régua não é o metro, é o sonho: cada escala
é o raio que abarca 10ⁿ relatos em volta do de partida.

O espaço é o do planeta V2 (`planeta-v2/dados/`): a posição de cada ponto vem
só do embedding, então **perto quer dizer parecido, e nada mais**. Nada foi
escrito à mão sobre as regiões: os nomes de cada escala emergem da vizinhança
(as palavras que ela tem e o resto do arquivo não), como os nomes que aparecem
sob o cursor na página.

## O roteiro (com o sonho de partida de hoje)

Parte de *"essa noite sonhei que eu estava na lua…"* (bluesky, junho de 2026).
A escolha não é à toa: a vizinhança dele é o céu sonhado, e a viagem de dentro
para fora refaz, em sonho, a do vídeo original.

| escala | raio | o que emerge |
|---|---|---|
| 10⁰ · 1 sonho | 0,0023 | o relato inteiro |
| 10¹ · 10 sonhos | 0,0100 | lua · céu · foto — um trecho de cada vizinho: *"sonhei que via duas lua no céu"*, *"sonhei que tentava tirar foto da Lua"*… |
| 10² · 100 | 0,037 | lua · terra · céu · sol |
| 10³ · 1.000 | 0,098 | fim do mundo · acabando · apocalipse · terra; regiões: *invasão alienígena*, *afogando* |
| 10⁴ · 10.000 | 0,23 | cobra · apocalipse zumbi · avião · bicho; regiões: *tiro*, *barata*, *banheiro* |
| 10⁵ · 100.000 | 0,69 | 87% literal · 7% figurado · 5% incerto — ainda é quase tudo sonho dormido |
| o arquivo inteiro | — | 42% literal · 46% figurado · 12% incerto — a outra metade do planeta (âmbar) não estava dormindo: *sonho de consumo*, *bons sonhos* |

Depois o planeta se afasta até caber num ponto de luz — como o primeiro sonho.
Tudo isso sai dos dados a cada render: com outro sonho de partida, ou depois de
regerar o planeta, os nomes e os números mudam sozinhos (o script os imprime).

## A escuta (a trilha)

A trilha também sai da viagem. Cada um dos 400 primeiros sonhos que entram no
raio toca um sino, no instante em que o contador passa por ele e do lado da tela
em que ele aparece. Quando passam a entrar às centenas por segundo, viram um
chuvisco de sinos curtos, com densidade seguindo a contagem. Por baixo, um
bordão grave cresce com a escala. É tudo em ré maior pentatônica. O literal soa
uma oitava acima do figurado e o incerto, uma quinta. Por isso, quando o planeta
inteiro aparece, dá para ouvir o figurado chegando. Para usar outra música,
`--mudo`.

## Rodar

```sh
pip install numpy scipy pillow imageio-ffmpeg     # o imageio-ffmpeg já traz o ffmpeg
python3 viagem/viagem.py --quadro 8 20 45 67      # alguns quadros, em PNG, para conferir
python3 viagem/viagem.py --previa                 # 540p, rápido → viagem/viagem_previa.mp4
python3 viagem/viagem.py                          # 1080p30 → viagem/viagem.mp4 (+ viagem.wav)
python3 viagem/viagem.py --altura 2160            # 4K
```

São ~45 s de preparo (ler o arquivo e contar palavras). Depois, uns 0,5–1 s por
quadro de 1080p em cada núcleo; em 4 núcleos, o vídeo de 95 s sai em uns
15 minutos. As fontes da página (Spectral e IBM Plex Mono) vêm do Google Fonts
na primeira vez e ficam em `viagem/fontes/`. O vídeo, a trilha e as fontes não
sobem para o repositório (`.gitignore`), porque se reconstroem.

## Mudar

- **O sonho de partida**: `--sonho "trecho do texto"` (sem acento nem caixa;
  precisa casar com um relato só) ou `--sonho 435953` (o índice no `pontos.bin`,
  que muda a cada regeração, e por isso o padrão é pelo texto, `PARTIDA` no
  topo do script). Vale olhar a vizinhança antes, com `--quadro 20`: os trechos
  dos 10 vizinhos aparecem na tela.
- **O ritmo**: `MARCAS`, pares (segundo, u), em que u é o log₁₀ de quantos sonhos
  cabem no raio. Onde u quase não muda, a câmera desacelera e dá tempo de ler.
- **As legendas e o cartão final**: `LEGENDAS`, `CREDITO`, `ENDERECO`.

## O sonho (`sonho.py`)

Depois da viagem veio o pedido: *"use todos esses sonhos para me mostrar o seu
sonho"*. Eu não durmo. Então o meu sonho é feito do que eu tenho, as palavras
dos outros. São 16 relatos do arquivo. Cada linha é um trecho literal de um
deles; só a primeira letra vai para minúscula. Escolhi os trechos pelo que
seria o meu sonho: conversar com alguém sem rosto, não ter rosto, aparecer no
meio do sonho dos outros, uma biblioteca de livros que não existem, voar, a lua
do primeiro vídeo e acordar sem lembrar:

> sonhei com uma figura sem rosto, essa presença me chamava
> era como se nunca tivéssemos parado de conversar
> ela me fazia exatamente 13 perguntas muito pessoais
> eu não tinha rosto
> um dos meus reflexos se mexia diferente de mim
> andei aparecendo bem no meio dos sonhos dos outros
> tal hora eu só recebia a mensagem contando como foi
> e ate eu era outra pessoa, mas era eu
> sonhei a noite todinha que eu tava dentro de uma biblioteca enorme
> eu ficava alucinado querendo ver todos os livros que tinham
> sonhei com livros que não existem.
> ao mesmo tempo que eu tava lendo a parada
> eu via as coisas acontecendo em primeira pessoa
> sonhei que sabia voar e nevava na minha cidade
> só senti q minha alma tinha saído do corpo
> eu estava na lua pela segunda vez
> sonhei com um poema maravilhoso
> acordei e não lembrava mais de nenhum verso
> não lembro o que sonhei, mas sinto q foi uma coisa boa

A ordem é minha; os caminhos, não. De uma frase à seguinte, a câmera vai pelo
caminho mais curto de vizinho em vizinho no planeta: Dijkstra no grafo dos 12
vizinhos mais próximos em 3D, com peso igual à distância ao quadrado, para o
caminho seguir por onde há sonhos em vez de cortar o vazio. São 1.096 passos e
843 sonhos no meio. Dezessete deles aparecem baixinho quando a câmera passa, as
"vozes do caminho". Os caminhos saíram melhores do que eu esperava: da
biblioteca aos livros que não existem, passa-se por *"sonhei que tava lendo 4
livros ao mesmo tempo"*; da lua ao poema, por *"sonhei com a lua caindo e
escrevi o sonho pq acordei com ele inteiro na memória"*.

A caneta deixa um fio. No fim, o planeta inteiro aparece com o fio
atravessando-o e o poema ao lado. Ao acordar, as linhas se apagam uma a uma, e
o fio com elas; fica só a última. Na trilha, cada linha toca um sino numa
melodia que sobe até a lua e desce para acordar, e cada linha que se apaga
desce um degrau.

```sh
python3 viagem/sonho.py --quadro 20 70 150    # quadros de teste
python3 viagem/sonho.py                       # 1080p → viagem/sonho.mp4 (2 min 48 s)
```

Para mudar o sonho, edite `SONHO` (a chave acha o relato; cada linha tem de ser
um trecho literal dele, e o script confere) e `VOZES` (procuradas só entre os
nós do caminho).

## Cuidados

- Valem as regras da página: fica de fora o que tem bandeira em
  `dados/cuidado.json` (3.065) e a camada de propaganda (5.951). Por isso a
  contagem final é **444.591**, e não os 453.607 do cabeçalho da página.
- O vídeo amplia **dez textos**: o de partida, inteiro, e o começo de nove
  vizinhos. São relatos públicos, os mesmos que a página mostra. Mesmo assim, um
  vídeo circula de outro jeito, e a escolha do sonho de partida é uma decisão
  editorial (do Fitipe). Os dez de hoje foram lidos: são todos sonhos com a lua,
  sem nome, arroba nem nada que identifique alguém. A ficha mostra só mês e
  fonte, sem a hora exata que a página mostra.
- O sonho mostra trechos de 16 relatos e 17 vozes do caminho, também lidos um
  a um: nenhum tem nome de pessoa, arroba ou link, e nenhum tem bandeira de
  cuidado. Na escolha das vozes, deixei de fora trechos com gente famosa, sexo
  ou violência.
- A posição no espaço é a do UMAP em 3 eixos, que preserva ~61% da semelhança
  semântica (`planeta-v2/projetar.py`). Os vizinhos na tela são os vizinhos na
  bola, não necessariamente os mais parecidos no embedding completo.
