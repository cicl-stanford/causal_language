import numpy as np
import pandas as pd
from scipy.optimize import minimize
import rsa
import pickle
import copy

w, h, s, m, u, o = (0, 1, 2, 3, 4, 5)
vocab = ["cause", "enable", "affect", "no_difference"]

#################
# Load the data #
#################

df_resp = pd.read_csv("../../data/experiment2/speaker_task_clean.csv")

response_list = [copy.copy([]) for _ in range(30)]

for row in df_resp.iterrows():
    # get the trial number and response
    tr = row[1]["trial"]
    resp = row[1]["response"]

    response_list[tr].append(vocab.index(resp))

resp_array = np.array(response_list)

proportions = []

for row in resp_array:
    counts = np.bincount(row, minlength=4)
    row_proportions = counts / len(row)
    proportions.append(row_proportions)

# Convert the list to a NumPy array
proportions_array = np.array(proportions)

##############
# Procedures #
##############

def convert_pred_to_df(pred, vocab=["cause", "enable", "affect", "no_difference"]):
    pred_dict = {
        "trial": [],
        "response": [],
        "model_y": []
    }

    for i, row in enumerate(pred):
        for j, resp in enumerate(vocab):
            pred_dict["trial"].append(i)
            pred_dict["response"].append(resp)
            pred_dict["model_y"].append(row[j])

    return pd.DataFrame(pred_dict)
        

def compute_likelihood(model_pred, human_resp):

    rows = np.arange(human_resp.shape[0])[:, None]
    resp_probs = model_pred[rows, human_resp]

    return np.sum(np.log(resp_probs))

def eval_model_params(params, aspects, human_resp, simple=False, model="full", trial_set=None):
    if simple:
        so, nap = params
        softener = None
    else:
        so, nap, softener = params
    if model == "full":
        model_pred = rsa.s2(aspects, so, nap=nap, softener=softener)
    elif model == "semantics":
        model_pred = rsa.semantics(aspects, so, nap=nap, softener=softener)
    else:
        raise ValueError("model must be 'full' or 'semantics'")
    
    if trial_set is not None:
        model_pred = model_pred[trial_set, :]
        assert model_pred.shape[0] == human_resp.shape[0]

    return -compute_likelihood(model_pred, human_resp)

def optimize_model(resp_array, simple=False, model="full", trial_set=None):
    unoise_range = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6]
    opt_list = []

    for unoise in unoise_range:
        aspects = rsa.load_aspects(unoise=unoise)
        if simple:
            opt = minimize(eval_model_params, [1.0, 0.5], args=(aspects, resp_array, simple, model, trial_set), bounds=[(0, None), (0, 1)])
        else:
            opt = minimize(eval_model_params, [1.0, 0.5, 0.5], args=(aspects, resp_array, simple, model, trial_set), bounds=[(0, None), (0, 1), (0, 1)])
        opt_list.append((unoise, opt))

    return min(opt_list, key=lambda x: x[1].fun)

def cross_val(splits, resp_array, proportions, model="full", simple=False):

    out_dict = {
        "split": [],
        "model": [],
        "unoise": [],
        "cause_soft": [],
        "nap": [],
        "so": [],
        "use": [],
        "trial": [],
        "verb": [],
        "model_pred": [],
        "data_val": [],
    }

    for i, split in enumerate(splits):
        if i % 10 == 0:
            print(f"Split {i}")
        train_tr, test_tr = split

        train_data = resp_array[train_tr, :]
        # test_data = resp_array[test_tr, :]
        
        opt = optimize_model(train_data, simple=simple, model=model, trial_set=train_tr)

        aspects = rsa.load_aspects(unoise=opt[0])

        if simple:
            opt_so, opt_nap = opt[1].x
            opt_softener = None
        else:
            opt_so, opt_nap, opt_softener = opt[1].x

        if model == "full":
            model_pred = rsa.s2(aspects, opt_so, nap=opt_nap, softener=opt_softener)
        elif model == "semantics":
            model_pred = rsa.semantics(aspects, opt_so, nap=opt_nap, softener=opt_softener)
        else:
            raise ValueError("model must be 'full' or 'semantics'")
        
        for tr in train_tr + test_tr:
            for j, verb in enumerate(vocab):
                out_dict["split"].append(i)
                out_dict["model"].append(model)
                out_dict["unoise"].append(opt[0])
                out_dict["cause_soft"].append(opt_softener)
                out_dict["nap"].append(opt_nap)
                out_dict["so"].append(opt_so)
                out_dict["use"].append("train" if tr in train_tr else "test")
                out_dict["trial"].append(tr)
                out_dict["verb"].append(verb)
                out_dict["model_pred"].append(model_pred[tr, j])
                out_dict["data_val"].append(proportions[tr, j])

    return pd.DataFrame(out_dict)

##############
# Fit Models #
##############

np.random.seed(3)

# Full Model
opt_full = optimize_model(resp_array, simple=False, model="full")

aspects = rsa.load_aspects(unoise=opt_full[0])
opt_so, opt_nap, opt_softener = opt_full[1].x
full_model_pred = rsa.s2(aspects, opt_so, nap=opt_nap, softener=opt_softener)

print("Full Model")
print("Unoise:", opt_full[0])
print("Cause Softener:", np.round(opt_softener, 2))
print("No Difference Softener:", np.round(opt_nap, 2))
print("Speaker Optimality:", np.round(opt_so, 2))
print()

df_full_model = convert_pred_to_df(full_model_pred)

df_full_model.to_csv("model_performance/speaker_full_model_predictions.csv")

# Semantics Model
opt_sem = optimize_model(resp_array, simple=False, model="semantics")

aspects = rsa.load_aspects(unoise=opt_sem[0])
opt_so, opt_nap, opt_softener = opt_sem[1].x
sem_model_pred = rsa.semantics(aspects, opt_so, nap=opt_nap, softener=opt_softener)

print("Semantics Model")
print("Unoise:", opt_sem[0])
print("Cause Softener:", np.round(opt_softener, 2))
print("No Difference Softener:", np.round(opt_nap, 2))
print("Speaker Optimality:", np.round(opt_so, 2))
print()

df_sem_model = convert_pred_to_df(sem_model_pred)

df_sem_model.to_csv("model_performance/speaker_no_pragmatics_predictions.csv")

# Simple Full Model
opt_simple_full = optimize_model(resp_array, simple=True, model="full")

aspects = rsa.load_aspects(unoise=opt_simple_full[0])
opt_so, opt_nap = opt_simple_full[1].x
simple_full_model_pred = rsa.s2(aspects, opt_so, nap=opt_nap)

print("Simple Full Model")
print("Unoise:", opt_simple_full[0])
print("No Difference Softener:", np.round(opt_nap, 2))
print("Speaker Optimality:", np.round(opt_so, 2))
print()

df_simple_full_model = convert_pred_to_df(simple_full_model_pred)

df_simple_full_model.to_csv("model_performance/speaker_full_model_simple_predictions.csv")

# Simple Semantics Model
opt_simple_sem = optimize_model(resp_array, simple=True, model="semantics")

aspects = rsa.load_aspects(unoise=opt_simple_sem[0])
opt_so, opt_nap = opt_simple_sem[1].x
simple_sem_model_pred = rsa.semantics(aspects, opt_so, nap=opt_nap)

print("Simple Semantics Model")
print("Unoise:", opt_simple_sem[0])
print("No Difference Softener:", np.round(opt_nap, 2))
print("Speaker Optimality:", np.round(opt_so, 2))
print()

df_simple_sem_model = convert_pred_to_df(simple_sem_model_pred)

df_simple_sem_model.to_csv("model_performance/speaker_no_pragmatics_simple_predictions.csv")

####################
# Cross Validation #
####################

with open("crossv_splits.pickle", "rb") as f:
    crossv_splits = pickle.load(f)

print("Full Model Cross Validation")
full_cv = cross_val(crossv_splits, resp_array, proportions_array, model="full")
full_cv.to_csv("model_performance/cv_speaker_full_model.csv")
print()

print("Semantics Model Cross Validation")
sem_cv = cross_val(crossv_splits, resp_array, proportions_array, model="semantics")
sem_cv.to_csv("model_performance/cv_speaker_no_pragmatics.csv")
print()

print("Full Simple Model Cross Validation")
simple_full_cv = cross_val(crossv_splits, resp_array, proportions_array, model="full", simple=True)
simple_full_cv.to_csv("model_performance/cv_speaker_full_model_simple.csv")
print()

print("Semantics Simple Model Cross Validation")
simple_sem_cv = cross_val(crossv_splits, resp_array, proportions_array, model="semantics", simple=True)
simple_sem_cv.to_csv("model_performance/cv_speaker_no_pragmatics_simple.csv")
print()