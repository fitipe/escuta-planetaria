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

## No arquipélago (o jogo, `arquipelago/`)

**O que o planeta já deixa de fora** — propaganda (camada 3) e os índices do
`cuidado.json` — fica fora das ilhas também: na geração e de novo na página,
que relê o `cuidado.json` do planeta enquanto ele for o mesmo de que as ilhas
saíram.
→ **Correto, não voltar.**

**Só uma amostra vira gente.** Cada ilha tem de 5 a 12 moradores, e cada um é
um sonho: 2.666 dos 444.591. Metade são os mais centrais do aglomerado, metade
ao acaso; texto repetido entra uma vez. Os outros contam no tamanho da ilha,
mas não aparecem.
→ **Por desenho**: é um jogo, não o arquivo — quem quer tudo tem o planeta.

**Nem todo morador tem um pedido.** A missão liga duas pessoas cujos sonhos
têm a mesma *coisa* ("o show", "o sapo"); 1.511 das 2.666 têm com quem se
ligar. Palavra que não é coisa (adjetivo antes do nome, "ao invés de",
"o quão"), xingamento e violência crua (tiro, facada, surra) não viram
pedido — o sonho aparece inteiro quando a pessoa conta, mas o jogo não manda
ninguém atrás disso.
→ Menor, registrado. As listas estão no `gerar.py` (`NAO_E_COISA`, `FEIO`).

**Nomes de gente saem em minúscula nos pedidos.** "sonhou com o jungkook":
a regra que reconhece nome próprio (maiúscula no meio da frase) não separa
bem ídolo de substantivo comum no Twitter, onde quase tudo é minúsculo.
Siglas sem vogal saem em maiúscula (BTS, BBB).
→ Menor, registrado.

**Relatos muito curtos ou muito longos só entram se faltar.** A amostra
prefere de 25 a 1.100 caracteres; os longos, quando entram, vão cortados.
→ Menor, registrado.

**O sonho de quem joga não passa pelo embedding.** O bge-m3 não roda no
navegador: a ilha nasce onde as *palavras* do sonho são características, não
onde o vetor dele cairia. Sonho sem palavra em comum com o arquivo nasce longe
de todas.
→ **Voltar se** couber um embedder pequeno na página. Um serviço próprio
resolveria, mas aí o sonho sairia do navegador — e hoje a promessa é que não sai.
