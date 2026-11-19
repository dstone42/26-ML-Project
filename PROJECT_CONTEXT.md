# CRC cross-omics project notes

## What we are trying to do

**Project title:** *Predicting Colorectal Cancer Biomarker Gene Expression from
DNA Methylation and Copy Number Alterations*

This is a course project proposed by Calder Lake and David Stone. We want to
ask whether genome-wide tumor DNA methylation and copy-number alteration (CNA)
profiles can predict the RNA expression of selected colorectal-cancer (CRC)
biomarker genes. Along the way, we also want to identify predictive features
that are stable enough to be worth discussing.

This is a same-tumor, cross-omics prediction project. It is not a survival or
clinical-outcome study, and it is not a causal-inference study. The longer-term
motivation is a tumor-tissue proof of concept for future cfDNA-methylation
work. We should not present results from tumor tissue as evidence that the
same approach will work in cfDNA: tumor fraction, sampling, and measurement
are different.

## Data

We are using the TCGA PanCancer Atlas colon and rectal cancer study (COADREAD)
downloaded from cBioPortal. The raw study files are in
`Project/coadread_tcga_pan_can_atlas_2018/`.

| What it is for | File | What is in it |
| --- | --- | --- |
| RNA targets | `data_mrna_seq_v2_rsem.txt` | 20,531 genes across 593 samples |
| CNA predictors | `data_log2_cna.txt` | Log2 copy-number values across 593 samples |
| Methylation predictors | `data_methylation_hm450.txt` | 396,064 CpG probes across 382 samples |

For analyses that use all three data types, we need to work with the samples
shared across all three matrices (at most 382 tumors). Before modelling, we
should confirm the sample IDs, check for duplicate samples or patients, look
at missingness, and transpose the matrices as needed. The source files have
features in rows and samples in columns; our modelling tables should have
samples in rows.

## Decisions we have already made

- The outcomes are continuous RNA-expression values for a small set of CRC
  biomarker genes, so this is a regression project.
- We will choose the final targets from CRC literature before looking at model
  performance. The final report should explain why we chose them.
- We will not limit predictors to CpGs or CNA features near the target gene.
  The point is to give the models genome-wide information and let feature
  selection identify potentially distal signals.
- Our main learners will be elastic-net regressions, with hyperparameters
  tuned by cross-validation.
- For each RNA target, we will compare a methylation-only model, a CNA-only
  model, and an integrated model.
- Selected CpGs or CNA genes are predictive features, not proven regulators.
  A feature that is selected in one model is not necessarily uniquely important
  or causal, especially when many features are correlated.

## Potential RNA targets

The main targets should be important CRC biomarkers in their own right. We do
not want to choose a target simply because a known local methylation-expression
relationship makes it easy to predict. The interesting question is whether
methylation predicts an independently meaningful RNA biomarker.

| Candidate | Why it is worth considering | Important caveat |
| --- | --- | --- |
| `EREG` | An EGFR-ligand biomarker with prognostic and anti-EGFR-treatment relevance in metastatic, RAS-wild-type CRC. | This dataset contains primary tumors and no treatment-response outcome. We can predict `EREG` expression, not treatment benefit. |
| `FAP` | A strong marker of the stromal/mesenchymal CMS4 phenotype, which is associated with poor prognosis and therapy resistance. | Much of the bulk-tissue signal comes from fibroblasts/stroma. Prediction may reflect microenvironment composition rather than tumor-cell-intrinsic regulation. |
| `CDX2` | A colorectal epithelial-differentiation and prognostic biomarker; low expression has been associated with worse outcomes. | This gives us a more tumor-cell-intrinsic contrast to `FAP`. |
| `MUC2` | Relevant to mucinous and MSI-associated CRC biology and to mucin-rich versus canonical phenotypes. | This is a phenotype/differentiation biomarker, not a direct treatment-selection biomarker. |

`MLH1` is a possible **positive control**, separate from the main panel.
Promoter methylation and reduced `MLH1` expression are already well established
in sporadic MSI CRC. If a methylation-only model predicts it well, that is a
useful check that the pipeline can recover a known relationship—not the main
new finding of the project.

`ERBB2` and `HNF4A` are also CRC-relevant, but they are not first choices for
the main panel because known copy-number/amplification relationships could make
the CNA comparison fairly straightforward.

## Aims

### 1. Interpretability

For each target we choose, fit separate genome-wide methylation-only and
CNA-only elastic-net models. We will look for features that are selected
consistently, report coefficient directions, and see whether they remain useful
in the integrated model. The result should be a short list of stable candidate
features for biological follow-up, not a claim that we have found causal
regulators.

### 2. RNA-expression prediction

Test whether combining selected methylation and CNA features improves
out-of-sample prediction of each biomarker's RNA expression compared with
using either data type alone.

## Modelling plan

For every target gene, we will evaluate the same three models on the same outer
resampling splits:

1. **Methylation only:** genome-wide CpG predictors, with tuning and feature
   selection done using only the training data.
2. **CNA only:** genome-wide CNA predictors, again tuned and selected using
   only the training data.
3. **Integrated model:** combine the features selected by the two
   modality-specific models, then train and tune a model using only the
   outer-training data.

The key rule is that every decision based on the target—including scaling,
supervised filtering, tuning, feature selection, and forming the integrated
feature set—happens inside the outer training split. The held-out samples are
used once, only for evaluation.

```text
outer training split
  ├─ preprocess methylation → inner-CV tune/select methylation elastic net
  ├─ preprocess CNA         → inner-CV tune/select CNA elastic net
  └─ combine selected features → tune integrated model
outer held-out split
  └─ evaluate all three models once
```

Even unsupervised steps, such as removing all-missing or zero-variance
features, should be fit on the outer training set and then applied to the
held-out set. We should preserve feature names throughout so we can report the
selected CpGs and CNA genes clearly.

## How we will evaluate results

- Use out-of-fold predictions and report RMSE, MAE, and out-of-fold R².
- Use repeated outer cross-validation, or another justified resampling plan,
  to describe uncertainty and selection stability.
- For selected features, report selection frequency and coefficient direction
  across outer training fits. A stable group of correlated features may be more
  informative than naming one feature as the winner.
- The main comparison is held-out accuracy for the integrated model versus
  each single-modality model, not in-sample fit.
- If time permits, a joint genome-wide regularized model could be a useful
  sensitivity analysis. It is an extension, not part of the primary plan.

## What we need to deliver

- Three models for each final RNA target.
- A clear, literature-based rationale for the target list.
- A held-out comparison of methylation-only, CNA-only, and integrated models.
- A table or figure showing consistently selected features and coefficient
  directions, with cautious biological interpretation.

## Key references already in the proposal

- The Cancer Genome Atlas Network (2012), comprehensive molecular
  characterization of colon and rectal cancer.
- Seal et al. (2020), cross-omic estimation of gene expression from DNA
  methylation and copy-number variation.
