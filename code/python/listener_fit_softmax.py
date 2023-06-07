import listener_model_fitting as lmf
from scipy.optimize import minimize_scalar
import numpy as np
import pandas as pd
from sys import argv

model_type = argv[1]

caused_version = "and_hmu_or_ws"
enabled_version = "or_ws"
affected_version = "or_whs"

if model_type == "full":

	full_params = {
		"uncertainty_noise": 0.9,
		"how_not_affect_param": 0.3,
		"stationary_softener": 0.4,
		"unique_softener": 0.4,
		"fine_tune": 1.25,
		"caused_version": caused_version,
		"enabled_version": enabled_version,
		"affected_version": affected_version
	}

	model_predictions, opt_beta = lmf.fit_and_compute_softmax(full_params, lmf.scaled_human_responses, model_type)
	df_model = lmf.convert_predictions_to_dataframe(model_predictions, lmf.trial_comparison_indices, lmf.trial_utterance_values)

	filename = "model_performance/listener_full_model_predictions.csv"

elif model_type == "no_pragmatics":

	sem_params = {
		"uncertainty_noise": 1.0,
		"how_not_affect_param": 1.0,
		"stationary_softener": 1.0,
		"unique_softener": 1.0,
		"fine_tune": 2.5,
		"caused_version": caused_version,
		"enabled_version": enabled_version,
		"affected_version": affected_version
	}

	model_predictions, opt_beta = lmf.fit_and_compute_softmax(sem_params, lmf.scaled_human_responses, model_type)
	df_model = lmf.convert_predictions_to_dataframe(model_predictions, lmf.trial_comparison_indices, lmf.trial_utterance_values)

	filename = "model_performance/listener_no_pragmatics_predictions.csv"

elif model_type == "regression":

	speaker_regression = pd.read_csv("model_performance/speaker_regression_predictions.csv")
	reg_pairings = lmf.get_trial_pairings(speaker_regression, lmf.trial_comparison_indices, lmf.trial_utterance_values)

	opt_beta = minimize_scalar(lmf.fit_square_error, args=(reg_pairings, lmf.scaled_human_responses))["x"]
	fit_reg_values = lmf.softmax_normalize(reg_pairings, beta=opt_beta)

	df_model = lmf.convert_predictions_to_dataframe(fit_reg_values.T, lmf.trial_comparison_indices, lmf.trial_utterance_values)
	filename = "model_performance/listener_regression_predictions.csv"

elif model_type == "participant":

	exp2_means = pd.read_csv("../../data/experiment2/participant_means.csv")
	exp2_pairings = lmf.get_trial_pairings(exp2_means, lmf.trial_comparison_indices, lmf.trial_utterance_values, model_type="participant")

	opt_beta = minimize_scalar(lmf.fit_square_error, args=(exp2_pairings, lmf.scaled_human_responses))["x"]
	fit_part_values = lmf.softmax_normalize(exp2_pairings, beta=opt_beta)

	df_model = lmf.convert_predictions_to_dataframe(fit_part_values.T, lmf.trial_comparison_indices, lmf.trial_utterance_values)
	filename = "model_performance/listener_part_means_predictions.csv"



print()
print("Softmax beta:", np.round(opt_beta, decimals=2))
print()
df_model.to_csv(filename)