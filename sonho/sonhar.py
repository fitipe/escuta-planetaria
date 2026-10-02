#!/usr/bin/env python3
"""Sonho — só com os dados.

Pedido do João (02/10/2026): "Use somente os dados e o embedding. Sonhe." e,
depois: "Ignore absolutamente tudo exceto os dados. Ignore também o embedding."

O que entra: o texto de cada um dos relatos (planeta-v3/dados/textos*.json),
na ordem em que estão lá (por data). Mais nada: nem posição, nem rótulo, nem
modelo, nem sorteio, nem a aparência de página nenhuma.

Como os dados sonham:

- Palavra é o que fica entre espaços, como foi escrita (maiúscula, pontuação e
  emoji fazem parte dela).
- A memória tem k palavras. O sonho começa onde os relatos começam e diz,
  a cada passo, a palavra que mais vezes veio depois das k últimas, em todos os
  relatos. O fim de um relato também conta como palavra: se ele vence, o sonho
  acaba.
- Empate: decide quem vem mais vezes depois das k-1 últimas, depois das k-2, e
  assim até a frequência da palavra no arquivo inteiro; se ainda empatar, a
  palavra que apareceu primeiro.
- Se o sonho volta a um ponto por onde já passou, nunca mais sai dali (é
  determinístico): a volta é escrita duas vezes e o sonho para.
- A noite vai de k = 0 (nenhuma memória: a palavra mais frequente, para sempre)
  até o primeiro k em que o sonho é, palavra por palavra, o relato inteiro de
  alguém. Ali o sonho virou lembrança, e a noite acaba.

Saída: sonho/sonho.txt (um sonho por parágrafo) e sonho/index.html (os mesmos
parágrafos, sem estilo além das cores e da margem que o navegador já tem).

    python3 sonho/sonhar.py     # ~2 min, só numpy
"""
import html
import json
from collections import Counter
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
DADOS = AQUI.parent / 'planeta-v3' / 'dados'
KMAX = 16
INI, FIM = 0, 1


def ler_textos():
    meta = json.load(open(DADOS / 'meta.json'))
    textos = []
    for k in range(meta['arquivos_texto']):
        bloco = json.load(open(DADOS / f'textos{k}.json'))
        assert bloco['i0'] == len(textos)
        textos += bloco['textos']
    return textos


class Arquivo:
    def __init__(self, textos):
        self.palavras = [t.split() for t in textos]
        ids = {}
        for ws in self.palavras:          # id pela ordem em que a palavra aparece
            for w in ws:
                if w not in ids:
                    ids[w] = len(ids) + 2
        self.pal = ['', ''] + list(ids)
        seqs = ([INI] * KMAX + [ids[w] for w in ws] + [FIM] for ws in self.palavras)
        self.arr = np.fromiter((x for s in seqs for x in s), dtype=np.int32)
        self.freq = np.bincount(self.arr, minlength=len(self.pal))
        self.inteiros = Counter(' '.join(ws) for ws in self.palavras)

    def seguintes(self, ctx):
        """{palavra: vezes} do que vem depois do contexto, em todos os relatos."""
        a, k = self.arr, len(ctx)
        m = a[:len(a) - k] == ctx[0]
        for j in range(1, k):
            m &= a[j:len(a) - k + j] == ctx[j]
        u, n = np.unique(a[np.nonzero(m)[0] + k], return_counts=True)
        return {int(w): int(c) for w, c in zip(u, n) if w != INI}

    def escolher(self, ctx):
        if not ctx:
            cand = [int(np.argmax(self.freq[2:])) + 2]
        else:
            d = self.seguintes(ctx)
            cand = [w for w, n in d.items() if n == max(d.values())]
        j = len(ctx) - 1
        while len(cand) > 1 and j >= 1:
            dj = self.seguintes(ctx[-j:])
            topo = max(dj.get(w, 0) for w in cand)
            cand = [w for w in cand if dj.get(w, 0) == topo]
            j -= 1
        if len(cand) > 1:
            topo = max(self.freq[w] for w in cand)
            cand = [w for w in cand if self.freq[w] == topo]
        return min(cand)

    def sonhar(self, k):
        ctx, saida, visto = [INI] * k, [], {}
        while True:
            estado = tuple(ctx)
            if estado in visto:                    # volta: escreve a volta mais uma vez
                return saida + saida[visto[estado]:], True
            visto[estado] = len(saida)
            w = self.escolher(ctx)
            if w == FIM:
                return saida, False
            saida.append(w)
            ctx = (ctx + [w])[1:] if k else []


def main():
    arq = Arquivo(ler_textos())
    noite = []
    for k in range(KMAX + 1):
        ws, volta = arq.sonhar(k)
        txt = ' '.join(arq.pal[w] for w in ws)
        lembranca = not volta and arq.inteiros.get(txt, 0) > 0
        noite.append(txt)
        print(f'[{k} palavras de memória{" · volta" if volta else ""}'
              f'{" · é um relato" if lembranca else ""}]\n{txt}\n')
        if lembranca:
            break
    else:
        raise SystemExit(f'nenhum sonho virou relato até k = {KMAX}')

    (AQUI / 'sonho.txt').write_text('\n\n'.join(noite) + '\n')
    corpo = '\n'.join(f'<p>{html.escape(t)}</p>' for t in noite)
    (AQUI / 'index.html').write_text(f'''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex">
<title>{html.escape(' '.join(noite[1].split()[:3]))}</title>
<style>
:root{{--fundo:Canvas;--texto:CanvasText;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{color-scheme:dark}}}}
:root[data-theme="dark"]{{color-scheme:dark}}
body{{background:var(--fundo);color:var(--texto);padding-inline:16px;padding-block:8px;overflow-wrap:anywhere}}
</style>
{corpo}
''')
    print(f'{len(noite)} sonhos → sonho/sonho.txt · sonho/index.html')


if __name__ == '__main__':
    main()
