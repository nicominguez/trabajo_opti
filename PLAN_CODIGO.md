# Plan técnico del código

## Objetivo

La aplicación debe resolver el problema de selección y asignación temporal del congreso, definido como un programa lineal entero mixto binario:

- Leer los datos desde CSV separados del código.
- Seleccionar como máximo una vez cada actividad; las obligatorias deben incluirse.
- Asignar cada actividad seleccionada a un espacio compatible, con capacidad suficiente y disponibilidad válida.
- Impedir solapamientos y cruces de día.
- Cumplir presupuesto e incompatibilidades temporales.
- Maximizar una combinación normalizada de asistencia, valoración y número de actividades.
- Mostrar solución óptima o inviabilidad.
- Mostrar actividades seleccionadas y descartadas, horario, coste, asistencia, valoración y número de actividades.
- Permitir modificar presupuesto y pesos y exportar los resultados a CSV.

Estos resultados son requisitos explícitos de las secciones 2, 6 y 7 del [documento de instrucciones](../instr_trabajo.pdf), páginas 1–3.

La instancia existente contiene 18 actividades, 3 espacios y 8 franjas; además, cumple los mínimos de actividades obligatorias, duración múltiple, restricciones de espacio y disponibilidad. Su formulación completa se conserva en [formulacion_modelo.md](formulacion_modelo.md), y el contexto e ampliación están documentados en [latex_informe_trabajo_opti.tex](latex_informe_trabajo_opti.tex).

## Implementación

Se propondrá un paquete Python mínimo con SciPy/HiGHS como motor MILP, Pandas para los CSV y Streamlit para la interfaz. SciPy reemplaza a PuLP sin introducir una capa de modelización adicional; Streamlit proporciona una interfaz web moderna con menos código que Tkinter.

```text
src/event_model/
  data.py       carga y validación de datos
  model.py      variables, objetivo y restricciones R1–R9
  reporting.py  indicadores, programación y exportación
  cli.py        ejecución reproducible por terminal
app.py          interfaz Streamlit
tests/          pruebas de datos, modelo y escenarios
data/           CSV de la instancia
requirements.txt
README.md
```

La salida se ejecutará mediante:

```bash
python -m event_model.cli --data-dir data --budget 6500 --weights 0.4 0.4 0.2 --output-dir resultados
streamlit run app.py
```

## Modelo

Variables binarias:

- $x_{i,e,t}=1$ si la actividad $i$ comienza en el espacio $e$ en la franja $t$.
- $y_i=1$ si la actividad $i$ se programa.

Función objetivo:

$$
\max \sum_i y_i
\left(
w_A\frac{a_i}{A_{\text{tot}}} +
w_V\frac{v_i}{V_{\text{tot}}} +
w_N\frac{1}{N}
\right)
$$

Restricciones a implementar exactamente según [formulacion_modelo.md](formulacion_modelo.md):

1. Relación $y_i=\sum x_{i,e,t}\leq1$.
2. $y_i=1$ para actividades obligatorias.
3. Compatibilidad entre actividad y espacio.
4. Capacidad suficiente.
5. Disponibilidad completa de actividad y espacio durante la duración.
6. Finalización dentro del horizonte y ausencia de cruces entre días.
7. Presupuesto.
8. Ocupación máxima de una actividad por espacio y franja.
9. Incompatibilidad temporal entre pares definidos.

La matriz se construirá con valores binarios explícitos, cotas lineales y nombres identificables para variables y restricciones. Los indicadores finales se recalcularán a partir de la solución, no únicamente a partir del resultado del solver.

## Entrada y salida

Se conservará el contrato de los siete CSV existentes. Los parámetros dinámicos serán presupuesto y pesos; el resto de datos se modificará exclusivamente en los archivos de entrada.

Se validarán: columnas e identificadores, valores numéricos positivos, pesos finitos con suma $1$, referencias válidas, disponibilidad no vacía y coherencia de los parámetros temporales. Se distinguirán:

- error de datos, que impide construir el modelo;
- problema inviable, que permite construir el modelo pero no obtener solución.

La interfaz contendrá configuración, estado e indicadores, tabla detallada y descarga CSV. La tabla de resultados tendrá, por actividad, selección, espacio, inicio, fin y parámetros económicos; el horario se presentará ordenado por espacio y franja.

## Verificación

Las pruebas cubrirán de forma independiente carga de datos, restricciones R1–R9, obligatoriedad, presupuesto, solapamientos, incompatibilidades, infeasibilidad y exportación.

Los tres escenarios conservarán presupuesto e instancia; únicamente cambiarán los pesos:

| Criterio prioritario | $w_A$ | $w_V$ | $w_N$ |
|---|---:|---:|---:|
| Asistencia | 1,0 | 0,0 | 0,0 |
| Valoración | 0,0 | 1,0 | 0,0 |
| Número de actividades | 0,1 | 0,1 | 0,8 |

Cada ejecución registrará coste, presupuesto, asistencia, valoración, número de actividades y diferencias de programación. Los resultados permitirán comprobar la convergencia entre instancias de datos y reproducir el análisis solicitado por el informe.
