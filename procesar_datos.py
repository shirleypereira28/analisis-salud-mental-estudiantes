import pandas as pd
import numpy as np
import os

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
INPUT     = os.path.join(BASE_DIR, '..', 'data', 'encuesta_raw.csv')
OUTPUT    = os.path.join(BASE_DIR, '..', 'data', 'encuesta_procesada.csv')

# ── Pesos por dimensión ───────────────────────────────────────────────────────
PESOS = {
    'score_depresion': 0.25,
    'score_estres':    0.20,
    'score_ansiedad':  0.15,
    'score_sueno':     0.10,
    'score_apoyo':     0.10,
    'score_carga':     0.10,
    'score_habitos':   0.10,
}

# ── Ítems por dimensión ───────────────────────────────────────────────────────
DIMENSIONES = {
    'score_estres':    ['E1', 'E2', 'E3', 'E4', 'E5'],
    'score_ansiedad':  ['A1', 'A2', 'A3', 'A4', 'A5'],
    'score_carga':     ['C1', 'C2', 'C3', 'C4', 'C5'],
    'score_habitos':   ['H1', 'H2', 'H3', 'H4', 'H5'],
    'score_depresion': ['D1', 'D2', 'D3', 'D4', 'D5'],
    'score_sueno':     ['S1', 'S2', 'S3', 'S4', 'S5'],
    'score_apoyo':     ['AP1', 'AP2', 'AP3', 'AP4', 'AP5'],
}


def clasificar_riesgo(row):
    """Crítico si score_total >= 4.2 O si D4 >= 4, sin importar el score general."""
    if row['D4'] >= 4 or row['score_total'] >= 4.2:
        return 'Crítico'
    elif row['score_total'] >= 3.5:
        return 'Alto'
    elif row['score_total'] >= 2.5:
        return 'Medio'
    else:
        return 'Bajo'


def main():
    df = pd.read_csv(INPUT)
    print(f"Registros cargados : {len(df)}")

    # ── Calcular score por dimensión ──────────────────────────────────────────
    for score_col, items in DIMENSIONES.items():
        df[score_col] = df[items].mean(axis=1).round(2)

    # ── Calcular score total ponderado ────────────────────────────────────────
    df['score_total'] = sum(
        df[col] * peso for col, peso in PESOS.items()
    ).round(2)

    # ── Clasificar nivel de riesgo ────────────────────────────────────────────
    df['nivel_riesgo'] = df.apply(clasificar_riesgo, axis=1)

    # ── Exportar ──────────────────────────────────────────────────────────────
    df.to_csv(OUTPUT, index=False)
    print(f"Archivo procesado  : {os.path.abspath(OUTPUT)}")

    # ── Reporte de resultados ─────────────────────────────────────────────────
    print("\n── Distribución de riesgo ──────────────────────────────")
    dist = df['nivel_riesgo'].value_counts().reindex(['Bajo', 'Medio', 'Alto', 'Crítico'])
    for nivel, n in dist.items():
        pct = n / len(df) * 100
        print(f"  {nivel:<10} {n:>3} estudiantes  ({pct:.1f}%)")

    print("\n── Score promedio por dimensión ────────────────────────")
    for col in PESOS:
        print(f"  {col:<22} {df[col].mean():.2f}")

    print(f"\n  {'score_total':<22} {df['score_total'].mean():.2f}")
    print(f"  {'bienestar_global':<22} {df['B1'].mean():.2f} / 10")

    print("\n── Estudiantes con D4 >= 4 (bandera crítica) ───────────")
    d4_criticos = df[df['D4'] >= 4]
    print(f"  {len(d4_criticos)} estudiantes")

    print("\n── Score total promedio por nivel de riesgo ────────────")
    print(df.groupby('nivel_riesgo')['score_total'].mean().round(2).reindex(
        ['Bajo', 'Medio', 'Alto', 'Crítico']
    ).to_string())


if __name__ == '__main__':
    main()
