#!/usr/bin/env python3
"""Sonho — feito só com os dados e o embedding.

Pedido do João (02/10/2026): "Use somente os dados e o embedding. Sonhe."

Entram duas coisas, e nada além delas:

  os dados      o texto e a data de cada relato do planeta V3 (planeta-v3/dados)
  o embedding   a posição de cada relato na bola: o bge-m3 projetado em 3D pelo
                UMAP (n_neighbors 15, cosseno), raios por posto
                (planeta-v2/projetar.py). É a forma publicada do embedding: os
                vetores de 1.024 dimensões ficam no banco, fora do repositório.

Ficam de fora: modelo de linguagem, rótulo de anotador (Opus, Fitipe), palpite
do aluno, a camada de propaganda (que vem do portão do aluno), sorteio e
escolha minha de trecho. Não há semente porque não há acaso: com os mesmos
dados, o sonho é sempre o mesmo.

O SONHO é o caminho mais curto, de vizinho em vizinho, do último relato que o
arquivo ouviu até o primeiro.

- As duas pontas são as datas extremas do arquivo. O sonho começa no resto do
  dia — a última coisa ouvida antes de dormir — e termina na lembrança mais
  antiga.
- Vizinho é um dos 15 mais próximos na bola: o mesmo 15 com que o UMAP fez o
  planeta (a ideia de vizinhança que o próprio embedding usa). O grafo é
  simétrico (basta um dos dois ter o outro entre os 15).
- O peso de cada passo é a distância na bola (o caminho é a geodésica do
  Isomap). Não é a distância ao quadrado do viagem/sonho.py (noutro ramo),
  que puxa o caminho para onde é denso: aqui não se escolhe por onde o sonho passa.
- Cada passo é um relato, inteiro. O texto não é cortado nem reordenado; só o
  @ e o link (que o caminho de hoje não tem) virariam reticência.

Saída: sonho/sonho.json (as posições, para o fio e a poeira), o texto do sonho
escrito dentro de sonho/index.html (entre as marcas <!--gerado:sonho-->, para a
página estar inteira antes de carregar qualquer coisa) e o sonho impresso.

    python3 sonho/sonhar.py            # ~6 s, só numpy e scipy
    python3 sonho/sonhar.py --k 10     # outra vizinhança, outro sonho (só imprime e grava o json)
"""
import argparse
import base64
import html
import json
import re
import struct
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

AQUI = Path(__file__).parent
DADOS = AQUI.parent / 'planeta-v3' / 'dados'
K = 15                 # n_neighbors do UMAP que fez o planeta
POEIRA = 12            # a página desenha 1 de cada 12 pontos do planeta (pelo índice)
BYTES_PONTO = 26       # planeta-v3/gerar.py: 3f · B B B H B H B B I
ARROBA = re.compile(r'@[\w.\-]+')
LINK = re.compile(r'https?://\S+|www\.\S+')


def ler_planeta():
    meta = json.load(open(DADOS / 'meta.json'))
    b = open(DADOS / 'pontos.bin', 'rb').read()
    n = struct.unpack_from('<I', b, 0)[0]
    reg = np.frombuffer(b, dtype=np.uint8, count=n * BYTES_PONTO, offset=4).reshape(n, BYTES_PONTO)
    xyz = reg[:, :12].copy().view('<f4').reshape(n, 3).astype('float64')
    fonte = reg[:, 13]          # o byte 12 é a camada, que não entra
    comunidade = reg[:, 14]
    textos, quando = [], []
    for k in range(meta['arquivos_texto']):
        bloco = json.load(open(DADOS / f'textos{k}.json'))
        assert bloco['i0'] == len(textos)
        textos += bloco['textos']
        quando += bloco['quando']
    assert len(textos) == n == meta['n']
    return meta, xyz, fonte, comunidade, textos, quando


def caminho(xyz, a, b, k=K):
    """Geodésica de a até b no grafo dos k vizinhos (peso = distância na bola)."""
    n = len(xyz)
    dist, viz = cKDTree(xyz).query(xyz, k=k + 1, workers=-1)
    linhas = np.repeat(np.arange(n), k)
    G = csr_matrix((dist[:, 1:].ravel(), (linhas, viz[:, 1:].ravel())), shape=(n, n))
    G = G.maximum(G.T)
    _, pred = dijkstra(G, indices=a, return_predecessors=True)
    c = [b]
    while c[-1] != a:
        assert pred[c[-1]] >= 0, 'as pontas não se ligam no grafo'
        c.append(int(pred[c[-1]]))
    return c[::-1]


def limpar(texto):
    return LINK.sub('…', ARROBA.sub('…', texto)).strip()


MESES = 'jan fev mar abr mai jun jul ago set out nov dez'.split()
milhar = lambda v: f'{v:,}'.replace(',', '.')
decimal = lambda v, casas=3: f'{v:.{casas}f}'.replace('.', ',')
dia = lambda q: f'{int(q[8:10])} {MESES[int(q[5:7]) - 1]} {q[:4]}'


def escrever_pagina(saida):
    """O texto do sonho e os números vão para dentro do index.html."""
    pagina = AQUI / 'index.html'
    h = pagina.read_text()
    estrofes = []
    for no in saida['nos']:
        versos = ''.join(f'<span>{html.escape(v.strip())}</span>'
                         for v in no['texto'].split('\n') if v.strip())
        q = no['quando']
        aviso = (' · <b class="sensivel">conteúdo sensível · violência sonhada endossada '
                 'ao acordar</b>') if no['sensivel'] else ''
        estrofes.append(f'    <li style="--d:{no["passo"]}"><p class="voz">{versos}</p>'
                        f'<p class="de">{MESES[int(q[5:7]) - 1]} {q[:4]} · '
                        f'{html.escape(no["origem"])}{aviso}</p></li>')
    h, n = re.subn(r'(<!--gerado:sonho-->\n).*?(<!--/gerado:sonho-->)',
                   lambda m: m.group(1) + '\n'.join(estrofes) + '\n' + m.group(2), h, flags=re.S)
    assert n == 1, 'faltam as marcas <!--gerado:sonho--> no index.html'
    numeros = {'de': dia(saida['de']), 'ate': dia(saida['ate']),
               'relatos': str(len(saida['nos'])), 'total': milhar(saida['n']),
               'k': str(saida['k']), 'passos': str(len(saida['nos']) - 1),
               'comprimento': decimal(saida['comprimento']), 'corda': decimal(saida['corda'])}
    for chave, valor in numeros.items():
        h, n = re.subn(rf'(data-g="{chave}">)[^<]*(<)', rf'\g<1>{valor}\g<2>', h)
        assert n >= 1, chave
    pagina.write_text(h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--k', type=int, default=K)
    args = ap.parse_args()

    meta, xyz, fonte, comunidade, textos, quando = ler_planeta()
    # as pontas: a data mais antiga e a mais recente (empate: o menor índice)
    tempo = sorted(range(len(quando)), key=lambda i: (quando[i], i))
    primeiro, ultimo = tempo[0], tempo[-1]

    c = caminho(xyz, ultimo, primeiro, args.k)
    passos = np.r_[0.0, np.linalg.norm(np.diff(xyz[c], axis=0), axis=1)]

    def origem(i):
        f = meta['fontes'][fonte[i]]
        com = meta['comunidades'][comunidade[i]]
        return 'bluesky' if f == 'bluesky' else f'r/{com}'

    # o caminho não desvia do conteúdo sensível (endosso de violência sonhada,
    # que a página do planeta mostra com etiqueta): se passar por um, a estrofe
    # leva a mesma etiqueta. Hoje não passa.
    sensivel = set(json.load(open(DADOS / 'sensivel.json')))
    nos = [{'i': int(i), 'texto': limpar(textos[i]), 'quando': quando[i],
            'origem': origem(i), 'xyz': [round(float(v), 5) for v in xyz[i]],
            'passo': round(float(p), 5), 'sensivel': int(i) in sensivel}
           for i, p in zip(c, passos)]

    poeira = np.round(xyz[::POEIRA] * 32767).astype('<i2')
    saida = {
        'pedido': 'Use somente os dados e o embedding. Sonhe.',
        'k': args.k, 'n': len(xyz),
        'de': quando[ultimo], 'ate': quando[primeiro],
        'corda': round(float(np.linalg.norm(xyz[ultimo] - xyz[primeiro])), 4),
        'comprimento': round(float(passos.sum()), 4),
        'nos': nos,
        'poeira': base64.b64encode(poeira.tobytes()).decode(),
        'poeira_passo': POEIRA,
    }
    nome = 'sonho.json' if args.k == K else f'sonho_k{args.k}.json'
    json.dump(saida, open(AQUI / nome, 'w'), ensure_ascii=False, separators=(',', ':'))
    if args.k == K:
        escrever_pagina(saida)

    print(f'{len(xyz)} relatos · do último ({quando[ultimo][:10]}) ao primeiro '
          f'({quando[primeiro][:10]}) · {len(c) - 1} passos de vizinho (k={args.k}) · '
          f'geodésica {passos.sum():.3f} para uma corda de {saida["corda"]:.3f}\n')
    for no in nos:
        print(no['texto'])
        print(f'    ({no["quando"][:7]} · {no["origem"]} · passo {no["passo"]:.3f})\n')
    print(f'→ sonho/{nome}')


if __name__ == '__main__':
    main()
