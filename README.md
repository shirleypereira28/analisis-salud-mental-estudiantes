
# Sistema de Análisis y Monitoreo del Bienestar y Salud Mental Estudiantil

Prototipo funcional (TRL5) para la identificación temprana de factores de riesgo en la salud mental de estudiantes universitarios, mediante simulación de encuestas, análisis estadístico en Python y dashboard HTML interactivo con conclusiones dinámicas.

---

## Estructura del proyecto

```
Simulacion/
├── data/
│   ├── encuesta_raw.csv          # 96 registros simulados (respuestas crudas)
│   ├── encuesta_procesada.csv    # Datos con scores y nivel de riesgo calculados
│   └── reporte_pruebas.txt       # Resultado de la suite de 20 pruebas estructuradas
├── src/
│   ├── generar_datos.py          # Genera la base de datos simulada
│   ├── procesar_datos.py         # Calcula scores y clasifica riesgo
│   ├── exportar_dashboard.py     # Genera el dashboard HTML autocontenido
│   ├── pruebas_sistema.py        # Suite de 20 pruebas estructuradas
│   └── exportar_informe_pdf.py   # Genera el PDF de validación para el informe
├── dashboard/
│   └── index.html                # Dashboard interactivo (sin servidor requerido)
├── docs/
│   ├── instrumento_encuesta.md   # Definición formal del instrumento
│   ├── trazabilidad_objetivos.md # Matriz de trazabilidad objetivos–evidencias
│   └── anexo_validacion.pdf      # Anexo de validación para el informe
├── SPEC.md                       # Especificación técnica completa
└── README.md
```

---

## Requisitos

- Python 3.8 o superior
- pip

### Instalación de dependencias

```bash
pip install numpy pandas reportlab
```

---

## Ejecución paso a paso

Los scripts deben ejecutarse en orden desde la raíz del proyecto.

### Paso 1 — Generar datos simulados

```bash
python src/generar_datos.py
```

**Salida:** `data/encuesta_raw.csv`

Genera 96 registros con respuestas simuladas sobre 7 dimensiones de bienestar (35 ítems Likert 1–5) más 8 variables demográficas. Usa semilla fija `42` para reproducibilidad total.

---

### Paso 2 — Procesar datos y clasificar riesgo

```bash
python src/procesar_datos.py
```

**Salida:** `data/encuesta_procesada.csv`

Calcula el score por dimensión y el score total ponderado. Clasifica cada estudiante en uno de cuatro niveles de riesgo.

**Pesos del modelo:**

| Dimensión | Peso |
|---|---|
| Depresión | 25% |
| Estrés | 20% |
| Ansiedad | 15% |
| Sueño | 10% |
| Apoyo Social | 10% |
| Carga Académica | 10% |
| Hábitos de Estudio | 10% |

**Clasificación de riesgo:**

| Condición | Nivel |
|---|---|
| score_total < 2.5 | Bajo |
| 2.5 ≤ score_total < 3.5 | Medio |
| 3.5 ≤ score_total < 4.2 | Alto |
| score_total ≥ 4.2 **o** D4 ≥ 4 | Crítico |

> El ítem D4 ("pensamientos de hacerme daño") activa Riesgo Crítico de forma independiente al score general.

---

### Paso 3 — Ejecutar pruebas estructuradas

```bash
python src/pruebas_sistema.py
```

**Salida:** `data/reporte_pruebas.txt`

Ejecuta 20 casos de prueba en 4 grupos: integridad de datos, cálculo de scores, clasificación de riesgo y validación estadística. Imprime el resultado por consola y guarda el reporte completo.

**Resultado esperado:** 20/20 pruebas APROBADAS (100%)

---

### Paso 4 — Generar dashboard HTML

```bash
python src/exportar_dashboard.py
```

**Salida:** `dashboard/index.html`

Genera un archivo HTML autocontenido con 12 visualizaciones interactivas, 4 tarjetas KPI, conclusiones dinámicas y una sección de **Validación del Sistema** con métricas de desempeño y tabla de trazabilidad.

```bash
# macOS
open dashboard/index.html

# Linux
xdg-open dashboard/index.html

# Windows
start dashboard/index.html
```

---

### Paso 5 — Exportar PDF de validación

```bash
python src/exportar_informe_pdf.py
```

**Salida:** `docs/anexo_validacion.pdf`

Genera un PDF de 4 páginas para adjuntar al informe académico:

| Página | Contenido |
|---|---|
| 1 | Portada, ficha del proyecto y contexto del feedback atendido |
| 2 | Suite de 20 pruebas estructuradas con resultados por caso |
| 3 | Métricas cuantificables de desempeño (integridad, modelo, D4, distribución) |
| 4 | Matriz de trazabilidad: objetivos específicos → entregables → evidencias |

---

## Instrumento de encuesta

El instrumento completo está documentado en `docs/instrumento_encuesta.md`.

| Sección | Ítems |
|---|---|
| Datos demográficos | 8 |
| Estrés (E1–E5) | 5 |
| Ansiedad (A1–A5) | 5 |
| Carga Académica (C1–C5) | 5 |
| Hábitos de Estudio (H1–H5) | 5 |
| Depresión (D1–D5) | 5 |
| Sueño (S1–S5) | 5 |
| Apoyo Social (AP1–AP5) | 5 |
| Bienestar global (B1) | 1 |
| **Total** | **44** |

---

## Dashboard — Visualizaciones

| Nivel | Contenido |
|---|---|
| Guía | Card explicativa de scores, niveles de riesgo, dimensiones y pesos |
| KPIs | Total estudiantes · % en riesgo Alto/Crítico · dimensión más crítica · bienestar global |
| 1 — Vista general | Infografía de género con íconos SVG, porcentajes y stats clave |
| 2 — Resumen de riesgo | Doughnut (distribución) + Radar (score por dimensión) |
| 3 — % en riesgo | Radial progress rings por las 7 dimensiones |
| 4 — Progresión académica | Stacked bar por semestre + Smooth area chart de scores críticos |
| 5 — Segmentación | Scatter · Programa · Estrato · Modalidad · Trabajo · Sueño |
| 6 — Validación | Métricas de desempeño del sistema + tabla de trazabilidad por objetivo |

---

## Validación del prototipo

| Artefacto | Descripción |
|---|---|
| `src/pruebas_sistema.py` | 20 casos de prueba en 4 grupos · 100% aprobados |
| `data/reporte_pruebas.txt` | Reporte detallado con resultado por caso y timestamp |
| `docs/trazabilidad_objetivos.md` | Matriz formal objetivo → entregable → evidencia cuantificable |
| `docs/anexo_validacion.pdf` | PDF de 4 páginas para adjuntar al informe académico |

---

## Metodología

- **Enfoque:** Cuantitativo — alcance descriptivo
- **Marco:** CDIO — Metodología: Scrum
- **Instrumento:** Encuesta estructurada, 7 dimensiones, escalas Likert 1–5
- **Procesamiento:** Python — numpy, pandas
- **Visualización:** Dashboard HTML autocontenido con Chart.js 4.4
- **Exportación:** PDF generado con reportlab
- **Datos:** 96 registros simulados con correlaciones contextuales realistas (seed = 42)
- **Nivel TRL:** 5 — Prototipo funcional validado en entorno relevante
