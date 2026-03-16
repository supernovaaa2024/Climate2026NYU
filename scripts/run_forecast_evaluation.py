from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.ar_model import AutoReg


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data_forecasts"
RESULTS_DIR = DATA_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

TEST_START = 2011
TEST_END = 2025


def rmse(y_true: pd.Series, y_pred: pd.Series) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def load_csv(filename: str, required_columns: list[str]) -> pd.DataFrame:
    frame = pd.read_csv(DATA_DIR / filename)
    frame.columns = [str(col).strip().lower() for col in frame.columns]
    missing = sorted(set(required_columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{filename} is missing required columns: {missing}")
    frame = frame.loc[:, ~frame.columns.duplicated()].copy()
    frame["year"] = frame["year"].astype(int)
    return frame.sort_values("year").reset_index(drop=True)


def load_inputs() -> pd.DataFrame:
    gmst = load_csv("gmst.csv", ["year", "temp"])
    fr = load_csv("fr_drivers.csv", ["year", "enso", "volcanic", "solar"])
    forcings = load_csv(
        "forcings.csv",
        [
            "year",
            "anthro_erf",
            "ghg_erf",
            "aerosol_erf",
            "solar_erf",
            "volcanic_erf",
            "ch4_erf",
            "ods_erf",
        ],
    )

    data = gmst.merge(fr, on="year", how="inner").merge(forcings, on="year", how="inner")
    data = data[(data["year"] >= 1979) & (data["year"] <= TEST_END)].copy()
    data = data.dropna().reset_index(drop=True)

    if data.empty:
        raise ValueError("Merged dataset is empty after alignment and dropna().")

    return data


def engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["time"] = out["year"] - out["year"].min()
    out["time_sq"] = out["time"] ** 2
    out["enso_sq"] = out["enso"] ** 2
    out["enso_x_volcanic"] = out["enso"] * out["volcanic"]
    out["solar_x_volcanic"] = out["solar_erf"] * out["volcanic_erf"]
    out["ghg_minus_aerosol"] = out["ghg_erf"] - out["aerosol_erf"]
    return out


def fit_ols(train: pd.DataFrame, features: list[str]):
    x_train = sm.add_constant(train[features], has_constant="add")
    y_train = train["temp"]
    return sm.OLS(y_train, x_train, missing="drop").fit()


def one_step_residual_forecast(residuals: pd.Series, lag_order: int) -> float:
    residuals = pd.Series(residuals).dropna()
    if lag_order <= 0 or len(residuals) <= lag_order + 2:
        return 0.0

    model = AutoReg(residuals, lags=lag_order, old_names=False).fit()
    forecast = model.predict(start=len(residuals), end=len(residuals))
    return float(np.asarray(forecast)[0])


def recursive_forecast(
    data: pd.DataFrame,
    features: list[str],
    start_year: int = TEST_START,
    end_year: int = TEST_END,
    ar_lag: int = 0,
) -> pd.DataFrame:
    rows = []

    for year in range(start_year, end_year + 1):
        train = data[data["year"] < year].copy()
        target = data[data["year"] == year].copy()

        if train.empty or target.empty:
            continue

        ols = fit_ols(train, features)
        x_target = sm.add_constant(target[features], has_constant="add")
        base_prediction = float(ols.predict(x_target).iloc[0])

        fitted_train = pd.Series(
            ols.predict(sm.add_constant(train[features], has_constant="add")),
            index=train.index,
        )
        residuals = train["temp"] - fitted_train
        ar_correction = one_step_residual_forecast(residuals, ar_lag)

        rows.append(
            {
                "year": year,
                "actual": float(target["temp"].iloc[0]),
                "predicted": base_prediction + ar_correction,
                "base_prediction": base_prediction,
                "ar_correction": ar_correction,
                "ar_lag": ar_lag,
            }
        )

    out = pd.DataFrame(rows)
    if out.empty:
        raise ValueError("No recursive forecasts were produced. Check the year coverage.")
    return out


def main() -> None:
    data = engineer_features(load_inputs())

    model_specs = {
        "foster_rahmstorf": ["time", "enso", "volcanic", "solar"],
        "forcing_rcm_like": [
            "anthro_erf",
            "solar_erf",
            "volcanic_erf",
            "ch4_erf",
            "ods_erf",
        ],
        "extended": [
            "time",
            "time_sq",
            "enso",
            "enso_sq",
            "volcanic",
            "solar",
            "ghg_erf",
            "aerosol_erf",
            "solar_erf",
            "volcanic_erf",
            "ch4_erf",
            "ods_erf",
            "enso_x_volcanic",
            "solar_x_volcanic",
            "ghg_minus_aerosol",
        ],
    }

    experiments = [
        ("foster_rahmstorf", model_specs["foster_rahmstorf"], 0),
        ("fr_ar1", model_specs["foster_rahmstorf"], 1),
        ("fr_ar2", model_specs["foster_rahmstorf"], 2),
        ("fr_ar3", model_specs["foster_rahmstorf"], 3),
        ("forcing_rcm_like", model_specs["forcing_rcm_like"], 0),
        ("forcing_ar1", model_specs["forcing_rcm_like"], 1),
        ("forcing_ar2", model_specs["forcing_rcm_like"], 2),
        ("forcing_ar3", model_specs["forcing_rcm_like"], 3),
        ("extended", model_specs["extended"], 0),
        ("extended_ar1", model_specs["extended"], 1),
        ("extended_ar2", model_specs["extended"], 2),
        ("extended_ar3", model_specs["extended"], 3),
    ]

    score_rows = []
    forecast_frames = []

    for model_name, features, ar_lag in experiments:
        preds = recursive_forecast(data, features, ar_lag=ar_lag)
        preds["model"] = model_name
        forecast_frames.append(preds)

        score_rows.append(
            {
                "model": model_name,
                "rmse": rmse(preds["actual"], preds["predicted"]),
                "mae": float(mean_absolute_error(preds["actual"], preds["predicted"])),
                "bias": float((preds["predicted"] - preds["actual"]).mean()),
                "n_forecasts": len(preds),
            }
        )

    scores = pd.DataFrame(score_rows).sort_values(["rmse", "mae"]).reset_index(drop=True)
    all_forecasts = pd.concat(forecast_frames, ignore_index=True)

    scores.to_csv(RESULTS_DIR / "forecast_scores.csv", index=False)
    all_forecasts.to_csv(RESULTS_DIR / "all_forecasts.csv", index=False)

    print(scores.to_string(index=False))
    print(f"\nSaved results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
