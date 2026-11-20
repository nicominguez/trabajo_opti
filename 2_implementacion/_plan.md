# Plan de la Parte 2

## Objetivo

Convertir el modelo formulado en una implementacion PLE reproducible y una interfaz Streamlit minima.

## Asignaciones

- Cargar las tablas desde `data/` mediante pandas.
- Validar columnas, identificadores, valores numericos y referencias entre tablas.
- Construir el modelo binario con PuLP.
- Resolver el modelo y distinguir errores de datos, solucion optima y problema inviable.
- Permitir modificar el presupuesto y los pesos de asistencia, valoracion y numero de actividades.
- Mostrar seleccion, descartes, asignacion por espacio y franja, y los indicadores principales.
- Permitir descargar los resultados principales en CSV.
- Mantener el codigo corto y separado en `modelo.py` y `streamlit_app.py`.

## Entregables

- Motor de optimizacion en `2_implementacion/modelo.py`.
- Interfaz funcional en `streamlit_app.py`.
- Dependencias e instrucciones breves de ejecucion.
