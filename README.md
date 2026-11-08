Quick Start: You don't need to rebuild the data, the model ready table is committed.

Any notebook in Notebooks can be started with 

```python 
import sys; sys.path.append("../src/models")
from model_setup import *
```

That import loads the data and gives you the feature lists, the train/test split, the CV folds, and the helper functions.


## Repo map

```
data/processed/model_ready_billz.csv - modeling table (one row per bill)

src/data/ - scripts that build the table

(run order in src/data/README.md)

src/models/model_setup.py - the shared features, split, CV folds, evaluate(), tune_weights()

Notebooks/

    Exploratory_Data_Analysis.ipynb - EDA; figures saved to /figures

    04_baseline_models.ipynb - dummy and logistic regression

    04b_random_forest.ipynb - decision tree and random forest tuning

    04c_gradient_boost.ipynb - HistGradientBoost tuning

    05_unsupervised.ipynb - TODO: clustering / PCA

    06_final_model_eval.ipynb - TODO: one-time eval on 118th congress

results/ - saved grid results, best params, class weights, comparison table

Miscellaneous/ - old data dictionary, notes on how datasets join

AI_README.md - AI usage log (add own section)


