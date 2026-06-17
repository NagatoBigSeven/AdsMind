# Third-Party Data Notice

The MIT [LICENSE](../LICENSE) covers the AdsMind source code. The curated
benchmark structures under `datasets/` are derived from third-party sources that
carry their own licenses and citation requirements. If you use these inputs,
please honor the upstream terms and cite the original work in addition to
AdsMind.

## `cmu20/` (manuscript label: AA20)

Generated locally by [`cmu20/download_cmu20_dataset.py`](cmu20/download_cmu20_dataset.py)
from **Materials Project** bulk structures (the `mp-...` identifiers listed in
that script), with adsorbate slabs constructed through the **FAIR-Chem / Open
Catalyst Project** demo API (`fairchem.demo.ocpapi`, AdsorbML).

- Materials Project crystal data is released under **CC-BY-4.0** and must be
  attributed. Cite: A. Jain et al., "Commentary: The Materials Project: A
  materials genome approach to accelerating materials innovation," *APL
  Materials* 1, 011002 (2013).
- FAIR-Chem / `fairchem` tooling is under the **MIT** license. Cite the Open
  Catalyst 2020 (OC20) dataset (L. Chanussot et al., *ACS Catalysis* 11, 6059,
  2021) and AdsorbML (J. Lan et al., *npj Computational Materials* 9, 172, 2023).

## `ocd62/` (manuscript label: OCD-GMAE62) and `ocd62_overlap12/`

Constructed from the **OCD-GMAE** dataset in
[schwallergroup/AdsMT](https://github.com/schwallergroup/AdsMT) (**MIT** license).

- Cite: J. Chen, X. Huang, C. Hua, Y. He, and P. Schwaller, "A multi-modal
  transformer for predicting global minimum adsorption energy," *Nature
  Communications* 16, 3232 (2025).

## `samples/`

Small hand-picked surfaces used only for documentation examples and the test
suite. They are not part of any benchmark.
