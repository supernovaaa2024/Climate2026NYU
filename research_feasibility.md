# Research Feasibility Assessment: Can This Repo and FaIR Answer the Model Prediction Accuracy Question?

## Short Answer

Yes. This workspace is a strong base for the research question, but not as a one-click replication.

The repo already gives you the simple climate model side of the problem through FaIR and the RCMIP Phase 2 material. What it does not yet include is the observational-regression layer needed to evaluate prediction accuracy against observed temperature records in the style of Foster-Rahmstorf (2011) or Su et al. (2024).

In practice, that means:

- You can reproduce the core forcing-to-temperature simulation workflow with FaIR.
- You can build the statistical attribution layer needed to remove ENSO, volcanic, and solar effects from observed temperatures.
- You can run out-of-sample forecast tests and compare model skill.
- You cannot claim an exact reproduction of Su et al. (2024) unless you match their SCM4OPT v3.3 setup and regression specification closely enough.

## What The Two Papers Contribute

### Foster-Rahmstorf (2011)

This paper is a statistical decomposition of observed temperature time series. It fits temperature against:

- a linear time trend
- ENSO, represented by MEI
- volcanic forcing, represented by aerosol optical depth
- solar variability, represented by total solar irradiance

It also tests lags for the exogenous predictors and accounts for autocorrelation when estimating uncertainty. The core deliverable is not a physical climate model forecast. It is a cleaned temperature series with short-term natural variability removed so that the underlying warming trend can be estimated more clearly.

This is directly reproducible with public data and standard Python regression tools.

### Su et al. (2024)

This paper is methodologically closer to the question of model-based prediction accuracy. It combines a reduced-complexity climate model workflow with regression-based treatment of internal variability. Based on the article metadata and the methodological description you summarized, the key structure is:

- a simple climate model framework, using SCM4OPT v3.3
- species- or forcing-level temperature contributions
- multiple regression using MEI lag terms to represent ENSO-driven variability
- attribution of the 1998-2012 slowdown, especially the role of declining non-CO2 greenhouse gases

This is reproducible in spirit with FaIR, but not necessarily identical in detail. FaIR can play the role of the simple climate model. The missing part is the exact SCM4OPT parameterization and any paper-specific regression design choices not already encoded in this repo.

## What This Repo Already Supports

### 1. FaIR is available and working in the workspace

The active notebook already imports FaIR and reports version 2.2.4. It sets up emissions-driven experiments and uses FaIR's built-in RCMIP data loader. See [trial1.ipynb](/Users/owenhuang/Desktop/Climate/trial1.ipynb#L29) and [trial1.ipynb](/Users/owenhuang/Desktop/Climate/trial1.ipynb#L84).

That means the environment is already capable of:

- running FaIR experiments
- loading standard species properties
- pulling RCMIP historical emissions and forcing inputs
- defining counterfactual scenarios for attribution experiments

### 2. The repo contains RCMIP Phase 2 infrastructure and model-comparison context

The repo is not just a random notebook folder. It includes the full RCMIP Phase 2 project, which already works with multiple reduced-complexity climate models, assessed ranges, and temperature/forcing comparisons. The plotting utilities explicitly include both FaIR and SCM4OPT families in the model palette. See [plotting.py](/Users/owenhuang/Desktop/Climate/rcmip-phase-2/src/utils/plotting.py#L24).

That is useful because it means the repo is already organized around the right objects:

- surface air temperature change
- effective radiative forcing
- scenario-based comparisons
- ensemble-based uncertainty summaries

### 3. The repo documentation confirms the right FaIR capabilities

The RCMIP supplementary text states that FaIR is an emissions-driven simple climate model written in Python, with added concentration-driven functionality and support for deriving CO2 emissions from prescribed concentrations. See [supplementary.tex](/Users/owenhuang/Desktop/Climate/rcmip-phase-2/paper/supplementary.tex#L260).

That matters because it means FaIR can support both of the key use cases behind your research question:

- historical simulation from emissions or prescribed concentrations
- counterfactual attribution experiments for specific forcing pathways

The same text also shows that the RCMIP workflow already evaluated FaIR members against historical temperature observations and selected members based on RMSE against an observational temperature record. See [supplementary.tex](/Users/owenhuang/Desktop/Climate/rcmip-phase-2/paper/supplementary.tex#L262).

So the repo is already adjacent to model-evaluation logic, even if it does not yet package the exact forecast-accuracy analysis you want.

## What Is Missing

The missing pieces are mostly in the observational and statistical layer, not the climate-model layer.

You still need to add or standardize:

- an observed global temperature dataset such as HadCRUT5 or GISTEMP
- ENSO data, ideally NOAA MEI v2
- a clean volcanic forcing series if you want the Foster-Rahmstorf style regression exactly
- a solar forcing series if you want the Foster-Rahmstorf style regression exactly
- a regression and forecasting pipeline, likely with `statsmodels`

If the goal is the Su et al. style hybrid workflow, you also need to decide whether you want:

- exact SCM4OPT replication
- or a FaIR-based analogue that answers the same scientific question

That distinction is important. The second option is much more feasible in this repo.

## What Is Feasible Right Now

### Fully feasible

1. Replicate Foster-Rahmstorf style temperature adjustment.
2. Use FaIR to simulate historical temperature responses under observed forcing pathways.
3. Compare adjusted observed temperatures against FaIR hindcasts.
4. Run counterfactual experiments for methane and ozone-depleting substances.
5. Score forecast skill over withheld periods such as 1998-2012 or 2020-2025.

### Feasible with moderate new code

1. Build a Su-style hybrid pipeline: FaIR species-level or forcing-level contributions plus regression on ENSO indicators.
2. Add residual autocorrelation structure such as AR(1), AR(2), or AR(3).
3. Add secondary modes such as PDO or AMO.
4. Evaluate whether those additions improve hindcast or forecast accuracy.

### Not fully feasible from this repo alone

1. Exact reproduction of SCM4OPT v3.3 results.
2. Exact paper-matched coefficient estimates without the full Su et al. data-processing and model specification.
3. Exact like-for-like comparison with any unpublished preprocessing choices.

## Best Research Framing

The strongest defensible framing is not:

"Can this repo reproduce Su et al. exactly?"

The stronger framing is:

"Can this repo and FaIR implement a reproducible analogue of the Foster-Rahmstorf and Su et al. approaches to test how much predictive skill improves when externally forced temperature response is combined with regression-based adjustment for internal variability?"

That question is well matched to this codebase.

## Recommended Analysis Ladder

### Phase 1: Statistical baseline

Reproduce Foster-Rahmstorf over a modern common period using observed temperature, MEI, volcanic AOD, and solar forcing.

Outputs:

- adjusted temperature series
- trend estimates with autocorrelation-aware uncertainty
- residual diagnostics

### Phase 2: FaIR hindcast baseline

Run FaIR historical experiments over the same interval and compare simulated temperature change to the observed adjusted series.

Outputs:

- hindcast plots
- RMSE and MAE
- trend agreement by subperiod

### Phase 3: Hybrid model

Construct a FaIR-plus-regression model:

- FaIR provides the forced temperature signal or species-level contributions
- regression terms capture ENSO and other short-timescale variability

Outputs:

- in-sample fit comparison against pure regression and pure FaIR
- variance explained
- residual autocorrelation diagnostics

### Phase 4: Forecast evaluation

Train on an earlier cutoff and forecast a later period, for example:

- train through 2010, test 2011-2025
- train through 1997, test 1998-2012

Evaluate:

- RMSE
- MAE
- trend error
- directional accuracy of year-to-year changes

This phase turns the question from attribution to actual predictive performance.

## Expected Findings

The likely result is:

- FaIR alone should capture the externally forced warming component reasonably well.
- Foster-Rahmstorf style regression should reduce noise and clarify the forced trend in observations.
- A hybrid FaIR plus regression model should improve short-horizon fit relative to FaIR alone.
- The improvement will probably come mostly from handling ENSO and other internal variability, not from a fundamentally different long-run forced trend.

That would make the research question scientifically worthwhile and methodologically tractable.

## Bottom-Line Assessment

Yes, this repo can support the research question.

More precisely:

- It already supports the reduced-complexity climate modeling side through FaIR and RCMIP workflows.
- It does not yet contain the observational regression pipeline needed for a full prediction-accuracy study.
- With a small amount of additional data ingestion and analysis code, it can reproduce Foster-Rahmstorf directly and implement a credible FaIR-based analogue of Su et al.
- If your standard is exact SCM4OPT v3.3 replication, then no, this repo alone is not sufficient.
- If your standard is a rigorous, reproducible FaIR-based test of the same scientific question, then yes, it is sufficient.

## Practical Next Step

The highest-value next artifact would be a notebook that does the following in order:

1. ingest observed temperature, MEI, volcanic, and solar series
2. fit the Foster-Rahmstorf baseline regression
3. run FaIR historical and counterfactual simulations
4. merge observed and modeled series on a common monthly timeline
5. evaluate in-sample and out-of-sample predictive skill

That would convert this assessment into an executable research workflow.

- train / validation split
- hindcast or forecast target period
- metrics such as RMSE, MAE, bias, coverage, and correlation
- whether the comparison is on raw temperatures, detrended temperatures, or forced-response estimates

That evaluation layer is not already present here.

## Recommended research path

### Phase 1: Reproduce the repo baseline

Use the existing notebooks and database flow to:

- ingest HadCRUT4
- load submitted FaIR / SCM4OPT historical temperature outputs
- reproduce historical comparison plots

This establishes what the workspace already supports with minimal new code.

### Phase 2: Build a Foster-Rahmstorf style notebook

Add a new notebook that:

- loads observed temperature series
- loads MEI, volcanic aerosol, and solar series
- fits an OLS model over the target window
- computes adjusted temperature series and trend estimates

This is straightforward and fully feasible with public datasets.

### Phase 3: Build a Su et al. style hybrid workflow

Add a notebook or script that:

- loads SCM component temperature responses
- fits the grouped-regression structure against observed temperature
- adds lagged MEI predictors
- compares explained variance and residuals

This is feasible, but it needs an SCM source outside this repo unless you rely only on precomputed submitted outputs.

### Phase 4: Evaluate prediction accuracy explicitly

For a more defensible research result, run:

- rolling-origin hindcasts
- fixed train / test splits
- recent holdout tests such as 2019-2025 if the required observations are available

That is the point where the project becomes a true prediction-accuracy study rather than a historical fit study.

## Assessment of the pasted summary

The pasted summary was directionally right, but two points needed correction:

1. Su et al. (2024) is specifically built around **SCM4OPT v3.3**, not FaIR.
2. This repo supports **analysis of submitted model outputs** and observation comparisons, but it does not by itself ship the full model engines or regression workflows required by the papers.

## Practical conclusion

The repo is a good base for this question if you frame it as:

- comparing historical temperature performance of simple climate model outputs
- reproducing regression-based de-noising and attribution workflows
- extending the repo with explicit hindcast / forecast scoring

It is not enough, unmodified, for a complete end-to-end reproduction of Su et al. (2024) or for a standalone claim about model prediction accuracy.

## Sources

- Foster, G. and Rahmstorf, S. (2011), "Global temperature evolution 1979-2010": [https://doi.org/10.1088/1748-9326/6/4/044022](https://doi.org/10.1088/1748-9326/6/4/044022)
- Su et al. (2024), "Reductions in atmospheric levels of non-CO2 greenhouse gases explain about a quarter of the 1998-2012 warming slowdown": [https://www.nature.com/articles/s43247-024-01723-x](https://www.nature.com/articles/s43247-024-01723-x)
