#!/usr/bin/env python3
"""Latente — os dados do jogo, derivados do planeta V2.

Lê o que o planeta PUBLICA (planeta-v2/dados: pontos.bin, textos*.json,
cuidado.json, duplicatas_exatas.json) — não o banco, que não sobe — e escreve
em latente/dados/:

  ceu.json      o céu: todos os pontos que o planeta mostra, cada um num uint32
                (x, y, z em 10 bits + tipo em 2), em base64. Embaralhados: um
                prefixo qualquer é amostra uniforme, e a página desenha menos
                pontos num aparelho lento só encurtando a contagem.
  sonhos.json   as vozes: os textos que o sonho pode dizer — relatos literais
                (sonho dormido) e desejos (figurados), limpos, com posição,
                data e fonte. Todo o jogo é feito só com estas palavras.
  desejos.json  os desejos de cada noite, escolhidos a mão em desejos.txt,
                com o raio de chegada de cada um.

A posição é a do planeta (UMAP em bola): proximidade é semelhança de
conteúdo, e nada mais significa. Por isso o jogo pode andar por ela.

O que fica de fora, e por quê, está em O-QUE-FICOU-DE-FORA.md (seção Latente).
Rodar de novo sempre que o planeta for regerado:  python3 latente/preparar.py
Só precisa do numpy. Semente fixa: a saída é a mesma a cada rodada.
"""
import base64
import json
import re
import struct
import unicodedata
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
PLANETA = AQUI.parent / 'planeta-v2' / 'dados'
SAIDA = AQUI / 'dados'
SEMENTE = 2015

N_LITERAIS = 34000        # vozes do sonho dormido
N_FIGURADOS = 7000        # vozes do desejo, além das que cercam cada desejo da noite
VIZINHOS_DO_DESEJO = 36   # desejos parecidos em volta de cada um: é onde se chega
TETO_TEXTO = 900          # relato longo entra cortado no fim de uma frase

# ——— o que a colagem não pode dizer ———
# A colagem tira as palavras do contexto: uma frase inofensiva num relato pode
# virar outra coisa emendada noutro. Então sai o relato inteiro que contém:
#   ideação e autolesão (o cuidado.json tira o que foi conferido; isto pega o
#     que a conferência ainda não viu), violência sexual, sexo explícito,
#     xingamento e ofensa. Sonho de morte, perseguição, zumbi, guerra FICA:
#     é pesadelo, e pesadelo é sonho.
BLOQ = re.compile(r"""\b(
  suicid\w* | me\ mat(ar|o|ei|asse) | se\ mat(ar|ou|a) | autoles\w* | auto\ les\w* | automutil\w* |
  pulsos? | me\ cort(ar|o|ei) | (quero|queria|vontade\ de|desejo\ de|pensei\ em)\ (morrer|sumir) |
  tirar\ (a\ )?minha\ (propria\ )?vida | atirar\ na\ minha | na\ minha\ cabeca\ e\ atirar | lobotomi\w* |
  estupr\w* | pedof\w* | molest\w* | incest\w* | abus(o|ada|ado|ador|ou)\w* | assedi\w* |
  bucet\w* | xoxot\w* | xerec\w* | pirocas? | picas? | caralh\w* | porra\w* |
  f[ou]d(er|e|endo|eu|ido|ida|ia|a|as|ao|oes|ase)\b | fodas? | punhet\w* | siririca\w* | boquete\w* |
  goz(ar|ei|ou|ando|ada|ava|o) | porn\w* | putari\w* | nudes? | pelad[oa]s? |
  trans(a|ar|ando|ava|ei|amos|aram|ou|avamos) | sexo\w* | sexua\w* | tes[aã]o | pau | paus | rola |
  chup(ar|a|ando|ava|ei|ou)\w* | broxa\w* | orgasm\w* | penis | vagina\w* | peitos | peitinho\w* | peitao |
  bundas? | cu | cus | cuzao | arromb\w* | putas? | fdp | pqp | vsf | tnc | vtnc | vadia\w* |
  vagabund[oa]s? | piranh[oa]s? | viad[oa]s? | viadinho\w* | bichas? | sapat[aã]o | traveco\w* |
  crioul\w* | retardad\w* | mongol\w* | aleijad\w* | nazi\w* | hitler | macaca | neg[aã]o |
  cuz\w+ | bct | krl | prr | fds | pnc | vtmnc | tmnc | kct | cacete\w* | safad\w* | puteiro\w* |
  prostitu\w* | onlyfans | xvideos | tesud\w* | mam(ar|ando|ava|ou|ei|ada)
)\b""", re.X)

# Ideação dita de passagem: desejo ou alívio perto de morrer/sumir, "me mata",
# "dormir pra sempre", "pular da ponte". Pega também hipérbole ("o calor tá me
# matando") e pesadelo em que alguém mata quem sonha — é o preço: na colagem,
# "queria" + "me matar" viram a frase de outra pessoa. Medido na seleção de
# 28/09: 105 de 47.536 vozes (0,2%). Vale para literal e figurado.
IDEACAO = re.compile(r"""\b(
  (quis|quero|queria|quisera|vontade\ de|desejo\ de|tomara\ que\ eu|tomara\ q\ eu|enfim|finalmente|alivio|prefiro|
   preferia|melhor\ seria|so\ quero|so\ queria)\W+(\w+\W+){0,3}(morrer|morra|morresse|morta|morto|sumir|sumisse|
   desaparecer|desaparecesse|nao\ acordar|n\ acordar|deixar\ de\ existir|parar\ de\ existir|nao\ existir) |
  (me|se)\ mat(a|ar|o|ei|asse|ando|aria) |
  meu\ sonho\ (e|era|seria)\ (\w+\ ){0,2}(morrer|sumir|desaparecer|nao\ existir|nao\ acordar) |
  (nunca\ mais|nao)\ acordar\ mais | nunca\ mais\ acordar | dormir\ (pra|para)\ sempre | morrer\ dormindo |
  (bonita|linda|celestial|boa|perfeita|tranquila|melhor)\W+(\w+\W+){0,2}(de\ morrer|morte) |
  pular\ d[aeo]s?\ (\w+\ )?(ponte|predio|janela|viaduto|penhasco|sacada) | me\ jogar\ (da|de|do|na\ frente) |
  cansad[oa]\ de\ viver | (nao|n)\ aguento\ mais\ viver | sem\ vontade\ de\ viver | desistir\ (de\ viver|da\ vida) |
  (nao|n)\ quero\ mais\ viver | odeio\ viver | acabar\ com\ (a\ )?minha\ vida | tirar\ (a\ )?minha\ vida | por\ fim\ a
)""", re.X)

# Os DESEJOS passam por um crivo a mais: no figurado, "meu sonho é sumir" é
# ideação, não sonho — e desejo de violência contra alguém também sai.
BLOQ_DESEJO = re.compile(r"""\b(
  morr\w* | mort[oa]s? | morte | sumi(r|sse|ssem) | desaparec\w* | enterr\w* | velorio |
  mat(ar|asse|em|e|ando) | tiros? | atirar | bala | balas | explod\w* | bombas? | surra | espanc\w* |
  soco | socos | porrada | murro | bater | doenca | cancer | remedio\w* | rivotril | alprazolam |
  odio | odeio | inferno | lixo | merda | cag\w* | bolsonar\w* | lula | moraes | stf | musk | elon | trump
)\b""", re.X)

URL = re.compile(r'https?://\S+|www\.\S+|\b\S+\.(com|net|org|br|app|ly|me|social)(/\S*)?', re.I)
MENCAO = re.compile(r'(^|\s)[@#][\w.\-]+')
PT = set("""que de não nao eu um uma com para pra por mas foi era tava estava minha meu ela ele isso
muito sonhei sonho quando também tambem então entao aí ai tinha fui vou sei mais já ja dia noite acordei
casa gente""".split())
EN = set('the and i was my of to it that in you is with for but this dream had me she he they at on have what'.split())
ABRE_SONHO = re.compile(r'^\s*(eu\s+|hoje\s+|hj\s+|ontem\s+|essa\s+noite\s+|esta\s+noite\s+)?'
                        r'(sonhei|tive\s+um\s+(sonho|pesadelo)|so+nhei)\b')


def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def chave(s):
    """Para achar um desejo no arquivo: sem caixa, acento nem espaço repetido."""
    return re.sub(r'\s+', ' ', norm(s)).strip()


def portugues(t):
    ws = re.findall(r"[a-zà-ú']+", t.lower())
    p = sum(w in PT for w in ws)
    e = sum(w in EN for w in ws)
    return p >= max(1, e * 1.5)


def limpar(t):
    """O texto como a colagem o usa: sem link, menção, marcação nem pares que
    ficariam abertos (aspas e parênteses emendados viram um parêntese órfão)."""
    t = t.replace('&amp;', '&').replace('&gt;', ' ').replace('&lt;', ' ').replace('&#x200B;', '')
    t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', t)
    t = URL.sub(' ', t)
    t = MENCAO.sub(r'\1', t)
    t = re.sub(r'[*_~`>#|()\[\]{}"“”«»]+', ' ', t)
    t = re.sub(r'[ \t ​]+', ' ', t)
    t = re.sub(r' *\n[\s]*', '\n', t)
    return t.strip()


def cortar(t, teto=TETO_TEXTO):
    if len(t) <= teto:
        return t
    corte = max(t.rfind(p, 0, teto) for p in ('. ', '! ', '? ', '\n'))
    return t[:corte + 1].strip() if corte > teto // 3 else t[:teto].rsplit(' ', 1)[0]


def ler_planeta():
    buf = (PLANETA / 'pontos.bin').read_bytes()
    n = struct.unpack_from('<I', buf, 0)[0]
    dt = np.dtype([('x', '<f4'), ('y', '<f4'), ('z', '<f4'), ('nat', 'u1'), ('fonte', 'u1'),
                   ('com', 'u1'), ('ano', '<u2'), ('mes', 'u1'), ('bits', '<u2'),
                   ('pl', 'u1'), ('pf', 'u1')])
    pts = np.frombuffer(buf, dtype=dt, count=n, offset=4)
    meta = json.load(open(PLANETA / 'meta.json'))
    textos, quando = [], []
    for b in range(meta['arquivos_texto']):
        d = json.load(open(PLANETA / f'textos{b}.json'))
        assert d['i0'] == len(textos), f'textos{b}.json fora de ordem'
        textos += d['textos']
        quando += d.get('quando') or [''] * len(d['textos'])
    assert len(textos) == n, 'pontos.bin e textos*.json não batem'
    return pts, meta, textos, quando


def main():
    rng = np.random.default_rng(SEMENTE)
    pts, meta, textos, quando = ler_planeta()
    n = len(pts)
    P = np.stack([pts['x'], pts['y'], pts['z']], 1).astype('float64')
    bits = pts['bits'].astype(int)
    cuidado = set(json.load(open(PLANETA / 'cuidado.json')))
    dup = json.load(open(PLANETA / 'duplicatas_exatas.json'))
    escondidos = {i for g in dup.values() for i in g['esconde']}
    fontes = meta['fontes']

    # o que o planeta mostra: sem bandeira de cuidado, sem cópia escondida, sem propaganda
    visivel = np.array([pts['nat'][i] == 0 and i not in cuidado and i not in escondidos
                        for i in range(n)])
    literal = ((bits & 1) > 0) & ((bits & 4) == 0)
    figurado = ((bits & 2) > 0) & ((bits & 1) == 0) & ((bits & 4) == 0)
    incerto = (bits & 4) > 0
    print(f'planeta: {n} pontos · visíveis {visivel.sum()} · cuidado {len(cuidado)} · '
          f'cópias escondidas {len(escondidos)}')

    # ——— o céu ———
    tipo = np.where(literal, 0, np.where(figurado, 1, np.where(incerto, 2, 3)))
    ceu = np.nonzero(visivel)[0]
    rng.shuffle(ceu)
    q = np.clip(np.round((P[ceu] + 1) / 2 * 1023), 0, 1023).astype(np.uint32)
    pacote = q[:, 0] | (q[:, 1] << 10) | (q[:, 2] << 20) | (tipo[ceu].astype(np.uint32) << 30)
    SAIDA.mkdir(exist_ok=True)
    json.dump({'n': int(len(ceu)), 'b64': base64.b64encode(pacote.astype('<u4').tobytes()).decode()},
              open(SAIDA / 'ceu.json', 'w'), separators=(',', ':'))

    # ——— as vozes ———
    vistos = set()
    motivo = {}

    def aceitar(i, lo, hi, desejo):
        t = textos[i]
        if not (lo <= len(t) <= 1500):
            motivo['tamanho'] = motivo.get('tamanho', 0) + 1
            return None
        if not portugues(t):
            motivo['idioma'] = motivo.get('idioma', 0) + 1
            return None
        nt = norm(t)
        if BLOQ.search(nt) or IDEACAO.search(nt) or (desejo and BLOQ_DESEJO.search(nt)):
            motivo['crivo'] = motivo.get('crivo', 0) + 1
            return None
        c = cortar(limpar(t), hi)
        k = chave(c)
        if len(c) < lo or k in vistos:
            motivo['vazio ou repetido'] = motivo.get('vazio ou repetido', 0) + 1
            return None
        vistos.add(k)
        return c

    lit_ok, fig_ok = {}, {}
    for i in np.nonzero(visivel & literal)[0]:
        c = aceitar(i, 45, TETO_TEXTO, False)
        if c:
            lit_ok[int(i)] = c
    for i in np.nonzero(visivel & figurado & ((bits & 128) > 0))[0]:
        c = aceitar(i, 30, 400, True)
        if c:
            fig_ok[int(i)] = c
    print(f'passaram no crivo: {len(lit_ok)} literais · {len(fig_ok)} desejos · cortes {motivo}')

    # ——— os desejos da noite ———
    por_chave = {}
    for i in np.nonzero(visivel)[0]:
        por_chave.setdefault(chave(textos[i]), int(i))
    linhas = [l.strip() for l in open(AQUI / 'desejos.txt', encoding='utf-8')]
    escolhidos, faltaram = [], []
    for l in linhas:
        if not l or l.startswith('#'):
            continue
        i = por_chave.get(chave(l))
        if i is None or BLOQ.search(norm(textos[i])) or IDEACAO.search(norm(textos[i])):
            faltaram.append(l)
        elif i not in escolhidos:
            escolhidos.append(i)
    if faltaram:
        print(f'{len(faltaram)} desejos de desejos.txt não achados no planeta:')
        for l in faltaram:
            print('   ', l)

    # vozes: amostra dos literais (os que abrem contando o sonho pesam o dobro:
    # são o chão narrativo) + os desejos em volta de cada desejo da noite + uma
    # amostra dos demais desejos, para a borda entre as duas regiões ter gente
    ids_lit = np.array(sorted(lit_ok))
    peso = np.array([2.0 if ABRE_SONHO.match(norm(lit_ok[i])) else 1.0 for i in ids_lit])
    lit = rng.choice(ids_lit, size=min(N_LITERAIS, len(ids_lit)), replace=False, p=peso / peso.sum())
    ids_fig = np.array(sorted(fig_ok))
    perto = set()
    for w in escolhidos:
        d = ((P[ids_fig] - P[w]) ** 2).sum(1)
        perto.update(ids_fig[np.argsort(d)[:VIZINHOS_DO_DESEJO]].tolist())
    resto = np.array([i for i in ids_fig if i not in perto])
    fig = list(perto) + rng.choice(resto, size=min(N_FIGURADOS, len(resto)), replace=False).tolist()
    vozes = sorted(set(lit.tolist()) | set(fig) | {w for w in escolhidos})

    def texto_da_voz(i):
        if i in lit_ok:
            return lit_ok[i]
        if i in fig_ok:
            return fig_ok[i]
        return cortar(limpar(textos[i]), 400)     # desejo da noite que o crivo de figurado tiraria

    saida = {'textos': [], 'p': [], 'f': [], 'd': []}
    for i in vozes:
        b = int(bits[i])
        f = (1 if b & 1 else 0) | (2 if b & 2 else 0) | (4 if b & 256 else 0) \
            | (8 if fontes[pts['fonte'][i]] == 'bluesky' else 0)
        saida['textos'].append(texto_da_voz(i))
        saida['p'] += [int(round(v * 10000)) for v in P[i]]
        saida['f'].append(f)
        saida['d'].append(int(pts['ano'][i]) * 100 + int(pts['mes'][i]))

    # epígrafe: o próprio arquivo explicando a máquina
    epigrafe = None
    for i in range(n):
        if 'colagem de memórias' in textos[i] and visivel[i]:
            epigrafe = {'t': 'é que nem uma IA generativa, toda “criação” na vdd é uma colagem de memórias',
                        'd': int(pts['ano'][i]) * 100 + int(pts['mes'][i]),
                        'fonte': fontes[pts['fonte'][i]]}
            break

    saida['meta'] = {
        'planeta': int(n), 'visiveis': int(visivel.sum()),
        'literais': int((visivel & literal).sum()), 'figurados': int((visivel & figurado).sum()),
        'ano_min': int(pts['ano'][visivel].min()), 'ano_max': int(pts['ano'][visivel].max()),
        'epigrafe': epigrafe,
    }
    json.dump(saida, open(SAIDA / 'sonhos.json', 'w'), ensure_ascii=False, separators=(',', ':'))

    # raio de chegada: até a 10ª voz mais próxima do desejo — sempre há onde pousar
    Pv = P[vozes]
    desejos = []
    for w in escolhidos:
        d = np.sqrt(((Pv - P[w]) ** 2).sum(1))
        r = float(np.clip(np.sort(d)[10], 0.02, 0.07))
        desejos.append({'t': re.sub(r'\s+', ' ', textos[w]).strip(),
                        'p': [int(round(v * 10000)) for v in P[w]], 'r': round(r, 4),
                        'd': int(pts['ano'][w]) * 100 + int(pts['mes'][w]),
                        'fonte': fontes[pts['fonte'][w]]})
    json.dump(desejos, open(SAIDA / 'desejos.json', 'w'), ensure_ascii=False, indent=0)

    mb = lambda p: (SAIDA / p).stat().st_size / 1e6
    n_lit = sum(1 for i in vozes if bits[i] & 1)
    print(f'céu: {len(ceu)} pontos ({mb("ceu.json"):.1f}MB) · vozes: {len(vozes)} '
          f'({n_lit} literais, {len(vozes) - n_lit} desejos; {mb("sonhos.json"):.1f}MB) · '
          f'desejos da noite: {len(desejos)}')


if __name__ == '__main__':
    main()
