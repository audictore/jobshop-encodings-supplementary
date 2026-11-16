// Núcleo en C++ del algoritmo genético para el taller de rutas variables (job-shop).
// Decodificador de calendario activo (Giffler-Thompson), tres codificaciones (binaria, permutación con repetición,
// llaves aleatorias), sus operadores genéticos y la búsqueda aleatoria de referencia.
// Se compila con: g++ -O2 -std=c++17 -shared -fPIC -o libnucleo.so nucleo.cpp   (ver jsp_ag/nucleo.py)
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <numeric>
#include <vector>

namespace {

// ---------------------------------------------------------------- generador aleatorio (xoshiro256**)
struct Rng {
    uint64_t s[4];
    static uint64_t splitmix(uint64_t& x) {
        uint64_t z = (x += 0x9E3779B97F4A7C15ULL);
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
        return z ^ (z >> 31);
    }
    explicit Rng(uint64_t seed) { uint64_t x = seed; for (auto& v : s) v = splitmix(x); }
    static inline uint64_t rotl(uint64_t x, int k) { return (x << k) | (x >> (64 - k)); }
    uint64_t next() {
        const uint64_t r = rotl(s[1] * 5, 7) * 9, t = s[1] << 17;
        s[2] ^= s[0]; s[3] ^= s[1]; s[1] ^= s[2]; s[0] ^= s[3]; s[2] ^= t; s[3] = rotl(s[3], 45);
        return r;
    }
    double uni() { return (next() >> 11) * (1.0 / 9007199254740992.0); }      // [0,1)
    int below(int n) { return (int)(next() % (uint64_t)n); }                    // [0,n)
    double gauss() {                                                            // Box-Muller
        double u1 = uni(), u2 = uni();
        if (u1 < 1e-300) u1 = 1e-300;
        return std::sqrt(-2.0 * std::log(u1)) * std::cos(6.283185307179586 * u2);
    }
};

// ---------------------------------------------------------------- instancia
struct Inst {
    int n = 0, m = 0, N = 0;
    std::vector<int> len, off, mach, pt;   // por orden: longitud y desplazamiento; por operación global: máquina y tiempo
    std::vector<int> job_of;               // orden de cada operación global
};

Inst make_inst(int n, int m, const int* len, const int* mach, const int* pt) {
    Inst I; I.n = n; I.m = m;
    I.len.assign(len, len + n); I.off.assign(n + 1, 0);
    for (int j = 0; j < n; ++j) I.off[j + 1] = I.off[j] + len[j];
    I.N = I.off[n];
    I.mach.assign(mach, mach + I.N); I.pt.assign(pt, pt + I.N);
    I.job_of.resize(I.N);
    for (int j = 0; j < n; ++j) for (int k = 0; k < len[j]; ++k) I.job_of[I.off[j] + k] = j;
    return I;
}

// ---------------------------------------------------------------- decodificador (Giffler-Thompson)
// prio[o]: prioridad de la operación global o (menor = se atiende antes; empates por el menor índice).
struct Decoder {
    const Inst& I;
    std::vector<int> nxt, jready, mfree;
    explicit Decoder(const Inst& in) : I(in), nxt(in.n), jready(in.n), mfree(in.m) {}
    int run(const double* prio, int* start_out /*puede ser nullptr*/) {
        std::fill(nxt.begin(), nxt.end(), 0); std::fill(jready.begin(), jready.end(), 0); std::fill(mfree.begin(), mfree.end(), 0);
        int mk = 0;
        for (int step = 0; step < I.N; ++step) {
            int best_ect = INT32_MAX, mstar = -1;
            for (int j = 0; j < I.n; ++j) {
                if (nxt[j] >= I.len[j]) continue;
                int o = I.off[j] + nxt[j], m = I.mach[o];
                int ect = std::max(jready[j], mfree[m]) + I.pt[o];
                if (ect < best_ect) { best_ect = ect; mstar = m; }
            }
            int chosen = -1; double bp = 0;
            for (int j = 0; j < I.n; ++j) {
                if (nxt[j] >= I.len[j]) continue;
                int o = I.off[j] + nxt[j];
                if (I.mach[o] != mstar) continue;
                int st = std::max(jready[j], mfree[mstar]);
                if (st >= best_ect) continue;                       // fuera del conjunto de conflicto
                if (chosen < 0 || prio[o] < bp) { chosen = o; bp = prio[o]; }
            }
            int j = I.job_of[chosen], st = std::max(jready[j], mfree[mstar]), en = st + I.pt[chosen];
            if (start_out) start_out[chosen] = st;
            jready[j] = en; mfree[mstar] = en; ++nxt[j];
            if (en > mk) mk = en;
        }
        return mk;
    }
};

// ---------------------------------------------------------------- individuos
enum Enc { BIN = 0, PERM = 1, KEYS = 2, RAND = 3 };

struct Ind {
    std::vector<uint8_t> b;      // BIN
    std::vector<int> p;          // PERM
    std::vector<double> k;       // KEYS
    int fit = 0;
};

struct Params {
    int enc, cx, gray, pop, gens, elite, tourn;
    int bits;                      // bits por operación en la codificación binaria (8 en el estudio base)
    double pc, pm_scale, sigma;
};

inline int gray_to_bin(int g, int bits) { int b = g; for (int s = 1; s < bits; s <<= 1) b ^= (b >> s); return b; }

void to_prio(const Inst& I, const Params& P, const Ind& x, std::vector<double>& prio, std::vector<int>& cnt) {
    prio.resize(I.N);
    if (P.enc == BIN) {
        for (int o = 0; o < I.N; ++o) {
            int v = 0; for (int t = 0; t < P.bits; ++t) v = (v << 1) | x.b[o * P.bits + t];
            prio[o] = P.gray ? gray_to_bin(v, P.bits) : v;
        }
    } else if (P.enc == PERM) {
        cnt.assign(I.n, 0);
        for (int pos = 0; pos < I.N; ++pos) { int j = x.p[pos]; prio[I.off[j] + cnt[j]++] = pos; }
    } else {
        for (int o = 0; o < I.N; ++o) prio[o] = x.k[o];
    }
}

void random_ind(const Inst& I, const Params& P, Rng& r, Ind& x) {
    if (P.enc == BIN) { x.b.resize(I.N * P.bits); for (auto& v : x.b) v = (uint8_t)(r.next() & 1); }
    else if (P.enc == PERM) {                                   // permutación aleatoria del multiconjunto (Fisher-Yates)
        x.p.clear(); for (int j = 0; j < I.n; ++j) for (int k = 0; k < I.len[j]; ++k) x.p.push_back(j);
        for (int i = I.N - 1; i > 0; --i) std::swap(x.p[i], x.p[r.below(i + 1)]);
    } else { x.k.resize(I.N); for (auto& v : x.k) v = r.uni(); }
}

// ---------------------------------------------------------------- operadores de cruza
void two_cuts(int L, Rng& r, int& a, int& b) {
    a = r.below(L); b = r.below(L); if (a > b) std::swap(a, b); if (a == b) b = std::min(L, b + 1);
}

void cx_bin(const Params& P, const Ind& A, const Ind& B, Ind& C, Ind& D, Rng& r) {
    int L = (int)A.b.size(); C.b = A.b; D.b = B.b;
    if (P.cx == 0) { int a, b; two_cuts(L, r, a, b); for (int i = a; i < b; ++i) { C.b[i] = B.b[i]; D.b[i] = A.b[i]; } }
    else if (P.cx == 1) { int a = 1 + r.below(L - 1); for (int i = a; i < L; ++i) { C.b[i] = B.b[i]; D.b[i] = A.b[i]; } }
    else { for (int i = 0; i < L; ++i) if (r.next() & 1) { C.b[i] = B.b[i]; D.b[i] = A.b[i]; } }
}

void cx_keys(const Params& P, const Ind& A, const Ind& B, Ind& C, Ind& D, Rng& r) {
    int L = (int)A.k.size(); C.k = A.k; D.k = B.k;
    if (P.cx == 0) { for (int i = 0; i < L; ++i) if (r.next() & 1) { C.k[i] = B.k[i]; D.k[i] = A.k[i]; } }
    else if (P.cx == 1) { int a, b; two_cuts(L, r, a, b); for (int i = a; i < b; ++i) { C.k[i] = B.k[i]; D.k[i] = A.k[i]; } }
    else { double al = r.uni(); for (int i = 0; i < L; ++i) { C.k[i] = al * A.k[i] + (1 - al) * B.k[i]; D.k[i] = (1 - al) * A.k[i] + al * B.k[i]; } }
}

// POX: un subconjunto de órdenes conserva sus posiciones en el padre A; el resto se completa en el orden del padre B.
void pox_child(const Inst& I, const std::vector<char>& inS, const std::vector<int>& A, const std::vector<int>& B, std::vector<int>& C) {
    C.assign(I.N, -1); int pb = 0;
    for (int i = 0; i < I.N; ++i) if (inS[A[i]]) C[i] = A[i];
    for (int i = 0; i < I.N; ++i) if (C[i] < 0) { while (inS[B[pb]]) ++pb; C[i] = B[pb++]; }
}

// OX generalizado: un segmento del padre A se conserva; el resto se completa con los genes del padre B a partir del segundo corte.
void ox_child(const Inst& I, int a, int b, const std::vector<int>& A, const std::vector<int>& B, std::vector<int>& C) {
    C.assign(I.N, -1); std::vector<int> rem(I.len);
    for (int i = a; i < b; ++i) { C[i] = A[i]; --rem[A[i]]; }
    int pos = b % I.N;
    for (int t = 0; t < I.N; ++t) {
        int g = B[(b + t) % I.N];
        if (rem[g] > 0) { --rem[g]; while (C[pos] >= 0) pos = (pos + 1) % I.N; C[pos] = g; pos = (pos + 1) % I.N; }
    }
}

// PPX: se construye de izquierda a derecha tomando el siguiente gen de uno de los padres según una máscara; se borra del otro.
void ppx_child(const Inst& I, const std::vector<char>& mask, const std::vector<int>& A, const std::vector<int>& B, std::vector<int>& C) {
    C.resize(I.N);
    const std::vector<int>* P[2] = {&A, &B};
    std::vector<char> del[2] = {std::vector<char>(I.N, 0), std::vector<char>(I.N, 0)};
    std::vector<int> ptr(2, 0);
    std::vector<std::vector<int>> posj[2];
    for (int q = 0; q < 2; ++q) { posj[q].assign(I.n, {}); for (int i = 0; i < I.N; ++i) posj[q][(*P[q])[i]].push_back(i); }
    std::vector<int> used[2] = {std::vector<int>(I.n, 0), std::vector<int>(I.n, 0)};
    for (int i = 0; i < I.N; ++i) {
        int x = mask[i] ? 1 : 0, y = 1 - x;
        while (del[x][ptr[x]]) ++ptr[x];
        int g = (*P[x])[ptr[x]]; del[x][ptr[x]] = 1; ++used[x][g];
        del[y][posj[y][g][used[y][g]]] = 1; ++used[y][g];
        C[i] = g;
    }
}

void cx_perm(const Inst& I, const Params& P, const Ind& A, const Ind& B, Ind& C, Ind& D, Rng& r) {
    if (P.cx == 0) {
        std::vector<char> inS(I.n, 0); int cnt = 0;
        do { cnt = 0; for (int j = 0; j < I.n; ++j) { inS[j] = (r.next() & 1); cnt += inS[j]; } } while (cnt == 0 || cnt == I.n);
        pox_child(I, inS, A.p, B.p, C.p); pox_child(I, inS, B.p, A.p, D.p);
    } else if (P.cx == 1) {
        int a, b; two_cuts(I.N, r, a, b);
        ox_child(I, a, b, A.p, B.p, C.p); ox_child(I, a, b, B.p, A.p, D.p);
    } else {
        std::vector<char> mask(I.N); for (auto& v : mask) v = (r.next() & 1);
        ppx_child(I, mask, A.p, B.p, C.p);
        for (auto& v : mask) v = !v;
        ppx_child(I, mask, A.p, B.p, D.p);
    }
}

// ---------------------------------------------------------------- mutación
void mutate(const Inst& I, const Params& P, Ind& x, Rng& r) {
    if (P.enc == BIN) {
        double p = std::min(1.0, P.pm_scale * 2.0 / (double)(I.N * P.bits));
        for (auto& v : x.b) if (r.uni() < p) v ^= 1;
    } else if (P.enc == PERM) {
        if (r.uni() < std::min(1.0, P.pm_scale * 0.30)) { int i = r.below(I.N), j = r.below(I.N); std::swap(x.p[i], x.p[j]); }
    } else {
        double p = std::min(1.0, P.pm_scale * 2.0 / (double)I.N);
        for (auto& v : x.k) if (r.uni() < p) { v += P.sigma * r.gauss(); v = std::min(std::nextafter(1.0, 0.0), std::max(0.0, v)); }
    }
}

// ---------------------------------------------------------------- diversidad (distancia de Spearman entre los órdenes de prioridad)
double diversidad(const Inst& I, const std::vector<std::vector<double>>& prios, Rng& r) {
    int pop = (int)prios.size(); int N = I.N;
    std::vector<std::vector<int>> rank(pop, std::vector<int>(N));
    std::vector<int> idx(N);
    for (int a = 0; a < pop; ++a) {
        std::iota(idx.begin(), idx.end(), 0);
        std::stable_sort(idx.begin(), idx.end(), [&](int x, int y) { return prios[a][x] < prios[a][y]; });
        for (int t = 0; t < N; ++t) rank[a][idx[t]] = t;
    }
    double tot = 0; int pairs = std::min(100, pop * (pop - 1) / 2);
    for (int q = 0; q < pairs; ++q) {
        int a = r.below(pop), b = r.below(pop - 1); if (b >= a) ++b;
        long long s = 0; for (int i = 0; i < N; ++i) s += std::abs(rank[a][i] - rank[b][i]);
        tot += (double)s / ((double)N * N / 2.0);
    }
    return tot / pairs;
}

}  // namespace

// ================================================================ API en C
extern "C" {

// Decodifica un vector de prioridades. Devuelve el makespan y, si start_out != NULL, los inicios de cada operación global.
int jsp_decodificar(int n, int m, const int* len, const int* mach, const int* pt, const double* prio, int* start_out) {
    Inst I = make_inst(n, m, len, mach, pt); Decoder D(I); return D.run(prio, start_out);
}

// Ejecuta una corrida completa. enc: 0 binaria, 1 permutación con repetición, 2 llaves aleatorias, 3 búsqueda aleatoria (llaves uniformes).
// Escribe en out_best[0..gens] el mejor makespan acumulado tras la población inicial y tras cada generación (cada una con pop-elite
// evaluaciones nuevas) y, si out_div != NULL, la diversidad de la población. out_prio (N dobles) recibe las prioridades del mejor individuo.
int jsp_ejecutar(int n, int m, const int* len, const int* mach, const int* pt,
                 int enc, int cx, int gray, int bits, int pop, int gens, int elite, int tourn,
                 double pc, double pm_scale, double sigma, uint64_t seed,
                 int* out_best, double* out_div, double* out_prio, long long* out_evals) {
    Inst I = make_inst(n, m, len, mach, pt); Decoder D(I); Rng r(seed);
    Params P{enc == RAND ? KEYS : enc, cx, gray, pop, gens, elite, tourn, bits, pc, pm_scale, sigma};
    std::vector<Ind> cur(pop), nxt; std::vector<double> prio; std::vector<int> cnt;
    long long evals = 0; int best = INT32_MAX; std::vector<double> best_prio(I.N);
    auto evaluate = [&](Ind& x) {
        to_prio(I, P, x, prio, cnt); x.fit = D.run(prio.data(), nullptr); ++evals;
        if (x.fit < best) { best = x.fit; best_prio = prio; }
    };
    for (auto& x : cur) { random_ind(I, P, r, x); evaluate(x); }
    out_best[0] = best;
    std::vector<std::vector<double>> prios;
    auto record_div = [&](int g) {
        if (!out_div) return;
        prios.assign(pop, {});
        for (int a = 0; a < pop; ++a) to_prio(I, P, cur[a], prios[a], cnt);
        out_div[g] = diversidad(I, prios, r);
    };
    record_div(0);
    std::vector<int> order(pop);
    for (int g = 1; g <= gens; ++g) {
        if (enc == RAND) {                                           // búsqueda aleatoria: mismo número de evaluaciones por bloque
            for (int t = 0; t < pop - elite; ++t) { Ind x; random_ind(I, P, r, x); evaluate(x); }
            out_best[g] = best; if (out_div) out_div[g] = 0; continue;
        }
        std::iota(order.begin(), order.end(), 0);
        std::stable_sort(order.begin(), order.end(), [&](int a, int b) { return cur[a].fit < cur[b].fit; });
        nxt.assign(pop, Ind()); int filled = 0;
        for (int e = 0; e < elite; ++e) nxt[filled++] = cur[order[e]];
        auto select = [&]() { int w = r.below(pop); for (int t = 1; t < tourn; ++t) { int c = r.below(pop); if (cur[c].fit < cur[w].fit) w = c; } return w; };
        while (filled < pop) {
            const Ind& A = cur[select()]; const Ind& B = cur[select()];
            Ind C, E;
            if (r.uni() < pc) {
                if (P.enc == BIN) cx_bin(P, A, B, C, E, r); else if (P.enc == PERM) cx_perm(I, P, A, B, C, E, r); else cx_keys(P, A, B, C, E, r);
            } else { C = A; E = B; }
            mutate(I, P, C, r); mutate(I, P, E, r);
            evaluate(C); nxt[filled++] = std::move(C);
            if (filled < pop) { evaluate(E); nxt[filled++] = std::move(E); }
        }
        cur.swap(nxt);
        out_best[g] = best; record_div(g);
    }
    if (out_prio) std::memcpy(out_prio, best_prio.data(), sizeof(double) * I.N);
    if (out_evals) *out_evals = evals;
    return best;
}


// Comprobación de los operadores de permutación: devuelve cuántos hijos (de 2*pruebas) no conservan el multiconjunto de órdenes.
int jsp_verificar_cruza_permutacion(int n, int m, const int* len, const int* mach, const int* pt, int cx, int pruebas, uint64_t seed) {
    Inst I = make_inst(n, m, len, mach, pt); Rng r(seed);
    Params P{PERM, cx, 0, 2, 1, 0, 2, 8, 1.0, 1.0, 0.15};
    int malos = 0;
    for (int t = 0; t < pruebas; ++t) {
        Ind A, B, C, D; random_ind(I, P, r, A); random_ind(I, P, r, B);
        cx_perm(I, P, A, B, C, D, r);
        for (const Ind* h : {&C, &D}) {
            std::vector<int> c(I.n, 0); bool ok = (int)h->p.size() == I.N;
            if (ok) for (int g : h->p) { if (g < 0 || g >= I.n) { ok = false; break; } ++c[g]; }
            if (ok) for (int j = 0; j < I.n; ++j) if (c[j] != I.len[j]) ok = false;
            if (!ok) ++malos;
        }
    }
    return malos;
}

}  // extern "C"
