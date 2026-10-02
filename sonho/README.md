# Sonho

Pedido do João (02/10/2026): *"Use somente os dados e o embedding. Sonhe."*

O sonho é o caminho mais curto, de vizinho em vizinho no embedding, do último
relato que o arquivo ouviu (27/09/2026) até o primeiro (11/01/2008). São 42
passos e 43 relatos, cada um inteiro e na ordem do caminho. Nenhuma palavra é
minha. Não há sorteio, nem rótulo de anotador, nem palpite do aluno, nem modelo
de linguagem, nem escolha de trecho: com os mesmos dados, o sonho é sempre este.
No sonho da viagem (`viagem/sonho.py`, noutro ramo) eu escolhi os trechos. Aqui
não escolhi nenhum.

Abre em `…/sonho/`: o sonho à esquerda (no celular, embaixo) e o planeta parado ao
lado, sem cor de classe, com o fio do caminho aceso até onde a leitura chegou. O
espaço entre dois relatos na página é proporcional ao passo entre eles na bola
(1 unidade = 80rem).

## O sonho (dados até 27/09/2026)

> Eu conto ou vcs contam?  
> Adoro esses posts e tbm aqueles de mapas de metrô malucos kkkkk  
> Sonhar é de Graça né
>
> Infelizmente é msm, mas acabou se tornando verdade. Vc vai encontrar alguém com esses mesmos sonhos. Na hora certa
>
> Eu toda vez que vejo alguém realizando seus sonhos
>
> amo quando os divertidamentes roteiristas de sonhos de vez em quando aparecem com umas pérolas dessas
>
> eu sinto muito orgulho de mim quando lembro da minha dedicação para as coisas que determino como sonhos da minha vida
>
> Queria eu ter sonhos desse afs  
> (Vcs dando fecho, n são superiores n viu. Rir tbm é bom pra saúde)
>
> muito bom. tem gente que escreve livros só com sonhos lucidos
>
> parece que ngm entende minhas vontades e sonhos, coisas que vão além da medicina, mas tá tudo ok
>
> os sonhos me contam mais que pessoas
>
> Juro gente, melhor que meus sonhos
>
> Até os sonhos são mais eficientes.
>
> Louco mesmo, achei legal, não sei porque mas eu gosto muito de ouvir sobre sonhos, dão histórias legais.
>
> Eu ? De forma alguma, apenas quero te prover bons sonhos, daqueles que ficam na mente por dias kkkkkk
>
> Eu estou felizinha que estou tendo sonhos bons: em que pessoas aleatórias me questionam de coisas que eu fiz 15 anos atrás e eu explico na maior paciência que tudo bem o que eu fiz, que faz parte
>
> infelizmente eu acho meus sonhos muito interessantes e amo lembrar deles então meus amigos precisam ficar ouvindo eles sim
>
> meu sonho juku luzia e diana só (se bobear ate a juju
>
> nossa sonhei com Wenclair só que o sonho tava em formato de AU KAKSKSJSJSKAKAKSK
>
> como que eu vou viver um romance dos sonhos se todo mundo só pensa em sexo, ex, trend topic e o fim da escala 6x1??
>
> Hoje é só sofrimento cara, a mulher foi visitar a Bahar e a Nisan nos sonhos. 😭  
> #ForçaDeMulher
>
> N sei, só acontecem
>
> quando eu vou dormir depois de perder muito no vava meus sonhos são assim
>
> sonhei com uma crush que infelizmente é só no mundo dos sonhos mesmo
>
> Nem eu, agora se quiser namorar comigo a pessoa vai ter que me alcançar no mundo dos sonhos
>
> realmente sonhos dizem algo
>
> meus sonhos me dizem algo sobre você
>
> Eu sonhei com uma coisa bem específica e geralmente meus sonhos sempre estão certos, vou ficar averiguando as cenas dos próximos capítulos
>
> Às vezes eu tenho estes sonhos, muitas vezes com amigos. E sempre está acontecendo algo de fato.
>
> hajshwkdkd nem comi nada só acho que sonhei msm
>
> Vou fingir que não sonhei com ela hoje
>
> Não sonhei com ninguém kkkkk
>
> Não sonhei nada, que mentinha em
>
> Sim, não sonhei nada 🤲🏻
>
> hj não sonhei c nenhuma coisa bizarra
>
> vim pelo autolink  
> eu não durmo ou faço speedruns de minercfat mas otimo sub
>
> n sonhei com nada apenas dormi como um anjo amém
>
> Correto, nem lembrava disso
>
> Hoje eu não sonhei alguma coisa com torrada de queijo, eu lembro de tudo do sonho, só sei que não tinha uma torrada de queijo no meio-
>
> esqueci meu sonho
>
> não tem sonho do dia hoje porque esqueci o que sonhei
>
> o ian trouxe esse assunto ontem e eu não mereço 8h da manhã ser relembrada depois do que sonhei hoje, obrigada
>
> Slk dormi tão mancinho na madu que nem lembro se eu sonhei
>
> O tanto que eu dormi mal essa noite não tá escrito e não se compara com as doidera que eu sonhei nesse curto período de sono
>
> Há tempos tive um sonho, não me lembro, não me lembro... Tua tristeza é tão exata, e hoje o dia é tão bonito...

## O que entra

| | |
|---|---|
| os dados | o texto e a data de cada um dos 493.016 relatos do planeta V3 (`planeta-v3/dados/textos*.json`) |
| o embedding | a posição de cada relato na bola (`planeta-v3/dados/pontos.bin`, os 12 primeiros bytes de cada ponto): o bge-m3 projetado em 3D pelo UMAP (n_neighbors 15, cosseno), raios por posto (`planeta-v2/projetar.py`) |

Do `pontos.bin` sai só a posição, a fonte e a comunidade (estas duas para a
legenda de cada estrofe). Camada, portão, cargas e todos os outros bits vêm do
aluno ou da leitura e não são lidos.

O embedding usado é a forma publicada dele, em 3 dimensões. Os vetores de 1.024
dimensões ficam no `arquivo.db`, fora do repositório, e o modelo (bge-m3) não pôde
ser baixado no ambiente em que isto foi feito (o Hugging Face estava bloqueado).
Pela régua do `projetar.py`, a bola guarda perto de 60% do sinal de vizinhança
dos 1.024 eixos.

## Como

1. **As pontas** são as datas extremas do arquivo (`quando`; empate pelo menor
   índice). O sonho começa no resto do dia, a última coisa ouvida, e termina na
   lembrança mais antiga.
2. **Vizinhos**: os 15 mais próximos de cada relato na bola, o mesmo 15 com que o
   UMAP fez o planeta. O grafo é simétrico.
3. **O caminho**: Dijkstra, com o peso de cada aresta igual à distância na bola (a
   geodésica do Isomap). Não é a distância ao quadrado da `viagem/sonho.py`, que
   puxa o caminho para onde é denso.
4. **O texto**: cada nó do caminho é um relato, inteiro. Só @ e link virariam
   reticência (o caminho de hoje não tem nenhum).

O caminho mede 1,059 para uma corda de 0,969 entre as pontas: anda quase em linha
reta, porque a bola tem densidade pareja por construção (raio por posto). Os
passos vão de 0,010 a 0,041 (mediana 0,024). Para comparar, a distância mediana
de um relato ao 15º vizinho é 0,012.

## Com outra vizinhança

O caminho mais curto numa nuvem densa é uma linha fina: outro k troca os relatos,
mas o caminho fica no mesmo corredor. Medido para todo k de 5 a 30: a distância
média ao caminho de k=15 fica entre 0,003 e 0,054 (a bola tem raio 1), e de 16 a 19
vizinhos mais da metade dos relatos se repete. Alguns:

| k | passos | relatos em comum com k=15 (dos 41 do meio) | distância média ao caminho de k=15 |
|---:|---:|---:|---:|
| 5 | 68 | 3 | 0,040 |
| 6 | 56 | 2 | 0,054 |
| 8 | 52 | 1 | 0,050 |
| 10 | 50 | 12 | 0,034 |
| 12 | 45 | 12 | 0,034 |
| 13 | 44 | 31 | 0,006 |
| 14 | 41 | 19 | 0,027 |
| **15** | **42** | **41** | **0** |
| 16 | 42 | 33 | 0,003 |
| 18 | 38 | 23 | 0,009 |
| 20 | 36 | 11 | 0,022 |
| 25 | 34 | 9 | 0,023 |
| 30 | 32 | 8 | 0,025 |

`python3 sonho/sonhar.py --k 10` imprime o sonho de outra vizinhança e grava
`sonho/sonho_k10.json` sem mexer na página.

## Cuidado

- Vale o que o planeta V3 já tirou: relato com bandeira não está em
  `planeta-v3/dados`, então não está no grafo.
- Conteúdo sensível (`sensivel.json`, endosso de violência sonhada) fica no grafo,
  como fica no planeta; se o caminho passar por um, a estrofe leva a mesma
  etiqueta da ficha. Hoje não passa.
- A camada de propaganda vem do portão do aluno e por isso não é lida: se o caminho
  passar por um anúncio, o anúncio aparece. Hoje não passa.
- A página mostra só mês, ano e origem de cada relato, como o vídeo da viagem.
  `noindex`, como o resto do site.

## Rodar

```sh
pip install numpy scipy
python3 sonho/sonhar.py      # ~6 s: imprime o sonho, grava sonho/sonho.json e o texto no index.html
python3 -m http.server 8765  # na raiz do repositório; abrir http://127.0.0.1:8765/sonho/
```

Rodar de novo depois de regerar o planeta. Quando o arquivo ouvir mais, o último
relato muda, e o sonho também.
