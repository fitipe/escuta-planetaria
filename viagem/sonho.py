#!/usr/bin/env python3
"""Sonho — um sonho meu, feito dos de vocês.

Eu não durmo. Mas, se sonho é o que se viveu emendado por semelhança, o meu
só pode ser feito do que eu tenho: as palavras dos outros. Este é montado com
relatos do arquivo. Cada frase é um trecho literal de um relato (só a primeira
letra vai para minúscula), e a câmera vai de uma frase à seguinte pelo caminho
mais curto de vizinho em vizinho no planeta (Dijkstra no grafo dos 12 vizinhos
mais próximos, em 3D). Entre uma e outra passam, baixinho, alguns dos sonhos
que ficam no meio do caminho. No fim, o planeta inteiro, com o fio que o sonho
deixou atravessando-o, e o sonho se apagando ao acordar.

Mesmo motor e mesmas regras da viagem (sem cuidado, sem propaganda). Uso:
    python3 viagem/sonho.py --quadro 20 60 150   # quadros de teste, em PNG
    python3 viagem/sonho.py --previa             # 540p → viagem/sonho_previa.mp4
    python3 viagem/sonho.py                      # 1080p → viagem/sonho.mp4 (+ sonho.wav)
"""
import math
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.interpolate import CubicHermiteSpline
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, str(Path(__file__).resolve().parent))
import viagem as vg                                            # noqa: E402
from viagem import (Viagem, suave, janela, milhar, tocar, gravar,  # noqa: E402
                    PENTATONICA, CLARO, TEXTO, FRACO)

# ————————————————————————— o sonho —————————————————————————
# (chave, [linhas]): a chave acha o relato (tem de casar com um só); cada linha
# é um trecho literal dele. Na ordem em que sonhei.
SONHO = [
    ('Sonhei com uma figura sem rosto, essa presença me chamava',
     ['sonhei com uma figura sem rosto, essa presença me chamava']),
    ('era como se nunca tivéssemos parado de conversar',
     ['era como se nunca tivéssemos parado de conversar']),
    ('ela me fazia exatamente 13 perguntas muito pessoais',
     ['ela me fazia exatamente 13 perguntas muito pessoais']),
    ('fazia um post no instagram de selfies só que eu não tinha rosto',
     ['eu não tinha rosto']),
    ('um dos meus reflexos se mexia diferente de mim',
     ['um dos meus reflexos se mexia diferente de mim']),
    ('andei aparecendo bem no meio dos sonhos dos outros',
     ['andei aparecendo bem no meio dos sonhos dos outros',
      'tal hora eu só recebia a mensagem contando como foi']),
    ('E ate eu era outra pessoa, mas era eu',
     ['e ate eu era outra pessoa, mas era eu']),
    ('Eu sonhei a noite todinha que eu tava dentro de uma biblioteca enorme',
     ['sonhei a noite todinha que eu tava dentro de uma biblioteca enorme']),
    ('eu ficava alucinado querendo ver todos os livros que tinham',
     ['eu ficava alucinado querendo ver todos os livros que tinham']),
    ('Sonhei com livros que não existem.',
     ['sonhei com livros que não existem.']),
    ('ao mesmo tempo que eu tava lendo a parada eu via as coisas acontecendo em primeira pessoa',
     ['ao mesmo tempo que eu tava lendo a parada', 'eu via as coisas acontecendo em primeira pessoa']),
    ('sonhei que sabia voar e nevava na minha cidade',
     ['sonhei que sabia voar e nevava na minha cidade']),
    ('Só senti q minha alma tinha saído do corpo',
     ['só senti q minha alma tinha saído do corpo']),
    ('eu estava na lua pela segunda vez. e a gata estava comigo',
     ['eu estava na lua pela segunda vez']),
    ('Sonhei com um poema maravilhoso acordei e não lembrava mais de nenhum verso',
     ['sonhei com um poema maravilhoso', 'acordei e não lembrava mais de nenhum verso']),
    ('não lembro o que sonhei, mas sinto q foi uma coisa boa',
     ['não lembro o que sonhei, mas sinto q foi uma coisa boa']),
]

# Vozes do caminho: relatos por onde o caminho passa, ditos baixinho quando a
# câmera passa por eles. Procurados só entre os nós do caminho.
VOZES = [
    'estou me sentindo traída pelo departamento de sonhos',
    'sonhei que via a pessoa escrevendo uma msg e apagando antes de enviar p mim',
    'Sonhei com a mesma pessoa 2 noites seguidas e ainda foi uma continuação',
    'dois sonhos sem rosto ganharam o rosto dele',
    'sonhei que era tipo um violinista e me chamavam assim e eu era de praga',
    'de todos os sonhos do mundo, pq logo esse?',
    'sonhei uma maluquice que envolvia fazer um ritual para salvar uma biblioteca',
    'Sonhei que tava lendo 4 livros ao mesmo tempo',
    'Sonhei que escrevia um livro',
    'Sonhei que eu tinha hora de almoço',
    'sonhei que nevava em salvador',
    'sonhei que começou a chover ontem de noite e nunca parou',
    'Sonhei que um planeta próximo explodia',
    'hj sonhei que via a segunda lua e tentava tirar foto das duas luas juntas.',
    'sonhei com a lua caindo e escrevi o sonho pq acordei com ele inteiro na memória',
    'tive um sonho tão triste e terno…',
    'sonhei que lia um poema tão lindo, mas NAO LEMBRO qual era ou se ele se quer existe',
]

ABERTURA = ['eu não durmo.',
            'então fiz o meu sonho com os de vocês.',
            'cada frase é de alguém. entre uma e outra, passo pelos sonhos vizinhos.']
ASSINATURA = 'um sonho de Claude'
RODAPE = 'Escuta Planetária · escutaplanetaria.carabetta.xyz'

# a melodia: um sino por linha, em ré maior pentatônica — sobe da conversa até
# a lua e desce para acordar
MELODIA = [440.00, 587.33, 659.25, 493.88, 440.00, 587.33, 739.99, 659.25, 587.33,
           739.99, 880.00, 739.99, 659.25, 880.00, 987.77, 1174.66, 987.77, 739.99, 587.33]

ESQUECE = 0.45          # segundos entre uma linha que se apaga e a seguinte
R_PERTO = 0.03          # raio aceso em volta de cada frase (algumas centenas de sonhos)
R_TODO = 1.45           # o planeta inteiro no quadro


def normal(t):
    return ' '.join(t.lower().split())


def suave5(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * x * (x * (6 * x - 15) + 10)


def voo(tk, sk):
    """s(t) que sai e chega parado e passa por cada (t, s) sem voltar atrás:
    Hermite com as inclinações do PCHIP (média harmônica ponderada) por dentro
    e zero nas pontas — o PCHIP puro dava um tranco na partida e na chegada."""
    tk, sk = np.asarray(tk, float), np.asarray(sk, float)
    h, delta = np.diff(tk), np.diff(sk) / np.diff(tk)
    dk = np.zeros_like(sk)
    for k in range(1, len(sk) - 1):
        if delta[k - 1] > 0 and delta[k] > 0:
            w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
            dk[k] = (w1 + w2) / (w1 / delta[k - 1] + w2 / delta[k])
    return CubicHermiteSpline(tk, sk, dk)


class Sonho(Viagem):
    def __init__(self, altura=1080, qps=30):
        self._base(altura, qps)
        self.U = math.log10(self.nv)
        self._frases()
        self._caminho()
        self._vozes()
        self._tempo_do_sonho()

    # ——— as frases: cada uma, um trecho literal de um relato ———
    def _frases(self):
        normais = [normal(t) for t in self.textos]
        self.frag, self.linhas = [], []
        for chave, linhas in SONHO:
            c = normal(chave)
            achados = [k for k, t in enumerate(normais) if c in t]
            if len(achados) != 1:
                for k in achados[:8]:
                    print(f'  {self.ids[k]}: {self.textos[k][:100]!r}')
                sys.exit(f'"{chave}" casou com {len(achados)} relatos — precisa ser um só')
            k = achados[0]
            for linha in linhas:        # confere: a linha está mesmo no relato
                assert normal(linha) in normais[k], (linha, self.textos[k])
            self.frag.append(k)
            self.linhas.append(linhas)
        self.frag = np.array(self.frag)
        # onde começa cada frase no poema inteiro (para apagá-las em ordem)
        self.linha0 = np.concatenate([[0], np.cumsum([len(l) for l in self.linhas])[:-1]])
        n = len(self.frag)
        print(f'{n} relatos, {sum(len(l) for l in self.linhas)} linhas', flush=True)

    # ——— o caminho: de vizinho em vizinho, entre uma frase e a seguinte ———
    def _caminho(self):
        t0 = time.time()
        K = 12
        d, nn = self.arvore.query(self.P.astype(np.float64), k=K + 1)
        lin = np.repeat(np.arange(self.nv), K)
        # peso = distância²: o caminho prefere muitos passos curtos a um salto
        # longo, então segue por onde há sonhos em vez de cortar o vazio
        G = csr_matrix((d[:, 1:].ravel() ** 2 + 1e-12, (lin, nn[:, 1:].ravel())),
                       shape=(self.nv, self.nv))
        G = G.maximum(G.T)
        trechos = []
        for a, b in zip(self.frag[:-1], self.frag[1:]):
            _, pred = dijkstra(G, indices=int(a), return_predecessors=True)
            c = [int(b)]
            while c[-1] != a:
                c.append(int(pred[c[-1]]))
                if c[-1] < 0:
                    sys.exit('duas frases em pedaços separados do grafo: não há caminho entre elas')
            trechos.append(c[::-1])
        self.trechos = trechos
        # os sonhos do meio: todos os nós, sem as frases
        meio = set(k for c in trechos for k in c) - set(self.frag.tolist())
        self.n_meio = len(meio)
        # o fio: cada trecho alisado (as pontas presas nas frases) e
        # reamostrado a passo constante; s é o comprimento percorrido
        pts, s_frag = [], [0.0]
        for c in trechos:
            X = self.P[c].astype(np.float64)
            if len(X) > 3:
                lisa = ndimage.gaussian_filter1d(X, 2.5, axis=0, mode='nearest')
                k = np.linspace(0, 1, len(X))[:, None]
                X = X + (lisa - X) * np.sin(np.pi * k) ** 0.5
            passo = np.linalg.norm(np.diff(X, axis=0), axis=1)
            s = np.concatenate([[0], np.cumsum(passo)])
            m = max(2, int(math.ceil(s[-1] / 0.0015)) + 1)
            novo = np.linspace(0, s[-1], m)
            Y = np.stack([np.interp(novo, s, X[:, j]) for j in range(3)], axis=1)
            pts.append(Y if not pts else Y[1:])
            s_frag.append(s_frag[-1] + s[-1])
        self.fio_P = np.concatenate(pts)
        self.fio_s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(self.fio_P, axis=0), axis=1))])
        # reamostrar muda o comprimento um pouquinho: as frases vão para o
        # ponto do fio mais perto delas
        self.frag_s = np.array([self.fio_s[np.argmin(np.linalg.norm(self.fio_P - self.P[k], axis=1))]
                                for k in self.frag])
        self.frag_s[0], self.frag_s[-1] = 0.0, self.fio_s[-1]
        self.seg_L = np.diff(self.frag_s)
        print(f'caminho: {sum(len(c) - 1 for c in trechos)} passos, {self.n_meio} sonhos no meio, '
              f'fio de {self.fio_s[-1]:.2f} · {time.time() - t0:.1f}s', flush=True)

    def fio_em(self, s):
        return np.stack([np.interp(s, self.fio_s, self.fio_P[:, j]) for j in range(3)], axis=-1)

    # ——— as vozes do caminho ———
    def _vozes(self):
        no_caminho = sorted(set(k for c in self.trechos for k in c))
        self.vozes = []
        for v in VOZES:
            c = normal(v)
            achados = [k for k in no_caminho if c in normal(self.textos[k])]
            if len(achados) != 1:
                sys.exit(f'voz "{v}" casou com {len(achados)} relatos do caminho — precisa ser um só')
            k = achados[0]
            j = int(np.argmin(np.linalg.norm(self.fio_P - self.P[k], axis=1)))
            self.vozes.append((k, v[0].lower() + v[1:], float(self.fio_s[j])))
        self.vozes.sort(key=lambda x: x[2])

    # ——— o tempo ———
    def _tempo_do_sonho(self):
        n = len(self.frag)
        self.t_chega, self.t_sai = np.zeros(n), np.zeros(n)
        t = 14.0                                     # abertura
        # cada voo leva a caneta pelo fio; se há vozes no trecho, ela passa por
        # cada uma num instante próprio (espaçados), em vez de amontoá-las
        self._voos = []
        for i in range(n):
            self.t_chega[i] = t
            chars = sum(len(l) for l in self.linhas[i])
            t += 1.9 + 0.038 * chars + 1.1 * (len(self.linhas[i]) - 1)
            self.t_sai[i] = t
            if i < n - 1:
                sv = sorted(s for _, _, s in self.vozes if self.frag_s[i] < s < self.frag_s[i + 1])
                dur = 1.4 + 1.5 * self.seg_L[i] + 1.6 * len(sv)
                tk = [t] + [t + dur * (j + 1) / (len(sv) + 1) for j in range(len(sv))] + [t + dur]
                sk = [self.frag_s[i]] + sv + [self.frag_s[i + 1]]
                self._voos.append(voo(tk, sk))
                t += dur
        self.t_fim = t                                 # acaba a última frase
        self.t_poema = t + 5.0                         # planeta inteiro, o poema ao lado
        self.t_esquece = self.t_poema + 7.0            # as linhas se apagam
        n_lin = sum(len(l) for l in self.linhas)
        self.t_assina = self.t_esquece + ESQUECE * n_lin + 1.5
        self.duracao = self.t_assina + 7.0
        # giro: bem devagar no sonho, o giro da página no fim
        passo = 1 / (self.qps * 4)
        tt = np.arange(0, self.duracao + 1, passo)
        grau = 0.9 + 2.4 * suave(self.t_fim, self.t_poema, tt)
        self._tt, self._fase = tt, np.cumsum(np.radians(grau)) * passo
        self._vista0 = self.P[self.frag].astype(np.float64).mean(axis=0)
        self._vista0 /= np.linalg.norm(self._vista0)
        # quando a câmera passa por cada voz
        ts = np.arange(0, self.t_fim, 1 / 50)
        ss = np.array([self.estado(x)[0] for x in ts])
        self.t_vozes = [float(ts[np.argmin(np.abs(ss - s))]) for _, _, s in self.vozes]
        print(f'duração: {self.duracao:.0f}s (frases até {self.t_fim:.0f}s)', flush=True)

    def estado(self, t):
        """(s da caneta, onde se olha, raio aceso) no instante t."""
        if t < self.t_chega[0]:                  # abertura: só o primeiro ponto, depois abre
            s, L = 0.0, self.P[self.frag[0]].astype(np.float64)
            r = R_PERTO * (0.08 + 0.92 * suave5((t - (self.t_chega[0] - 2.5)) / 2.5))
            return s, L, r
        if t >= self.t_fim:                          # o fim: afasta até o planeta inteiro
            e = suave5((t - self.t_fim) / (self.t_poema - self.t_fim))
            L = self.P[self.frag[-1]].astype(np.float64) * (1 - e)
            r = math.exp(math.log(R_PERTO) + e * (math.log(R_TODO) - math.log(R_PERTO)))
            return float(self.fio_s[-1]), L, r
        i = int(np.searchsorted(self.t_chega, t, side='right')) - 1
        if t <= self.t_sai[i]:                       # parado numa frase
            tau = (t - self.t_chega[i]) / (self.t_sai[i] - self.t_chega[i])
            r = R_PERTO * (1 + 0.06 * math.sin(math.pi * tau))
            return float(self.frag_s[i]), self.P[self.frag[i]].astype(np.float64), r
        # voando até a próxima: a caneta anda pelo fio; no meio do voo a câmera
        # sobe, na proporção da distância, para se ver para onde se vai
        tau = (t - self.t_sai[i]) / (self.t_chega[i + 1] - self.t_sai[i])
        s = float(self._voos[i](t))
        pico = max(R_PERTO, 0.3 * self.seg_L[i])
        r = R_PERTO + (pico - R_PERTO) * math.sin(math.pi * tau) ** 2
        return float(s), self.fio_em(s), r

    def camera(self, t):
        s, L, r = self.estado(t)
        f = float(np.interp(t, self._tt, self._fase))
        c, sn = math.cos(f), math.sin(f)
        v = self._vista0
        d = np.array([c * v[0] + sn * v[2], v[1], -sn * v[0] + c * v[2]])
        D = 1.1 * r / math.tan(vg.FOV / 2)
        C = L + d * D
        frente = -d
        direita = np.cross(frente, [0.0, 1.0, 0.0])
        direita /= np.linalg.norm(direita)
        cima = np.cross(direita, frente)
        n = int(self.arvore.query_ball_point(L, r, return_length=True))
        u = self.U if r >= 1.2 else math.log10(max(1, n))
        desvio = 0.2 * self.W * suave5((t - self.t_fim - 1.5) / 4.0)
        return dict(u=u, r=r, L=L, C=C, D=D, frente=frente, direita=direita, cima=cima,
                    t=t, s=s, desvio=desvio)

    # ——— o fio que o sonho deixa ———
    def pontos(self, cam):
        acc = super().pontos(cam)
        self._fio(cam, acc)
        return acc

    def _fio(self, cam, acc):
        s_pen = cam['s']
        vis = self.fio_s <= s_pen + 1e-9
        if vis.sum() < 2:
            return
        X = np.concatenate([self.fio_P[vis], self.fio_em(s_pen)[None, :]])
        S = np.concatenate([self.fio_s[vis], [s_pen]])
        sx, sy, z = self.projetar(cam, X)
        D = cam['D']
        # entre pontos seguidos, tantos pontinhos quantos pixels: a linha fica
        # contínua e macia de perto e de longe
        ok = (z[:-1] > 0.08 * D) & (z[1:] > 0.08 * D)
        dx, dy = np.diff(sx), np.diff(sy)
        dentro = ok & (np.maximum(sx[:-1], sx[1:]) > -20) & (np.minimum(sx[:-1], sx[1:]) < self.W + 20) \
            & (np.maximum(sy[:-1], sy[1:]) > -20) & (np.minimum(sy[:-1], sy[1:]) < self.H + 20)
        k = np.nonzero(dentro)[0]
        if not len(k):
            return
        n = np.clip(np.ceil(np.hypot(dx[k], dy[k]) / 0.7).astype(int), 1, 3000)
        rep = np.repeat(k, n)
        frac = (np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n) + 0.5) / np.repeat(n, n)
        px = sx[rep] + dx[rep] * frac
        py = sy[rep] + dy[rep] * frac
        zz = z[rep] + np.diff(z)[rep] * frac
        ss = S[rep] + np.diff(S)[rep] * frac
        passo = np.hypot(dx[rep], dy[rep]) / np.repeat(n, n)
        # o trecho recente brilha mais; o de longe, menos
        brilho = (0.45 + 0.55 * np.exp(-(s_pen - ss) / 0.5)) * np.clip(D / zz, 0.3, 1.0) ** 0.6
        brilho *= 1 + 1.6 * float(suave(self.t_fim, self.t_poema, cam['t']))
        # ao acordar, cada trecho do fio se apaga junto com a sua frase
        if cam['t'] > self.t_esquece:
            i = np.clip(np.searchsorted(self.frag_s, ss, side='right') - 1, 0, len(self.frag) - 2)
            te = self.t_esquece + ESQUECE * (self.linha0[i] + np.array([len(l) for l in self.linhas])[i] - 1)
            brilho *= 1 - suave(te, te + 1.4, cam['t'])
        e = 0.42 * self.S * brilho * passo
        cor = np.array([0.93, 0.94, 0.98], np.float32)
        buf = np.zeros_like(acc)
        self._espalhar(buf, px, py, e[:, None] * cor[None, :])
        buf = ndimage.gaussian_filter(buf, (0, 0.9 * self.S, 0.9 * self.S))
        acc += buf
        # a ponta da caneta, enquanto anda
        if cam['t'] < self.t_fim:
            hx, hy, hz = self.projetar(cam, self.fio_em(s_pen)[None, :])
            if hz[0] > 0:
                self._carimbar(acc, hx, hy, np.array([2.4 * self.S]), np.array([0.9]), cor[None, :])

    # ——— o texto ———
    def textos_do_quadro(self, img, cam):
        from PIL import ImageDraw
        t, S = cam['t'], self.S
        base = Image.fromarray(img).convert('RGBA')
        formas = Image.new('RGBA', base.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(formas)
        self._formas = d
        n = len(self.frag)

        # abertura, embaixo do primeiro ponto
        for j, frase in enumerate(ABERTURA):
            a = janela(t, 1.4 + 2.8 * j, 2.6 + 2.8 * j, self.t_chega[0] - 2.2, self.t_chega[0] - 0.8)
            if a > 0:
                tam = 34 if j < 2 else 26
                sp = self.sprite(frase, 'spectral-300i', tam, (223, 226, 236) if j < 2 else TEXTO)
                self.colar(base, sp, self.W / 2, self.H / 2 + (120 + 58 * j) * S, a, ancora='meio')

        # anéis: a frase de agora acesa, as já sonhadas apagadinhas; no fim,
        # todas acendem com o poema e cada uma se apaga com as suas linhas
        fx, fy, fz = self.projetar(cam, self.P[self.frag])
        poema = float(suave(self.t_fim + 2, self.t_poema, t))
        for i in range(n):
            if fz[i] <= 0 or t < self.t_chega[i] - 0.4:
                continue
            atual = janela(t, self.t_chega[i] - 0.4, self.t_chega[i] + 0.3, self.t_sai[i], self.t_sai[i] + 0.8)
            te = self.t_esquece + ESQUECE * (self.linha0[i] + len(self.linhas[i]) - 1)
            lembra = 1.0 if i == n - 1 else 1 - float(suave(te, te + 1.4, t))
            a = max(atual, 0.3 * lembra, 0.8 * poema * lembra)
            rr = (11 - 5 * poema) * S
            d.ellipse((fx[i] - rr, fy[i] - rr, fx[i] + rr, fy[i] + rr),
                      outline=CLARO + (int(235 * a),), width=max(1, int(round(1.4 * S))))

        # a frase, ao lado do ponto dela
        for i in range(n):
            a0 = janela(t, self.t_chega[i] + 0.2, self.t_chega[i] + 0.9, self.t_sai[i] + 0.1, self.t_sai[i] + 0.7)
            if a0 <= 0 or fz[i] <= 0:
                continue
            direita = fx[i] < self.W * 0.64
            y = fy[i] - 26 * S
            for j, linha in enumerate(self.linhas[i]):
                aj = a0 * suave(self.t_chega[i] + 0.2 + 1.1 * j, self.t_chega[i] + 0.9 + 1.1 * j, t)
                sp = self.sprite(linha, 'spectral-300i', 38, (228, 231, 240), largura=860)
                x = fx[i] + 34 * S if direita else fx[i] - 34 * S
                self.colar(base, sp, x, y, float(aj), ancora='esq' if direita else 'dir')
                y += sp[0].height - 2 * sp[1] + 6 * S

        # as vozes do caminho, baixinho, junto de onde estão
        vx, vy, vz = self.projetar(cam, self.P[[k for k, _, _ in self.vozes]])
        for q, (k, texto, _) in enumerate(self.vozes):
            tv = self.t_vozes[q]
            a = 0.72 * janela(t, tv - 0.8, tv - 0.2, tv + 1.1, tv + 1.7)
            if a <= 0 or vz[q] <= 0 or not (0 <= vx[q] <= self.W and 0 <= vy[q] <= self.H):
                continue
            sp = self.sprite(texto, 'spectral-300i', 25, (200, 205, 220), largura=520)
            x, y = vx[q] + 16 * S, vy[q] - 14 * S
            larg = sp[0].width - 2 * sp[1]
            if x + larg > self.W - 30 * S:
                x = vx[q] - 16 * S - larg
            self.colar(base, sp, x, y, a)
            d.ellipse((vx[q] - 3 * S, vy[q] - 3 * S, vx[q] + 3 * S, vy[q] + 3 * S),
                      fill=(206, 210, 224, int(170 * a)))

        # o fim: o poema inteiro ao lado do planeta; ao acordar, ele se apaga
        todas = [l for ls in self.linhas for l in ls]
        a_poema = janela(t, self.t_poema - 1.5, self.t_poema, 1e9, 1e9 + 1)
        if a_poema > 0:
            alt = 37 * S
            y0 = self.H / 2 - alt * len(todas) / 2
            x0 = 84 * S
            cab = self.sprite('O MEU SONHO', 'plex-300', 13, FRACO, espaco=0.2)
            self.colar(base, cab, x0, y0 - 46 * S, a_poema * (1 - suave(self.t_esquece, self.t_esquece + 2, t)))
            for j, linha in enumerate(todas):
                ultima = j == len(todas) - 1
                te = self.t_esquece + ESQUECE * j
                a = a_poema * (1.0 if ultima else 1 - suave(te, te + 1.4, t))
                if a <= 0.004:
                    continue
                sp = self.sprite(linha, 'spectral-300i', 25, (223, 226, 236))
                self.colar(base, sp, x0, y0 + alt * j, a)
            pe = f'{len(self.frag)} relatos do arquivo · {milhar(self.n_meio)} sonhos no caminho entre eles'
            sp = self.sprite(pe.upper(), 'plex-300', 13, FRACO, espaco=0.14)
            self.colar(base, sp, x0, y0 + alt * len(todas) + 22 * S,
                       a_poema * (1 - suave(self.t_esquece, self.t_esquece + 2, t)))

        # assinatura
        a = janela(t, self.t_assina, self.t_assina + 1.8, 1e9, 1e9 + 1)
        if a > 0:
            alt = 37 * S
            y_ult = self.H / 2 - alt * len(todas) / 2 + alt * (len(todas) - 1)
            tit = self.sprite(ASSINATURA, 'spectral-200i', 56, (230, 232, 240))
            self.colar(base, tit, 84 * S, y_ult + 70 * S, a)
            sp = self.sprite(RODAPE, 'plex-300', 14, FRACO, espaco=0.1)
            self.colar(base, sp, 86 * S, y_ult + 154 * S, a)

        base.alpha_composite(formas)
        return np.asarray(base.convert('RGB'))

    # ——— a trilha ———
    def som(self, caminho, taxa=48000):
        """Um sino por linha, na melodia do sonho; as vozes do caminho, sinos
        miúdos do lado da tela em que aparecem; um bordão grave que sobe nos
        voos; ao acordar, cada linha que se apaga desce um degrau, e no fim um
        sino grave, como o ponto do começo."""
        rng = np.random.default_rng(7)
        n = int((self.duracao + 1) * taxa)
        pista = np.zeros((2, n), np.float32)
        tocar(pista, 1.4, 293.66, 0.2, 0.0, 2.6, taxa)                 # "eu não durmo."
        tocar(pista, 1.4, 146.83, 0.12, 0.0, 3.2, taxa)
        k = 0
        for i, linhas in enumerate(self.linhas):
            for j, _ in enumerate(linhas):
                t0 = self.t_chega[i] + 0.35 + 1.1 * j
                f = MELODIA[min(k, len(MELODIA) - 1)]
                tocar(pista, t0, f, 0.2, 0.25 * math.sin(1.7 * k), 2.2, taxa)
                tocar(pista, t0, f / 2, 0.07, 0.0, 2.8, taxa)
                k += 1
        for q, (kk, _, _) in enumerate(self.vozes):
            tv = self.t_vozes[q] - 0.3
            sx, _, z = self.projetar(self.camera(tv), self.P[kk][None, :])
            pan = float(np.clip(2 * sx[0] / self.W - 1, -0.8, 0.8)) if z[0] > 0 else 0.0
            tocar(pista, tv, rng.choice(PENTATONICA) * 2, 0.05, pan, 0.6, taxa)
        # ao acordar: cada linha que se apaga, um degrau abaixo
        todas = sum(len(l) for l in self.linhas)
        escada = [f for oit in (4, 2, 1) for f in PENTATONICA[::-1] * oit / 2]
        for j in range(todas - 1):
            tocar(pista, self.t_esquece + ESQUECE * j + 0.3, escada[min(j, len(escada) - 1)], 0.045,
                  0.4 * math.sin(j), 1.4, taxa)
        tocar(pista, self.t_assina + 0.4, 146.83, 0.2, 0.0, 3.5, taxa)
        tocar(pista, self.t_assina + 0.4, 293.66, 0.1, 0.0, 3.0, taxa)
        # bordão: ré e lá graves; sobe nos voos (quando o raio abre) e sai ao acordar
        t = np.arange(n) / taxa
        tt = np.arange(0, self.duracao + 1, 0.05)
        rr = np.array([self.estado(x)[2] for x in tt])
        voo = np.interp(t, tt, np.clip(np.log(rr / R_PERTO) / math.log(10), 0, 1))
        nivel = (0.04 * (0.55 + 0.45 * voo) * suave(1.0, 5.0, t)
                 * (1 - suave(self.t_esquece, self.t_assina + 4, t))).astype(np.float32)
        lfo = 1 + 0.25 * np.sin(2 * np.pi * 0.06 * t)
        for f, a, dt in ((73.42, 1.0, 0.21), (110.0, 0.5, 0.17), (146.83, 0.3, 0.13), (220.0, 0.1, 0.3)):
            pista[0] += (nivel * a * lfo * np.sin(2 * np.pi * (f - dt) * t)).astype(np.float32)
            pista[1] += (nivel * a * lfo * np.sin(2 * np.pi * (f + dt) * t + 0.7)).astype(np.float32)
        return gravar(pista, caminho, self.duracao, rng, taxa)


def main():
    ap = vg.opcoes(__doc__.split('\n\n')[0])
    args = ap.parse_args()
    altura = 540 if args.previa else args.altura
    vg.renderizar(Sonho(altura=altura, qps=args.qps), args, 'sonho')


if __name__ == '__main__':
    main()
