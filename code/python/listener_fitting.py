import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
import rsa

###################################
# Global variables and Procedures #
###################################

vocabulary_dataset = ["cause", "enable", "affect", "no_difference"]
vocabulary = ["caused", "enabled", "affected", "no_difference"]
w, h, s, m, u, o = (0,1,2,3,4,5)

participant_means = pd.read_csv("../../data/experiment3/participant_means.csv").drop(columns="Unnamed: 0")
trial_comparison_indices = participant_means[["video_a", "video_b"]].to_numpy()
trial_utterance_values = participant_means[["utterance"]].to_numpy()

def softmax_normalize(arr, beta=1): return rsa.softmax(arr, beta=beta, axis=1)

def convert_utterance(arr): 
    convert_dict = {"caused": 0, "enabled": 1, "affected": 2, "no_difference": 3}
    return np.array([convert_dict[utt[0]] for utt in arr])

trial_utterance_values = convert_utterance(trial_utterance_values)
scaled_human_responses = participant_means.Mean.to_numpy()

def get_trial_pairings(model_type, model_params=None, model_df=None, trial_comparison_indices=trial_comparison_indices, trial_utterance_values=trial_utterance_values):

    if model_type == "full" or model_type == "no_pragmatics":
        assert model_params is not None, "Model Parameters must be provided for full and no_pragmatics models."
        aspects = rsa.load_aspects(unoise=model_params["uncertainty_noise"])
    elif model_type == "regression" or model_type == "participant":
        assert model_df is not None, "Model Dataframe must be provided for regression and participant models."
    else:
        raise Exception("Model Version {} not implemented.".format(model_type))
    
    if model_type == "full":
        model_array = rsa.l1(aspects, model_params["fine_tune"], nap=model_params["how_not_affect_param"], softener=model_params["caused_softener"])
    elif model_type == "no_pragmatics":
        model_array = rsa.l0(aspects, nap=model_params["how_not_affect_param"], softener=model_params["caused_softener"])
    elif model_type == "regression":
        df_pivot = model_df.pivot(index="trial", columns="response", values="model_y").reset_index(drop=True)
        model_array = df_pivot[["cause", "enable", "affect", "no_difference"]].to_numpy()
    elif model_type == "participant":
        df_pivot = model_df.pivot(index="trial", columns="response", values="data_y").reset_index(drop=True)
        model_array = df_pivot[["cause", "enable", "affect", "no_difference"]].to_numpy()

    return model_array[trial_comparison_indices, trial_utterance_values[:,np.newaxis]]

def compute_square_error(beta, human_response, trial_pairings):
    softmax_predictions = softmax_normalize(trial_pairings, beta=beta)
    compare_values = softmax_predictions[:,1]

    return np.sum((human_response - compare_values)**2)

def fit_and_compute_softmax(human_response, trial_pairings):

    optimal_beta = minimize_scalar(compute_square_error, args=(human_response, trial_pairings))['x']
    model_predictions = softmax_normalize(trial_pairings, beta=optimal_beta)

    return model_predictions, optimal_beta

def convert_predictions_to_dataframe(model_predictions, trial_comparison_indices, trial_utterance_values):
    
    data_dict = {"trial":[], "utterance":[], "video_a":[], "video_b":[], "video_a_prob":[], "video_b_prob":[]}
    
    for tr in range(model_predictions.shape[0]):
        
        utterance = vocabulary[trial_utterance_values[tr]]
        clip1 = trial_comparison_indices[tr,0]
        clip2 = trial_comparison_indices[tr,1]
        clip1_prob = model_predictions[tr,0]
        clip2_prob = model_predictions[tr,1]
        
        data_dict['trial'].append(tr)
        data_dict['utterance'].append(utterance)
        data_dict['video_a'].append(clip1)
        data_dict['video_b'].append(clip2)
        data_dict['video_a_prob'].append(clip1_prob)
        data_dict['video_b_prob'].append(clip2_prob)
        
        
    return pd.DataFrame(data_dict)

def cross_validate(model_type, train, test, model_params=None, model_df=None, human_responses=scaled_human_responses, trial_utterance_values=trial_utterance_values):
    
    trial_pairings = get_trial_pairings(model_type, model_params=model_params, model_df=model_df)

    num_splits = train.shape[0]

    model_performance = {
        "split": [],
        "use": [],
        "model": [],
        "beta": [],
        "trial": [],
        "verb": [],
        "model_pred": [],
        "data_val": []
    }

    for split in range(num_splits):

        train_tr = train[split, :]
        test_tr = test[split, :]

        train_pairings = trial_pairings[train_tr, :]
        train_responses = human_responses[train_tr]

        _, opt_beta = fit_and_compute_softmax(train_responses, train_pairings)

        model_predictions = softmax_normalize(trial_pairings, beta=opt_beta)

        for tr in train_tr.tolist() + test_tr.tolist():
            model_performance["split"].append(split)
            model_performance["use"].append("train" if tr in train_tr else "test")
            model_performance["model"].append(model_type)
            model_performance["beta"].append(opt_beta)
            model_performance["trial"].append(tr)
            model_performance["verb"].append(vocabulary[trial_utterance_values[tr]])
            model_performance["model_pred"].append(model_predictions[tr, 1])
            model_performance["data_val"].append(human_responses[tr])

    return pd.DataFrame(model_performance)

##############
# Fit Models #
##############

# Full
full_params = {
    "uncertainty_noise": 1.0,
    "how_not_affect_param": 0.25,
    "caused_softener": 0.65,
    "fine_tune": 40.18,
}

full_trial_pairings = get_trial_pairings("full", model_params=full_params)
full_model_predictions, opt_beta = fit_and_compute_softmax(scaled_human_responses, full_trial_pairings)
print("Full Model")
print("Beta: ", opt_beta)
print()

df_model_full = convert_predictions_to_dataframe(full_model_predictions, trial_comparison_indices, trial_utterance_values)
df_model_full.to_csv("model_performance/listener_full_model_predictions.csv")

# No Pragmatics
sem_params = {
    "uncertainty_noise": 1.0,
    "how_not_affect_param": 1.0,
    "caused_softener": 0.95,
    "fine_tune": 2.54,
}

sem_trial_pairings = get_trial_pairings("no_pragmatics", model_params=sem_params)
sem_model_predictions, opt_beta = fit_and_compute_softmax(scaled_human_responses, sem_trial_pairings)
print("No Pragmatics Model")
print("Beta: ", opt_beta)
print()
df_model_sem = convert_predictions_to_dataframe(sem_model_predictions, trial_comparison_indices, trial_utterance_values)
df_model_sem.to_csv("model_performance/listener_no_pragmatics_predictions.csv")

# Regression
df_reg = pd.read_csv("model_performance/speaker_regression_predictions.csv").drop(columns="Unnamed: 0")

reg_trial_pairings = get_trial_pairings("regression", model_df=df_reg)
reg_model_predictions, opt_beta = fit_and_compute_softmax(scaled_human_responses, reg_trial_pairings)
print("Regression Model")
print("Beta: ", opt_beta)
print()
df_model_reg = convert_predictions_to_dataframe(reg_model_predictions, trial_comparison_indices, trial_utterance_values)
df_model_reg.to_csv("model_performance/listener_regression_predictions.csv")

# Participant
df_part = pd.read_csv("../../data/experiment2/participant_means.csv").drop(columns="Unnamed: 0")

part_trial_pairings = get_trial_pairings("participant", model_df=df_part)
part_model_predictions, opt_beta = fit_and_compute_softmax(scaled_human_responses, part_trial_pairings)
print("Participant Model")
print("Beta: ", opt_beta)
print()
df_model_part = convert_predictions_to_dataframe(part_model_predictions, trial_comparison_indices, trial_utterance_values)
df_model_part.to_csv("model_performance/listener_part_means_predictions.csv")

####################
# Cross Validation #
####################

print("Running Cross Validation")

# Setup train test splits
num_trials = 36
num_splits = 100

trial_ind = np.arange(num_trials, dtype=int)
split_ind = np.zeros((num_splits, num_trials), dtype=int)

np.random.seed(1)
for split in range(num_splits):
    split_ind[split, :] = np.random.permutation(trial_ind)

train_ind = split_ind[:, :int(num_trials/2)]
test_ind = split_ind[:, int(num_trials/2):]

# Full Model
print("Full Model")
df_full_cv = cross_validate("full", train_ind, test_ind, model_params=full_params)
df_full_cv.to_csv("model_performance/cv_listener_full.csv")

# No Pragmatics Model
print("No Pragmatics Model")
df_sem_cv = cross_validate("no_pragmatics", train_ind, test_ind, model_params=sem_params)
df_sem_cv.to_csv("model_performance/cv_listener_no_pragmatics.csv")

# Regression Model
print("Regression Model")
df_reg_cv = cross_validate("regression", train_ind, test_ind, model_df=df_reg)
df_reg_cv.to_csv("model_performance/cv_listener_regression.csv")
