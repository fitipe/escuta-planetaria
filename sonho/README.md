# Sonho

Pedido do João (02/10/2026): *"Use somente os dados e o embedding. Sonhe."* e,
depois da primeira versão: *"Ignore absolutamente tudo exceto os dados. Ignore
também o embedding."*

Entra só o texto dos 493.016 relatos (`planeta-v3/dados/textos*.json`, como
estão publicados). Não entram posição, rótulo, modelo, sorteio nem a aparência
de página nenhuma: `index.html` é só os parágrafos, com a fonte e as cores que
o navegador já tem.

## Como

- Palavra é o que fica entre espaços, como foi escrita.
- Com memória de k palavras, o sonho começa onde os relatos começam e diz, a
  cada passo, a palavra que mais vezes veio depois das k últimas, em todos os
  relatos. O fim de um relato também conta como palavra: se ele vence, o sonho
  acaba.
- Empate: decide quem vem mais vezes depois das k−1 últimas, depois das k−2, e
  assim até a frequência no arquivo inteiro; depois, a palavra que apareceu
  primeiro.
- Se o sonho volta a um ponto por onde já passou, nunca mais sai dali: a volta
  é escrita duas vezes e o sonho para.
- A noite vai de k = 0 até o primeiro k em que o sonho é, palavra por palavra, o
  relato inteiro de alguém. Foi k = 7.

Nenhuma dessas regras olha o que as palavras querem dizer. De 1 a 6 palavras de
memória, nenhum sonho é igual a um relato nem cabe dentro de um.

## A noite

**0 palavras de memória · volta**

> que que

**1 · volta**

> sonhei que eu não é um sonho é um sonho é

**2 · volta**

> sonhei que eu não sei se é o meu sonho é ter um relacionamento de 3 anos e não sei se é o meu sonho é ter um relacionamento de 3 anos e não sei

**3 · volta**

> sonhei que eu tava no show do bruno mars e ele me disse que não queria mais nada com ela e ela me disse que não queria mais nada com ela e ela me disse que

**4**

> sonhei que eu tava no show do bts e o yoongi começava a cantar dday eu fiquei tão animada que eu sonhei sobre isso e que o fez de forma mais covarde depois que todo sentimento já havia sido instalado. Correu para longe e me deixou sozinho em um quarto de hotel e o marido de uma amiga da minha mãe e eu não quero que ela se sinta mal por não ter uma boa relação com a minha mãe e ela me ofereceu uma fruta típica da região, eu provei e disse que não queria mais nada com ele. Mas estávamos conversando ainda... Até que dias depois, estávamos assistindo o jogo de futebol dos meus sonhos, espero que o corinthians tenha empatia com nós coitados do interior que não seja longe daqui. Sim, na capital tem de tudo, é daora, público diverso e tal. Pra quem é LGBT é praticamente um paraíso comparado com os arredores, mas depois de um tempo eu comecei a me sentir muito mal, com raiva, com medo, com sentimentos bons e ruins pq eu tô assim também, só não vem com orgulho tá... pq eu me arrependo de ter feito isso eu sempre me apaixonei por qualquer mina que me desse o valor que eu tenho, de poder passar o dia todo com a sensação de que eu nunca vou conseguir realizar meus sonhos e ser feliz com todos os meus amigos e eu não sabia o que fazer e não sei como lidar com isso no momento, mesmo que tenha sentimentos fortes e planos para o futuro. Eu já estive exatamente onde tu está, boa tenho 24 anos e sou um fracassado, eu falei isso com a depressão que eu já tinha. Agora eu tô aqui me sentindo mal por isso

**5**

> sonhei que eu tava no show do travis scott e ele me chamou no palco pra cantar a parte do kendrick em goosebumbs 😭😭😭

**6**

> sonhei que eu tava no show do travis no rock in rio (tava na grade) e eu tinha conseguido a blusa dele😭 mds não queria ter acordado nao

**7 · é o relato inteiro de alguém**

> sonhei que eu tava no show do travis scott 😞😞😞

## Rodar

```sh
pip install numpy
python3 sonho/sonhar.py   # ~2 min: imprime a noite e grava sonho.txt e index.html
```

A primeira versão (o caminho mais curto no embedding entre o último relato e o
primeiro) está no histórico, no commit dce284e.
