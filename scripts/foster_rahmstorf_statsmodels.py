from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA


@dataclass
class FosterRahmstorfFit:
    results: object
    design_matrix: pd.DataFrame
    response: pd.Series
    features: list[str]
    lags: dict[str, int]


def add_time_index(frame: pd.DataFrame, time_col: str = "time_index") -> pd.DataFrame:
    out = frame.copy()
    if time_col not in out.columns:
        out[time_col] = np.arange(len(out), dtype=float)
    return out


def add_fourier_terms(
    frame: pd.DataFrame,
    time_col: str = "time_index",
    period: int = 12,
    order: int = 2,
) -> pd.DataFrame:
    out = add_time_index(frame, time_col=time_col)
    for harmonic in range(1, order + 1):
        angle = 2 * np.pi * harmonic * out[time_col] / period
        out[f"sin_{harmonic}"] = np.sin(angle)
        out[f"cos_{harmonic}"] = np.cos(angle)
    return out


def build_design_matrix(
    frame: pd.DataFrame,
    temp_col: str = "temp",
    enso_col: str = "enso",
    volcanic_col: str = "volcanic",
    solar_col: str = "solar",
    lag_map: dict[str, int] | None = None,
    include_fourier: bool = True,
    period: int = 12,
    order: int = 2,
) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    lag_map = lag_map or {enso_col: 0, volcanic_col: 0, solar_col: 0}
    out = add_time_index(frame)

    for col, lag in lag_map.items():
        out[f"{col}_lag_{lag}"] = out[col].shift(lag)

    features = [
        "time_index",
        f"{enso_col}_lag_{lag_map[enso_col]}",
        f"{volcanic_col}_lag_{lag_map[volcanic_col]}",
        f"{solar_col}_lag_{lag_map[solar_col]}",
    ]

    if include_fourier:
        out = add_fourier_terms(out, period=period, order=order)
        for harmonic in range(1, order + 1):
            features.extend([f"sin_{harmonic}", f"cos_{harmonic}"])

    design = out[[temp_col, *features]].dropna().copy()
    response = design.pop(temp_col)
    return design, response, features


def fit_foster_rahmstorf_ols(
    frame: pd.DataFrame,
    temp_col: str = "temp",
    enso_col: str = "enso",
    volcanic_col: str = "volcanic",
    solar_col: str = "solar",
    lag_map: dict[str, int] | None = None,
    include_fourier: bool = True,
    period: int = 12,
    order: int = 2,
) -> FosterRahmstorfFit:
    design, response, features = build_design_matrix(
        frame,
        temp_col=temp_col,
        enso_col=enso_col,
        volcanic_col=volcanic_col,
        solar_col=solar_col,
        lag_map=lag_map,
        include_fourier=include_fourier,
        period=period,
        order=order,
    )
    model = sm.OLS(response, sm.add_constant(design, has_constant="add")).fit()
    return FosterRahmstorfFit(
        results=model,
        design_matrix=design,
        response=response,
        features=features,
        lags=lag_map or {enso_col: 0, volcanic_col: 0, solar_col: 0},
    )


def search_foster_rahmstorf_lags(
    frame: pd.DataFrame,
    temp_col: str = "temp",
    enso_col: str = "enso",
    volcanic_col: str = "volcanic",
    solar_col: str = "solar",
    max_lag: int = 24,
    include_fourier: bool = True,
    period: int = 12,
    order: int = 2,
) -> FosterRahmstorfFit:
    best_fit: FosterRahmstorfFit | None = None
    best_ssr = np.inf

    lag_names = (enso_col, volcanic_col, solar_col)
    for lag_combo in product(range(max_lag + 1), repeat=3):
        lag_map = dict(zip(lag_names, lag_combo))
        fit = fit_foster_rahmstorf_ols(
            frame,
            temp_col=temp_col,
            enso_col=enso_col,
            volcanic_col=volcanic_col,
            solar_col=solar_col,
            lag_map=lag_map,
            include_fourier=include_fourier,
            period=period,
            order=order,
        )
        if fit.results.ssr < best_ssr:
            best_fit = fit
            best_ssr = fit.results.ssr

    if best_fit is None:
        raise ValueError("No Foster-Rahmstorf lag combination produced a valid fit.")

    return best_fit


def fit_residual_arma11(residuals: pd.Series):
    clean = pd.Series(residuals).dropna()
    if clean.empty:
        raise ValueError("Residual series is empty.")
    return ARIMA(clean, order=(1, 0, 1)).fit()


def effective_sample_size_ar1(residuals: pd.Series) -> tuple[float, float]:
    clean = pd.Series(residuals).dropna()
    if len(clean) < 3:
        return float(len(clean)), np.nan

    rho1 = float(clean.autocorr(lag=1))
    if not np.isfinite(rho1) or abs(rho1) >= 1:
        return float(len(clean)), rho1

    n_eff = len(clean) * (1 - rho1) / (1 + rho1)
    return float(n_eff), rho1
