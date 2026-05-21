"""
Suite de pruebas estructuradas — Sistema de Bienestar Estudiantil TRL5
Ejecutar: python src/pruebas_sistema.py
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
RAW_PATH   = os.path.join(BASE_DIR, '..', 'data', 'encuesta_raw.csv')
PROC_PATH  = os.path.join(BASE_DIR, '..', 'data', 'encuesta_procesada.csv')
REPORT_PATH = os.path.join(BASE_DIR, '..', 'data', 'reporte_pruebas.txt')

PESOS = {
    'score_depresion': 0.25,
    'score_estres':    0.20,
    'score_ansiedad':  0.15,
    'score_sueno':     0.10,
    'score_apoyo':     0.10,
    'score_carga':     0.10,
    'score_habitos':   0.10,
}

DIMENSIONES = {
    'score_estres':    ['E1', 'E2', 'E3', 'E4', 'E5'],
    'score_ansiedad':  ['A1', 'A2', 'A3', 'A4', 'A5'],
    'score_carga':     ['C1', 'C2', 'C3', 'C4', 'C5'],
    'score_habitos':   ['H1', 'H2', 'H3', 'H4', 'H5'],
    'score_depresion': ['D1', 'D2', 'D3', 'D4', 'D5'],
    'score_sueno':     ['S1', 'S2', 'S3', 'S4', 'S5'],
    'score_apoyo':     ['AP1', 'AP2', 'AP3', 'AP4', 'AP5'],
}

LIKERT_COLS = [c for dim in DIMENSIONES.values() for c in dim]
DEMO_CATS = {
    'genero':    {'Masculino', 'Femenino', 'Otro'},
    'modalidad': {'Presencial', 'Virtual', 'Híbrida'},
    'trabaja':   {'Sí', 'No'},
    'subsidio':  {'Sí', 'No'},
    'programa':  {'Ingeniería', 'Psicología', 'Administración', 'Derecho',
                  'Medicina', 'Música', 'Artes Plásticas', 'Danza', 'Licenciatura'},
}

# ── Carga de datos ─────────────────────────────────────────────────────────────

def cargar_datos():
    raw  = pd.read_csv(RAW_PATH)
    proc = pd.read_csv(PROC_PATH)
    return raw, proc


# ── Definición de pruebas ──────────────────────────────────────────────────────
# Cada función retorna (bool, str): éxito y detalle del resultado.

def t01_numero_registros(raw, _):
    n = len(raw)
    return n == 96, f"Registros encontrados: {n} (esperado: 96)"

def t02_columnas_raw(raw, _):
    cols_esperadas = (
        ['id_estudiante', 'edad', 'genero', 'semestre', 'programa',
         'modalidad', 'trabaja', 'estrato', 'subsidio']
        + LIKERT_COLS + ['B1']
    )
    faltantes = [c for c in cols_esperadas if c not in raw.columns]
    return len(faltantes) == 0, (
        f"Todas las columnas presentes ({len(cols_esperadas)})"
        if not faltantes else f"Faltan: {faltantes}"
    )

def t03_sin_nulos_raw(raw, _):
    total_nulos = int(raw.isnull().sum().sum())
    return total_nulos == 0, f"Valores nulos encontrados: {total_nulos}"

def t04_rango_likert(raw, _):
    fuera = int(~raw[LIKERT_COLS].apply(lambda col: col.between(1, 5)).all(axis=1).all())
    invalidos = sum(
        int((~raw[c].between(1, 5)).sum()) for c in LIKERT_COLS
    )
    total = len(LIKERT_COLS) * len(raw)
    return invalidos == 0, (
        f"Todos los {total} ítems Likert en [1,5]"
        if invalidos == 0 else f"{invalidos}/{total} ítems fuera de rango"
    )

def t05_rango_demograficos(raw, _):
    checks = [
        ('edad',     raw['edad'].between(17, 30).all(),     '17–30'),
        ('semestre', raw['semestre'].between(1, 10).all(),  '1–10'),
        ('estrato',  raw['estrato'].between(1, 6).all(),    '1–6'),
        ('B1',       raw['B1'].between(1, 10).all(),        '1–10'),
    ]
    fallas = [(c, r) for c, ok, r in checks if not ok]
    return len(fallas) == 0, (
        "Todos los rangos demográficos válidos"
        if not fallas else f"Fuera de rango: {fallas}"
    )

def t06_valores_categoricos(raw, _):
    fallas = [
        col for col, vals in DEMO_CATS.items()
        if not set(raw[col].unique()).issubset(vals)
    ]
    return len(fallas) == 0, (
        "Todos los campos categóricos con valores permitidos"
        if not fallas else f"Valores inesperados en: {fallas}"
    )

def t07_calculo_scores_dimension(_, proc):
    tolerancia = 0.01
    errores = 0
    for score_col, items in DIMENSIONES.items():
        esperado = proc[items].mean(axis=1).round(2)
        desviacion = (proc[score_col] - esperado).abs().max()
        if desviacion > tolerancia:
            errores += 1
    return errores == 0, (
        f"Los 7 scores de dimensión coinciden con el promedio de sus ítems (tol={tolerancia})"
        if errores == 0 else f"{errores} dimensiones con desviación > {tolerancia}"
    )

def t08_score_total_ponderado(_, proc):
    tolerancia = 0.01
    esperado = sum(proc[col] * peso for col, peso in PESOS.items()).round(2)
    desviacion_max = (proc['score_total'] - esperado).abs().max()
    return desviacion_max <= tolerancia, (
        f"score_total coincide con la fórmula ponderada (desviación máx: {desviacion_max:.4f})"
    )

def t09_pesos_normalizados(_, __):
    suma = round(sum(PESOS.values()), 10)
    return suma == 1.0, f"Suma de pesos: {suma} (esperado: 1.0)"

def t10_rango_scores_procesados(_, proc):
    score_cols = list(PESOS.keys()) + ['score_total']
    fuera = {c: int((~proc[c].between(1.0, 5.0)).sum()) for c in score_cols}
    total_fuera = sum(fuera.values())
    return total_fuera == 0, (
        "Todos los scores calculados en [1.0, 5.0]"
        if total_fuera == 0 else f"Fuera de rango: {fuera}"
    )

def t11_clasificacion_bajo(_, proc):
    mask = (proc['score_total'] < 2.5) & (proc['D4'] < 4)
    incorrectos = int((proc.loc[mask, 'nivel_riesgo'] != 'Bajo').sum())
    n = int(mask.sum())
    return incorrectos == 0, f"{n} registros con score<2.5 y D4<4 → todos clasificados Bajo"

def t12_clasificacion_medio(_, proc):
    mask = (proc['score_total'] >= 2.5) & (proc['score_total'] < 3.5) & (proc['D4'] < 4)
    incorrectos = int((proc.loc[mask, 'nivel_riesgo'] != 'Medio').sum())
    n = int(mask.sum())
    return incorrectos == 0, f"{n} registros en rango Medio sin D4 → todos clasificados Medio"

def t13_clasificacion_alto(_, proc):
    mask = (proc['score_total'] >= 3.5) & (proc['score_total'] < 4.2) & (proc['D4'] < 4)
    incorrectos = int((proc.loc[mask, 'nivel_riesgo'] != 'Alto').sum())
    n = int(mask.sum())
    return incorrectos == 0, f"{n} registros en rango Alto sin D4 → todos clasificados Alto"

def t14_clasificacion_critico_score(_, proc):
    mask = proc['score_total'] >= 4.2
    incorrectos = int((proc.loc[mask, 'nivel_riesgo'] != 'Crítico').sum())
    n = int(mask.sum())
    return incorrectos == 0, f"{n} registros con score≥4.2 → todos clasificados Crítico"

def t15_bandera_d4(_, proc):
    mask = proc['D4'] >= 4
    incorrectos = int((proc.loc[mask, 'nivel_riesgo'] != 'Crítico').sum())
    n = int(mask.sum())
    return incorrectos == 0, (
        f"{n} registros con D4≥4 → todos clasificados Crítico (bandera independiente)"
    )

def t16_correlacion_bienestar(_, proc):
    corr = round(float(proc['score_total'].corr(proc['B1'])), 3)
    return corr < -0.5, f"Correlación score_total ↔ B1: r={corr} (esperado < -0.5)"

def t17_separacion_monotona(_, proc):
    medias = proc.groupby('nivel_riesgo')['score_total'].mean()
    orden = ['Bajo', 'Medio', 'Alto', 'Crítico']
    vals  = [round(float(medias[n]), 2) for n in orden]
    monotona = all(vals[i] < vals[i+1] for i in range(len(vals) - 1))
    detalle = ' < '.join(f"{orden[i]}({vals[i]})" for i in range(4))
    return monotona, f"Score promedio por nivel: {detalle}"

def t18_efecto_trabajo(raw, proc):
    merged = raw[['id_estudiante', 'trabaja']].merge(proc[['id_estudiante', 'score_estres']])
    m_trabaja    = round(float(merged[merged['trabaja'] == 'Sí']['score_estres'].mean()), 2)
    m_no_trabaja = round(float(merged[merged['trabaja'] == 'No']['score_estres'].mean()), 2)
    return m_trabaja > m_no_trabaja, (
        f"Score estrés: trabaja={m_trabaja} > no trabaja={m_no_trabaja} "
        f"(diferencia={round(m_trabaja - m_no_trabaja, 2)})"
    )

def t19_efecto_estrato(raw, proc):
    merged = raw[['id_estudiante', 'estrato']].merge(proc[['id_estudiante', 'score_depresion']])
    m_bajo = round(float(merged[merged['estrato'] <= 2]['score_depresion'].mean()), 2)
    m_alto = round(float(merged[merged['estrato'] >= 4]['score_depresion'].mean()), 2)
    return m_bajo > m_alto, (
        f"Score depresión: estrato 1–2={m_bajo} > estrato 4–6={m_alto} "
        f"(diferencia={round(m_bajo - m_alto, 2)})"
    )

def t20_distribucion_aproximada(_, proc):
    objetivo = {'Bajo': 24, 'Medio': 43, 'Alto': 21, 'Crítico': 8}
    dist_obs = proc['nivel_riesgo'].value_counts()
    tolerancia = 10
    desvios = {
        nivel: abs(int(dist_obs.get(nivel, 0)) - objetivo[nivel])
        for nivel in objetivo
    }
    max_desv = max(desvios.values())
    dentro = all(d <= tolerancia for d in desvios.values())
    detalle = ' | '.join(f"{n}: obs={dist_obs.get(n,0)} obj={objetivo[n]} Δ={desvios[n]}"
                         for n in ['Bajo', 'Medio', 'Alto', 'Crítico'])
    return dentro, f"Distribución vs objetivo (tol≤{tolerancia}): {detalle}"


# ── Ejecución ──────────────────────────────────────────────────────────────────

PRUEBAS = [
    ("Integridad de datos raw", [
        ("T01", "Número de registros (96 esperados)",           t01_numero_registros),
        ("T02", "Columnas requeridas presentes (44 columnas)",  t02_columnas_raw),
        ("T03", "Sin valores nulos en dataset raw",             t03_sin_nulos_raw),
        ("T04", "Rango válido ítems Likert [1–5]",             t04_rango_likert),
        ("T05", "Rangos demográficos válidos",                  t05_rango_demograficos),
        ("T06", "Valores categóricos permitidos",               t06_valores_categoricos),
    ]),
    ("Cálculo de scores", [
        ("T07", "Score por dimensión = promedio de ítems",      t07_calculo_scores_dimension),
        ("T08", "Score total = promedio ponderado correcto",    t08_score_total_ponderado),
        ("T09", "Pesos normalizados (suma = 1.0)",              t09_pesos_normalizados),
        ("T10", "Rango de scores calculados [1.0–5.0]",        t10_rango_scores_procesados),
    ]),
    ("Clasificación de riesgo", [
        ("T11", "Clasificación Bajo  (score < 2.5)",            t11_clasificacion_bajo),
        ("T12", "Clasificación Medio (2.5 ≤ score < 3.5)",     t12_clasificacion_medio),
        ("T13", "Clasificación Alto  (3.5 ≤ score < 4.2)",     t13_clasificacion_alto),
        ("T14", "Clasificación Crítico por score (≥ 4.2)",     t14_clasificacion_critico_score),
        ("T15", "Bandera D4 activa Crítico (independiente)",   t15_bandera_d4),
    ]),
    ("Validación estadística", [
        ("T16", "Correlación negativa score ↔ bienestar",      t16_correlacion_bienestar),
        ("T17", "Separación monótona entre niveles de riesgo", t17_separacion_monotona),
        ("T18", "Efecto del trabajo en score de estrés",       t18_efecto_trabajo),
        ("T19", "Efecto del estrato en score de depresión",    t19_efecto_estrato),
        ("T20", "Distribución próxima al objetivo (±10)",      t20_distribucion_aproximada),
    ]),
]


def ejecutar():
    try:
        raw, proc = cargar_datos()
    except FileNotFoundError as e:
        print(f"\n[ERROR] No se encontró el archivo de datos: {e}")
        print("Ejecute primero: python src/generar_datos.py && python src/procesar_datos.py")
        return

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sep = '═' * 62

    lineas = [
        sep,
        "  SUITE DE PRUEBAS — Sistema de Bienestar Estudiantil TRL5",
        f"  Fecha: {timestamp}",
        f"  Dataset raw  : {os.path.basename(RAW_PATH)}  ({len(raw)} registros)",
        f"  Dataset proc : {os.path.basename(PROC_PATH)}  ({len(proc)} registros)",
        sep,
    ]

    total_pass = 0
    total_fail = 0

    for grupo, pruebas in PRUEBAS:
        lineas.append(f"\nGRUPO: {grupo}")
        lineas.append('─' * 62)
        for codigo, nombre, fn in pruebas:
            ok, detalle = fn(raw, proc)
            estado = "PASS" if ok else "FAIL"
            if ok:
                total_pass += 1
            else:
                total_fail += 1
            lineas.append(f"  [{estado}] {codigo} — {nombre}")
            lineas.append(f"         → {detalle}")

    total = total_pass + total_fail
    pct   = round(total_pass / total * 100, 1)

    lineas += [
        '',
        sep,
        f"  RESULTADO FINAL: {total_pass}/{total} pruebas APROBADAS ({pct}%)",
        sep,
    ]

    output = '\n'.join(lineas)
    print(output)

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f"\n  Reporte guardado en: {os.path.abspath(REPORT_PATH)}")

    return total_pass, total_fail, pct


if __name__ == '__main__':
    ejecutar()
