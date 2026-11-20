# Especificacion tecnica del modelo

Esta especificacion define el modelo de forma independiente de la herramienta. Su sintaxis cambia segun el solver, pero no su formulacion.

## Conjuntos, parametros y variables

| Tipo | Simbolo | Definicion | Fuente |
|---|---|---|---|
| Conjunto | $I$ | Actividades | `actividades.csv` |
| Conjunto | $E$ | Espacios | `espacios.csv` |
| Conjunto | $T=\{1,\ldots,F\}$ | Franjas | `parametros.csv` |
| Conjunto | $O\subseteq I$ | Actividades obligatorias | `actividades.csv` |
| Conjunto | $P$ | Pares de actividades incompatibles | `incompatibilidades.csv` |
| Parametro | $d_i$ | Duracion de $i$ en franjas | `actividades.csv` |
| Parametro | $a_i$ | Asistencia esperada de $i$ | `actividades.csv` |
| Parametro | $v_i$ | Valoracion de $i$ | `actividades.csv` |
| Parametro | $c_i$ | Coste de $i$ | `actividades.csv` |
| Parametro | $\mathrm{cap}_e$ | Capacidad de $e$ | `espacios.csv` |
| Parametro | $\mathrm{comp}(i,e)$ | $1$ si $i$ es compatible con $e$ | `compat_espacios.csv` |
| Parametro | $\mathrm{dispA}(i,s)$ | $1$ si $i$ esta disponible en $s$ | `disp_actividades.csv` |
| Parametro | $\mathrm{dispE}(e,s)$ | $1$ si $e$ esta disponible en $s$ | `disp_espacios.csv` |
| Parametro | $F$ | Numero de franjas | `parametros.csv` |
| Parametro | $FD$ | Franjas por dia | `parametros.csv` |
| Parametro | $\mathrm{dia}(t)=\lceil t/FD\rceil$ | Dia de la franja $t$ | Calculado |
| Parametro | $B$ | Presupuesto | `parametros.csv` |
| Parametro | $w_A,w_V,w_N$ | Pesos de los tres criterios | `parametros.csv` |
| Parametro | $N=\lvert I\rvert$ | Numero de actividades | Calculado |
| Parametro | $A_{\mathrm{tot}}=\sum_{i\in I}a_i$ | Suma de asistencias | Calculado |
| Parametro | $V_{\mathrm{tot}}=\sum_{i\in I}v_i$ | Suma de valoraciones | Calculado |
| Variable | $y_i$ | $1$ si $i$ se programa | Binaria |
| Variable | $x_{i,e,t}$ | $1$ si $i$ empieza en $e$ en $t$ | Binaria |

## Restricciones

**$R_1$.** Seleccion y relacion entre $y_i$ y $x_{i,e,t}$:
$$
y_i=\sum_{e\in E}\sum_{t\in T}x_{i,e,t}\leq 1
\qquad \forall i\in I
$$

**$R_2$.** Las actividades obligatorias se programan:
$$
y_i=1 \qquad \forall i\in O
$$

**$R_3$.** Solo se asignan espacios compatibles:
$$
x_{i,e,t}=0 \qquad \text{si } \mathrm{comp}(i,e)=0
$$

**$R_4$.** La asistencia debe caber en la capacidad:
$$
x_{i,e,t}=0 \qquad \text{si } a_i>\mathrm{cap}_e
$$

**$R_5$.** Actividad y espacio deben estar disponibles durante toda la duracion:
$$
x_{i,e,t}\leq
\mathrm{dispA}(i,s)\,\mathrm{dispE}(e,s)
\qquad \forall s\in\{t,\ldots,t+d_i-1\}
$$

**$R_6$.** No se termina despues del horizonte ni se cruza de dia:
$$
x_{i,e,t}=0
\qquad \text{si } t+d_i-1>F
\ \text{o}\ \mathrm{dia}(t)\neq\mathrm{dia}(t+d_i-1)
$$

**$R_7$.** El coste total no supera el presupuesto:
$$
\sum_{i\in I}c_i y_i\leq B
$$

**$R_8$.** Un espacio no alberga solapamientos:
$$
\sum_{i\in I}
\sum_{t=\max(1,s-d_i+1)}^{s}
x_{i,e,t}\leq 1
\qquad \forall e\in E,\ \forall s\in T
$$

**$R_9$.** Actividades incompatibles no coinciden en ninguna franja:
$$
\sum_{e\in E}\sum_{t=\max(1,s-d_i+1)}^{s}x_{i,e,t}
+
\sum_{e\in E}\sum_{t=\max(1,s-d_j+1)}^{s}x_{j,e,t}
\leq 1
\qquad \forall (i,j)\in P,\ \forall s\in T
$$

## Modelo

El modelo maximiza la suma ponderada y normalizada de asistencia, valoracion y numero de actividades:
$$
\max \sum_{i\in I} y_i
\left(
w_A\frac{a_i}{A_{\mathrm{tot}}}
+
w_V\frac{v_i}{V_{\mathrm{tot}}}
+
\frac{w_N}{N}
\right)
$$
