from __future__ import annotations

import shutil
import subprocess
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd


START_YEAR = 1970
END_YEAR = 2025
HISTORICAL_END_YEAR = 2014

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data_forecasts"
DATA_DIR.mkdir(exist_ok=True)

RAW_FILES = {
    "gistemp": (
        "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv",
        DATA_DIR / "GLB.Ts+dSST.csv",
    ),
    "mei": (
        "https://psl.noaa.gov/enso/mei/data/meiv2.data",
        DATA_DIR / "meiv2.data",
    ),
    "rcmip_forcing": (
        "https://rcmip-protocols-au.s3-ap-southeast-2.amazonaws.com/v5.1.0/rcmip-radiative-forcing-annual-means-v5-1-0.csv",
        DATA_DIR / "rcmip-radiative-forcing-annual-means-v5-1-0.csv",
    ),
}


def ensure_download(url: str, path: Path) -> None:
    if path.exists():
        return

    try:
        urllib.request.urlretrieve(url, path)
        return
    except Exception:
        pass

    curl = shutil.which("curl")
    if not curl:
        raise RuntimeError(f"Failed to download {url} and curl is not available")

    subprocess.run([curl, "-L", url, "-o", str(path)], check=True)


def load_gmst(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, skiprows=1)
    df.columns = [str(col).strip() for col in df.columns]
    out = df.rename(columns={"Year": "year", "J-D": "temp"})[["year", "temp"]].copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out["temp"] = pd.to_numeric(out["temp"], errors="coerce")
    out = out.dropna(subset=["year", "temp"])
    out["year"] = out["year"].astype(int)
    out = out[out["year"].between(START_YEAR, END_YEAR)].reset_index(drop=True)
    return out


def load_mei(path: Path) -> pd.DataFrame:
    rows: list[dict[str, float]] = []

    with path.open() as fh:
        lines = [line.strip() for line in fh if line.strip()]

    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 13 or not parts[0].lstrip("-").isdigit():
            continue
        year = int(parts[0])
        if not START_YEAR <= year <= END_YEAR:
            continue

        month_values = pd.to_numeric(parts[1:13], errors="coerce")
        month_values = pd.Series(month_values).replace(-999.0, np.nan)
        rows.append({"year": year, "enso": float(np.nanmean(month_values))})

    out = pd.DataFrame(rows)
    out = out[out["year"].between(START_YEAR, END_YEAR)].reset_index(drop=True)
    return out


def load_rcmip_forcing(path: Path) -> pd.DataFrame:
    year_cols = [str(year) for year in range(START_YEAR, END_YEAR + 1)]
    usecols = ["Scenario", "Region", "Variable", *year_cols]
    df = pd.read_csv(path, usecols=usecols)
    df = df[df["Region"].eq("World") & df["Scenario"].isin(["historical", "ssp245"])].copy()
    return df


def combine_rcmip_variable(df: pd.DataFrame, variable: str) -> pd.DataFrame:
    year_cols = [str(year) for year in range(START_YEAR, END_YEAR + 1)]
    subset = df[df["Variable"].eq(variable)][["Scenario", *year_cols]].copy()
    if subset.empty:
        raise ValueError(f"Missing RCMIP forcing variable: {variable}")

    long = subset.melt(id_vars=["Scenario"], var_name="year", value_name="value")
    long["year"] = long["year"].astype(int)
    wide = long.pivot_table(index="year", columns="Scenario", values="value", aggfunc="first")

    values = []
    for year in range(START_YEAR, END_YEAR + 1):
        if year <= HISTORICAL_END_YEAR and "historical" in wide.columns:
            value = wide.loc[year, "historical"]
        else:
            value = np.nan

        if pd.isna(value) and "ssp245" in wide.columns:
            value = wide.loc[year, "ssp245"]

        values.append({"year": year, "value": float(value)})

    return pd.DataFrame(values)


def build_forcings(rcmip: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "anthro_erf": "Effective Radiative Forcing|Anthropogenic",
        "aerosol_erf": "Effective Radiative Forcing|Anthropogenic|Aerosols",
        "solar_erf": "Effective Radiative Forcing|Natural|Solar",
        "volcanic_erf": "Effective Radiative Forcing|Natural|Volcanic",
        "ch4_erf": "Effective Radiative Forcing|Anthropogenic|CH4",
        "co2_erf": "Effective Radiative Forcing|Anthropogenic|CO2",
        "n2o_erf": "Effective Radiative Forcing|Anthropogenic|N2O",
        "other_wmghg_erf": "Effective Radiative Forcing|Anthropogenic|Other|Other WMGHGs",
    }

    out = pd.DataFrame({"year": np.arange(START_YEAR, END_YEAR + 1)})
    for column, variable in mapping.items():
        out[column] = combine_rcmip_variable(rcmip, variable)["value"]

    out["ghg_erf"] = (
        out["co2_erf"] + out["ch4_erf"] + out["n2o_erf"] + out["other_wmghg_erf"]
    )
    out["ods_erf"] = out["other_wmghg_erf"]

    out = out[
        [
            "year",
            "anthro_erf",
            "ghg_erf",
            "aerosol_erf",
            "solar_erf",
            "volcanic_erf",
            "ch4_erf",
            "ods_erf",
        ]
    ].copy()
    return out


def build_fr_drivers(forcings: pd.DataFrame, mei: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({"year": np.arange(START_YEAR, END_YEAR + 1)})
    out = out.merge(mei, on="year", how="left")
    out = out.merge(forcings[["year", "volcanic_erf", "solar_erf"]], on="year", how="left")
    out = out.rename(columns={"volcanic_erf": "volcanic", "solar_erf": "solar"})
    return out


def main() -> None:
    for _, (url, path) in RAW_FILES.items():
        ensure_download(url, path)

    gmst = load_gmst(RAW_FILES["gistemp"][1])
    mei = load_mei(RAW_FILES["mei"][1])
    rcmip = load_rcmip_forcing(RAW_FILES["rcmip_forcing"][1])
    forcings = build_forcings(rcmip)
    fr_drivers = build_fr_drivers(forcings, mei)

    gmst.to_csv(DATA_DIR / "gmst.csv", index=False)
    fr_drivers.to_csv(DATA_DIR / "fr_drivers.csv", index=False)
    forcings.to_csv(DATA_DIR / "forcings.csv", index=False)

    print("Wrote:")
    for name in ["gmst.csv", "fr_drivers.csv", "forcings.csv"]:
        path = DATA_DIR / name
        df = pd.read_csv(path)
        print(f"  {path}: {len(df)} rows, non-null rows={df.dropna().shape[0]}")


if __name__ == "__main__":
    main()
