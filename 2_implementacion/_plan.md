# Plan de la Parte 2
## Objetivo
Convertir el modelo formulado en una implementacion PLE reproducible y una interfaz Streamlit minima.
## Asignaciones
### Implementacion (`2_implementacion/modelo.py`)
- Cargar y validar los siete archivos CSV de `data/` con pandas.
- Construir con PuLP el modelo binario y resolverlo con HiGHS.
- Devolver seleccion, asignacion por espacio y franja e indicadores; distinguir error de datos, solucion optima, inviabilidad y error del solver.
### Interfaz (`streamlit_app.py`)
- Leer los datos externos y permitir modificar presupuesto y pesos de los tres criterios.
- Normalizar los pesos efectivos para que sumen uno antes de resolver.
- Ejecutar el modelo y mostrar actividades, asistencia, valoracion, coste, presupuesto y calendario.
- Mostrar una tabla con actividad, categoria, duracion, asistencia, valoracion, coste,
  espacio y franjas temporales.
- Permitir descargar las actividades seleccionadas y el calendario en CSV.
- Incorporar una captura de la interfaz en el informe.
### Instrucciones (`README.md`)
- Documentar dependencias y ejecucion local de Streamlit.
- Documentar la compilacion del informe LaTeX.
