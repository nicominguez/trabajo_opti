# Formulacion del modelo (texto plano, independiente de la herramienta)

Valido para Lindo, Lingo o PuLP: cambia la sintaxis, no el modelo.
Version: sin minimos por categoria (R10 eliminada). La ampliacion es R9 (incompatibilidades).

## 1. Conjuntos

- I : actividades (id 1..18, ver actividades.csv)
- E : espacios (E1, E2, E3, ver espacios.csv)
- T : franjas 1..F, con F = num_franjas (parametros.csv). Cada dia tiene franjas_por_dia franjas (con los datos actuales: F = 8, 4 por dia: dia 1 = franjas 1-4, dia 2 = franjas 5-8)
- O : subconjunto de I con obligatoria = 1
- P : pares (i,j) de actividades incompatibles (incompatibilidades.csv)

## 2. Parametros (y de que archivo salen)

| Parametro | Significado | Archivo |
|---|---|---|
| d_i | duracion en franjas | actividades.csv (duracion) |
| a_i | asistencia esperada | actividades.csv (asistencia) |
| v_i | valoracion | actividades.csv (valoracion) |
| c_i | coste | actividades.csv (coste) |
| cap_e | capacidad del espacio e | espacios.csv (capacidad) |
| comp(i,e) | 1 si i es compatible con e, 0 si no | compat_espacios.csv (1 si existe la fila) |
| dispA(i,s) | 1 si i puede ocupar la franja s | disp_actividades.csv (1 si existe la fila; sin fila = 0) |
| dispE(e,s) | 1 si e esta disponible en la franja s | disp_espacios.csv (1 si existe la fila) |
| F | numero de franjas | parametros.csv (num_franjas) |
| FD | franjas por dia | parametros.csv (franjas_por_dia) |
| dia(t) | dia de la franja t = techo(t / FD) | calculado |
| B | presupuesto | parametros.csv (presupuesto) |
| w_A, w_V, w_N | pesos de asistencia, valoracion y numero de actividades (suman 1) | parametros.csv |
| N | numero total de actividades | calculado: |I| |
| A_tot | suma de a_i sobre todas las actividades | calculado |
| V_tot | suma de v_i sobre todas las actividades | calculado |

## 3. Variables (binarias)

- x(i,e,t) = 1 si la actividad i empieza en el espacio e en la franja t; 0 si no
- y(i) = 1 si la actividad i se programa; 0 si no

x se define para TODAS las combinaciones (i,e,t). Las reglas de compatibilidad, capacidad, disponibilidad y horario se imponen como restricciones (R3 a R6).

## 4. Funcion objetivo

```
max  suma sobre i en I de:  y(i) * ( w_A * a_i / A_tot + w_V * v_i / V_tot + w_N / N )
```

## 5. Restricciones

```
R1  y(i) = suma sobre e en E y t en T de x(i,e,t)        para todo i
    y(i) <= 1                                             para todo i

R2  y(i) = 1                                              para todo i en O

R3  x(i,e,t) = 0        si comp(i,e) = 0

R4  x(i,e,t) = 0        si a_i > cap_e

R5  x(i,e,t) <= dispA(i,s) * dispE(e,s)
    para cada s desde t hasta t + d_i - 1                 (todas las franjas que ocupa)

R6  x(i,e,t) = 0        si t + d_i - 1 > F
    x(i,e,t) = 0        si dia(t) != dia(t + d_i - 1)     (no cruzar de dia)

R7  suma sobre i en I de c_i * y(i) <= B

R8  para cada e en E y cada s en T:
    suma sobre i en I, y sobre t desde max(1, s - d_i + 1) hasta s, de x(i,e,t) <= 1

R9  para cada par (i,j) en P y cada s en T:
    [ suma sobre e en E y t desde max(1, s - d_i + 1) hasta s de x(i,e,t) ]
  + [ suma sobre e en E y t desde max(1, s - d_j + 1) hasta s de x(j,e,t) ] <= 1
```

## 6. Que significa cada restriccion

- R1: cada actividad se programa como maximo una vez.
- R2: las obligatorias siempre se programan.
- R3: solo espacios compatibles.
- R4: la asistencia cabe en el espacio.
- R5: actividad y espacio estan disponibles en todas las franjas que ocupa, no solo en la de inicio.
- R6: no terminar despues de la ultima franja F ni cruzar de un dia a otro.
- R7: el coste total no supera el presupuesto.
- R8: un espacio no tiene dos actividades a la vez. Una actividad que empieza en t ocupa t, t+1, ..., t+d_i-1.
- R9 (ampliacion): dos actividades incompatibles no coinciden en ninguna franja, aunque esten en espacios distintos.

## 7. Notas para programarlo

- En R8 y R9, t nunca baja de 1: hay que saltarse los valores que no existan.
- Sin fila en disp_actividades.csv = sin disponibilidad. El validador debe avisar si una actividad no tiene ninguna fila.
- Los pesos w_A, w_V y w_N deben sumar 1: el validador debe comprobarlo.
- Los escenarios del informe usan exactamente estos pesos (w_A, w_V, w_N): asistencia 1 / 0 / 0; valoracion 0 / 1 / 0; numero de actividades 0,1 / 0,1 / 0,8. Con presupuesto 6.500 salen programaciones distintas (9, 12 y 12 actividades). El archivo parametros.csv trae los pesos por defecto 0,4 / 0,4 / 0,2.
- El numero de franjas y las franjas por dia salen de parametros.csv (num_franjas, franjas_por_dia): no deben estar fijos en el codigo (ni el 8 ni el 4).
- "Problema inviable" es un resultado valido: la app debe indicarlo, no fallar.
- R3 a R6 se pueden implementar fijando x(i,e,t) = 0 o con la desigualdad equivalente. Mantener las cuatro reglas visibles en el codigo, no filtradas antes de crear variables, para que la formulacion del informe coincida con el codigo.
- La columna "categoria" de actividades.csv ya no interviene en el modelo; se mantiene en el archivo como dato descriptivo.
