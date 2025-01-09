import numpy as np
import pandas as pd
from scipy.optimize import minimize
from itertools import product
import json
import copy

###################################
# Determine valid definition sets #
###################################

propositions = ['w', 'h', 's']
ind_dict = {"w": 0, "h": 1, "s": 2}
# All possible worlds
poss_worlds = list(product([True, False], repeat=len(propositions)))

# All possible definitions for individual words
definitions = ["w", "h", "s",
                "w|h", "w|s", "h|s", "w&h", "w&s", "h&s",
                "w|h|s", "w|(h&s)", "(w|h)&s", "(w|s)&h", "w&(h|s)", "(w&h)|s", "(w&s)|h", "w&h&s"]


# Procedure to evaluate a the truth of a definition in a particular world (truth_value)
def evaluate(definition, world):

    if len(definition) == 1:
        ind = ind_dict[definition]
        # print(world)
        # print(ind)
        return world[ind]
    
    elif len(definition) == 3:
        if definition[1] == "|":
            return evaluate(definition[0], world) or evaluate(definition[2], world)
        elif definition[1] == "&":
            return evaluate(definition[0], world) and evaluate(definition[2], world)
        else:
            raise ValueError("Invalid definition")
    
    elif "(" in definition and ")" in definition:
        # extract the part of the definition that is in the parentheses
        start = definition.index("(")
        end = definition.index(")")
        sub_def = definition[start+1:end]
        paren_eval = evaluate(sub_def, world)

        # remove the sub_def from the definition
        rm_paren = definition.replace(f"({sub_def})", "")

        if "|" in rm_paren:
            rm_prop = rm_paren.replace("|", "")
            return evaluate(rm_prop, world) or paren_eval
        elif "&" in rm_paren:
            rm_prop = rm_paren.replace("&", "")
            return evaluate(rm_prop, world) and paren_eval
        else:
            raise ValueError("Invalid definition")
        
    elif len(definition) == 5:
        if "|" in definition:
            return evaluate(definition[0], world) or evaluate(definition[2], world) or evaluate(definition[4], world)
        elif "&" in definition:
            return evaluate(definition[0], world) and evaluate(definition[2], world) and evaluate(definition[4], world)
        else:
            raise ValueError("Invalid definition")
        
    else:
        raise ValueError("Invalid definition")
    

# For each definition, determine the set of possible worlds in which it is true
def_poss_worlds = {}

for defi in definitions:
    def_set = set()
    for world in poss_worlds:
        if evaluate(defi, world):
            def_set.add(world)
    def_poss_worlds[defi] = def_set


# For each definition, determine the set of definitions that it implies
imp_dict = {}

for def1 in definitions:

    def_list = []
    for def2 in definitions:
        if def1 != def2:
            pw1 = def_poss_worlds[def1]
            pw2 = def_poss_worlds[def2]

            if pw1.issubset(pw2):
                def_list.append(def2)

    imp_dict[def1] = def_list


# Determine all the sets of three definitions, where the first implies the second, and the second implies the third
valid_def_sets = []

for defi in definitions:
    for imp_def in imp_dict[defi]:
        for imp2_def in imp_dict[imp_def]:
            valid_def_sets.append((defi, imp_def, imp2_def))

################################
# Evaluate the definition sets #
################################


# Load data and aspects
w, h, s, m, o, u = (0, 1, 2, 3, 4, 5)
vocab = ["cause", "enable", "affect", "no_difference"]

df_human = pd.read_csv("../../data/experiment2/speaker_task_clean.csv")

response_list = [copy.copy([]) for _ in range(30)]

for row in df_human.iterrows():
    # get the trial number and response
    tr = row[1]["trial"]
    resp = row[1]["response"]

    response_list[tr].append(vocab.index(resp))

resp_array = np.array(response_list)

# Uncertainty noise based on Gerstenberg et al. 2021 (CSM paper)
with open("aspects_paper/aspects_noise_0.9_samples_1000.json", "r") as f:
    aspects_json = json.load(f)

aspects = np.array([asp["rep"] for asp in aspects_json[0]])[:30, :]


# RSA and definition set evaluation functions
def disjunction (a, b):
    return a + b - (a * b)

def conjunction (a, b):
    return a * b

def compute_def(definition, aspects):

    whe = aspects[:, w]
    how = aspects[:, h]
    suf = aspects[:, s]
    
    if definition == "w":
        return whe
    
    elif definition == "h":
        return how
    
    elif definition == "s":
        return suf
    
    elif definition == "w|h":
        return disjunction(whe, how)
    
    elif definition == "w|s":
        return disjunction(whe, suf)
    
    elif definition == "h|s":
        return disjunction(how, suf)
    
    elif definition == "w&h":
        return conjunction(whe, how)
    
    elif definition == "w&s":
        return conjunction(whe, suf)
    
    elif definition == "h&s":
        return conjunction(how, suf)
    
    elif definition == "w|h|s":
        return disjunction(disjunction(whe, how), suf)
    
    elif definition == "w|(h&s)":
        return disjunction(whe, conjunction(how, suf))
    
    elif definition == "(w|h)&s":
        return conjunction(disjunction(whe, how), suf)
    
    elif definition == "(w|s)&h":
        return conjunction(disjunction(whe, suf), how)
    
    elif definition == "w&(h|s)":
        return conjunction(whe, disjunction(how, suf))
    
    elif definition == "(w&h)|s":
        return disjunction(conjunction(whe, how), suf)
    
    elif definition == "(w&s)|h":
        return disjunction(conjunction(whe, suf), how)
    
    elif definition == "w&h&s":
        return conjunction(conjunction(whe, how), suf)
    
    else:
        raise ValueError("Invalid definition")
    
def made_no_diff(aspects, nap):
    whe = aspects[:, w]
    how = aspects[:, h]
    suf = aspects[:, s]

    not_whe = 1 - whe
    not_how = 1 - how
    not_suf = 1 - suf

    soft_not_how = disjunction(not_how, nap)

    return conjunction(conjunction(not_whe, soft_not_how), not_suf)

def meaning(verb_defs, nap, aspects):
    sem_evals = [compute_def(defi, aspects) for defi in verb_defs]
    sem_evals.append(made_no_diff(aspects, nap))

    return np.array(sem_evals).T

def softmax(x, beta, axis):
    expo = np.exp(beta * x)
    summands = np.sum(expo, axis=axis)
    if axis == 1:
        return expo / summands[:, None]
    else:
        return expo / summands[None, :]
    
def l0(verb_defs, nap, aspects):
    sem_evals = meaning(verb_defs, nap, aspects)
    return sem_evals/sem_evals.sum(axis=0)[None, :]

def s1(verb_defs, nap, so, aspects):
    lit_list = l0(verb_defs, nap, aspects)
    return softmax(lit_list, so, 1)

def l1(verb_defs, nap, so, aspects):
    speaker_probs = s1(verb_defs, nap, so, aspects)
    return speaker_probs/speaker_probs.sum(axis=0)[None, :]

def s2(verb_defs, nap, so, aspects):
    listener_probs = l1(verb_defs, nap, so, aspects)
    return softmax(listener_probs, so, 1)


def compute_likelihood(model_pred, human_resp):

    # smooth model_pred so there are no zero values
    model_pred_smooth = model_pred + 0.001
    model_pred_smooth = model_pred_smooth / model_pred_smooth.sum(axis=1)[:, None]

    rows = np.arange(human_resp.shape[0])[:, None]
    resp_probs = model_pred_smooth[rows, human_resp]

    return np.sum(np.log(resp_probs))

def eval_model_params(params, definitions, aspects, human_resp):
    nap, so = params
    model_pred = s2(definitions, nap, so, aspects)
    return -compute_likelihood(model_pred, human_resp)


# Run Evaluation

def_comp_dict = {
    "caused": [],
    "enabled": [],
    "affected": [],
    "nll": [],
    "nap": [],
    "so": []
}

for def_set in valid_def_sets:
    opt = minimize(eval_model_params, (0.5, 1), args=(def_set, aspects, resp_array), method="L-BFGS-B", bounds=[(0, 1), (0, None)])
    def_comp_dict["caused"].append(def_set[0])
    def_comp_dict["enabled"].append(def_set[1])
    def_comp_dict["affected"].append(def_set[2])
    def_comp_dict["nll"].append(opt["fun"])
    def_comp_dict["nap"].append(opt["x"][0])
    def_comp_dict["so"].append(opt["x"][1])

df_def_comp = pd.DataFrame(def_comp_dict)
df_def_comp = df_def_comp.sort_values("nll").reset_index(drop=True)
df_def_comp["nll"] = df_def_comp["nll"].round(2)

df_def_comp.to_csv("semantics_ranking.csv", index=False)
