# O que ficou de fora, e em que etapa

*Levantado em 24/09/2026 a pedido do Fitipe. Cada linha diz o que foi excluído,
por qual decisão, e se é para voltar. **Este arquivo é para ser atualizado
sempre que uma etapa nova cortar alguma coisa.***

A regra que vale para tudo aqui é a que o Fitipe estabeleceu na rubrica:
**descartar exige justificativa.** Uma exclusão sem motivo escrito é um buraco,
não uma decisão.

---

## Na coleta

**Bluesky sem nenhuma imagem — 138.212 relatos.** O coletor nunca leu o campo
`embed` da API e nem o guardou no payload cru, então o dado **não existe no
arquivo**: só voltando à API post a post. Post de piada com imagem, print de
conversa, sonho desenhado — tudo entrou como texto solto e incompleto.
→ **Voltar.** Sugerido: só na fatia de literal com pouco texto, onde a imagem
provavelmente carrega o sentido.

**358 posts do Bluesky com carimbo de tempo corrompido**, que caem em 1970.
→ **Voltar**, ou vão virar um tufo em 1970 na linha do tempo do planeta.

**Textos mutilados pela coleta.** Relatos que chegaram cortados no meio da
palavra ("abando-") ou terminando em "+", porque a thread seguia noutro post
que não foi guardado. A marca `texto_truncado` os conta, mas só entre os
anotados.
→ **Medir quantos são** antes de decidir.

---

## Na moagem

**Lotes com "Dreams" ou "Lucid" no nome — 54.215 pendentes.** O moinho os exclui
por padrão, com `--tudo` para incluir. **Não sei por que essa exclusão existe** —
é anterior a mim. Provavelmente subreddits em inglês ou de sonho lúcido que
foram decididos fora de escopo.
→ **Decisão do Fitipe.** Se for para incluir, é só rodar com `--tudo`.

**491 relatos do piloto**, com id de 10 caracteres e sem autor. Estão no arquivo
e funcionam, mas não têm hash de autor, então as duas regras de duplicata que
dependem dele não pegam neles.
→ Menor, mas registrado.

**1.700 relatos sem embedding** (e crescendo), porque o moinho está rodando com
`--sem-embed` enquanto a gente decide qual embedder usar.
→ **Voltar obrigatoriamente**: sem embedding não há posição no planeta, não há
régua e não há busca. É backfill, não recoleta.

---

## Na classificação

**Duplicatas — 2.153.** Marcadas por `canonico_de`, ficam fora do planeta de
propósito: são a mesma pessoa repetindo. **Correto, não voltar.**

**Menos de 25 caracteres — 8.888.** Aqui mora "pesadelo", "Que pesadelo", "meu
sonho 😭" — e a amostra-prova mostrou que **138 pessoas diferentes escreveram
só "pesadelo"** na mesma semana do bloqueio do X. Isso não é lixo: é o sonho
coletivo na sua forma mais curta.
→ **Voltar.** É a exclusão mais questionável de todas.

**Mais de 700 caracteres — 27.916.** Relatos longos, que costumam ser os mais
narrados e mais ricos. O corte existe por custo de processamento, não por
conteúdo.
→ **Voltar**, pelo menos truncando em vez de excluindo.

**1.449 sem a palavra sonho/pesadelo/devaneio.** Entraram por outro critério da
coleta. Provavelmente ruído, mas não conferido.
→ **Amostrar e decidir.**

---

## Nas ferramentas

**A régua é cega para 22.641 relatos.** Ela só compara os que a anotação v2.1 do
qwen chamou de `relato` — e é justamente onde mora o anúncio: três textos de
marketing da mesma fôrma entraram no material de treino com zero entradas na
tabela de ecos.
→ **Consertar a régua** para comparar tudo que tem embedding.

**O sorteio de fatias excluía 65.177 relatos** cujo id começa com letra, por um
`CAST` decimal sobre id hexadecimal. **Já consertado**, mas os 519 primeiros
anotados vieram desse universo menor. Medido: sem viés de conteúdo (mesmo
tamanho médio, mesma proporção de "sonhei que", mesma divisão por fonte).
→ Consertado; registrado para a tese.

---

## Na rubrica

**O tom não é usado.** A cabeça do classificador falhou (5,3% contra 43% de
chute) e a causa está diagnosticada: a rubrica define `leve` e não define `seco`,
e os emojis que decidem o tom sozinhos não estão mapeados.
→ **Voltar depois da v3.3.**

**As classes raras do portão não são previstas**: `obra`, `noticia`,
`fala_do_sonhar`, `devaneio` têm de 6 a 37 exemplos de treino e revocação zero.
Elas existem na camada aberta e são achadas por busca; o classificador é que não
as reconhece.
→ **Voltar via aprendizado ativo**, com os 8.678 indecisos.

**Tudo que está em `rubrica/pendente-v3.3.md`** — o quarto quadrante da carga, o
`estranha`, os valores que faltam no `despertar`, a recorrência de figura, as
espécies de atribuição, o jogo do bicho, o celebratório.

---

## No Latente (o jogo, 28/09)

O Latente (`latente/`) não lê o banco: parte do que o planeta V2 publica e
escolhe dali as suas vozes. É uma colagem — as palavras saem do contexto e se
emendam com as de outra pessoa —, por isso o crivo é mais duro que o do
planeta. **Nada disto vale para o planeta.** Números de `latente/preparar.py`.

**O céu: tudo o que o planeta mostra (444.498).** Fora ficam o `cuidado.json`
(3.065), as cópias escondidas (103) e a camada de propaganda.
→ **Correto.**

**As vozes: 47.532 de ~250 mil que passam no crivo.** Amostra com semente fixa:
34 mil literais (os que abrem contando o sonho pesam o dobro) e 13,5 mil
desejos (os 36 mais próximos de cada desejo da noite, mais 7 mil ao acaso).
→ Corte por **tamanho de download** (7 MB), não por conteúdo. Pode crescer.

**Tamanho: literal com menos de 45 caracteres, desejo com menos de 30, e tudo
acima de 1.500 (66.591 somados).** Os longos que ficam entram até 900
caracteres, cortados no fim de uma frase.
→ O curto ("pesadelo") não tem o que emendar: não serve à colagem. Os longos
voltam se o teto de download subir.

**Idioma: 4.708** que não parecem português (os subs em inglês, sobretudo).
→ Correto para o jogo: a emenda precisa da mesma língua.

**O crivo: 29.094 relatos (~10% dos candidatos).** Sai o relato inteiro com
sexo explícito (e gíria dele), xingamento e ofensa, violência sexual e **ideação** (`IDEACAO`:
desejo ou alívio perto de morrer/sumir, "me mata", "dormir pra sempre", "pular
da ponte"). O `IDEACAO` pega também hipérbole ("o calor tá me matando") e
pesadelos em que alguém mata quem sonha — de propósito: na colagem, o "queria"
de uma pessoa e o "me matar" de outra viram uma frase. Nos desejos, sai também
morte, violência, doença e política. **Pesadelo de morte, perseguição, zumbi e
guerra fica**: é sonho.
→ Correto para o jogo. Em tempo de jogo, uma vigia no `motor.js` ainda impede
que uma emenda forme vontade + morte.

**Os desejos da noite: 206 escolhidos a mão** entre ~900 candidatos
(`latente/desejos.txt`). Saíram os que dependem do post a que respondiam, os que
nomeiam pessoa privada, os agressivos, os sexuais, os de corpo e peso, e todo
desejo de sumir, morrer ou se ferir, mesmo dito como piada.
→ Critério escrito no próprio arquivo.

**Achado de passagem, para o cuidado:** o `IDEACAO` casa com 5.587 relatos do
planeta, e **3.984 não estão no `cuidado.json`**. Muitos são hipérbole ou
pesadelo, mas não todos, e o planeta os mostra.
→ **Rodar como sonda**, no fluxo das bandeiras.
