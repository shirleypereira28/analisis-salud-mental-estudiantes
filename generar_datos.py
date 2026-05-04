import numpy as np
import pandas as pd
import os

np.random.seed(42)

N = 96

PROGRAMAS = [
    'Ingeniería', 'Psicología', 'Administración', 'Derecho', 'Medicina',
    'Música', 'Artes Plásticas', 'Danza', 'Licenciatura'
]
MODALIDADES = ['Presencial', 'Virtual', 'Híbrida']
GENEROS     = ['Masculino', 'Femenino', 'Otro']

# Target: ~24 Bajo, ~43 Medio, ~21 Alto, ~8 Crítico
profiles = ['Bajo'] * 24 + ['Medio'] * 43 + ['Alto'] * 21 + ['Crítico'] * 8
np.random.shuffle(profiles)

PROFILE_PARAMS = {
    'Bajo':    {'mean': 1.8, 'std': 0.35},
    'Medio':   {'mean': 3.0, 'std': 0.35},
    'Alto':    {'mean': 3.8, 'std': 0.25},
    'Crítico': {'mean': 4.4, 'std': 0.25},
}

def clip_score(val):
    return float(np.clip(val, 1.0, 5.0))

def clip_likert(val):
    return int(np.clip(round(val), 1, 5))

def gen_items(base, n=5, noise=0.7):
    return [clip_likert(base + np.random.normal(0, noise)) for _ in range(n)]


records = []

for i in range(N):
    profile = profiles[i]
    params  = PROFILE_PARAMS[profile]

    # ── Demográficos ──────────────────────────────────────────────────────────
    semestre = int(np.random.choice(
        range(1, 11),
        p=[0.12, 0.12, 0.12, 0.12, 0.11, 0.10, 0.08, 0.08, 0.08, 0.07]
    ))

    # Probabilidad de trabajar según semestre
    if semestre <= 3:
        p_trabaja = 0.15
    elif semestre <= 6:
        p_trabaja = 0.30
    else:
        p_trabaja = 0.60
    trabaja = np.random.choice(['Sí', 'No'], p=[p_trabaja, 1 - p_trabaja])

    # Estrato ponderado hacia estratos bajos
    estrato = int(np.random.choice(
        [1, 2, 3, 4, 5, 6],
        p=[0.20, 0.25, 0.25, 0.15, 0.10, 0.05]
    ))

    # Subsidio: mayor probabilidad en estratos bajos
    if estrato <= 2:
        p_subsidio = 0.65
    elif estrato == 3:
        p_subsidio = 0.35
    else:
        p_subsidio = 0.10
    subsidio = np.random.choice(['Sí', 'No'], p=[p_subsidio, 1 - p_subsidio])

    modalidad = np.random.choice(MODALIDADES, p=[0.40, 0.35, 0.25])
    programa  = np.random.choice(PROGRAMAS)
    genero    = np.random.choice(GENEROS, p=[0.45, 0.50, 0.05])
    edad      = int(np.clip(round(np.random.normal(18 + semestre * 0.4, 1.5)), 17, 30))

    # ── Score base del perfil ─────────────────────────────────────────────────
    base = clip_score(np.random.normal(params['mean'], params['std']))

    # ── Modificadores contextuales por dimensión ──────────────────────────────
    mod_estres   = (0.4 if trabaja == 'Sí' else 0.0) + (0.3 if 4 <= semestre <= 6 else 0.0)
    mod_carga    = (0.4 if trabaja == 'Sí' else 0.0) + (0.4 if 4 <= semestre <= 6 else 0.0)
    mod_depresion = 0.3 if estrato <= 2 else 0.0
    mod_ansiedad  = 0.2 if estrato <= 2 else 0.0
    mod_apoyo    = (0.3 if modalidad == 'Virtual' else 0.0) + (0.2 if estrato <= 2 else 0.0)

    b_estres    = clip_score(base + mod_estres)
    b_ansiedad  = clip_score(base + mod_ansiedad)
    b_carga     = clip_score(base + mod_carga)
    b_habitos   = clip_score(base)
    b_depresion = clip_score(base + mod_depresion)
    b_sueno     = clip_score(base)
    b_apoyo     = clip_score(base + mod_apoyo)

    # ── Ítems individuales ────────────────────────────────────────────────────
    e  = gen_items(b_estres)
    a  = gen_items(b_ansiedad)
    c  = gen_items(b_carga)
    h  = gen_items(b_habitos)
    d  = gen_items(b_depresion)
    s  = gen_items(b_sueno)
    ap = gen_items(b_apoyo)

    # D4 (ideación): críticos tienen 60% de probabilidad de responder 4 o 5;
    # el resto queda capado en 3
    if profile == 'Crítico':
        d[3] = int(np.random.choice([4, 5])) if np.random.random() < 0.6 \
               else clip_likert(b_depresion + np.random.normal(0, 0.5))
    else:
        d[3] = min(d[3], 3)

    # Bienestar global: inverso al score base
    b1 = int(np.clip(round(11 - (base * 2) + np.random.normal(0, 0.8)), 1, 10))

    records.append({
        'id_estudiante': i + 1,
        'edad': edad, 'genero': genero, 'semestre': semestre,
        'programa': programa, 'modalidad': modalidad,
        'trabaja': trabaja, 'estrato': estrato, 'subsidio': subsidio,
        'E1': e[0],  'E2': e[1],  'E3': e[2],  'E4': e[3],  'E5': e[4],
        'A1': a[0],  'A2': a[1],  'A3': a[2],  'A4': a[3],  'A5': a[4],
        'C1': c[0],  'C2': c[1],  'C3': c[2],  'C4': c[3],  'C5': c[4],
        'H1': h[0],  'H2': h[1],  'H3': h[2],  'H4': h[3],  'H5': h[4],
        'D1': d[0],  'D2': d[1],  'D3': d[2],  'D4': d[3],  'D5': d[4],
        'S1': s[0],  'S2': s[1],  'S3': s[2],  'S4': s[3],  'S5': s[4],
        'AP1': ap[0], 'AP2': ap[1], 'AP3': ap[2], 'AP4': ap[3], 'AP5': ap[4],
        'B1': b1,
    })

df = pd.DataFrame(records)

output_dir  = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'encuesta_raw.csv')
df.to_csv(output_path, index=False)

print(f"Registros generados : {len(df)}")
print(f"Archivo             : {os.path.abspath(output_path)}")
print(f"\nColumnas ({len(df.columns)}): {list(df.columns)}")
print("\nPrimeros 5 registros (campos demográficos):")
print(df[['id_estudiante', 'edad', 'genero', 'semestre', 'programa',
          'modalidad', 'trabaja', 'estrato', 'subsidio', 'B1']].head().to_string(index=False))
