# Copilot repository instructions

## Project state

This is a Spanish-language academic optimization project. The mathematical formulation is complete, but the Python implementation and the Parte 2/Parte 3 report sections are not yet present. Preserve the terminology and numbering used by the assignment:

- `I` / activities
- `E` / spaces
- `T` / time slots
- `y_i` / whether activity `i` is selected
- `x_{i,e,t}` / whether activity `i` starts in space `e` at slot `t`

The repository is split by deliverable:

- `1_data_and_formulation/` contains the model specification and the work plan.
- `data/` is the shared, canonical instance; do not duplicate or move these CSV files.
- `2_model_implementation/` is reserved for the loading, solving, interface, and export implementation.
- `3_testing_and_analysis/` is reserved for executable tests and scenario analysis.
- `informe/` contains the LaTeX report assembled by `informe/latex_informe_trabajo_opti.tex`.
- `_instr/` is the original, unmodified assignment PDF.

## Commands

### Python environment and Streamlit

Use Python exclusively through a project virtual environment; never install project dependencies into the system or user-wide Python environment.

From the repository root, create and activate `.venv` before installing or running anything:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Keep `.venv/` out of Git with a repository `.gitignore`; verify with `git status --short` that it is not tracked. If a different environment manager is already configured for the repository, use that project environment instead and document the equivalent commands.

For Streamlit work:

- Use `python -m streamlit run streamlit_app.py` so the app uses the virtual environment's interpreter and packages.
- Keep `requirements.txt` as the shared dependency manifest and install dependencies only with `python -m pip` inside `.venv`.
- Keep Streamlit at the latest stable release in `requirements.txt` or as a compatible version constraint; do not introduce or retain a known-old Streamlit pin.
- Run Streamlit with `python -m streamlit run streamlit_app.py`. For an explicitly managed port or automated/headless validation, add only the required `--server.port`, `--server.headless`, or `--server.address` flags.
- Before finalizing Streamlit code changes, type-check changed Python files with the project's configured checker, or install and use `ty` inside `.venv`.

There is currently no Python package, test runner, linter, build script, or Makefile beyond `requirements.txt`. Do not invent one as part of a small change.

The report source can be compiled with TeX when a LaTeX distribution is installed:

```bash
cd informe
pdflatex -interaction=nonstopmode -halt-on-error latex_informe_trabajo_opti.tex
pdflatex -interaction=nonstopmode -halt-on-error latex_informe_trabajo_opti.tex
```

Run the two passes because the report uses `\input` sections and may contain table-of-contents or cross-reference metadata.

No automated test suite exists yet. When pytest is introduced, run the full suite with `pytest`, a file with `pytest path/to/test_file.py`, and one test with `pytest path/to/test_file.py::test_name`.

No lint command exists yet. If project tooling is added, record the actual commands here instead of assuming a formatter or linter.

## Model architecture

The canonical model specification is in `1_data_and_formulation/formulacion_modelo.md`. Keep code, CSV handling, and report text consistent with it.

The instance is a binary selection and scheduling problem:

- `actividades.csv` supplies duration, attendance, rating, cost, category, and mandatory status.
- `espacios.csv` supplies capacities.
- `compat_espacios.csv` supplies the activity-space compatibility relation.
- `disp_actividades.csv` supplies slots when an activity can start.
- `disp_espacios.csv` supplies slots when a space is open.
- `incompatibilidades.csv` supplies pairs that cannot overlap.
- `parametros.csv` supplies budget, criterion weights, total slot count, and slots per day.

The objective is the normalized weighted sum in the formulation. The default parameters are in `data/parametros.csv`; the required comparison scenarios are 1/0/0 for attendance, 0/1/0 for rating, and 0.1/0.1/0.8 for number of activities.

The implementation must distinguish invalid input from infeasible optimization:

- Invalid CSV data or broken references should be reported as data/schema errors.
- A valid instance with no feasible schedule should be reported as infeasible.

Scheduling is slot-based. An activity can occupy all slots from its start through `start + duration - 1`, cannot extend beyond `F`, and cannot cross a day boundary. Space capacity and compatibility are applied through `x_{i,e,t}`; space availability and activity availability must hold for every occupied slot.

## CSV and validation conventions

- Treat IDs in CSV files as identifiers, not free-form display names.
- CSV headers and IDs should remain as currently defined: for example `actividad_1` and `actividad_2` in incompatibilities, and `presupuesto,w_A,w_V,w_N,num_franjas,franjas_por_dia` in parameters.
- `disp_*.csv` rows describe allowed starts or availability by slot; an activity or space with no row has no availability entry rather than an implicit value.
- Preserve the relationship structure between IDs: incompatible, compatibility, activity, and space IDs must reference existing records.
- Durations, costs, attendance, ratings, budgets, weights, slot counts, and IDs require sensible validation before building the model.
- The weights in parameters must be understood as the sum of `w_A + w_V + w_N`.

## Report conventions

- The report is written in Spanish and uses LaTeX.
- `informe/latex_informe_trabajo_opti.tex` is the composition root; add new report sections as `\input` files and keep implementation results in `informe/2_implementacion_interfaz.tex` and test analysis in `informe/3_pruebas_analisis.tex`.
- Keep numerical examples consistent with the CSV instance. The main instance has 18 activities, 3 spaces, 8 slots, 4 slots per day, a 6500 budget, and default weights 0.4/0.4/0.2.
- If generated figures or CSV exports are added for the report, keep them outside the source directories or in clearly identified generated-output folders; do not overwrite canonical `data/` inputs.
