#!/usr/bin/env python3
"""Viagem — potências de dez, em sonho.

Na trilha do "Zooming out from Earth to the Observable Universe"
(https://youtu.be/x896_J1k8rM), mas no espaço dos sonhos: parte de UM relato
e se afasta em potências de dez — 1, 10, 100, 1.000, 10.000, 100.000 sonhos —
até o planeta inteiro, e dali até ele virar um ponto de luz, como o primeiro.

O espaço é o do planeta V2 (planeta-v2/dados): a posição de cada ponto vem
só da semântica, então perto quer dizer parecido, e nada mais. A régua da
viagem não é o metro, é o sonho: cada escala é o raio que abarca 10ⁿ relatos
em volta do de partida. E os nomes de cada escala não são escritos à mão:
emergem da vizinhança (as palavras que ela tem e o resto do arquivo não),
como os nomes que aparecem sob o cursor na página.

Valem as mesmas regras da página: fica de fora o que tem bandeira de cuidado
(dados/cuidado.json) e a propaganda; as cores são as dela (literal, figurado,
incerto).

Uso (numpy, scipy, pillow e imageio-ffmpeg — este último já traz o ffmpeg):
    python3 viagem/viagem.py                   # 1080p, 30 qps → viagem/viagem.mp4
    python3 viagem/viagem.py --previa          # 540p, para conferir o ritmo
    python3 viagem/viagem.py --quadro 20       # só o quadro do segundo 20, em PNG
    python3 viagem/viagem.py --sonho "sonhei com praia de novo"   # outra partida
    python3 viagem/viagem.py --altura 2160     # 4K
As fontes (Spectral e IBM Plex Mono, as da página) vêm do Google Fonts na
primeira vez e ficam em viagem/fontes/.
"""
import argparse
import json
import math
import re
import struct
import subprocess
import sys
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage
from scipy.cluster.vq import kmeans2
from scipy.interpolate import PchipInterpolator
from scipy.spatial import cKDTree

AQUI = Path(__file__).resolve().parent
DADOS = AQUI.parent / 'planeta-v2' / 'dados'
PASTA_FONTES = AQUI / 'fontes'

# ————————————————————————— o roteiro —————————————————————————
# Trecho do texto do sonho de partida (sem acento nem caixa, basta ser único).
# O índice do ponto muda a cada regeração do planeta; o texto, não.
PARTIDA = 'sonhei que eu estava na lua'

# (segundo, u) — u é o log10 do número de sonhos em volta: 0 é um sonho,
# 3 são mil. 'T' é o arquivo inteiro. Entre as marcas o movimento é contínuo
# (PCHIP, monótono); onde u quase não muda, a câmera desacelera e dá tempo de
# ler. Os trechos sem pressa são os de 1 e de 10 sonhos, onde há texto.
MARCAS = [
    (0.0, -0.35), (12.0, 0.0),        # um sonho só: tempo de ler
    (16.0, 0.93), (23.5, 1.07),       # 10
    (27.0, 1.95), (31.5, 2.07),       # 100
    (35.0, 2.95), (39.5, 3.07),       # 1.000
    (43.0, 3.95), (47.5, 4.07),       # 10.000
    (51.0, 4.95), (55.5, 5.07),       # 100.000
    (62.0, 'T'), (74.0, 'T'),         # o planeta inteiro, girando
    (84.0, 'T+2.6'), (95.0, 'T+2.75'),  # até caber num ponto
]

# (início, fim, texto) — {todos} vira o número de relatos no planeta
LEGENDAS = [
    (16.5, 23.0, 'aqui, perto quer dizer parecido'),
    (63.0, 72.5, '{todos} relatos públicos de sonho e desejo · 2015–2026'),
    (76.0, 82.0, 'de longe, o arquivo inteiro cabe num ponto de luz'),
    (83.0, 88.5, 'em volta, tudo o que se sonhou e ninguém contou'),
]
CARTAO_FINAL = (89.0, 95.0)
CREDITO = 'arquivo de sonhos e desejos públicos · Fitipe, PPGCA/UFF · com João Carabetta'
ENDERECO = 'escutaplanetaria.carabetta.xyz'

# ————————————————————————— a aparência (a da página) —————————————————————————
VAZIO = np.array([5, 6, 11], np.float32) / 255
COR_LIT, COR_FIG, COR_INC, COR_OUTRO = (107, 168, 255), (255, 190, 92), (195, 155, 255), (91, 99, 118)
CINZA = np.array([122, 128, 150], np.float32) / 255
CLARO, TEXTO, FRACO = (230, 234, 244), (198, 201, 214), (111, 116, 136)
CLASSES = ['literal', 'figurado', 'incerto']
CORES_CLASSE = [COR_LIT, COR_FIG, COR_INC]

FOV = math.radians(50)
GANHO = 1.6                 # exposição do mapa de tons (1 − e^(−ganho·luz))

TIRA_ACENTO = str.maketrans('áàâãäéèêëíìîïóòôõöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')
# palavras que estão em toda parte e não nomeiam vizinhança nenhuma
VAZIAS = set("""a o e de da do das dos em um uma que com para por nao mais eu me minha meu se
ela ele isso essa esse sua seu voce vc ja como mas ou foi era ser ter tem tinha muito muita
quando sempre pra pro tambem depois ate anos ano dia dias hoje ontem noite sonho sonhos sonhei
sonhar sonhando sonhou sonha sonhava tudo nada aqui ali onde nunca antes agora ainda vez vezes
outra outro outros outras dela dele deles delas meus minhas seus suas tenho tive sinto acho
sei fazer faz vou estou esta sou sao fui gente coisa coisas vida pessoa pessoas tempo casa pq
porque entao the and to of in that you was it is for with on this but not have are my
na no nos nas num numa uns umas ao aos pela pelo pelas pelos mim ta tava tavam estava estavam
estar estou tipo eh la so ne kkk kkkk kkkkk kkkkkk kkkkkkk tbm mto vcs voces cara mano
aquele aquela aqueles isto dessa desse nessa nesse neste nesta mesmo mesma bem bom boa assim
sim nem sem sobre cada todo toda todos todas sendo sido seja fosse fica ficou ficar vai vem
veio ver vi via teve fez disse dizer falar falei falou acordei acordar dormir dormi qual
quem pois lá algo alguma algum alguns muitos muitas pouco quase tao tanto tanta la aí ai
ter tive tivesse ia iam indo ir vai vão tem ta to tô voce você dele alguem ninguem
uma umas porra caralho kkkkkkkk hein aff mds meu deus lembro lembrar lembrei lembra queria
quero quer queriam sentia sentindo achava achei parecia parece acontecer aconteceu fiquei
ficava ficando dizendo falando pensando sabe sabia alguma nenhum nenhuma dentro frente
acontece acontecendo pessoal comigo contigo desde disso nisso daquilo naquele naquela aquilo consigo
consegui conseguir conseguia posso pode podia poder""".split())
# o que não pode abrir nem fechar uma expressão ("na lua" não é expressão;
# "fim do mundo" é) — e o que pode ligar as duas pontas de uma de três
BORDA = (VAZIAS | set("""a o as os e de da do das dos em na no nas nos um uma uns umas que com
pra pro para por se me eu meu minha te ao aos essa esse isso tive tenho tinha ter foi era
estava estavam tava tavam sou estou vou fui ser sendo fiquei ficou mais muito muita tao ja so
sonhei""".split())) - {'sonho', 'sonhos'}      # "sonho de consumo", "bons sonhos"
LIGA = set('de da do das dos no na nos nas em e'.split())


# ————————————————————————— utilidades —————————————————————————
def suave(a, b, x):
    """smoothstep de a até b (aceita escalares e vetores)."""
    t = np.clip((np.asarray(x, dtype=np.float64) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def janela(x, a, b, c, d):
    """0 antes de a, sobe até b, fica em 1 até c, desce até d."""
    return float(suave(a, b, x) * (1 - suave(c, d, x)))


def milhar(n):
    return f'{n:,}'.replace(',', '.')


def fichas(texto):
    return set(re.findall(r'[a-z]{3,}', texto.lower().translate(TIRA_ACENTO))) - VAZIAS


def baixar_fontes():
    """As fontes da página, do Google Fonts, uma vez só."""
    PASTA_FONTES.mkdir(exist_ok=True)
    querer = {'spectral-200i': ('Spectral', 'italic', 200),
              'spectral-300i': ('Spectral', 'italic', 300),
              'plex-300': ('IBM Plex Mono', 'normal', 300),
              'plex-400': ('IBM Plex Mono', 'normal', 400)}
    faltam = {k: v for k, v in querer.items() if not (PASTA_FONTES / f'{k}.ttf').exists()}
    if faltam:
        url = ('https://fonts.googleapis.com/css2?family=Spectral:ital,wght@1,200;1,300'
               '&family=IBM+Plex+Mono:wght@300;400')
        # agente antigo: o Google só serve .ttf (que o Pillow lê) para quem não entende woff2
        css = urlopen(Request(url, headers={'User-Agent': 'Mozilla/4.0'}), timeout=30).read().decode()
        for bloco in re.findall(r'@font-face\s*{([^}]*)}', css):
            fam = re.search(r"font-family:\s*'([^']+)'", bloco).group(1)
            est = re.search(r'font-style:\s*(\w+)', bloco).group(1)
            peso = int(re.search(r'font-weight:\s*(\d+)', bloco).group(1))
            ttf = re.search(r'url\((https://[^)]+)\)', bloco).group(1)
            for k, alvo in faltam.items():
                if alvo == (fam, est, peso):
                    (PASTA_FONTES / f'{k}.ttf').write_bytes(urlopen(ttf, timeout=30).read())
    return {k: str(PASTA_FONTES / f'{k}.ttf') for k in querer}


# ————————————————————————— o som —————————————————————————
# ré maior pentatônica: consonante em qualquer combinação
PENTATONICA = np.array([293.66, 329.63, 369.99, 440.00, 493.88])


def tocar(pista, t0, freq, amp, pan, tau=1.2, taxa=48000):
    """Um sino na pista (2×n): seno com dois parciais que se apagam antes dele,
    ataque de 6 ms (sem estalo), pan de potência constante."""
    n = pista.shape[1]
    dur = min(6 * tau + 0.05, 8.0)
    t = np.arange(int(dur * taxa)) / taxa
    x = (np.sin(2 * np.pi * freq * t) * np.exp(-t / tau)
         + 0.22 * np.sin(2 * np.pi * 2.0 * freq * t + 0.3) * np.exp(-t / (0.45 * tau))
         + 0.07 * np.sin(2 * np.pi * 3.01 * freq * t + 1.1) * np.exp(-t / (0.25 * tau)))
    x *= (1 - np.exp(-t / 0.006)) * amp
    i0 = int(t0 * taxa)
    if i0 >= n:
        return
    x = x[:n - i0]
    ang = (np.clip(pan, -1, 1) + 1) * math.pi / 4
    pista[0, i0:i0 + len(x)] += (x * math.cos(ang)).astype(np.float32)
    pista[1, i0:i0 + len(x)] += (x * math.sin(ang)).astype(np.float32)


def gravar(pista, caminho, duracao, rng, taxa=48000):
    """Sala (ruído que se apaga, escurecido, convolvido: 2,5 s de cauda),
    entrada e saída suaves, teto macio e WAV de 16 bits."""
    from scipy.signal import fftconvolve, lfilter
    import wave
    n = pista.shape[1]
    t = np.arange(n) / taxa
    m = int(2.5 * taxa)
    cauda = np.exp(-np.arange(m) / (0.8 * taxa))
    sala = np.stack([lfilter([0.35], [1, -0.65], rng.standard_normal(m)) * cauda for _ in range(2)])
    sala /= np.sqrt((sala ** 2).sum(axis=1, keepdims=True))
    molhado = np.stack([fftconvolve(pista[c], sala[c])[:n] for c in range(2)]).astype(np.float32)
    mix = 0.75 * pista + 0.55 * molhado
    mix *= (suave(0, 0.6, t) * (1 - suave(duracao - 1.5, duracao, t))).astype(np.float32)
    mix = np.tanh(1.3 * mix) / math.tanh(1.3)
    mix *= 0.89 / max(1e-6, float(np.abs(mix).max()))
    with wave.open(str(caminho), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(taxa)
        w.writeframes((mix.T * 32767).astype('<i2').tobytes())
    return caminho


# ————————————————————————— a viagem —————————————————————————
class Viagem:
    def __init__(self, altura=1080, qps=30, partida=PARTIDA):
        self._base(altura, qps)
        self._partida(partida)
        self._escalas()
        self._tempo()
        self._rotulos()

    def _base(self, altura, qps):
        """Tela, dados, fundo e fontes: o que a viagem e o sonho têm em comum."""
        self.H = int(altura) // 8 * 8
        self.W = int(round(self.H * 16 / 9)) // 8 * 8
        self.S = self.H / 1080            # tudo que é pixel é escrito para 1080p
        self.qps = qps
        self.F = (self.H / 2) / math.tan(FOV / 2)
        self._carregar()
        self._fundo()
        self.fontes = baixar_fontes()
        self._cache_sprites = {}

    # ——— dados: exatamente o que a página mostra por padrão ———
    def _carregar(self):
        t0 = time.time()
        buf = (DADOS / 'pontos.bin').read_bytes()
        n = struct.unpack_from('<I', buf, 0)[0]
        dt = np.dtype([('pos', '<f4', 3), ('nat', 'u1'), ('fonte', 'u1'), ('com', 'u1'),
                       ('ano', '<u2'), ('mes', 'u1'), ('bits', '<u2'), ('plit', 'u1'), ('pfig', 'u1')])
        rec = np.frombuffer(buf, dtype=dt, count=n, offset=4)
        meta = json.load(open(DADOS / 'meta.json'))
        cuidado = [i for i in json.load(open(DADOS / 'cuidado.json')) if 0 <= i < n]
        textos = []
        for b in range(meta['arquivos_texto']):
            bloco = json.load(open(DADOS / f'textos{b}.json'))
            assert bloco['i0'] == len(textos), f'textos{b}.json fora de ordem'
            textos += bloco['textos']
        bits = rec['bits'].astype(np.int64)
        # como o visivel() da página com os filtros de fábrica: sem bandeira de
        # cuidado, sem a camada de propaganda, com algum marcador aceso
        vis = (rec['nat'] == 0) & ((bits & 7) > 0)
        vis[cuidado] = False
        self.ids = np.nonzero(vis)[0]
        self.nv = len(self.ids)
        self.P = rec['pos'][self.ids].astype(np.float32)
        b = bits[self.ids]
        inc, lit, fig = (b & 4) > 0, (b & 1) > 0, (b & 2) > 0
        cor = np.zeros((self.nv, 3), np.float32)
        cor[:] = COR_OUTRO
        cor[lit & ~fig] = COR_LIT
        cor[fig & ~lit] = COR_FIG
        cor[lit & fig] = [(a + c) / 2 for a, c in zip(COR_LIT, COR_FIG)]
        cor[inc] = COR_INC                       # incerto: cor própria, sempre
        self.cor = cor / 255
        self.classe = np.where(inc, 2, np.where(lit, 0, 1)).astype(np.int8)
        self.ano, self.mes = rec['ano'][self.ids], rec['mes'][self.ids]
        self.com = rec['com'][self.ids]
        self.meta = meta
        self.textos = [textos[i] for i in self.ids]
        self.arvore = cKDTree(self.P.astype(np.float64))
        print(f'{self.nv} relatos no campo ({n} no arquivo) · {time.time() - t0:.1f}s', flush=True)

    def _contar_palavras(self):
        """As palavras de cada relato, para os nomes que emergem."""
        t0 = time.time()
        self.docs = [fichas(t) for t in self.textos]
        self.df = Counter()
        for d in self.docs:
            self.df.update(d)
        print(f'palavras contadas · {time.time() - t0:.1f}s', flush=True)

    def _partida(self, partida):
        if str(partida).isdigit():             # índice no pontos.bin
            onde = np.nonzero(self.ids == int(partida))[0]
            if not len(onde):
                sys.exit(f'o ponto {partida} não está no campo (cuidado, propaganda ou inexistente)')
            self.a = int(onde[0])
        else:
            chave = ' '.join(partida.lower().translate(TIRA_ACENTO).split())
            achados = [k for k, t in enumerate(self.textos)
                       if chave in ' '.join(t.lower().translate(TIRA_ACENTO).split())]
            if len(achados) != 1:
                for k in achados[:12]:
                    print(f'  {self.ids[k]}: {self.textos[k][:100]!r}')
                sys.exit(f'"{partida}" casou com {len(achados)} relatos — precisa ser um só '
                         '(use um trecho mais longo ou o índice)')
            self.a = achados[0]
        self.T = self.P[self.a].astype(np.float64)
        n = self.T / np.linalg.norm(self.T)
        self.n = n
        # "para cima" da câmera: o eixo vertical do planeta, como na página
        self.cima = np.array([0.0, 1.0, 0.0]) if abs(n[1]) < 0.9 else np.array([0.0, 0.0, 1.0])
        print(f'partida: {self.ids[self.a]} · {self.textos[self.a][:90]!r}', flush=True)

    # ——— a régua: o raio que abarca 10ⁿ sonhos em volta do de partida ———
    def _escalas(self):
        ks = [2] + [10 ** j for j in range(1, 6)]
        d, _ = self.arvore.query(self.T, k=ks)
        self.U = math.log10(self.nv)                        # o arquivo inteiro
        # u=0 é metade da distância ao vizinho mais próximo: só ele na tela
        us = [0.0, 1, 2, 3, 4, 5, self.U]
        rs = [0.5 * d[0]] + list(d[1:]) + [1.45]
        self._us, self._lr = np.array(us), np.log10(rs)
        print('raios: ' + ' · '.join(f'10^{u:g}: {r:.4f}' for u, r in zip(us, rs)), flush=True)

    def raio(self, u):
        if u <= 0:
            inc = self._lr[1] - self._lr[0]
            return 10 ** (self._lr[0] + u * inc)
        if u >= self.U:
            return 10 ** (self._lr[-1] + (u - self.U))
        return 10 ** float(np.interp(u, self._us, self._lr))

    def olhar(self, u):
        """Para onde a câmera aponta: o sonho de partida e, do 10⁵ em diante,
        o centro do planeta — para que ele termine inteiro no quadro."""
        s = float(suave(5.0, self.U, u))
        return self.T * (1 - s)

    # ——— o tempo: u(t), o giro ———
    def _tempo(self):
        ts, us = [], []
        for t, u in MARCAS:
            if isinstance(u, str):
                u = self.U + (float(u[2:]) if '+' in u else 0.0)
            ts.append(t)
            us.append(u)
        self.duracao = ts[-1]
        self._u = PchipInterpolator(ts, us)
        # giro: devagar na viagem (paralaxe, para o 3D se ler), mais rápido no
        # planeta inteiro (o giro automático da página)
        passo = 1 / (self.qps * 4)
        tt = np.arange(0, self.duracao + 1, passo)
        grau = 1.4 + 3.2 * (suave(58, 64, tt) * (1 - suave(73, 80, tt)))
        self._tt, self._fase = tt, np.cumsum(np.radians(grau)) * passo

    def u(self, t):
        return float(self._u(min(max(t, 0), self.duracao)))

    def fase(self, t):
        return float(np.interp(t, self._tt, self._fase))

    def camera(self, t):
        u = self.u(t)
        r = self.raio(u)
        L = self.olhar(u)
        f = self.fase(t)
        c, s = math.cos(f), math.sin(f)
        n = self.n
        d = np.array([c * n[0] + s * n[2], n[1], -s * n[0] + c * n[2]])
        D = 1.1 * r / math.tan(FOV / 2)
        C = L + d * D
        frente = -d
        direita = np.cross(frente, self.cima)
        direita /= np.linalg.norm(direita)
        cima = np.cross(direita, frente)
        return dict(u=u, r=r, L=L, C=C, D=D, frente=frente, direita=direita, cima=cima, t=t)

    def projetar(self, cam, X):
        """Pontos 3D (n×3) → coordenadas de tela e profundidade. Em float32
        quando são os 444 mil (sobra precisão: o erro fica em centésimos de pixel)."""
        tipo = np.float32 if len(X) > 1000 else np.float64
        Y = np.asarray(X, tipo) - cam['C'].astype(tipo)
        base = np.stack([cam['direita'], cam['cima'], cam['frente']], axis=1).astype(tipo)
        xyz = Y @ base
        z = xyz[:, 2]
        z = np.where(np.abs(z) < 1e-12, 1e-12, z)
        # 'desvio' empurra o centro da imagem para o lado (o sonho usa, no fim)
        sx = self.W / 2 + cam.get('desvio', 0.0) + self.F * xyz[:, 0] / z
        sy = self.H / 2 - self.F * xyz[:, 1] / z
        return sx, sy, z

    # ——— o que se escreve em cada escala ———
    def emergentes(self, sel, n=4, minimo=0.03):
        """As palavras que esta vizinhança tem e o resto do arquivo não.
        Mesmo espírito do nomear() da página, com o texto inteiro."""
        c = Counter()
        for j in sel:
            c.update(self.docs[j])
        k = len(sel)
        notas = []
        for w, m in c.items():
            if m < max(3, minimo * k):
                continue
            pin, pg = m / k, self.df[w] / self.nv
            if pin > 2 * pg:
                notas.append((pin * math.log(pin / pg), w))
        notas.sort(reverse=True)
        saida = []
        chaves = lambda f: set(f.translate(TIRA_ACENTO).split())
        for _, w in notas[:40]:
            if any(w in chaves(o) or any(w in (p + 's', p + 'es') or p in (w + 's', w + 'es')
                                         for p in chaves(o)) for o in saida):
                continue                          # lua e luas: fica a mais forte
            frase = self.expressao(w, sel)
            # "mundo" e depois "fim do mundo": a expressão toma o lugar da palavra
            dentro = [k for k, o in enumerate(saida) if chaves(o) & chaves(frase)]
            if dentro:
                if all(chaves(saida[k]) <= chaves(frase) for k in dentro):
                    saida[dentro[0]] = frase
                    saida = [o for k, o in enumerate(saida) if k not in dentro[1:]]
                continue
            saida.append(frase)
            if len(saida) == n:
                break
        return saida

    def expressao(self, w, sel):
        """A palavra como as pessoas escreveram — com acento, e inteira quando
        ela quase sempre vem numa expressão (fim do mundo, sonho de consumo,
        bons sonhos): 'consumo' sozinho não diz nada."""
        palavra, frases, n = Counter(), Counter(), 0
        com_w = [j for j in sel if w in self.docs[j]]
        for j in com_w[::max(1, len(com_w) // 3000)]:
            toks = re.findall(r'[a-zà-ÿ]+', self.textos[j].lower())
            norm = [t.translate(TIRA_ACENTO) for t in toks]
            for k, t in enumerate(norm):
                if t != w:
                    continue
                n += 1
                palavra[toks[k]] += 1
                # duas palavras de conteúdo juntas ("bons sonhos"), ou três com
                # uma de ligação no meio ("fim do mundo", "sonho de consumo")
                for a, b in ((k - 1, k + 1), (k, k + 2), (k - 2, k + 1), (k, k + 3)):
                    if a < 0 or b > len(toks) or norm[a] in BORDA or norm[b - 1] in BORDA:
                        continue
                    if b - a == 3 and norm[a + 1] not in LIGA:
                        continue
                    frases[' '.join(toks[a:b])] += 1
        if not n:
            return w
        boas = [(len(f.split()), m, f) for f, m in frases.items() if m >= max(3, 0.5 * n)]
        return max(boas)[2] if boas else palavra.most_common(1)[0][0]

    def composicao(self, sel):
        n = np.bincount(self.classe[sel], minlength=3) / max(1, len(sel))
        return [(CLASSES[k], CORES_CLASSE[k], n[k]) for k in range(3)]

    def _rotulos(self):
        self._contar_palavras()
        t0 = time.time()
        # 10¹: os vizinhos legíveis, com um trecho de cada
        _, viz = self.arvore.query(self.T, k=10)
        self.trechos = []
        for j in viz:
            t = ' '.join(self.textos[j].split())
            self.trechos.append((int(j), t))
        # nome de cada escala (1 a 4) e, do 10³ em diante, as regiões dentro dela
        self.nomes, self.regioes = {}, {}
        for j in range(1, 6):
            _, sel = self.arvore.query(self.T, k=10 ** j)
            sel = np.asarray(sel)
            if j <= 4:
                self.nomes[j] = self.emergentes(sel, n=3 if j == 1 else 4)
            if j >= 3:
                self.regioes[j] = self._agrupar(sel, {3: 4, 4: 6, 5: 9}[j], semente=j)
        todos = np.arange(self.nv)
        self.regioes['T'] = self._agrupar(todos, 18, semente=7)
        _, sel5 = self.arvore.query(self.T, k=10 ** 5)
        self.comp5, self.compT = self.composicao(np.asarray(sel5)), self.composicao(todos)
        print('nomes: ' + ' | '.join(f'10^{j}: ' + ' · '.join(v) for j, v in self.nomes.items()))
        for j, rr in self.regioes.items():
            print(f'regiões 10^{j}: ' + ' · '.join(w for _, w, _ in rr))
        print(f'rótulos · {time.time() - t0:.1f}s', flush=True)

    def _agrupar(self, sel, K, semente):
        pts = self.P[sel].astype(np.float64)
        centros, lab = kmeans2(pts, K, minit='++', seed=semente)
        saida, usadas = [], set()
        for c in np.argsort(-np.bincount(lab, minlength=K)):
            mem = sel[lab == c]
            if len(mem) < 0.03 * len(sel):
                continue
            nomes = [w for w in self.emergentes(mem, n=3, minimo=0.04) if w not in usadas]
            if not nomes:
                continue
            usadas.add(nomes[0])
            # âncora: o relato mais perto do centro do grupo (o centro pode cair no vazio)
            k = mem[np.argmin(((self.P[mem] - centros[c]) ** 2).sum(1))]
            saida.append((self.P[k].astype(np.float64), nomes[0], len(mem)))
        return saida

    # ——— fundo: as estrelas fixas da página ———
    def _fundo(self):
        g = np.random.default_rng(2015)
        self.estrelas = np.zeros((3, self.H, self.W), np.float32)
        n = int(260 * self.S ** 0.5)
        xs, ys = g.random(n) * self.W, g.random(n) * self.H
        al = 0.05 + g.random(n) * 0.16
        cor = np.array([190, 196, 220], np.float32) / 255
        self._espalhar(self.estrelas, xs, ys, al[:, None] * cor[None, :] * 1.6)

    # ——— desenho dos pontos ———
    def _espalhar(self, buf, sx, sy, E):
        """Soma a luz E (n×3) nos 4 pixels em volta de cada ponto (bilinear):
        sem isso os pontos pulam de pixel em pixel e a imagem cintila."""
        _, h, w = buf.shape
        M = 4                                   # moldura: o que cai fora é descartado
        x, y = sx - 0.5, sy - 0.5
        x0, y0 = np.floor(x), np.floor(y)
        fx, fy = (x - x0).astype(np.float32), (y - y0).astype(np.float32)
        xi = np.clip(x0.astype(np.int64) + M, 0, w + 2 * M - 2)
        yi = np.clip(y0.astype(np.int64) + M, 0, h + 2 * M - 2)
        L = w + 2 * M
        i00 = yi * L + xi
        idx = np.concatenate([i00, i00 + 1, i00 + L, i00 + L + 1])
        gx, gy = 1 - fx, 1 - fy
        pesos = [gx * gy, fx * gy, gx * fy, fx * fy]
        n = (h + 2 * M) * L
        for c in range(3):
            e = E[:, c].astype(np.float32)
            soma = np.bincount(idx, weights=np.concatenate([p * e for p in pesos]), minlength=n)
            buf[c] += soma.reshape(h + 2 * M, L)[M:M + h, M:M + w]

    def _carimbar(self, buf, sx, sy, sig, pico, cor):
        """Poucos pontos grandes: um a um, com a gaussiana no lugar exato."""
        _, h, w = buf.shape
        for x, y, s, p, c in zip(sx, sy, sig, pico, cor):
            R = int(math.ceil(3 * s))
            ix, iy = int(math.floor(x)), int(math.floor(y))
            x0, x1, y0, y1 = max(0, ix - R), min(w, ix + R + 1), max(0, iy - R), min(h, iy + R + 1)
            if x0 >= x1 or y0 >= y1:
                continue
            gx = np.exp(-((np.arange(x0, x1) + 0.5 - x) ** 2) / (2 * s * s))
            gy = np.exp(-((np.arange(y0, y1) + 0.5 - y) ** 2) / (2 * s * s))
            k = (gy[:, None] * gx[None, :]) * p
            for ch in range(3):
                buf[ch, y0:y1, x0:x1] += k * c[ch]

    def _ampliar(self, img, q):
        """Volta um buffer reduzido (3×h×w) ao tamanho da tela, bilinear."""
        saida = np.empty((3, self.H, self.W), np.float32)
        for c in range(3):
            saida[c] = np.asarray(Image.fromarray(img[c]).resize((self.W, self.H), Image.BILINEAR))
        return saida

    def estilo(self, u):
        """Tamanho (px, em 1080p) e brilho de cada ponto conforme a escala:
        poucos → grandes e nítidos; muitos → finos, para a densidade aparecer
        (o escalaPonto da página, contínuo)."""
        uu = min(u, self.U)
        sig = 7.0 * 10 ** (-0.21 * uu)
        alfa = 10 ** (-0.135 * uu)
        if u > self.U:
            # o planeta se afasta: o brilho por área fica o mesmo até ele virar
            # um ponto, e daí a luz total para de cair — sobra uma estrela
            e_ponto = 2 * math.pi * (max(sig, 0.45) * self.S) ** 2
            piso = 1.4 * 2 * math.pi * (7.0 * self.S) ** 2 / (self.nv * e_ponto)
            alfa = max(alfa * 10 ** (-2 * (u - self.U)), piso)
        return sig * self.S, alfa

    def pontos(self, cam):
        u, r, L, D = cam['u'], cam['r'], cam['L'], cam['D']
        sx, sy, z = self.projetar(cam, self.P)
        dist = np.linalg.norm(self.P - L.astype(np.float32), axis=1) / r
        # a vizinhança acesa: quem está dentro do raio. A borda é curta para que
        # o que se vê bata com a contagem — e cada sonho novo acende ao entrar
        w = np.exp(-(dist / 1.2) ** 5)
        # o resto do arquivo atrás do que se olha, como uma atmosfera cinza
        nevoa = 0.035 * janela(u, 0.4, 1.6, 3.2, 4.8)
        if nevoa > 0:
            w = np.maximum(w, nevoa * suave(1.0 * D, 2.2 * D, z))
        w *= suave(0.06 * D, 0.45 * D, z)     # o que passa rente à câmera some
        sig0, alfa = self.estilo(u)
        # σ em pixels desta resolução; a luz total de cada ponto é pico·2πσ², de
        # modo que a imagem é a mesma em 540p ou em 4K, só mais ou menos nítida
        sig = np.clip(sig0 * D / np.maximum(z, 1e-9), 0.45 * self.S, 42 * self.S)
        pico = alfa * w
        m = 3 * sig
        ok = ((z > 0.03 * D) & (w > 1e-3) & (sx > -m) & (sx < self.W + m)
              & (sy > -m) & (sy < self.H + m))
        sx, sy, sig, pico, dist = sx[ok], sy[ok], sig[ok], pico[ok], dist[ok]
        # longe do que se olha, a cor desbota até o cinza (o cinzento() da página)
        g = np.clip((dist / 2.4) ** 3, 0, 0.8)[:, None].astype(np.float32)
        cor = self.cor[ok] * (1 - g) + CINZA[None, :] * g
        acc = np.zeros((3, self.H, self.W), np.float32)
        # por tamanho: os finos vão direto para o pixel; os poucos e grandes, um
        # a um, com a gaussiana exata; os muitos, somados por oitava de tamanho e
        # borrados juntos (as oitavas grandes em resolução menor)
        fino = sig < 0.62
        if fino.any():
            E = pico[fino] * 2 * math.pi * sig[fino] ** 2
            self._espalhar(acc, sx[fino], sy[fino], E[:, None] * cor[fino])
        resto = np.nonzero(~fino)[0]
        if len(resto):
            t = np.log2(sig[resto] / 0.62)
            perto = np.round(t).astype(int)
            um_a_um = np.bincount(perto)[perto] < 350
            if um_a_um.any():
                q_ = resto[um_a_um]
                self._carimbar(acc, sx[q_], sy[q_], sig[q_], pico[q_], cor[q_])
            resto, t = resto[~um_a_um], t[~um_a_um]
            # cada ponto reparte a luz entre as duas oitavas vizinhas: assim
            # cresce sem saltar de um tamanho para o outro
            k0 = np.floor(t).astype(int)
            f = (t - k0).astype(np.float32)
            for k in np.unique(np.concatenate([k0, k0 + 1])):
                a, b = k0 == k, k0 + 1 == k
                parte = np.concatenate([np.nonzero(a)[0], np.nonzero(b)[0]])
                peso = np.concatenate([1 - f[a], f[b]])
                parte, peso = parte[peso > 1e-4], peso[peso > 1e-4]
                if not len(parte):
                    continue
                qual = resto[parte]
                q = 1 if k <= 1 else 2 ** (k - 1)
                h, w_ = -(-self.H // q), -(-self.W // q)
                ex, ey = w_ / self.W, h / self.H            # tela → grade reduzida
                sb = 0.62 * 2.0 ** k * ex
                pequeno = np.zeros((3, h, w_), np.float32)
                E = (peso * pico[qual] * 2 * math.pi * sb ** 2)[:, None] * cor[qual]
                self._espalhar(pequeno, sx[qual] * ex, sy[qual] * ey, E)
                pequeno = ndimage.gaussian_filter(pequeno, (0, sb, sb), truncate=3.0)
                acc += pequeno if q == 1 else self._ampliar(pequeno, q)
        return acc

    def luz(self, acc, cam):
        u = cam['u']
        # brilho difuso: a luz dos aglomerados vaza um pouco, como na tela
        h4, w4 = self.H // 4, self.W // 4
        red = acc.reshape(3, h4, 4, w4, 4).mean(axis=(2, 4))
        b1 = ndimage.gaussian_filter(red, (0, 2.2 * self.S, 2.2 * self.S))
        b2 = ndimage.gaussian_filter(red, (0, 9 * self.S, 9 * self.S))
        acc += self._ampliar(0.45 * b1 + 0.3 * b2, 4)
        acc += self.estrelas
        # fundo + (1 − fundo)·(1 − e^(−ganho·luz)), feito no lugar
        np.multiply(acc, -GANHO, out=acc)
        np.exp(acc, out=acc)
        # o fundo: o vazio e, quando o planeta é visto de fora, o halo em volta
        # dele, por baixo da luz (a página o pinta antes dos pontos)
        fator = (1 - VAZIO)[:, None, None]
        k = float(suave(4.9, self.U, u))
        if k > 0:
            cx, cy, zc = self.projetar(cam, np.zeros((1, 3)))
            dc = float(np.linalg.norm(cam['C']))
            if zc[0] > 0 and dc > 1.01:
                R = self.F * math.tan(math.asin(1 / dc))
                yy, xx = np.ogrid[:self.H, :self.W]
                rho = np.sqrt((xx - cx[0]) ** 2 + (yy - cy[0]) ** 2) / max(R, 1e-6)
                a = (0.30 * k * np.clip((1.3 - rho) / 0.75, 0, 1)).astype(np.float32)
                halo = np.array([24, 30, 48], np.float32) / 255
                fator = fator - a[None] * (halo - VAZIO)[:, None, None]
        img = acc
        img *= -fator
        img += 1                          # 1 − (1 − fundo)·e^(−ganho·luz)
        img *= 255
        img += 0.5
        np.clip(img, 0, 255, out=img)
        return np.ascontiguousarray(img.astype(np.uint8).transpose(1, 2, 0))

    # ——— texto ———
    def fonte(self, nome, px):
        return ImageFont.truetype(self.fontes[nome], max(6, int(round(px * self.S))))

    def sprite(self, texto, nome, px, cor, espaco=0.0, sombra=True, largura=None):
        """Texto com a sombra da página (text-shadow escuro em volta), em RGBA.
        Guardado: o mesmo texto aparece em muitos quadros."""
        chave = (texto, nome, px, cor, espaco, sombra, largura)
        if chave in self._cache_sprites:
            return self._cache_sprites[chave]
        f = self.fonte(nome, px)
        linhas = self.quebrar(texto, f, largura * self.S) if largura else [texto]
        alt = int(f.size * 1.45)
        larg = max(self.medir(l, f, espaco) for l in linhas) if linhas else 1
        m = int(18 * self.S)
        w, h = int(larg + 2 * m), int(alt * len(linhas) + 2 * m)
        mascara = Image.new('L', (w, h), 0)
        d = ImageDraw.Draw(mascara)
        for i, l in enumerate(linhas):
            self.escrever(d, (m, m + i * alt), l, f, espaco, 255)
        rgba = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        if sombra:
            s1 = mascara.filter(ImageFilter.GaussianBlur(9 * self.S))
            s2 = mascara.filter(ImageFilter.GaussianBlur(2.5 * self.S))
            a = np.maximum(np.asarray(s1, np.float32) * 1.6, np.asarray(s2, np.float32) * 1.4)
            rgba.putalpha(Image.fromarray(np.clip(a * 0.9, 0, 255).astype(np.uint8)))
        corpo = Image.new('RGBA', (w, h), cor + (255,))
        corpo.putalpha(mascara)
        rgba = Image.alpha_composite(rgba, corpo)
        self._cache_sprites[chave] = (rgba, m)
        return rgba, m

    @staticmethod
    def medir(texto, f, espaco):
        return f.getlength(texto) + espaco * f.size * max(0, len(texto) - 1)

    @staticmethod
    def escrever(d, xy, texto, f, espaco, cor):
        if not espaco:
            d.text(xy, texto, font=f, fill=cor)
            return
        x, y = xy
        for ch in texto:
            d.text((x, y), ch, font=f, fill=cor)
            x += f.getlength(ch) + espaco * f.size

    @staticmethod
    def quebrar(texto, f, largura):
        linhas, atual = [], ''
        for p in texto.split():
            tent = (atual + ' ' + p).strip()
            if f.getlength(tent) <= largura or not atual:
                atual = tent
            else:
                linhas.append(atual)
                atual = p
        if atual:
            linhas.append(atual)
        return linhas

    def colar(self, base, sp, x, y, alfa, ancora='esq'):
        """Cola o sprite com a transparência do quadro. (x, y) é o canto de
        cima do texto (sem a margem da sombra); ancora: esq, meio, dir."""
        if alfa <= 0.004:
            return None
        img, m = sp
        if ancora == 'meio':
            x -= (img.width - 2 * m) / 2
        elif ancora == 'dir':
            x -= img.width - 2 * m
        x, y = int(round(x - m)), int(round(y - m))
        # só o pedaço que cai dentro da tela (o resto quebrava o recorte)
        x0, y0 = max(0, x), max(0, y)
        dentro = (x0 - x, y0 - y, min(img.width, base.width - x), min(img.height, base.height - y))
        if dentro[2] <= dentro[0] or dentro[3] <= dentro[1]:
            return None
        if alfa < 0.999:
            a = np.asarray(img.getchannel('A'), np.float32) * alfa
            img = img.copy()
            img.putalpha(Image.fromarray(a.astype(np.uint8)))
        base.alpha_composite(img, (x0, y0), dentro)
        return (x + m, y + m, x + img.width - m, y + img.height - m)

    def trecho(self, texto, n=46):
        if len(texto) <= n:
            return texto
        corte = texto[:n].rsplit(' ', 1)[0]
        return corte.rstrip(' ,.;:—-') + '…'

    def textos_do_quadro(self, img, cam):
        t, u = cam['t'], cam['u']
        S = self.S
        base = Image.fromarray(img).convert('RGBA')
        # formas numa camada à parte: o ImageDraw sobre RGBA troca o pixel em
        # vez de misturar, e a transparência se perdia
        formas = Image.new('RGBA', base.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(formas)
        self._formas = d

        # o anel no sonho de partida (o marcarSel da página), da primeira à última escala
        ax, ay, az = self.projetar(cam, self.T[None, :])
        ax, ay = float(ax[0]), float(ay[0])
        a_anel = janela(t, 1.5, 3.5, 74, 78) * (1 - 0.45 * float(suave(3.5, 5.5, u)))
        if a_anel > 0 and az[0] > 0:
            rr = 11 * S
            d.ellipse((ax - rr, ay - rr, ax + rr, ay + rr), outline=CLARO + (int(230 * a_anel),),
                      width=max(1, int(round(1.4 * S))))

        # 10⁰: o relato inteiro, ao lado do ponto
        a1 = janela(t, 2.2, 4.2, 99, 100) * (1 - float(suave(0.2, 0.5, u)))
        if a1 > 0:
            i = self.a
            cls = CLASSES[self.classe[i]]
            topo = f'{self.ano[i]}/{self.mes[i]:02d} · {self.meta["comunidades"][self.com[i]]} · {cls}'
            corpo = self.sprite(self.textos[self.a], 'spectral-300i', 40, (223, 226, 236),
                                largura=620)
            alto = corpo[0].height - 2 * corpo[1]
            x0, y0 = ax + 70 * S, ay - alto / 2 + 16 * S
            cab = self.sprite(topo.upper(), 'plex-300', 15, FRACO, espaco=0.14)
            self.colar(base, cab, x0 + 20 * S, y0 - 44 * S, a1)
            cc = CORES_CLASSE[self.classe[i]]
            d.ellipse((x0, y0 - 38 * S, x0 + 9 * S, y0 - 29 * S), fill=cc + (int(255 * a1),))
            self.colar(base, corpo, x0, y0, a1)

        # 10¹: um trecho de cada vizinho, junto do ponto dele
        a10 = float(suave(0.55, 0.85, u) * (1 - suave(1.3, 1.6, u)))
        if a10 > 0:
            xs, ys, zs = self.projetar(cam, self.P[[j for j, _ in self.trechos]])
            caixas = []
            ordem = np.argsort(zs)                 # os da frente primeiro
            for k in ordem:
                j, texto = self.trechos[k]
                if zs[k] <= 0:
                    continue
                x, y = float(xs[k]), float(ys[k])
                sp = self.sprite(self.trecho(texto), 'spectral-300i', 25, CLARO, largura=330)
                w, h = sp[0].width - 2 * sp[1], sp[0].height - 2 * sp[1]
                lado = 1 if x >= self.W / 2 - 40 * S else -1
                bx = x + 16 * S if lado > 0 else x - 16 * S - w
                by = y - 17 * S
                caixa = (bx, by, bx + w, by + h)
                if any(not (caixa[2] < c[0] or caixa[0] > c[2] or caixa[3] < c[1] or caixa[1] > c[3])
                       for c in caixas):
                    continue
                if caixa[0] < 20 * S or caixa[2] > self.W - 20 * S or caixa[1] < 20 * S \
                        or caixa[3] > self.H - 150 * S:
                    continue
                caixas.append(caixa)
                self.colar(base, sp, bx, by, a10 * (0.95 if j != self.a else 1.0))

        # regiões: os nomes que emergem, presos ao lugar delas no espaço
        for j, janela_u in ((3, (2.55, 2.85, 3.45, 3.75)), (4, (3.55, 3.85, 4.45, 4.75)),
                            (5, (4.55, 4.85, 5.3, 5.5)), ('T', (5.45, self.U, self.U + 0.05, self.U + 0.3))):
            a = janela(u, *janela_u)
            if a <= 0:
                continue
            reg = self.regioes[j]
            pos = np.array([p for p, _, _ in reg])
            xs, ys, zs = self.projetar(cam, pos)
            prof_foco = cam['D']
            caixas = [(ax - 20 * S, ay - 20 * S, ax + 20 * S, ay + 20 * S)]
            for k, (p, nome, tam) in enumerate(reg):
                if zs[k] <= 0:
                    continue
                # atrás do plano em foco, o nome recua (e some do outro lado)
                fundo = float(np.clip((zs[k] - prof_foco) / (0.9 * cam['r']), -1, 1))
                ak = a * (1.0 if fundo < 0 else max(0.0, 1 - 1.4 * fundo))
                if ak <= 0.02:
                    continue
                sp = self.sprite(nome, 'spectral-300i', 30, CLARO)
                w, h = sp[0].width - 2 * sp[1], sp[0].height - 2 * sp[1]
                bx, by = float(xs[k]) - w / 2, float(ys[k]) - h / 2
                caixa = (bx - 8 * S, by, bx + w + 8 * S, by + h)
                if any(not (caixa[2] < c[0] or caixa[0] > c[2] or caixa[3] < c[1] or caixa[1] > c[3])
                       for c in caixas):
                    continue
                if caixa[0] < 30 * S or caixa[2] > self.W - 30 * S or caixa[1] < 30 * S \
                        or caixa[3] > self.H - 190 * S:
                    continue
                caixas.append(caixa)
                self.colar(base, sp, bx, by, ak)

        # a régua, embaixo à esquerda: 10ⁿ, quantos sonhos, e o nome da escala
        a_regua = janela(t, 3.0, 5.0, 73.0, 76.5)
        if a_regua > 0:
            x0, y0 = 64 * S, self.H - 64 * S
            for j in range(0, 6):
                aj = a_regua * float(np.clip(1 - (abs(u - j) - 0.3) / 0.15, 0, 1))
                if u > 5.2:
                    aj = 0
                if aj <= 0:
                    continue
                self._potencia(base, x0, y0, j, aj)
                if j in self.nomes:
                    nome = self.sprite(' · '.join(self.nomes[j]), 'spectral-300i', 30, TEXTO)
                    self.colar(base, nome, x0, y0 - 150 * S, aj)
                if j == 5:
                    self._composicao(base, x0, y0 - 146 * S, self.comp5, aj)
            # a contagem corre sempre: é quantos cabem no raio agora
            n = self.contar(cam)
            rot = f'{milhar(n)} sonho' + ('' if n == 1 else 's')
            sp = self.sprite(rot.upper(), 'plex-300', 17, FRACO, espaco=0.14)
            self.colar(base, sp, x0 + 2 * S, y0 - 18 * S, a_regua)
            # no planeta inteiro, a composição: a outra metade não estava dormindo
            aT = a_regua * float(suave(self.U - 0.25, self.U, u))
            if aT > 0:
                self._composicao(base, x0, y0 - 146 * S, self.compT, aT)
                todos = self.sprite('o arquivo inteiro', 'spectral-200i', 60, (230, 232, 240))
                self.colar(base, todos, x0, y0 - 104 * S, aT)

        # legendas no centro, embaixo
        for (a, b, texto) in LEGENDAS:
            al = janela(t, a, a + 1.2, b - 1.2, b)
            if al > 0:
                texto = texto.replace('{todos}', milhar(self.nv))
                sp = self.sprite(texto, 'spectral-300i', 36, (223, 226, 236))
                self.colar(base, sp, self.W / 2, self.H - 150 * S, al, ancora='meio')

        # abertura e cartão final
        ab = janela(t, 0.6, 2.2, 7.5, 9.5)
        if ab > 0:
            tit = self.sprite('Escuta Planetária', 'spectral-200i', 44, (230, 232, 240))
            self.colar(base, tit, 64 * S, 52 * S, ab)
            sub = self.sprite('POTÊNCIAS DE DEZ, EM SONHO', 'plex-300', 14, FRACO, espaco=0.18)
            self.colar(base, sub, 66 * S, 112 * S, ab)
        a0, a1_ = CARTAO_FINAL
        af = janela(t, a0, a0 + 1.6, a1_ + 5, a1_ + 6)
        if af > 0:
            tit = self.sprite('Escuta Planetária', 'spectral-200i', 76, (230, 232, 240))
            self.colar(base, tit, self.W / 2, self.H / 2 + 70 * S, af, ancora='meio')
            sub = self.sprite(CREDITO.upper(), 'plex-300', 14, FRACO, espaco=0.14)
            self.colar(base, sub, self.W / 2, self.H / 2 + 186 * S, af, ancora='meio')
            end = self.sprite(ENDERECO, 'plex-400', 18, (107, 168, 255), espaco=0.04)
            self.colar(base, end, self.W / 2, self.H / 2 + 226 * S, af, ancora='meio')
        base.alpha_composite(formas)
        return np.asarray(base.convert('RGB'))

    def _potencia(self, base, x, y, j, a):
        dez = self.sprite('10', 'spectral-200i', 88, (230, 232, 240))
        exp_ = self.sprite(str(j), 'spectral-200i', 46, (230, 232, 240))
        larg = dez[0].width - 2 * dez[1]
        self.colar(base, dez, x, y - 118 * self.S, a)
        self.colar(base, exp_, x + larg + 3 * self.S, y - 121 * self.S, a)

    def _composicao(self, base, x, y, comp, a):
        d = self._formas
        S = self.S
        for nome, cor, frac in comp:
            rot = f'{round(100 * frac)}% {nome}'
            sp = self.sprite(rot.upper(), 'plex-300', 15, TEXTO, espaco=0.12)
            d.ellipse((x, y + 7 * S, x + 9 * S, y + 16 * S), fill=cor + (int(255 * a),))
            caixa = self.colar(base, sp, x + 18 * S, y, a)
            if caixa:
                x = caixa[2] + 26 * S

    def contar(self, cam):
        """Quantos relatos cabem no raio desta escala, em volta de onde se olha."""
        u = cam['u']
        if u >= self.U:
            return self.nv
        n = int(self.arvore.query_ball_point(cam['L'], cam['r'], return_length=True))
        return max(1, min(n, self.nv))

    # ——— um quadro ———
    def quadro(self, t):
        cam = self.camera(t)
        acc = self.pontos(cam)
        img = self.luz(acc, cam)
        # entrada e saída em preto
        f = janela(t, 0.0, 1.2, self.duracao - 1.2, self.duracao)
        img = self.textos_do_quadro(img, cam)
        if f < 1:
            img = (img.astype(np.float32) * f + (VAZIO * 255) * (1 - f)).astype(np.uint8)
        return img

    # ——— a escuta: cada sonho que entra no raio soa uma vez ———
    def som(self, caminho, taxa=48000):
        """Trilha tirada da própria viagem. Os primeiros sonhos a entrar no raio
        tocam um sino cada, na hora exata e do lado da tela em que aparecem;
        quando entram às centenas por segundo, viram um chuvisco de sinos
        curtos (a densidade acompanha a contagem); por baixo, um bordão que
        cresce com a escala. Tudo em ré maior pentatônica — consonante em
        qualquer combinação, para que mil sinos juntos não virem ruído. O
        literal soa uma oitava acima do figurado; o incerto, uma quinta."""
        rng = np.random.default_rng(2015)
        n = int((self.duracao + 1) * taxa)
        pista = np.zeros((2, n), np.float32)
        escala = PENTATONICA
        registro = {0: 2.0, 1: 1.0, 2: 1.5}             # literal, figurado, incerto

        def sino(t0, freq, amp, pan, tau=1.2):
            tocar(pista, t0, freq, amp, pan, tau, taxa)

        def pan_de(t, k):
            sx, _, z = self.projetar(self.camera(t), self.P[k][None, :])
            return float(np.clip(2 * sx[0] / self.W - 1, -0.85, 0.85)) if z[0] > 0 else 0.0

        # quando cada um entra: o raio só cresce, então é ver quando ele passa
        # pela distância de cada sonho (a mesma conta do contador na tela)
        tt = np.arange(0, self.duracao, 1 / 200)
        uu = np.array([self.u(t) for t in tt])
        rr = np.array([self.raio(u) for u in uu])
        d_todos = np.sort(np.linalg.norm(self.P - self.T.astype(np.float32), axis=1))
        K = 400
        d, viz = self.arvore.query(self.T, k=K)
        sino(1.3, escala[0] * 2, 0.24, 0.0, tau=2.2)      # o primeiro sonho
        for k, (dk, j) in enumerate(zip(d[1:], viz[1:]), start=1):
            i = np.searchsorted(rr, dk)
            if i >= len(tt) or uu[i] > 5:
                continue
            t0 = tt[i]
            f = escala[j % 5] * registro[int(self.classe[j])]
            # os primeiros, nítidos; conforme se amontoam, mais baixos e mais curtos
            sino(t0, f, 0.16 / (1 + k / 8) ** 0.7, pan_de(t0, j), tau=max(0.25, 2.0 / (1 + k / 25)))
        # depois deles, o chuvisco: grãos por segundo = sonhos novos por segundo,
        # com teto; o registro de cada grão sorteado entre os que entraram agora
        passo = 1 / 30
        for t0 in np.arange(0, tt[-1], passo):
            u0, u1 = self.u(t0), self.u(t0 + passo)
            if u0 >= self.U + 0.1:
                break
            if u1 <= 5:
                a_ = np.searchsorted(d_todos, self.raio(u0))
                b_ = np.searchsorted(d_todos, self.raio(u1))
            else:
                a_ = int(self.arvore.query_ball_point(self.olhar(u0), self.raio(u0), return_length=True))
                b_ = int(self.arvore.query_ball_point(self.olhar(u1), self.raio(u1), return_length=True))
            novos = max(0, b_ - max(a_, K))
            if not novos:
                continue
            taxa_s = novos / passo
            g = min(taxa_s, 26.0)
            amp = 0.05 / math.sqrt(max(1.0, g / 6))
            for _ in range(rng.poisson(g * passo)):
                if u1 <= 5:
                    # um dos que acabaram de entrar, sorteado pela distância
                    dk = rng.uniform(self.raio(u0), self.raio(u1))
                    cls = int(self.classe[self._perto_de(dk)])
                else:
                    cls = int(rng.choice(3, p=[c[2] for c in self.compT]))
                f = rng.choice(escala) * registro[cls] * rng.choice([0.5, 1.0, 1.0, 2.0])
                sino(t0 + rng.uniform(0, passo), f, amp * rng.uniform(0.6, 1.0),
                     rng.uniform(-0.9, 0.9), tau=rng.uniform(0.25, 0.6))
        # o bordão: ré e lá graves, entrando com a escala e saindo com o planeta
        t = np.arange(n) / taxa
        u_t = np.interp(t, tt, uu)
        nivel = (0.045 * (0.3 + 0.7 * suave(0.3, 5.6, u_t)) * suave(0.5, 4.0, t)
                 * (1 + 0.35 * suave(60, 64, t)) * (1 - suave(78, 90, t))).astype(np.float32)
        lfo = 1 + 0.25 * np.sin(2 * np.pi * 0.07 * t)
        for f, a, dt in ((73.42, 1.0, 0.21), (110.0, 0.5, 0.17), (146.83, 0.35, 0.13), (220.0, 0.12, 0.3)):
            pista[0] += (nivel * a * lfo * np.sin(2 * np.pi * (f - dt) * t)).astype(np.float32)
            pista[1] += (nivel * a * lfo * np.sin(2 * np.pi * (f + dt) * t + 0.7)).astype(np.float32)
        # e quando o arquivo inteiro vira um ponto, um sino só, como no começo
        t_ponto = float(tt[np.searchsorted(uu, self.U + 2.2)]) if uu[-1] > self.U + 2.2 else 83.0
        sino(t_ponto, escala[0], 0.2, 0.0, tau=3.0)
        sino(t_ponto, escala[0] * 2, 0.1, 0.0, tau=2.4)
        return gravar(pista, caminho, self.duracao, rng, taxa)

    def _perto_de(self, dist):
        """Um relato à distância `dist` do de partida (para o registro dos grãos)."""
        if not hasattr(self, '_dist_ord'):
            dd = np.linalg.norm(self.P - self.T.astype(np.float32), axis=1)
            self._dist_ord = np.argsort(dd)
            self._dist_val = dd[self._dist_ord]
        k = min(len(self._dist_ord) - 1, int(np.searchsorted(self._dist_val, dist)))
        return self._dist_ord[k]


V = None


def _um(i):
    return V.quadro(i / V.qps).tobytes()


def opcoes(descricao):
    """As opções de linha de comando que a viagem e o sonho têm em comum."""
    ap = argparse.ArgumentParser(description=descricao)
    ap.add_argument('--altura', type=int, default=1080)
    ap.add_argument('--qps', type=int, default=30, help='quadros por segundo')
    ap.add_argument('--previa', action='store_true', help='540p, rápido')
    ap.add_argument('--quadro', type=float, nargs='*', help='só estes segundos, em PNG')
    ap.add_argument('--saida', default=None)
    ap.add_argument('--processos', type=int, default=None)
    ap.add_argument('--de', type=float, default=0.0, help='começar neste segundo')
    ap.add_argument('--ate', type=float, default=None, help='parar neste segundo')
    ap.add_argument('--mudo', action='store_true', help='sem a trilha (a escuta)')
    return ap


def main():
    ap = opcoes(__doc__.split('\n\n')[0])
    ap.add_argument('--sonho', default=PARTIDA, help='trecho do texto (ou índice) do sonho de partida')
    args = ap.parse_args()
    altura = 540 if args.previa else args.altura
    renderizar(Viagem(altura=altura, qps=args.qps, partida=args.sonho), args, 'viagem')


def renderizar(peca, args, nome):
    """Os quadros pedidos (--quadro), em PNG, ou o vídeo inteiro com a trilha."""
    global V
    V = peca                     # os processos do Pool herdam daqui (fork)
    if args.quadro:
        for s in args.quadro:
            t0 = time.time()
            img = V.quadro(s)
            arq = Path(args.saida or AQUI / f'{nome}_{s:05.1f}.png')
            if len(args.quadro) > 1 or arq.suffix != '.png':
                arq = (arq if arq.suffix != '.png' else arq.parent) / f'{nome}_{s:05.1f}.png'
            arq.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(img).save(arq)
            print(f'{arq} · {time.time() - t0:.2f}s')
        return

    import imageio_ffmpeg
    saida = Path(args.saida or AQUI / (f'{nome}_previa.mp4' if args.previa else f'{nome}.mp4'))
    i0 = int(args.de * V.qps)
    i1 = int((args.ate if args.ate is not None else V.duracao) * V.qps)
    som = None
    if not args.mudo:
        t0 = time.time()
        som = V.som(saida.with_suffix('.wav'))
        print(f'trilha: {som} · {time.time() - t0:.0f}s', flush=True)
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-loglevel', 'error',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{V.W}x{V.H}', '-r', str(V.qps), '-i', '-']
    if som:
        cmd += ['-ss', f'{args.de}', '-i', str(som)]
    cmd += ['-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-tune', 'film', '-pix_fmt', 'yuv420p']
    if som:
        cmd += ['-c:a', 'aac', '-b:a', '192k', '-shortest']
    cmd += ['-movflags', '+faststart', str(saida)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    with Pool(args.processos) as pool:
        for k, q in enumerate(pool.imap(_um, range(i0, i1), chunksize=2)):
            ff.stdin.write(q)
            if k % (V.qps * 5) == 0:
                feito = (k + 1) / (i1 - i0)
                print(f'  {k / V.qps:5.1f}s de vídeo · {100 * feito:3.0f}% · '
                      f'{time.time() - t0:5.0f}s', flush=True)
    ff.stdin.close()
    ff.wait()
    print(f'{saida} · {(i1 - i0) / V.qps:.0f}s de vídeo em {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
