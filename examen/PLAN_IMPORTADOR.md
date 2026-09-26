# Plan del importador universal (cero fallos)

Objetivo de negocio: cualquier club sube su Excel o CSV y en menos de 5 minutos tiene sus socios, cuotas, pagos y reservas dentro, **sin datos basura y sin perder nada**.

## Principios (no negociables)
1. **Nunca se escribe nada sin vista previa y confirmación** del gerente.
2. **Todo o nada:** cada importación va en una sola transacción. Si falla algo, no queda nada a medias.
3. **Se puede deshacer:** cada importación tiene un `lote_id`, y el botón "Deshacer esta importación" borra solo ese lote.
4. **Sin duplicados:** se comprueba antes contra los datos ya existentes (teléfono normalizado y nombre sin tildes). Si hay posible duplicado, se pregunta.
5. **Mejor avisar que equivocarse:** si la confianza es baja, la app lo dice y pide ayuda. Nunca adivina en silencio.
6. **Errores y avisos:** un error bloquea la fila (por ejemplo, una fecha imposible). Un aviso deja importar (por ejemplo, un email vacío).
7. **RGPD:** solo se importan los campos necesarios. Las columnas de notas libres no se importan por defecto (pueden tener datos de salud). A Gemini solo le llegan cabeceras y ejemplos seudonimizados.
8. **Siempre por negocio_id**, sin excepción.

## Lectura robusta del archivo
- Formatos .xlsx, .xls y .csv. En CSV se detectan solos el separador (`;` `,` tabulador) y la codificación (UTF-8, UTF-8 con BOM, Windows-1252).
- Se leen **todas las hojas** y se descartan las que no tienen datos (como "Notas").
- Se detecta **la fila de cabecera real** (saltando títulos y filas vacías) y las cabeceras dobles combinadas.
- Se descartan filas vacías, filas de TOTAL o suma y duplicados exactos.
- Normalización:
  - Fechas: dd/mm/aaaa, dd/mm/aa, ISO, "1 de octubre", número de serie de Excel. Siempre día/mes, nunca mes/día.
  - Importes: "65,00 €", "65€", "65.5".
  - Sí/No: Sí/No, X, ✓/✗, TRUE/FALSE, 1/0, Pagado/Pendiente.
  - Teléfonos: +34, 0034, guiones y espacios. Se guardan 9 dígitos.
  - Nombres: "Apellidos, Nombre" pasa a "Nombre Apellidos". Apellidos repartidos en 2 columnas se unen.

## Cómo entiende la estructura (por escalones)
1. **¿Es lista o cuadrícula?** Lo decide un clasificador rápido por hoja.
2. **Listas:** mapeo de columnas a campos con reglas, sinónimos (incluido inglés) y un modelo pequeño sobre el contenido de la columna. Formato ancho (un mes por columna) se pasa a una fila por pago.
3. **Cuadrículas:** el modelo de celdas ya entrenado, más el lector que separa varios nombres por celda.
4. **Duda:** Gemini propone un mapeo a partir de la estructura seudonimizada, y se valida con reglas.
5. **Sigue la duda:** el gerente elige con desplegables. Se guarda como **perfil del club** y la próxima vez va solo.
6. **Imposible:** "Te lo importamos nosotros gratis" (servicio manual de Diego).

## Tareas (en orden, sustituyen a B3–B5)
- **B3. Lector robusto de archivos:** formatos, codificaciones, hojas, cabecera real, filas basura, normalizadores, con tests unitarios de cada normalizador. Hecho cuando: los 60 archivos de `examen/listas/` se leen sin excepción.
- **B4. Mapeo de listas:** socios y pagos, incluido el formato ancho. Hecho cuando: ≥ 98 % de filas correctas y 0 filas de más en `examen/listas/`.
- **B5. Lector de cuadrículas:** modelo de celdas y separación de nombres. Hecho cuando: ≥ 98 % de reservas correctas en `examen/cuadriculas/`.
- **B6. Página "Importar":** vista previa editable, errores y avisos, detección de duplicados, transacción, `lote_id` y "Deshacer". Pregunta antes de cambiar el esquema de la BD.
- **B7. Perfil por club y respaldo con Gemini** (solo si la confianza es baja; sin clave, la app sigue funcionando).
- **B8. Informe del examen:** script `examen/evaluar.py` que saca las 4 métricas del LEEME por familia. Se ejecuta en cada PR del importador.

## Métricas del negocio
- ≥ 80 % de archivos importados sin ayuda.
- 100 % importados con ayuda en menos de 5 minutos.
- **0 filas basura** importadas.
- Cada Excel real de un club (con permiso y anonimizado) pasa a ser un examen nuevo.
