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
- A posição no espaço é a do UMAP em 3 eixos, que preserva ~61% da semelhança
  semântica (`planeta-v2/projetar.py`). Os vizinhos na tela são os vizinhos na
  bola, não necessariamente os mais parecidos no embedding completo.
