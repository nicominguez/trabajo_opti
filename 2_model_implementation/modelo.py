from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pulp


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"


class DataValidationError(ValueError):
    pass


def _read_csv(name: str, required_columns: list[str]) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        raise DataValidationError(f"Falta el archivo CSV: {path}")
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise DataValidationError(f"No se pudo leer {name}: {exc}") from exc
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise DataValidationError(
            f"{name}: faltan las columnas {', '.join(missing)}"
        )
    return df


def load_instance() -> dict[str, Any]:
    actividades = _read_csv(
        "actividades.csv",
        [
            "id",
            "nombre",
            "duracion",
            "categoria",
            "asistencia",
            "valoracion",
            "coste",
            "obligatoria",
        ],
    )
    espacios = _read_csv("espacios.csv", ["id", "nombre", "capacidad"])
    compat = _read_csv("compat_espacios.csv", ["actividad", "espacio"])
    disp_actividades = _read_csv(
        "disp_actividades.csv", ["actividad", "franja"]
    )
    disp_espacios = _read_csv("disp_espacios.csv", ["espacio", "franja"])
    incompat = _read_csv(
        "incompatibilidades.csv", ["actividad_1", "actividad_2"]
    )
    parametros = _read_csv(
        "parametros.csv",
        [
            "presupuesto",
            "w_A",
            "w_V",
            "w_N",
            "num_franjas",
            "franjas_por_dia",
        ],
    )

    if len(parametros) != 1:
        raise DataValidationError("parametros.csv debe contener exactamente una fila")

    numeric_frames = {
        "actividades.csv": (
            actividades,
            ["id", "duracion", "asistencia", "valoracion", "coste", "obligatoria"],
        ),
        "espacios.csv": (espacios, ["capacidad"]),
        "disp_actividades.csv": (disp_actividades, ["actividad", "franja"]),
        "disp_espacios.csv": (disp_espacios, ["espacio", "franja"]),
        "compat_espacios.csv": (compat, ["actividad", "espacio"]),
        "incompatibilidades.csv": (
            incompat,
            ["actividad_1", "actividad_2"],
        ),
    }
    for name, (df, columns) in numeric_frames.items():
        if df.empty and name not in {"disp_actividades.csv", "disp_espacios.csv"}:
            raise DataValidationError(f"{name} no puede estar vacio")
        for column in columns:
            if df.empty:
                continue
            if column in {"actividad", "espacio", "actividad_1", "actividad_2"}:
                continue
            if df[column].isna().any():
                raise DataValidationError(f"{name}: hay valores vacios en {column}")

    if actividades["id"].duplicated().any():
        raise DataValidationError("actividades.csv contiene ids duplicados")
    if espacios["id"].duplicated().any():
        raise DataValidationError("espacios.csv contiene ids de espacios duplicados")

    activity_ids = set(actividades["id"].astype(str))
    space_ids = set(espacios["id"].astype(str))

    for df, activity_columns, name in [
        (compat, ["actividad"], "compat_espacios.csv"),
        (disp_actividades, ["actividad"], "disp_actividades.csv"),
        (incompat, ["actividad_1", "actividad_2"], "incompatibilidades.csv"),
    ]:
        for column in activity_columns:
            unknown = set(df[column].astype(str)) - activity_ids
            if unknown:
                raise DataValidationError(
                    f"{name}: referencias de actividad desconocidas: "
                    + ", ".join(sorted(unknown))
                )

    unknown_spaces = set(compat["espacio"].astype(str)) - space_ids
    if unknown_spaces:
        raise DataValidationError(
            "compat_espacios.csv: espacios desconocidos: "
            + ", ".join(sorted(unknown_spaces))
        )
    unknown_space_availability = set(disp_espacios["espacio"].astype(str)) - space_ids
    if unknown_space_availability:
        raise DataValidationError(
            "disp_espacios.csv: espacios desconocidos: "
            + ", ".join(sorted(unknown_space_availability))
        )

    for column in ["duracion", "asistencia", "valoracion", "coste", "obligatoria"]:
        numeric = pd.to_numeric(actividades[column], errors="coerce")
        if numeric.isna().any():
            raise DataValidationError(
                f"actividades.csv: {column} debe contener valores numericos"
            )
        actividades[column] = numeric
    for column in ["capacidad"]:
        numeric = pd.to_numeric(espacios[column], errors="coerce")
        if numeric.isna().any():
            raise DataValidationError(
                f"espacios.csv: {column} debe contener valores numericos"
            )
        espacios[column] = numeric

    if (actividades["duracion"] <= 0).any():
        raise DataValidationError("Las duraciones deben ser mayores que cero")
    if (actividades["asistencia"] < 0).any():
        raise DataValidationError("Las asistencias no pueden ser negativas")
    if (actividades["valoracion"] < 0).any():
        raise DataValidationError("Las valoraciones no pueden ser negativas")
    if (actividades["coste"] < 0).any():
        raise DataValidationError("Los costes no pueden ser negativos")
    if not actividades["obligatoria"].isin([0, 1]).all():
        raise DataValidationError("obligatoria debe ser 0 o 1")
    if (espacios["capacidad"] <= 0).any():
        raise DataValidationError("Las capacidades deben ser mayores que cero")
    if actividades["asistencia"].sum() <= 0:
        raise DataValidationError("La suma de asistencias debe ser mayor que cero")
    if actividades["valoracion"].sum() <= 0:
        raise DataValidationError("La suma de valoraciones debe ser mayor que cero")

    params = parametros.iloc[0]
    param_values = {
        "presupuesto": float(params["presupuesto"]),
        "w_A": float(params["w_A"]),
        "w_V": float(params["w_V"]),
        "w_N": float(params["w_N"]),
        "num_franjas": int(params["num_franjas"]),
        "franjas_por_dia": int(params["franjas_por_dia"]),
    }
    if (
        param_values["presupuesto"] < 0
        or param_values["num_franjas"] <= 0
        or param_values["franjas_por_dia"] <= 0
    ):
        raise DataValidationError("Presupuesto o franjas invalidos en parametros.csv")

    for df, columns, name in [
        (disp_actividades, ["actividad", "franja"], "disp_actividades.csv"),
        (disp_espacios, ["espacio", "franja"], "disp_espacios.csv"),
        (compat, ["actividad", "espacio"], "compat_espacios.csv"),
    ]:
        for column in columns:
            if column in {"franja"}:
                numeric = pd.to_numeric(df[column], errors="coerce")
                if numeric.isna().any():
                    raise DataValidationError(f"{name}: franja invalida")

    if not compat.empty:
        if compat.isna().any().any():
            raise DataValidationError("compat_espacios.csv contiene valores vacios")

    return {
        "actividades": actividades,
        "espacios": espacios,
        "compat": compat,
        "disp_actividades": disp_actividades,
        "disp_espacios": disp_espacios,
        "incompat": incompat,
        "parametros": param_values,
    }


def solve_instance(
    instance: dict[str, Any],
    budget: float,
    weights: tuple[float, float, float],
) -> dict[str, Any]:
    actividades = instance["actividades"]
    espacios = instance["espacios"]
    compat = instance["compat"]
    disp_actividades = instance["disp_actividades"]
    disp_espacios = instance["disp_espacios"]
    incompat = instance["incompat"]
    params = instance["parametros"]

    if budget < 0:
        raise ValueError("El presupuesto no puede ser negativo")
    if any(weight < 0 for weight in weights):
        raise ValueError("Los pesos no pueden ser negativos")
    if sum(weights) <= 0:
        raise ValueError("Al menos un peso debe ser positivo")

    F = params["num_franjas"]
    slots_per_day = params["franjas_por_dia"]
    activity_ids = actividades["id"].tolist()
    space_ids = espacios["id"].astype(str).tolist()

    compat_pairs = set(
        zip(
            compat["actividad"].astype(int),
            compat["espacio"].astype(str),
        )
    )
    activity_availability = set(
        zip(
            disp_actividades["actividad"].astype(int),
            disp_actividades["franja"].astype(int),
        )
    )
    space_availability = set(
        zip(
            disp_espacios["espacio"].astype(str),
            disp_espacios["franja"].astype(int),
        )
    )

    model = pulp.LpProblem("Planificacion_evento", pulp.LpMaximize)
    y = {
        int(row["id"]): pulp.LpVariable(f"y_{int(row['id'])}", cat="Binary")
        for _, row in actividades.iterrows()
    }
    x: dict[tuple[int, str, int], pulp.LpVariable] = {}

    for _, activity in actividades.iterrows():
        i = int(activity["id"])
        duration = int(activity["duracion"])
        attendance = float(activity["asistencia"])
        for _, space in espacios.iterrows():
            e = str(space["id"])
            capacity = float(space["capacidad"])
            for t in range(1, F + 1):
                feasible = (i, e) in compat_pairs
                feasible = feasible and attendance <= capacity
                feasible = feasible and t + duration - 1 <= F
                feasible = feasible and (
                    (t - 1) // slots_per_day
                    == (t + duration - 2) // slots_per_day
                )
                if feasible:
                    for s in range(t, t + duration):
                        if (i, s) not in activity_availability:
                            feasible = False
                        if (e, s) not in space_availability:
                            feasible = False
                if feasible:
                    x[(i, e, t)] = pulp.LpVariable(
                        f"x_{i}_{e}_{t}", cat="Binary"
                    )

    for i in activity_ids:
        i = int(i)
        model += (
            y[i] == pulp.lpSum(x[key] for key in x if key[0] == i),
            f"seleccion_y_x_{i}",
        )

    for _, activity in actividades.iterrows():
        i = int(activity["id"])
        if int(activity["obligatoria"]) == 1:
            model += y[i] == 1, f"obligatoria_{i}"

    model += (
        pulp.lpSum(
            float(row["coste"]) * y[int(row["id"])]
            for _, row in actividades.iterrows()
        )
        <= budget,
        "presupuesto",
    )

    for e in space_ids:
        for s in range(1, F + 1):
            occupied_starts = [
                variable
                for (i, ee, t), variable in x.items()
                if ee == e
                and t
                <= s
                <= t
                + int(
                    actividades.loc[
                        actividades["id"].astype(int) == i, "duracion"
                    ].iloc[0]
                )
                - 1
            ]
            model += pulp.lpSum(occupied_starts) <= 1, f"espacio_{e}_franja_{s}"

    for _, pair in incompat.iterrows():
        i = int(pair["actividad_1"])
        j = int(pair["actividad_2"])
        for s in range(1, F + 1):
            starts_i = []
            starts_j = []
            for (activity, e, t), variable in x.items():
                duration_activity = int(
                    actividades.loc[
                        actividades["id"].astype(int) == activity, "duracion"
                    ].iloc[0]
                )
                if activity == i and t <= s <= t + duration_activity - 1:
                    starts_i.append(variable)
                if activity == j and t <= s <= t + duration_activity - 1:
                    starts_j.append(variable)
            model += (
                pulp.lpSum(starts_i) + pulp.lpSum(starts_j) <= 1,
                f"incompatibles_{i}_{j}_franja_{s}",
            )

    A_tot = float(actividades["asistencia"].sum())
    V_tot = float(actividades["valoracion"].sum())
    N = len(actividades)
    w_A, w_V, w_N = weights
    model += pulp.lpSum(
        y[int(row["id"])]
        * (
            w_A * float(row["asistencia"]) / A_tot
            + w_V * float(row["valoracion"]) / V_tot
            + w_N / N
        )
        for _, row in actividades.iterrows()
    )

    solver_errors: list[str] = []
    status = 0
    solver = None

    try:
        highs_solver = pulp.HiGHS(msg=False)
        if highs_solver.available():
            solver = highs_solver
            status = model.solve(solver)
    except Exception as exc:
        solver_errors.append(f"HiGHS: {exc}")

    if solver is None or pulp.LpStatus[status] == "Undefined":
        try:
            cbc_solver = pulp.PULP_CBC_CMD(msg=False)
            status = model.solve(cbc_solver)
        except (OSError, pulp.PulpSolverError) as exc:
            return {
                "status": "SolverError",
                "assignments": pd.DataFrame(),
                "selected": [],
                "error": f"No se pudo ejecutar un solver compatible. "
                f"{'; '.join(solver_errors)}; CBC: {exc}",
            }
    status_name = pulp.LpStatus[status]
    if status_name != "Optimal":
        return {"status": status_name, "assignments": pd.DataFrame(), "selected": []}

    assignments = []
    selected = []
    for _, activity in actividades.iterrows():
        i = int(activity["id"])
        if pulp.value(y[i]) is not None and pulp.value(y[i]) > 0.5:
            selected.append(i)
    for (i, e, t), variable in x.items():
        if pulp.value(variable) is not None and pulp.value(variable) > 0.5:
            activity_name = actividades.loc[
                actividades["id"].astype(int) == i, "nombre"
            ].iloc[0]
            space_name = espacios.loc[
                espacios["id"].astype(str) == str(e), "nombre"
            ].iloc[0]
            duration = int(
                actividades.loc[
                    actividades["id"].astype(int) == i, "duracion"
                ].iloc[0]
            )
            assignments.append(
                {
                    "actividad": i,
                    "nombre": activity_name,
                    "espacio": e,
                    "nombre_espacio": space_name,
                    "inicio": t,
                    "fin": t + duration - 1,
                }
            )

    assignment_df = pd.DataFrame(assignments).sort_values(
        ["espacio", "inicio", "actividad"],
        ignore_index=True,
    )
    return {
        "status": status_name,
        "assignments": assignment_df,
        "selected": selected,
    }
