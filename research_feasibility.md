# Forecast Study Framing

## Research Question

How accurate are global mean temperature forecasts through 2025 when built from:

- the Foster-Rahmstorf (2011) regression-style model over 1979-2010
- the 2024 reduced-complexity hybrid model centered on SCM4OPT v3.3 and MEI-based regression

And how much accuracy improves when those baselines are extended with:

- additional forcings
- extra climate indices
- nonlinear terms
- AR(1), AR(2), and AR(3) residual structure

## Important Comparison Rule

There are two different forecast questions here:

1. Conditional hindcast
   Use realized future ENSO, volcanic, solar, and forcing inputs for 2011-2025.
   This measures model fit given the future drivers.

2. True ex ante forecast
   Use only information available at the forecast origin.
   This is harder because ENSO and volcanic shocks are not known in advance.

The current notebook is set up for the first case unless you add separate forecasts for the exogenous drivers.

## Paper-Specific Model Definitions

### Foster-Rahmstorf (2011)

Use a baseline linear specification with:

- time trend
- ENSO
- volcanic forcing
- solar forcing

This is best treated as a statistical benchmark for separating forced warming from short-term variability.

### 2024 Reduced-Complexity Hybrid

Use a forcing-driven reduced-complexity specification with:

- anthropogenic forcing terms
- natural forcing terms
- methane and ODS terms where available
- ENSO or MEI-based variability adjustment

For an exact paper match, SCM4OPT v3.3 details matter. In this repo, the practical analogue is a forcing-based hybrid model driven by the columns in `data_forecasts/forcings.csv`.

## Fair Evaluation Window

For a clean shared holdout:

- train through December 2010
- forecast January 2011 through December 2025

For a paper-faithful secondary comparison:

- Foster-Rahmstorf style baseline: fit on 1979-2010
- 2024-style hybrid: fit on 1979-2010 or 1998-2010, then compare sensitivity to the training window

## Accuracy Metrics

The notebook should compare models on:

- RMSE
- MAE
- mean bias
- annual error path

If you expand the study, also track:

- correlation
- trend error over 2011-2025
- performance by subperiod such as 2011-2015, 2016-2020, and 2021-2025

## Extension Ladder

### Baselines

- `foster_rahmstorf`
- `forcing_rcm_like`

### Structural extensions

- add quadratic time or forcing terms
- add interactions such as ENSO x volcanic
- add methane and ODS specific terms
- add net forcing contrasts such as GHG minus aerosol forcing

### Time-series extensions

- AR(1) residual correction
- AR(2) residual correction
- AR(3) residual correction

### Additional predictors worth testing

- PDO
- AMO
- NAO
- additional aerosol breakdowns
- alternative solar or volcanic reconstructions

## Role of GAMS

GAMS is not needed for the baseline notebook workflow.

It becomes useful if you want to formalize:

- constrained model selection
- parameter estimation under explicit optimization objectives
- scenario design with multiple competing forecast targets

For the current repo, Python is the simpler default. GAMS or GAMSPy is more useful once the study turns into a structured optimization problem rather than a direct forecast comparison.

## Sources

- Foster and Rahmstorf (2011): https://ui.adsabs.harvard.edu/abs/2011ERL.....6d4022F/abstract
- Su et al. (2024): https://www.nature.com/articles/s43247-024-01723-x
- GAMS: https://www.gams.com/
