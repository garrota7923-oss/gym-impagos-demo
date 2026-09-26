# Examen del importador (100 archivos) — NO usar para entrenar

Datos 100 % inventados. Sirven solo para **medir** el importador. No se entrena con ellos, y el generador no se ajusta a estos nombres ni a estos archivos concretos. Si algo falla, se añade al generador de entrenamiento el **tipo** de formato que falta.

## Contenido
- `listas/` (60): 10 familias × 6 archivos (socios y pagos). Hay .xlsx y .csv con separador `;`, `,` y tabulador, y con codificaciones Windows-1252, UTF-8 y UTF-8 con BOM.
- `cuadriculas/` (40): 4 familias × 10 archivos (horarios y reservas).
- `manifiesto.csv`: qué prueba cada archivo.
- `esperado_socios.csv`, `esperado_pagos.csv`, `esperado_reservas.csv`: las respuestas correctas.

## Reglas de corrección
- Nombres: sin distinguir mayúsculas ni tildes, espacios normalizados. En L09, "Apellidos, Nombre" debe acabar como "Nombre Apellidos".
- Teléfono: se comparan los últimos 9 dígitos.
- Importes: tolerancia de ±0,01.
- Fechas: exactas, en formato ISO. En los pagos de L06 no hay fecha: solo se compara el mes.
- `pagado_mes` se refiere a septiembre de 2026.
- `estado`: `baja` solo para las filas de la hoja "Bajas" de L08.
- NO deben importarse: filas de título, filas vacías, la fila TOTAL, el duplicado de L05 ni la hoja "Notas".
- Las "Observaciones" de L05 no se importan como datos del socio, porque pueden contener datos de salud.

## Métricas (por familia y en total)
1. **% de archivos importados sin ayuda** (todo correcto sin tocar nada). Objetivo: ≥ 80 %.
2. **% de filas correctas** (socios, pagos o reservas). Objetivo: ≥ 98 %.
3. **Filas inventadas o importadas de más** (títulos, totales, duplicados). Objetivo: **0**. Es el error más grave, porque mete basura en los datos del cliente.
4. **Archivos en los que la app avisa de que no está segura**: bien. Si se equivoca sin avisar: mal.
