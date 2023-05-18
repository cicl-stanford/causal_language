import listener_model_fitting as lmf
import numpy as np
import pandas as pd
from sys import argv

model_type = argv[1]

num_trials = 36
num_splits = 100

trial_ind = np.arange(num_trials, dtype=int)
split_ind = np.zeros((num_trials, num_splits), dtype=int)

np.random.seed(1)

for spl_num in range(num_splits):
	split = np.random.permutation(trial_ind)
	split_ind[:,spl_num] = split

train_ind = split_ind[np.arange((num_trials/2), dtype=int), :]
test_ind = split_ind[np.arange((num_trials/2), num_trials, dtype=int), :]

if model_type == "full":

	params = {
		"uncertainty_noise": 0.9,
		"how_not_affect_param": 0.3,
		"stationary_softener": 0.4,
		"unique_softener": 0.4,
		"fine_tune": 1.25,
		"caused_version": "and_hmu_or_ws",
		"enabled_version": "or_ws",
		"affected_version": "or_whs"
	}


elif model_type == "no_pragmatics":

	params = {
		"uncertainty_noise": 1.0,
		"how_not_affect_param": 1.0,
		"stationary_softener": 1.0,
		"unique_softener": 1.0,
		"fine_tune": 2.5,
		"caused_version": "and_hmu_or_ws",
		"enabled_version": "or_ws",
		"affected_version": "or_whs"
	}

elif model_type == "regression":

	params = None

else:

	raise Exception("Model type '{}' not implemented.".format(model_type))


df_cv = lmf.cross_validate(train_ind, test_ind, model_type, params)
df_cv.to_csv("model_performance/cv_listener_{}.csv".format(model_type))
