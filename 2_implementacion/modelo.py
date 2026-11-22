from pathlib import Path

import pandas as pd
import pulp


class DataValidationError(ValueError):
    pass


def _read_csv(data_dir, name, required):
    path = data_dir / name
    if not path.is_file():
        raise DataValidationError(f"Falta el archivo {name}.")
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        raise DataValidationError(f"No se pudo leer {name}: {exc}") from exc
    missing = set(required) - set(frame.columns)
    if missing:
        raise DataValidationError(
            f"{name}: faltan columnas {', '.join(sorted(missing))}."
        )
    return frame


def _require_positive(series, name, allow_zero=False):
    if series.isna().any():
        raise DataValidationError(f"{name}: existen valores vacios.")
    valid = (series >= 0) if allow_zero else (series > 0)
    if not valid.all():
        raise DataValidationError(
            f"{name}: los valores deben ser {'no negativos' if allow_zero else 'positivos'}."
        )


def load_instance(data_dir=None):
    data_dir = (
        Path(data_dir)
        if data_dir is not None
        else Path(__file__).resolve().parents[1] / "data"
    )
    activities = _read_csv(
        data_dir,
        "actividades.csv",
        ["id", "nombre", "duracion", "categoria", "asistencia",
         "valoracion", "coste", "obligatoria"],
    )
    spaces = _read_csv(data_dir, "espacios.csv", ["id", "nombre", "capacidad"])
    compatibility = _read_csv(
        data_dir, "compat_espacios.csv", ["actividad", "espacio"]
    )
    activity_availability = _read_csv(
        data_dir, "disp_actividades.csv", ["actividad", "franja"]
    )
    space_availability = _read_csv(
        data_dir, "disp_espacios.csv", ["espacio", "franja"]
    )
    incompatibilities = _read_csv(
        data_dir,
        "incompatibilidades.csv",
        ["actividad_1", "actividad_2"],
    )
    parameters = _read_csv(
        data_dir,
        "parametros.csv",
        ["presupuesto", "w_A", "w_V", "w_N",
         "num_franjas", "franjas_por_dia"],
    )

    numeric_columns = (
        (activities, ["id", "duracion", "asistencia", "valoracion", "coste", "obligatoria"]),
        (spaces, ["capacidad"]),
        (compatibility, ["actividad"]),
        (activity_availability, ["actividad", "franja"]),
        (space_availability, ["franja"]),
        (incompatibilities, ["actividad_1", "actividad_2"]),
    )
    for frame, columns in numeric_columns:
        for column in columns:
            values = pd.to_numeric(frame[column], errors="coerce")
            if values.isna().any():
                raise DataValidationError(
                    f"{column}: existen valores no numericos o vacios."
                )
            frame[column] = values

    integer_columns = (
        (activities, ["id", "duracion", "obligatoria"]),
        (compatibility, ["actividad"]),
        (activity_availability, ["actividad", "franja"]),
        (space_availability, ["franja"]),
        (incompatibilities, ["actividad_1", "actividad_2"]),
    )
    for frame, columns in integer_columns:
        for column in columns:
            if (frame[column] % 1 != 0).any():
                raise DataValidationError(f"{column}: los valores deben ser enteros.")
            frame[column] = frame[column].astype(int)

    if len(parameters) != 1:
        raise DataValidationError("parametros.csv debe contener una sola fila.")
    params = parameters.iloc[0].to_dict()
    numeric_params = [
        "presupuesto", "w_A", "w_V", "w_N",
        "num_franjas", "franjas_por_dia",
    ]
    for name in numeric_params:
        try:
            params[name] = float(params[name])
        except (TypeError, ValueError) as exc:
            raise DataValidationError(
                f"parametros.csv: {name} debe ser numerico."
            ) from exc

    _require_positive(activities["id"], "actividades.id")
    _require_positive(activities["duracion"], "actividades.duracion")
    _require_positive(activities["asistencia"], "actividades.asistencia",
                      allow_zero=True)
    _require_positive(activities["valoracion"], "actividades.valoracion",
                      allow_zero=True)
    _require_positive(activities["coste"], "actividades.coste", allow_zero=True)
    _require_positive(spaces["capacidad"], "espacios.capacidad")
    if activities["id"].duplicated().any():
        raise DataValidationError("actividades.csv contiene IDs duplicados.")
    if spaces["id"].duplicated().any():
        raise DataValidationError("espacios.csv contiene IDs duplicados.")

    mandatory = set(activities["obligatoria"].dropna().astype(str))
    if not set(mandatory).issubset({"0", "1"}):
        raise DataValidationError(
            "obligatoria debe contener solo 0 o 1."
        )

    activity_ids = set(activities["id"].astype(int))
    space_ids = set(spaces["id"].astype(str))
    horizon = int(params["num_franjas"])
    slots_per_day = int(params["franjas_por_dia"])
    if horizon <= 0 or slots_per_day <= 0 or horizon % slots_per_day != 0:
        raise DataValidationError(
            "num_franjas y franjas_por_dia deben ser enteros positivos "
            "y formar un horizonte completo en dias."
        )
    if params["presupuesto"] < 0 or params["w_A"] < 0 or params["w_V"] < 0 or params["w_N"] < 0:
        raise DataValidationError("Presupuesto y pesos deben ser no negativos.")
    if any(value % 1 for value in (params["num_franjas"], params["franjas_por_dia"])):
        raise DataValidationError(
            "num_franjas y franjas_por_dia deben ser enteros."
        )
    weight_sum = params["w_A"] + params["w_V"] + params["w_N"]
    if abs(weight_sum - 1.0) > 1e-9:
        raise DataValidationError(
            "Los pesos w_A, w_V y w_N deben sumar 1."
        )

    if not set(compatibility["actividad"]).issubset(activity_ids):
        raise DataValidationError("compat_espacios.csv contiene una actividad desconocida.")
    if not set(compatibility["espacio"]).issubset(space_ids):
        raise DataValidationError("compat_espacios.csv contiene un espacio desconocido.")
    if not set(activity_availability["actividad"]).issubset(activity_ids):
        raise DataValidationError("disp_actividades.csv contiene una actividad desconocida.")
    if not set(space_availability["espacio"]).issubset(space_ids):
        raise DataValidationError("disp_espacios.csv contiene un espacio desconocido.")
    if not set(incompatibilities["actividad_1"]).issubset(activity_ids):
        raise DataValidationError("incompatibilidades.csv contiene una actividad desconocida.")
    if not set(incompatibilities["actividad_2"]).issubset(activity_ids):
        raise DataValidationError("incompatibilidades.csv contiene una actividad desconocida.")

    for frame, column in (
        (activity_availability, "franja"),
        (space_availability, "franja"),
    ):
        if ((frame[column] < 1) | (frame[column] > horizon)).any():
            raise DataValidationError(
                f"{column}: existen franjas fuera del horizonte."
            )

    return {
        "actividades": activities,
        "espacios": spaces,
        "compatibilidad": compatibility,
        "disp_actividades": activity_availability,
        "disp_espacios": space_availability,
        "incompatibilidades": incompatibilities,
        "parametros": params,
    }


def solve_instance(instance, budget=None, weights=None):
    activities = instance["actividades"]
    spaces = instance["espacios"]
    compatibility = instance["compatibilidad"]
    availability_activity = instance["disp_actividades"]
    availability_space = instance["disp_espacios"]
    incompatibilities = instance["incompatibilidades"]
    params = instance["parametros"]

    if budget is None:
        budget = float(params["presupuesto"])
    if weights is None:
        weights = (float(params["w_A"]), float(params["w_V"]), float(params["w_N"]))
    if budget < 0 or any(float(weight) < 0 for weight in weights):
        raise ValueError("El presupuesto y los pesos deben ser no negativos.")
    weight_sum = sum(weights)
    if weight_sum <= 0:
        raise ValueError("Los tres pesos no pueden ser cero.")
    w_a, w_v, w_n = (float(w) / weight_sum for w in weights)

    horizon = int(params["num_franjas"])
    slots_per_day = int(params["franjas_por_dia"])
    activity_ids = set(activities["id"].astype(int))
    space_ids = set(spaces["id"].astype(str))
    compatible = set(
        zip(
            compatibility["actividad"].astype(int),
            compatibility["espacio"].astype(str),
        )
    )
    available_activity = set(
        zip(
            availability_activity["actividad"].astype(int),
            availability_activity["franja"].astype(int),
        )
    )
    available_space = set(
        zip(
            availability_space["espacio"].astype(str),
            availability_space["franja"].astype(int),
        )
    )

    model = pulp.LpProblem("Planificacion_evento", pulp.LpMaximize)
    y = {
        int(row.id): pulp.LpVariable(f"y_{int(row.id)}", cat="Binary")
        for row in activities.itertuples()
    }
    x = {}
    capacities = dict(zip(spaces["id"].astype(str), spaces["capacidad"].astype(float)))
    by_id = activities.set_index("id")

    for i in activity_ids:
        duration = int(by_id.loc[i, "duracion"])
        attendance = float(by_id.loc[i, "asistencia"])
        for e in space_ids:
            if (i, e) not in compatible:
                continue
            if attendance > capacities[e]:
                continue
            for t in range(1, horizon + 1):
                occupied = range(t, t + duration)
                if t + duration - 1 > horizon:
                    continue
                if any((t + k - 1 - 1) // slots_per_day != (t - 1) // slots_per_day for k in range(1, duration)):
                    continue
                if any((i, s) not in available_activity or (e, s) not in available_space
                       for s in occupied):
                    continue
                x[i, e, t] = pulp.LpVariable(f"x_{i}_{e}_{t}", cat="Binary")

        model += y[i] == pulp.lpSum(
            x[key] for key in x if key[0] == i
        )
        if int(by_id.loc[i, "obligatoria"]) == 1:
            model += y[i] == 1

    for s in range(1, horizon + 1):
        for e in space_ids:
            model += pulp.lpSum(
                x[key] for key in x
                if key[1] == e
                and key[2] <= s
                and s < key[2] + int(by_id.loc[key[0], "duracion"])
            ) <= 1

    model += pulp.lpSum(
        float(by_id.loc[i, "coste"]) * y[i] for i in activity_ids
    ) <= float(budget)

    for _, row in incompatibilities.iterrows():
        i = int(row["actividad_1"])
        j = int(row["actividad_2"])
        for s in range(1, horizon + 1):
            model += pulp.lpSum(
                x[key] for key in x
                if key[0] == i
                and key[2] <= s
                and s < key[2] + int(by_id.loc[i, "duracion"])
            ) + pulp.lpSum(
                x[key] for key in x
                if key[0] == j
                and key[2] <= s
                and s < key[2] + int(by_id.loc[j, "duracion"])
            ) <= 1

    total_attendance = activities["asistencia"].sum()
    total_rating = activities["valoracion"].sum()
    activity_count = len(activities)
    model += (
        w_a * pulp.lpSum(float(by_id.loc[i, "asistencia"]) * y[i] for i in activity_ids)
        / (total_attendance if total_attendance else 1)
        + w_v * pulp.lpSum(float(by_id.loc[i, "valoracion"]) * y[i] for i in activity_ids)
        / (total_rating if total_rating else 1)
        + w_n * pulp.lpSum(y[i] for i in activity_ids) / activity_count
    )

    try:
        status_code = model.solve(pulp.HiGHS(msg=False))
        status = pulp.LpStatus[status_code]
    except Exception as exc:
        return {"status": "SolverError", "error": str(exc)}
    if status != "Optimal":
        return {"status": status, "selected": [], "assignments": pd.DataFrame()}

    selected = sorted(i for i in activity_ids if pulp.value(y[i]) > 0.5)
    rows = []
    for i, e, t in x:
        if pulp.value(x[i, e, t]) > 0.5:
            duration = int(by_id.loc[i, "duracion"])
            rows.append({
                "actividad": i,
                "nombre": by_id.loc[i, "nombre"],
                "espacio": e,
                "nombre_espacio": spaces.set_index("id").loc[e, "nombre"],
                "inicio": t,
                "fin": t + duration - 1,
            })
    assignments = pd.DataFrame(rows).sort_values(
        ["espacio", "inicio", "actividad"]
    ) if rows else pd.DataFrame.from_records(
        [],
        columns=["actividad", "nombre", "espacio", "nombre_espacio", "inicio", "fin"],
    )

    selected_rows = activities[activities["id"].isin(selected)]
    return {
        "status": "Optimal",
        "selected": selected,
        "assignments": assignments,
        "attendance": int(selected_rows["asistencia"].sum()),
        "rating": float(selected_rows["valoracion"].sum()),
        "cost": float(selected_rows["coste"].sum()),
        "objective": pulp.value(model.objective),
    }
