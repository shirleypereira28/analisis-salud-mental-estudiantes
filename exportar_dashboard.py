import pandas as pd
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT    = os.path.join(BASE_DIR, '..', 'data', 'encuesta_procesada.csv')
OUTPUT   = os.path.join(BASE_DIR, '..', 'dashboard', 'index.html')

RIESGO_ORDER   = ['Bajo', 'Medio', 'Alto', 'Crítico']
COLORES_RIESGO = ['#4fc3f7', '#1976d2', '#0d47a1', '#37474f']

DIM_COLS   = ['score_estres', 'score_ansiedad', 'score_carga',
              'score_habitos', 'score_depresion', 'score_sueno', 'score_apoyo']
DIM_LABELS = ['Estrés', 'Ansiedad', 'Carga Académica',
              'Hábitos de Estudio', 'Depresión', 'Sueño', 'Apoyo Social']


def preparar_datos(df):
    total          = len(df)
    n_critico      = int((df['nivel_riesgo'] == 'Crítico').sum())
    pct_ar         = round(df['nivel_riesgo'].isin(['Alto', 'Crítico']).sum() / total * 100, 1)
    medias_dim     = [round(df[c].mean(), 2) for c in DIM_COLS]
    dim_mayor      = DIM_LABELS[medias_dim.index(max(medias_dim))]
    bienestar_prom = round(df['B1'].mean(), 1)

    # Chart 1 — Doughnut: distribución de riesgo
    c1 = {
        'labels': RIESGO_ORDER,
        'data':   df['nivel_riesgo'].value_counts()
                   .reindex(RIESGO_ORDER).fillna(0).astype(int).tolist(),
        'colors': COLORES_RIESGO,
    }

    # Chart 2 — Radar: score promedio por dimensión
    c2 = {'labels': DIM_LABELS, 'data': medias_dim}

    # Chart 3 — Stacked bar: riesgo por semestre
    sems = list(range(1, 11))
    c3 = {
        'labels': [str(s) for s in sems],
        'datasets': [
            {
                'label': nivel,
                'data': [int(((df['semestre'] == s) & (df['nivel_riesgo'] == nivel)).sum()) for s in sems],
                'backgroundColor': COLORES_RIESGO[i],
            }
            for i, nivel in enumerate(RIESGO_ORDER)
        ],
    }

    # Chart 4 — Scatter: bienestar global vs score total
    c4 = {
        'data': [{'x': round(float(r['score_total']), 2), 'y': int(r['B1']),
                  'riesgo': r['nivel_riesgo']}
                 for _, r in df.iterrows()],
        'colors': {n: c for n, c in zip(RIESGO_ORDER, COLORES_RIESGO)},
    }

    # Chart 5 — Horizontal bar: score por programa
    prog = df.groupby('programa')['score_total'].mean().round(2).sort_values()
    c5 = {'labels': prog.index.tolist(), 'data': prog.tolist()}

    # Chart 6 — Grouped bar: depresión y estrés por estrato
    estratos = sorted(df['estrato'].unique())
    c6 = {
        'labels':    [f'Estrato {e}' for e in estratos],
        'depresion': [round(df[df['estrato'] == e]['score_depresion'].mean(), 2) for e in estratos],
        'estres':    [round(df[df['estrato'] == e]['score_estres'].mean(), 2) for e in estratos],
    }

    # Chart 7 — Grouped bar: riesgo por modalidad
    mods = ['Presencial', 'Virtual', 'Híbrida']
    c7 = {
        'labels': mods,
        'datasets': [
            {
                'label': nivel,
                'data': [int(((df['modalidad'] == m) & (df['nivel_riesgo'] == nivel)).sum()) for m in mods],
                'backgroundColor': COLORES_RIESGO[i],
            }
            for i, nivel in enumerate(RIESGO_ORDER)
        ],
    }

    # Chart 8 — Grouped bar: % de cada nivel de riesgo por situación laboral
    n_trabaja    = (df['trabaja'] == 'Sí').sum()
    n_no_trabaja = (df['trabaja'] == 'No').sum()
    c8 = {
        'labels': RIESGO_ORDER,
        'trabaja':    [round(((df['trabaja'] == 'Sí') & (df['nivel_riesgo'] == n)).sum() / n_trabaja * 100, 1) for n in RIESGO_ORDER],
        'no_trabaja': [round(((df['trabaja'] == 'No') & (df['nivel_riesgo'] == n)).sum() / n_no_trabaja * 100, 1) for n in RIESGO_ORDER],
    }

    # Chart 9 — Smooth area: evolución de scores críticos por semestre
    sems = list(range(1, 11))
    def sem_avg(col, s):
        vals = df[df['semestre'] == s][col]
        return round(float(vals.mean()), 2) if len(vals) > 0 else None
    c9 = {
        'labels':    [str(s) for s in sems],
        'estres':    [sem_avg('score_estres', s)    for s in sems],
        'depresion': [sem_avg('score_depresion', s) for s in sems],
        'ansiedad':  [sem_avg('score_ansiedad', s)  for s in sems],
    }

    # Chart 10 — Radial rings: % de estudiantes en riesgo por dimensión (score >= 3.5)
    ring_cols   = ['score_estres', 'score_ansiedad', 'score_depresion',
                   'score_sueno', 'score_apoyo', 'score_carga', 'score_habitos']
    ring_labels = ['Estrés', 'Ansiedad', 'Depresión',
                   'Sueño', 'Apoyo Social', 'Carga Acad.', 'Hábitos']
    c10 = {
        'labels': ring_labels,
        'valores': [round((df[col] >= 3.5).sum() / len(df) * 100, 1) for col in ring_cols],
    }

    # Chart 11 — Gender infographic
    c11 = []
    for g in ['Masculino', 'Femenino', 'Otro']:
        gdf = df[df['genero'] == g]
        n   = len(gdf)
        if n == 0:
            continue
        medias = [gdf[col].mean() for col in DIM_COLS]
        c11.append({
            'genero':      g,
            'pct':         round(n / len(df) * 100, 1),
            'n':           n,
            'score':       round(float(gdf['score_total'].mean()), 2),
            'pct_riesgo':  round(gdf['nivel_riesgo'].isin(['Alto', 'Crítico']).sum() / n * 100, 1),
            'dim_mayor':   DIM_LABELS[medias.index(max(medias))],
        })

    # Chart 12 — Bar: score promedio de sueño por nivel de riesgo
    c12 = {
        'labels': RIESGO_ORDER,
        'data':   [round(float(df[df['nivel_riesgo'] == n]['score_sueno'].mean()), 2) for n in RIESGO_ORDER],
        'colors': COLORES_RIESGO,
    }

    # ── Conclusiones dinámicas ────────────────────────────────────────────────
    conc = {}

    # Género
    g_ar   = max(c11, key=lambda g: g['pct_riesgo'])
    g_sc   = max(c11, key=lambda g: g['score'])
    conc['genero'] = [
        f"El grupo '{g_ar['genero']}' concentra el mayor porcentaje en riesgo Alto/Crítico ({g_ar['pct_riesgo']}%).",
        f"'{g_sc['genero']}' presenta el score total promedio más alto ({g_sc['score']}), indicando mayor vulnerabilidad general.",
        "La dimensión más crítica varía por género: " + " · ".join(f"{g['genero']} → {g['dim_mayor']}" for g in c11) + ".",
    ]

    # Riesgo general
    pct_bajo    = round(c1['data'][0] / total * 100, 1)
    pct_critico = round(c1['data'][3] / total * 100, 1)
    dim_max_lbl = DIM_LABELS[c2['data'].index(max(c2['data']))]
    dim_min_lbl = DIM_LABELS[c2['data'].index(min(c2['data']))]
    conc['riesgo'] = [
        f"El {pct_critico}% de los estudiantes se encuentra en nivel Crítico, requiriendo intervención inmediata.",
        f"Solo el {pct_bajo}% está en riesgo Bajo, evidenciando un panorama de bienestar comprometido en la mayoría.",
        f"'{dim_max_lbl}' es la dimensión con mayor score promedio; '{dim_min_lbl}' la más protegida.",
    ]

    # Rings
    ring_pairs  = list(zip(c10['labels'], c10['valores']))
    ring_max    = max(ring_pairs, key=lambda x: x[1])
    ring_min    = min(ring_pairs, key=lambda x: x[1])
    over_50     = [l for l, v in ring_pairs if v >= 50]
    conc['rings'] = [
        f"'{ring_max[0]}' es la dimensión con más estudiantes en riesgo ({ring_max[1]}%).",
        f"'{ring_min[0]}' es la dimensión más protegida, con {ring_min[1]}% en riesgo.",
        (f"{len(over_50)} dimensión(es) superan el 50%: {', '.join(over_50)}." if over_50
         else "Ninguna dimensión supera el 50% de estudiantes en riesgo."),
    ]

    # Progresión académica
    sem_ar = {s: round(df[df['semestre'] == s]['nivel_riesgo'].isin(['Alto', 'Crítico']).sum()
                       / max(len(df[df['semestre'] == s]), 1) * 100, 1) for s in range(1, 11)}
    sem_peak  = max(sem_ar, key=sem_ar.get)
    sem_low   = min(sem_ar, key=sem_ar.get)
    sem_e_max = max((s for s in range(1, 11) if len(df[df['semestre'] == s]) > 0),
                    key=lambda s: df[df['semestre'] == s]['score_estres'].mean())
    conc['academica'] = [
        f"El semestre {sem_peak} concentra el mayor % de estudiantes en riesgo Alto/Crítico ({sem_ar[sem_peak]}%).",
        f"El estrés alcanza su pico en el semestre {sem_e_max}, coincidiendo con la etapa de mayor carga académica.",
        f"El semestre {sem_low} presenta la situación más favorable, con solo {sem_ar[sem_low]}% en riesgo elevado.",
    ]

    # Bienestar + Programa
    corr      = round(float(df['score_total'].corr(df['B1'])), 2)
    prog_hi   = c5['labels'][-1]; prog_hi_v = c5['data'][-1]
    prog_lo   = c5['labels'][0];  prog_lo_v = c5['data'][0]
    conc['bienestar_programa'] = [
        f"La correlación entre score total y bienestar global es {corr} — a mayor riesgo, menor bienestar percibido.",
        f"'{prog_hi}' tiene el score de riesgo más alto ({prog_hi_v}); '{prog_lo}' el más bajo ({prog_lo_v}).",
        f"La diferencia entre el programa más y menos vulnerable es de {round(prog_hi_v - prog_lo_v, 2)} puntos.",
    ]

    # Estrato + Modalidad
    est_dep  = df.groupby('estrato')['score_depresion'].mean()
    est_peak = int(est_dep.idxmax()); est_peak_v = round(float(est_dep.max()), 2)
    mod_crit = df[df['nivel_riesgo'] == 'Crítico']['modalidad'].value_counts()
    mod_peak = mod_crit.index[0] if len(mod_crit) > 0 else '—'
    conc['estrato_modalidad'] = [
        f"El estrato {est_peak} registra el score de depresión más alto ({est_peak_v}), reflejando mayor vulnerabilidad socioeconómica.",
        f"La modalidad '{mod_peak}' concentra la mayor cantidad de estudiantes en nivel Crítico.",
        "Los estratos 1 y 2 muestran consistentemente scores más elevados en depresión y estrés.",
    ]

    # Trabajo + Sueño
    pct_ar_w  = round(c8['trabaja'][2]    + c8['trabaja'][3], 1)
    pct_ar_nw = round(c8['no_trabaja'][2] + c8['no_trabaja'][3], 1)
    sl_bajo   = c12['data'][0]; sl_crit = c12['data'][3]
    conc['trabajo_sueno'] = [
        f"Estudiantes que trabajan tienen {pct_ar_w}% en riesgo Alto/Crítico vs {pct_ar_nw}% entre quienes no trabajan.",
        f"El score de sueño escala de {sl_bajo} (riesgo Bajo) a {sl_crit} (Crítico), evidenciando el impacto del descanso en la salud mental.",
        "El trabajo y el mal sueño se refuerzan mutuamente como factores de riesgo acumulados.",
    ]

    return {
        'kpis': {
            'total': total, 'n_critico': n_critico,
            'pct_alto_critico': pct_ar,
            'dim_mayor': dim_mayor,
            'bienestar_prom': bienestar_prom,
        },
        'c1': c1, 'c2': c2, 'c3': c3, 'c4': c4,
        'c5': c5, 'c6': c6, 'c7': c7, 'c8': c8,
        'c9': c9, 'c10': c10, 'c11': c11, 'c12': c12,
        'conc': conc,
    }


def generar_html(data):
    payload = json.dumps(data, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard — Bienestar Estudiantil</title>
<link rel="stylesheet" href="./styles.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>

<header>
  <h1>Sistema de Análisis de Bienestar y Salud Mental Estudiantil</h1>
  <p>Análisis descriptivo — 96 estudiantes universitarios · Semilla: 42</p>
</header>

<div class="container">

  <!-- Guía de lectura -->
  <div class="guide-card">
    <h2>¿Cómo leer este dashboard?</h2>
    <div class="guide-grid">

      <div class="guide-section">
        <h3>¿Qué es el Score?</h3>
        <p>Cada estudiante respondió 35 preguntas en una escala del <strong>1 al 5</strong>, agrupadas en 7 dimensiones de bienestar. El <strong>score</strong> de cada dimensión es el promedio de sus 5 respuestas.</p>
        <p style="margin-top:8px">El <strong>score total</strong> es un promedio <em>ponderado</em> de las 7 dimensiones. A mayor score, mayor nivel de riesgo.</p>
      </div>

      <div class="guide-section">
        <h3>Niveles de riesgo</h3>
        <ul>
          <li><span class="risk-badge badge-bajo">Bajo</span> Score &lt; 2.5 — bienestar estable</li>
          <li style="margin-top:4px"><span class="risk-badge badge-medio">Medio</span> Score 2.5–3.4 — señales de alerta leves</li>
          <li style="margin-top:4px"><span class="risk-badge badge-alto">Alto</span> Score 3.5–4.1 — requiere seguimiento</li>
          <li style="margin-top:4px"><span class="risk-badge badge-critico">Crítico</span> Score ≥ 4.2 o ideación activa — intervención inmediata</li>
        </ul>
      </div>

      <div class="guide-section">
        <h3>Las 7 dimensiones</h3>
        <ul>
          <li><strong>Estrés</strong> — tensión por carga académica</li>
          <li><strong>Ansiedad</strong> — preocupación y nerviosismo</li>
          <li><strong>Carga Académica</strong> — volumen y tiempo de estudio</li>
          <li><strong>Hábitos de Estudio</strong> — organización y constancia</li>
          <li><strong>Depresión</strong> — tristeza, desmotivación, ideación</li>
          <li><strong>Sueño</strong> — calidad y cantidad del descanso</li>
          <li><strong>Apoyo Social</strong> — red de apoyo percibida</li>
        </ul>
      </div>

      <div class="guide-section">
        <h3>Pesos del modelo</h3>
        <p>No todas las dimensiones pesan igual. Las de mayor impacto clínico tienen más peso en el score total:</p>
        <ul style="margin-top:8px">
          <li><strong>Depresión:</strong> 25%</li>
          <li><strong>Estrés:</strong> 20%</li>
          <li><strong>Ansiedad:</strong> 15%</li>
          <li>Resto: 10% c/u</li>
        </ul>
        <p style="margin-top:8px; color:#c62828; font-size:.78rem">⚠ Si un estudiante responde 4 o 5 en el ítem de ideación (D4), se clasifica automáticamente como <strong>Crítico</strong>.</p>
      </div>

    </div>
  </div>

  <!-- KPI cards -->
  <div class="kpi-grid" id="kpis"></div>

  <!-- ── Nivel 1: Vista general ──────────────────────────────────────── -->
  <div class="charts-grid">
    <div class="gender-card">
      <div class="chart-title">Composición demográfica por género</div>
      <div class="gender-grid" id="c11"></div>
    </div>

    <!-- ── Nivel 2: Resumen de riesgo ──────────────────────────────────── -->
    <div class="chart-card"><div class="chart-title">Distribución de niveles de riesgo</div><canvas id="c1"></canvas></div>
    <div class="chart-card"><div class="chart-title">Score promedio por dimensión</div><canvas id="c2"></canvas></div>
    <div class="conc-card" id="conc-riesgo"></div>

    <!-- ── Nivel 3: % en riesgo por dimensión ──────────────────────────── -->
    <div class="chart-card full">
      <div class="chart-title">% de estudiantes en riesgo por dimensión (score ≥ 3.5)</div>
      <div class="rings-grid" id="c10"></div>
    </div>
    <div class="conc-card" id="conc-rings"></div>

    <!-- ── Nivel 4: Progresión académica ───────────────────────────────── -->
    <div class="chart-card full"><div class="chart-title">Distribución de riesgo por semestre</div><canvas id="c3"></canvas></div>
    <div class="chart-card full"><div class="chart-title">Evolución de scores críticos por semestre</div><canvas id="c9"></canvas></div>
    <div class="conc-card" id="conc-academica"></div>

    <!-- ── Nivel 5: Segmentación y correlaciones ───────────────────────── -->
    <div class="chart-card"><div class="chart-title">Bienestar global vs Score total</div><canvas id="c4"></canvas></div>
    <div class="chart-card"><div class="chart-title">Score promedio por programa académico</div><canvas id="c5"></canvas></div>
    <div class="conc-card" id="conc-bienestar-programa"></div>
    <div class="chart-card"><div class="chart-title">Depresión y estrés por estrato socioeconómico</div><canvas id="c6"></canvas></div>
    <div class="chart-card"><div class="chart-title">Nivel de riesgo por modalidad de estudio</div><canvas id="c7"></canvas></div>
    <div class="conc-card" id="conc-estrato-modalidad"></div>
    <div class="chart-card"><div class="chart-title">Nivel de riesgo: trabaja vs no trabaja</div><canvas id="c8"></canvas></div>
    <div class="chart-card"><div class="chart-title">Score de sueño promedio por nivel de riesgo</div><canvas id="c12"></canvas></div>
    <div class="conc-card" id="conc-trabajo-sueno"></div>
  </div>

</div>

<footer>Prototipo funcional TRL5 · Datos simulados con fines académicos · seed=42</footer>

<script>
const D = {payload};

// ── KPI cards ────────────────────────────────────────────────────────────────
const kpiEl = document.getElementById('kpis');
const kpis = [
  {{ label: 'Total estudiantes',     value: D.kpis.total,             sub: 'registros analizados',        cls: 'success' }},
  {{ label: 'En riesgo Alto o Crítico', value: D.kpis.pct_alto_critico + '%', sub: D.kpis.n_critico + ' en nivel Crítico', cls: 'warning' }},
  {{ label: 'Dimensión más crítica', value: D.kpis.dim_mayor,         sub: 'mayor score promedio',        cls: '' }},
  {{ label: 'Bienestar global prom.',value: D.kpis.bienestar_prom + '/10', sub: 'escala 1–10',            cls: 'critico' }},
];
kpis.forEach(k => {{
  kpiEl.innerHTML += `<div class="kpi-card ${{k.cls}}">
    <div class="kpi-label">${{k.label}}</div>
    <div class="kpi-value">${{k.value}}</div>
    <div class="kpi-sub">${{k.sub}}</div>
  </div>`;
}});

// ── C1: Doughnut ─────────────────────────────────────────────────────────────
new Chart(document.getElementById('c1'), {{
  type: 'doughnut',
  data: {{
    labels: D.c1.labels,
    datasets: [{{ data: D.c1.data, backgroundColor: D.c1.colors, borderWidth: 2, borderColor: '#fff' }}]
  }},
  options: {{
    plugins: {{ legend: {{ position: 'bottom' }} }},
    cutout: '60%',
  }}
}});

// ── C2: Radar ────────────────────────────────────────────────────────────────
new Chart(document.getElementById('c2'), {{
  type: 'radar',
  data: {{
    labels: D.c2.labels,
    datasets: [{{
      label: 'Score promedio',
      data: D.c2.data,
      backgroundColor: 'rgba(25,118,210,.15)',
      borderColor: '#1976d2',
      pointBackgroundColor: '#1976d2',
      borderWidth: 2,
    }}]
  }},
  options: {{
    scales: {{ r: {{ min: 1, max: 5, ticks: {{ stepSize: 1 }} }} }},
    plugins: {{ legend: {{ display: false }} }},
  }}
}});

// ── C3: Stacked bar semestre ──────────────────────────────────────────────────
new Chart(document.getElementById('c3'), {{
  type: 'bar',
  data: {{ labels: D.c3.labels, datasets: D.c3.datasets }},
  options: {{
    scales: {{ x: {{ stacked: true }}, y: {{ stacked: true, ticks: {{ stepSize: 1 }} }} }},
    plugins: {{ legend: {{ position: 'bottom' }} }},
  }}
}});

// ── C4: Scatter ───────────────────────────────────────────────────────────────
const scatterColors = D.c4.data.map(p => D.c4.colors[p.riesgo]);
new Chart(document.getElementById('c4'), {{
  type: 'scatter',
  data: {{
    datasets: [{{
      label: 'Estudiantes',
      data: D.c4.data.map(p => ({{ x: p.x, y: p.y }})),
      backgroundColor: scatterColors,
      pointRadius: 5,
      pointHoverRadius: 7,
    }}]
  }},
  options: {{
    scales: {{
      x: {{ title: {{ display: true, text: 'Score total ponderado' }} }},
      y: {{ title: {{ display: true, text: 'Bienestar global (1-10)' }}, min: 1, max: 10 }},
    }},
    plugins: {{ legend: {{ display: false }} }},
  }}
}});

// ── C5: Horizontal bar programas ──────────────────────────────────────────────
new Chart(document.getElementById('c5'), {{
  type: 'bar',
  data: {{
    labels: D.c5.labels,
    datasets: [{{
      label: 'Score promedio',
      data: D.c5.data,
      backgroundColor: '#1976d2',
      borderRadius: 4,
    }}]
  }},
  options: {{
    indexAxis: 'y',
    scales: {{ x: {{ min: 1, max: 5 }} }},
    plugins: {{ legend: {{ display: false }} }},
  }}
}});

// ── C6: Grouped bar estrato ───────────────────────────────────────────────────
new Chart(document.getElementById('c6'), {{
  type: 'bar',
  data: {{
    labels: D.c6.labels,
    datasets: [
      {{ label: 'Depresión', data: D.c6.depresion, backgroundColor: '#0d47a1', borderRadius: 4 }},
      {{ label: 'Estrés',    data: D.c6.estres,    backgroundColor: '#4fc3f7', borderRadius: 4 }},
    ]
  }},
  options: {{
    scales: {{ y: {{ min: 1, max: 5 }} }},
    plugins: {{ legend: {{ position: 'bottom' }} }},
  }}
}});

// ── C7: Grouped bar modalidad ─────────────────────────────────────────────────
new Chart(document.getElementById('c7'), {{
  type: 'bar',
  data: {{ labels: D.c7.labels, datasets: D.c7.datasets }},
  options: {{
    scales: {{ y: {{ ticks: {{ stepSize: 1 }} }} }},
    plugins: {{ legend: {{ position: 'bottom' }} }},
  }}
}});

// ── C8: Grouped bar trabaja ───────────────────────────────────────────────────
new Chart(document.getElementById('c8'), {{
  type: 'bar',
  data: {{
    labels: D.c8.labels,
    datasets: [
      {{ label: 'Trabaja',    data: D.c8.trabaja,    backgroundColor: '#0d47a1', borderRadius: 4 }},
      {{ label: 'No trabaja', data: D.c8.no_trabaja, backgroundColor: '#90caf9', borderRadius: 4 }},
    ]
  }},
  options: {{
    scales: {{
      y: {{
        min: 0, max: 100,
        ticks: {{ callback: v => v + '%' }},
      }},
    }},
    plugins: {{
      legend: {{ position: 'bottom' }},
      tooltip: {{
        callbacks: {{
          label: ctx => ` ${{ctx.dataset.label}}: ${{ctx.parsed.y}}%`,
        }},
      }},
    }},
  }}
}});

// ── Conclusiones ─────────────────────────────────────────────────────────────
function renderConc(id, bullets) {{
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = '<ul>' + bullets.map(b => `<li>${{b}}</li>`).join('') + '</ul>';
}}
renderConc('conc-riesgo',              D.conc.riesgo);
renderConc('conc-rings',               D.conc.rings);
renderConc('conc-academica',           D.conc.academica);
renderConc('conc-bienestar-programa',  D.conc.bienestar_programa);
renderConc('conc-estrato-modalidad',   D.conc.estrato_modalidad);
renderConc('conc-trabajo-sueno',       D.conc.trabajo_sueno);

// También para género (debajo de la gender card, renderizado aparte)
const gCard = document.querySelector('.gender-card');
if (gCard) {{
  const concDiv = document.createElement('div');
  concDiv.className = 'conc-card';
  concDiv.style.marginTop = '12px';
  concDiv.innerHTML = '<ul>' + D.conc.genero.map(b => `<li>${{b}}</li>`).join('') + '</ul>';
  gCard.appendChild(concDiv);
}}

// ── C11: Gender infographic ───────────────────────────────────────────────────
const GENDER_ICONS = {{
  Masculino: `<svg width="64" height="120" viewBox="0 0 64 120" fill="none">
    <circle cx="32" cy="16" r="13" fill="#90caf9"/>
    <rect x="20" y="32" width="24" height="36" rx="5" fill="#90caf9"/>
    <rect x="8"  y="32" width="11" height="9"  rx="4" fill="#90caf9"/>
    <rect x="45" y="32" width="11" height="9"  rx="4" fill="#90caf9"/>
    <rect x="20" y="65" width="10" height="36" rx="4" fill="#90caf9"/>
    <rect x="34" y="65" width="10" height="36" rx="4" fill="#90caf9"/>
  </svg>`,
  Femenino: `<svg width="64" height="120" viewBox="0 0 64 120" fill="none">
    <circle cx="32" cy="16" r="13" fill="#e3f2fd"/>
    <rect x="22" y="32" width="20" height="18" rx="4" fill="#e3f2fd"/>
    <polygon points="32,48 8,100 56,100" fill="#e3f2fd"/>
    <rect x="8"  y="32" width="13" height="9" rx="4" fill="#e3f2fd"/>
    <rect x="43" y="32" width="13" height="9" rx="4" fill="#e3f2fd"/>
    <rect x="19" y="98" width="10" height="20" rx="4" fill="#e3f2fd"/>
    <rect x="35" y="98" width="10" height="20" rx="4" fill="#e3f2fd"/>
  </svg>`,
  Otro: `<svg width="64" height="120" viewBox="0 0 64 120" fill="none">
    <circle cx="32" cy="16" r="13" fill="#b3e5fc"/>
    <rect x="20" y="32" width="24" height="30" rx="5" fill="#b3e5fc"/>
    <polygon points="32,60 14,95 50,95" fill="#b3e5fc"/>
    <rect x="8"  y="32" width="11" height="9" rx="4" fill="#b3e5fc"/>
    <rect x="45" y="32" width="11" height="9" rx="4" fill="#b3e5fc"/>
    <rect x="20" y="93" width="10" height="24" rx="4" fill="#b3e5fc"/>
    <rect x="34" y="93" width="10" height="24" rx="4" fill="#b3e5fc"/>
  </svg>`,
}};

const g11 = document.getElementById('c11');
D.c11.forEach(g => {{
  g11.innerHTML += `
    <div class="gender-item">
      <div class="gender-icon">${{GENDER_ICONS[g.genero] || ''}}</div>
      <div class="gender-info">
        <div class="gender-pct">${{g.pct}}%</div>
        <div class="gender-name">${{g.genero}}</div>
        <div class="gender-stat">
          <strong>${{g.n}}</strong> estudiantes<br>
          Score promedio: <strong>${{g.score}}</strong><br>
          En riesgo Alto/Crítico: <strong>${{g.pct_riesgo}}%</strong><br>
          Dimensión más crítica: <strong>${{g.dim_mayor}}</strong>
        </div>
      </div>
    </div>`;
}});

// ── C12: Bar — score sueño por nivel de riesgo ───────────────────────────────
new Chart(document.getElementById('c12'), {{
  type: 'bar',
  data: {{
    labels: D.c12.labels,
    datasets: [{{
      label: 'Score sueño promedio',
      data: D.c12.data,
      backgroundColor: D.c12.colors,
      borderRadius: 6,
    }}]
  }},
  options: {{
    scales: {{
      y: {{ min: 1, max: 5, title: {{ display: true, text: 'Score promedio (1–5)' }} }},
    }},
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{ callbacks: {{ label: ctx => ` Score: ${{ctx.parsed.y}}` }} }},
    }},
  }}
}});

// ── C9: Smooth area — evolución scores por semestre ───────────────────────────
new Chart(document.getElementById('c9'), {{
  type: 'line',
  data: {{
    labels: D.c9.labels,
    datasets: [
      {{
        label: 'Estrés',
        data: D.c9.estres,
        borderColor: '#0d47a1',
        backgroundColor: 'rgba(13,71,161,.12)',
        fill: true, tension: 0.4, borderWidth: 2.5,
        pointBackgroundColor: '#0d47a1', pointRadius: 4,
      }},
      {{
        label: 'Depresión',
        data: D.c9.depresion,
        borderColor: '#1976d2',
        backgroundColor: 'rgba(25,118,210,.10)',
        fill: true, tension: 0.4, borderWidth: 2.5,
        pointBackgroundColor: '#1976d2', pointRadius: 4,
      }},
      {{
        label: 'Ansiedad',
        data: D.c9.ansiedad,
        borderColor: '#4fc3f7',
        backgroundColor: 'rgba(79,195,247,.10)',
        fill: true, tension: 0.4, borderWidth: 2.5,
        pointBackgroundColor: '#4fc3f7', pointRadius: 4,
      }},
    ]
  }},
  options: {{
    scales: {{
      y: {{ min: 1, max: 5, title: {{ display: true, text: 'Score promedio' }} }},
      x: {{ title: {{ display: true, text: 'Semestre' }} }},
    }},
    plugins: {{ legend: {{ position: 'bottom' }} }},
    spanGaps: true,
  }}
}});

// ── C10: Radial rings — % en riesgo por dimensión ─────────────────────────────
const ringColors = ['#0d47a1','#1565c0','#1976d2','#1e88e5','#42a5f5','#64b5f6','#90caf9'];
const R = 37, CIRC = 2 * Math.PI * R;
const container = document.getElementById('c10');
D.c10.labels.forEach((label, i) => {{
  const pct = D.c10.valores[i];
  const offset = CIRC * (1 - pct / 100);
  container.innerHTML += `
    <div class="ring-item">
      <div class="ring-wrap">
        <svg viewBox="0 0 90 90">
          <circle class="ring-track" cx="45" cy="45" r="${{R}}"/>
          <circle class="ring-fill" cx="45" cy="45" r="${{R}}"
            stroke="${{ringColors[i]}}"
            stroke-dasharray="${{CIRC.toFixed(1)}}"
            stroke-dashoffset="${{offset.toFixed(1)}}"/>
        </svg>
        <div class="ring-label">${{pct}}%</div>
      </div>
      <div class="ring-name">${{label}}</div>
    </div>`;
}});
</script>
</body>
</html>"""


def main():
    df   = pd.read_csv(INPUT)
    data = preparar_datos(df)
    html = generar_html(data)

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Dashboard generado : {os.path.abspath(OUTPUT)}")
    print(f"Tamaño             : {os.path.getsize(OUTPUT) / 1024:.1f} KB")


if __name__ == '__main__':
    main()
