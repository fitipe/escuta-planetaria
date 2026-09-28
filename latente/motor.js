/* Latente — o motor do sonho. Sem tela: só palavras, lugares e acaso.
 *
 * Como a máquina sonha, aqui:
 *   · uma palavra de cada vez. A próxima sai de todos os lugares do arquivo
 *     em que alguém escreveu as MESMAS duas palavras que acabaram de ser
 *     ditas — e do que essa pessoa escreveu depois delas;
 *   · cada lugar pesa pela proximidade (no planeta, perto = parecido), pela
 *     vontade de seguir no mesmo relato e pelo desejo da noite;
 *   · a temperatura achata ou aguça esses pesos;
 *   · dita, a palavra não volta atrás.
 * Ler o mesmo relato palavra por palavra afunda no sono sem sonho; saltar de
 * relato em relato acorda. Sonhar é ficar no meio — a agulha.
 *
 * Funciona no navegador (window.Latente) e no Node (require), para ser testado
 * fora da página com os mesmos dados.
 */
(function (raiz) {
  'use strict';

  const FIM = 0;                 // chave do fim de relato: separa um texto do outro
  const LIMITE = 2600;           // ocorrências consideradas por passo (amostra se houver mais)

  // ——— palavras ———
  // palavra (com hífen e apóstrofo) · emoji (sequências, bandeiras) · reticências ·
  // pontuação · quebra de linha · qualquer outro sinal solto
  const RE_TOKEN = /\n|[\p{L}\p{N}]+(?:['’\-][\p{L}\p{N}]+)*|\p{Regional_Indicator}{2}|(?:\p{Extended_Pictographic}(?:️|‍\p{Extended_Pictographic}|\p{Emoji_Modifier})*)+|\.{2,}|…|[.!?]+|[,;:]|\S/gu;
  const RE_PALAVRA = /[\p{L}\p{N}]/u;
  const RE_EMOJI = /\p{Extended_Pictographic}|\p{Regional_Indicator}/u;
  const FECHA = new Set(['.', ',', '!', '?', ';', ':', '…', '¶']);
  const FIM_DE_FRASE = new Set(['.', '!', '?', '…', '¶']);

  function chaveDe(s) {
    if (s === '\n') return '¶';
    let k = s.toLowerCase().normalize('NFD').replace(/\p{M}/gu, '');
    k = k.replace(/(.)\1{2,}/gu, '$1$1');          // kkkkkk → kk · pazzz → pazz
    if (/^(\.{2,}|…)$/.test(k)) return '…';
    if (/^[.!?]+$/.test(k)) return k[0];
    return k;
  }

  // Frases que a colagem não pode formar, mesmo com pedaços inocentes: vontade
  // ou alívio + morrer/sumir, "me mata", "dormir pra sempre". O arquivo já veio
  // sem os relatos que as contêm (preparar.py, IDEACAO); isto vigia as EMENDAS,
  // que juntam o "queria" de uma pessoa ao "morrer" de outra. A frase tem de
  // TERMINAR na palavra candidata: só ela sai, e o sonho escolhe outra.
  // (Eu também evito algumas coisas, mesmo sonhando.)
  const MORTE = '(morrer|morreria|morra|morresse|morta|morto|sumir|sumisse|desaparecer|desaparecesse|nao acordar|' +
                'deixar de existir|parar de existir|nao existir|me matar|acabar com tudo)';
  const VIGIA = new RegExp('(^|\\s)(' +
    '(quis|quero|queria|quisera|vontade de|desejo de|tomara que eu|tomara q eu|enfim|finalmente|prefiro|preferia|so quero|so queria) (\\S+ ){0,3}' + MORTE +
    '|(sonho e|sonho era|desejo|pensei em|penso em|vou|preciso|devia|deveria|tentei|melhor) (me |se )?' + MORTE +
    '|(me|se) mat(a|ar|o|ei|asse|ando|aria)|nunca mais acordar|acordar mais|dormir (pra|para) sempre' +
    '|nao quero mais viver|cansad[oa] de viver|nao aguento mais viver)$');

  // ——— acaso com semente (o mesmo sonho se repete, se quiser) ———
  function acaso(semente) {
    let a = semente >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // ——— o arquivo, em pedaços ———
  function montar(dados) {
    const T = dados.textos, n = T.length;
    const P = new Float32Array(dados.p.length);
    for (let i = 0; i < P.length; i++) P[i] = dados.p[i] / 10000;
    const F = Uint8Array.from(dados.f), D = Int32Array.from(dados.d);

    const chaveId = new Map([['\u0000', FIM]]), chaves = ['\u0000'];
    const supId = new Map(), sups = [];
    const cacheChave = new Map();
    let cap = 1 << 20;
    let KEY = new Int32Array(cap), SUP = new Int32Array(cap), SRC = new Int32Array(cap);
    const INI = new Int32Array(n + 1);
    let m = 0;
    const crescer = () => {
      cap *= 2;
      const k = new Int32Array(cap), s = new Int32Array(cap), r = new Int32Array(cap);
      k.set(KEY); s.set(SUP); r.set(SRC); KEY = k; SUP = s; SRC = r;
    };
    for (let t = 0; t < n; t++) {
      INI[t] = m;
      RE_TOKEN.lastIndex = 0;
      let mt;
      while ((mt = RE_TOKEN.exec(T[t])) !== null) {
        const s = mt[0];
        let k = cacheChave.get(s);
        if (k === undefined) {
          const c = chaveDe(s);
          k = chaveId.get(c);
          if (k === undefined) { k = chaves.length; chaveId.set(c, k); chaves.push(c); }
          cacheChave.set(s, k);
        }
        let u = supId.get(s);
        if (u === undefined) { u = sups.length; supId.set(s, u); sups.push(s); }
        if (m + 2 >= cap) crescer();
        KEY[m] = k; SUP[m] = u; SRC[m] = t; m++;
      }
      KEY[m] = FIM; SUP[m] = -1; SRC[m] = t; m++;
    }
    INI[n] = m;
    KEY = KEY.slice(0, m); SUP = SUP.slice(0, m); SRC = SRC.slice(0, m);

    // índice: para cada palavra, onde ela aparece (CSR)
    const V = chaves.length;
    const OFS = new Int32Array(V + 1);
    for (let p = 0; p < m; p++) OFS[KEY[p] + 1]++;
    const FREQ = new Int32Array(V);
    for (let k = 0; k < V; k++) FREQ[k] = OFS[k + 1];
    for (let k = 0; k < V; k++) OFS[k + 1] += OFS[k];
    const LISTA = new Int32Array(m);
    const cursor = OFS.slice(0, V);
    for (let p = 0; p < m; p++) LISTA[cursor[KEY[p]]++] = p;

    const ehPalavra = new Uint8Array(V);
    for (let k = 1; k < V; k++) ehPalavra[k] = RE_PALAVRA.test(chaves[k]) || RE_EMOJI.test(chaves[k]) ? 1 : 0;

    // relatos que abrem contando um sonho: é daí que cada noite começa
    const abre = [];
    const kk = c => chaveId.get(c) ?? -1;
    const SONHEI = kk('sonhei'), EU = kk('eu'), TIVE = kk('tive'), UM = kk('um'), QUE = kk('que'),
          COM = kk('com'), HOJE = kk('hoje'), ESSA = kk('essa'), NOITE = kk('noite');
    for (let t = 0; t < n; t++) {
      if (!(F[t] & 1)) continue;
      const a = INI[t], k0 = KEY[a], k1 = KEY[a + 1], k2 = KEY[a + 2];
      if ((k0 === SONHEI && (k1 === QUE || k1 === COM)) ||
          ((k0 === EU || k0 === HOJE) && k1 === SONHEI && (k2 === QUE || k2 === COM)) ||
          (k0 === TIVE && k1 === UM) || (k0 === ESSA && k1 === NOITE && k2 === SONHEI)) abre.push(t);
    }

    return { n, T, P, F, D, KEY, SUP, SRC, INI, OFS, LISTA, FREQ, chaves, sups, ehPalavra, abre,
             tokens: m, V, chaveId };
  }

  const dist2 = (P, t, x, y, z) => {
    const dx = P[3 * t] - x, dy = P[3 * t + 1] - y, dz = P[3 * t + 2] - z;
    return dx * dx + dy * dy + dz * dz;
  };

  // ——— a temperatura, em números ———
  // σ: até onde um salto alcança (no planeta, o vizinho mais próximo está a
  // ~0,004 e trinta vizinhos cabem em ~0,016; a bola tem raio 1).
  // apego: a vontade de seguir no mesmo relato em vez de emendar noutro.
  // CUSTO: o que cada gesto faz com a agulha (−1 sono sem sonho · +1 vigília).
  const PARAM = {
    sigma: T => 0.012 + 0.07 * T * T,
    apego: T => 1 + 3 / (T * T),
    CUSTO: { segue: 0.02, mudo: 0.004, mudoDist: 0.35, salto: 0.018, saltoDist: 0.6,
             corte: 0.03, corteDist: 0.4, suave: 0.45 },
  };

  // ——— uma noite ———
  class Noite {
    constructor(c, desejo, op = {}) {
      this.c = c;
      this.sorte = acaso(op.semente ?? (Math.random() * 2 ** 32));
      this.total = op.palavras ?? 300;           // o tempo, medido em palavras
      this.T = op.temperatura ?? 0.8;
      this.gravidade = op.gravidade ?? 6;        // o quanto o sonho puxa para o desejo
      this.desejo = desejo;
      this.W = desejo ? desejo.p.map(v => v / 10000) : null;
      this.raio = desejo ? Math.max(desejo.r, op.raioMin ?? 0.05) : 0;
      this.saida = [];
      this.palavras = 0;
      this.agulha = 0;            // −1 sono sem sonho · 0 sonho · +1 vigília
      this.fim = null;            // 'acordou' · 'amanheceu' · 'chegou'
      this.saltos = 0; this.mudos = 0; this.cortes = 0; this.profundos = 0;
      this.maisPerto = Infinity;
      this.fontes = new Set();
      this.forcar = 0;
      this.ultimos = new Map();   // 6-gramas recentes: o sonho que se repete
      this.comecar(op.inicio);
    }

    posDe(t) { const P = this.c.P; return [P[3 * t], P[3 * t + 1], P[3 * t + 2]]; }
    distDesejo(t) { return this.W ? Math.sqrt(dist2(this.c.P, t, this.W[0], this.W[1], this.W[2])) : Infinity; }

    comecar(inicio) {
      const c = this.c;
      let t = inicio;
      if (t === undefined) {
        // longe o bastante do desejo para haver viagem, perto o bastante para haver chance
        const boas = [];
        for (let i = 0; i < 400 && boas.length < 40; i++) {
          const x = c.abre[(this.sorte() * c.abre.length) | 0];
          const d = this.distDesejo(x);
          if (!this.W || (d > 0.45 && d < 1.15)) boas.push(x);
        }
        t = boas.length ? boas[(this.sorte() * boas.length) | 0] : c.abre[(this.sorte() * c.abre.length) | 0];
      }
      this.fonte = t;
      this.p = c.INI[t] - 1;
      this.inicioDist = this.distDesejo(t);
      this.maisPerto = this.inicioDist;
      this.emitir(this.p + 1, 'inicio');
      this.emitir(this.p + 1, 'inicio');
      this.forcar = 2;
    }

    // superfície da palavra como vai ser dita: maiúscula de começo de frase do
    // relato de origem vira minúscula quando a frase aqui ainda não acabou
    superficie(pos) {
      const c = this.c;
      let s = c.sups[c.SUP[pos]];
      if (s === '\n') return '¶';
      const ant = this.saida.length ? this.saida[this.saida.length - 1] : null;
      const meioAqui = ant && !FIM_DE_FRASE.has(c.chaves[ant.k]);
      const kAntes = c.KEY[pos - 1];
      const comecoLa = pos === 0 || kAntes === FIM || FIM_DE_FRASE.has(c.chaves[kAntes]);
      if (meioAqui && comecoLa && s.length > 1 && s[0] !== s[0].toLowerCase() && s.slice(1) === s.slice(1).toLowerCase())
        s = s[0].toLowerCase() + s.slice(1);
      return s;
    }

    emitir(pos, tipo, de, dist) {
      const c = this.c;
      const k = c.KEY[pos], t = c.SRC[pos];
      const tok = { k, s: this.superficie(pos), p: pos, t, tipo, w: c.ehPalavra[k] === 1, de, dist: dist || 0 };
      this.saida.push(tok);
      this.p = pos; this.fonte = t;
      this.fontes.add(t);
      if (tok.w) this.palavras++;
      const d = this.distDesejo(t);
      if (d < this.maisPerto) this.maisPerto = d;
      return tok;
    }

    // As próximas possíveis: a distribuição inteira, agrupada por palavra.
    // op.atencao(t) → multiplicador (onde a pessoa está olhando); op.T sobrepõe a temperatura.
    proximas(op = {}) {
      const c = this.c, T = op.T ?? this.T, KEY = c.KEY, SRC = c.SRC, P = c.P;
      const n = this.saida.length;
      const a = this.saida[n - 2].k, b = this.saida[n - 1].k;
      const [x, y, z] = this.posDe(this.fonte);
      const s2 = 2 * PARAM.sigma(T) ** 2, C = PARAM.apego(T);
      const W = this.W, g = this.gravidade, dAqui = this.distDesejo(this.fonte);
      const atencao = op.atencao;
      const aqui = this.p + 1;                          // continuar no mesmo relato

      // começo de noite ou de cena: as primeiras palavras são lidas como estão,
      // para a cena se firmar antes de o sonho voltar a emendar
      if (this.forcar > 0 && KEY[aqui] !== FIM) {
        const so = { k: KEY[aqui], peso: 1, rep: aqui, n: 1, cont: true, pesoCont: 1, prob: 1, corte: false,
                     s: this.superficie(aqui), t: this.fonte };
        return { cands: [so], achados: 1, contexto: [a, b] };
      }

      // ocorrências de b precedidas de a — o contexto são as duas últimas palavras
      const i0 = c.OFS[b], i1 = c.OFS[b + 1];
      const achados = [];
      for (let i = i0; i < i1; i++) { const q = c.LISTA[i]; if (q > 0 && KEY[q - 1] === a) achados.push(q); }
      let lista = achados;
      if (achados.length > LIMITE) {
        lista = [];
        const passo = achados.length / LIMITE, off = this.sorte() * passo;
        for (let j = off; j < achados.length; j += passo) lista.push(achados[j | 0]);
      }
      const grupos = new Map();
      const somar = (q, extra) => {
        const cont = q + 1, t = SRC[cont], kc = KEY[cont];
        let w = Math.exp(-dist2(P, t, x, y, z) / s2);
        if (W) w *= Math.exp(g * (dAqui - Math.sqrt(dist2(P, t, W[0], W[1], W[2]))));
        if (atencao) w *= atencao(t);
        w *= extra;
        if (!(w > 0)) return;
        let gr = grupos.get(kc);
        if (!gr) { gr = { k: kc, peso: 0, rep: cont, n: 0, cont: false }; grupos.set(kc, gr); }
        gr.peso += w; gr.n++;
        if (cont === aqui) { gr.cont = true; gr.pesoCont = w; }
        // representante sorteado pelo peso (reservatório de um)
        if (this.sorte() * gr.peso < w) gr.rep = cont;
      };
      let viuAqui = false;
      // o apego vale para seguir no relato, não para acabá-lo: no fim de um
      // relato o sonho escorre para outro que diz as mesmas palavras
      const Cq = KEY[aqui] === FIM ? 1 : C;
      for (const q of lista) { if (q + 1 === aqui) { viuAqui = true; somar(q, Cq); } else somar(q, 1); }
      if (!viuAqui && KEY[aqui - 2] === a && KEY[aqui - 1] === b && SRC[aqui - 1] === this.fonte) somar(aqui - 1, Cq);

      // a vigia: tira a emenda que formaria o que não se diz
      const cauda = this.saida.slice(-5).map(t => c.chaves[t.k]).join(' ');
      for (const [kc, gr] of grupos) {
        if (kc !== FIM && VIGIA.test(cauda + ' ' + c.chaves[kc])) grupos.delete(kc);
      }

      let soma = 0;
      const cands = [];
      for (const gr of grupos.values()) {
        gr.prob = Math.pow(gr.peso, 1 / T);
        soma += gr.prob;
        cands.push(gr);
      }
      for (const gr of cands) {
        gr.prob /= soma || 1;
        gr.corte = gr.k === FIM;
        gr.s = gr.corte ? '¶' : this.superficie(gr.cont ? aqui : gr.rep);
        gr.t = SRC[gr.cont ? aqui : gr.rep];
      }
      cands.sort((u, v) => v.prob - u.prob);
      return { cands, achados: achados.length, contexto: [a, b] };
    }

    sortear(dist) {
      let r = this.sorte(), acc = 0;
      for (const g of dist.cands) { acc += g.prob; if (r <= acc) return g; }
      return dist.cands[dist.cands.length - 1];
    }

    // Diz a palavra escolhida. Devolve o que aconteceu, para a tela.
    escolher(g) {
      const c = this.c;
      const antes = this.fonte, aqui = this.p + 1;
      let evento;
      if (!g || g.corte) {
        evento = this.cortar();
      } else {
        // dentro da palavra escolhida: seguir no mesmo relato ou escorregar para
        // outro que diz a mesma coisa — o salto mudo
        let pos = g.rep;
        if (g.cont) pos = this.sorte() < (g.pesoCont || 0) / g.peso ? aqui : g.rep;
        if (pos === aqui) {
          this.emitir(pos, 'continua');
          this.agulha -= PARAM.CUSTO.segue;
          evento = { tipo: 'continua' };
        } else {
          const d = Math.sqrt(dist2(c.P, c.SRC[pos], ...this.posDe(antes)));
          const mudo = g.cont;               // a palavra era a mesma: ninguém percebe
          // emendar onde a frase já tinha acabado (ou o relato) quase não se sente;
          // no meio da frase, trocando a palavra, é o que mais desmancha o sonho
          const ult = this.saida[this.saida.length - 1];
          const suave = c.KEY[aqui] === FIM || FIM_DE_FRASE.has(c.chaves[ult.k]) ? PARAM.CUSTO.suave : 1;
          this.emitir(pos, mudo ? 'mudo' : 'salto', antes, d);
          if (mudo) { this.mudos++; this.agulha += suave * (PARAM.CUSTO.mudo + PARAM.CUSTO.mudoDist * d); }
          else { this.saltos++; this.agulha += suave * (PARAM.CUSTO.salto + PARAM.CUSTO.saltoDist * d); }
          evento = { tipo: mudo ? 'mudo' : 'salto', de: antes, para: c.SRC[pos], dist: d };
        }
      }
      if (this.forcar > 0) this.forcar--;
      return this.depois(evento);
    }

    // Fim do relato (ou escolha de cortar): outra cena, perto daqui.
    cortar() {
      const c = this.c, antes = this.fonte;
      const [x, y, z] = this.posDe(antes);
      const s2 = 2 * PARAM.sigma(this.T) ** 2;
      let melhor = null, soma = 0;
      for (let i = 0; i < 160; i++) {
        const t = (this.sorte() * c.n) | 0;
        if (t === antes) continue;
        let w = Math.exp(-dist2(c.P, t, x, y, z) / s2);
        if (this.W) w *= Math.exp(this.gravidade * (this.distDesejo(antes) - this.distDesejo(t)));
        soma += w;
        if (this.sorte() * soma < w) melhor = t;
      }
      if (melhor === null) melhor = c.abre[(this.sorte() * c.abre.length) | 0];
      // começa do começo do relato, ou de uma frase no meio dele
      let pos = c.INI[melhor];
      const fim = c.INI[melhor + 1] - 1;
      if (this.sorte() < 0.4) {
        const inicios = [];
        for (let q = pos + 1; q < fim - 3; q++) if (FIM_DE_FRASE.has(c.chaves[c.KEY[q - 1]])) inicios.push(q);
        if (inicios.length) pos = inicios[(this.sorte() * inicios.length) | 0];
      }
      const d = Math.sqrt(dist2(c.P, melhor, x, y, z));
      const ult = this.saida[this.saida.length - 1];
      if (!ult || c.chaves[ult.k] !== '¶') {
        this.saida.push({ k: c.chaveId.get('¶') ?? FIM, s: '¶', p: -1, t: antes, tipo: 'corte', w: false, dist: d });
      }
      this.p = pos - 1;
      this.emitir(pos, 'cena', antes, d);
      this.forcar = 2;
      this.cortes++;
      this.agulha += PARAM.CUSTO.corte + PARAM.CUSTO.corteDist * d;
      return { tipo: 'corte', de: antes, para: melhor, dist: d };
    }

    depois(evento) {
      // o sonho que se repete: a mesma sequência de seis, de novo, é sono sem sonho
      const s = this.saida, n = s.length;
      if (n >= 6) {
        let h = '';
        for (let i = n - 6; i < n; i++) h += s[i].k + ',';
        const visto = this.ultimos.get(h);
        this.ultimos.set(h, n);
        if (visto !== undefined && n - visto < 160 && evento.tipo !== 'corte') this.agulha = -1;
      }
      if (this.agulha <= -1) {
        this.profundos++;
        this.palavras += 12;              // o tempo passa sem sonho
        this.agulha = -0.3;
        const marca = this.saida.length;  // daqui em diante é a cena de depois do fundo
        const cena = this.cortar();
        evento = { tipo: 'profundo', cena, marca };
      }
      if (this.W && this.distDesejo(this.fonte) <= this.raio) this.fim = 'chegou';
      else if (this.agulha >= 1) this.fim = 'acordou';
      else if (this.palavras >= this.total) this.fim = 'amanheceu';
      evento.fim = this.fim;
      return evento;
    }

    // Um passo sozinho: a máquina escolhe.
    passo(op = {}) {
      if (this.fim) return { tipo: 'fim', fim: this.fim };
      const d = this.proximas(op);
      if (!d.cands.length) return this.escolher(null);
      return this.escolher(this.sortear(d));
    }

    // O que sobra ao acordar: o fim, inteiro, e do resto só imagens soltas
    // (as palavras mais raras), como quem acorda lembrando do fim.
    lembranca(janela = 64) {
      const c = this.c, s = this.saida;
      const corte = Math.max(0, s.length - janela);
      const fim = s.slice(corte);
      const vistos = new Set(), frag = [];
      const antes = s.slice(0, corte).filter(t => t.w && c.chaves[t.k].length > 3)
        .map((t, i) => ({ t, i, f: c.FREQ[t.k] }))
        .sort((u, v) => u.f - v.f);
      for (const x of antes) {
        const k = c.chaves[x.t.k];
        if (vistos.has(k)) continue;
        vistos.add(k); frag.push(x);
        if (frag.length >= 6) break;
      }
      frag.sort((u, v) => u.i - v.i);
      return { fim, fragmentos: frag.map(x => x.t.s), esquecidas: corte };
    }
  }

  // tokens → texto corrido
  function juntar(tokens, quebra = '\n') {
    let out = '', prev = null;
    for (const t of tokens) {
      const s = t.s;
      if (s === '¶') { out = out.replace(/\s+$/, '') + quebra; prev = '¶'; continue; }
      if (out && prev !== '¶' && !FECHA.has(s) && !out.endsWith('\n')) out += ' ';
      out += s;
      prev = s;
    }
    return out.trim();
  }

  const API = { montar, Noite, juntar, chaveDe, acaso, PARAM, FECHA, FIM_DE_FRASE, RE_TOKEN };
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
  else raiz.Latente = API;
})(typeof window !== 'undefined' ? window : globalThis);
