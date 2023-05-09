import numpy as np
import pandas as pd
from scipy.stats import multinomial
import rsa
import pickle
import sqlite3
import json
import time

vocabulary_dataset = ["cause", "enable", "affect", "no_difference"]
vocabulary = ["caused", "enabled", "affected", "didn't affect"]
w, h, s, m, o, u = (0, 1, 2, 3, 4, 5)

trial_max = 31

############################################
# Load data from sql file and format as df #
############################################

# Code to load the data from the sql file
database_path = "../../data/speaker_experiment_anonymized.db"
experiment = "forced_choice_2"

# connect to sql database
con = sqlite3.connect(database_path)
df_sql = pd.read_sql_query("SELECT * from language", con)

# filter database based on experiment, status, and completion
is_live = df_sql["mode"] == "live"
is_experiment = df_sql["codeversion"] == "forced_choice_2"
is_complete = df_sql["status"].isin([3,4,5])

df_sql = df_sql[is_live & is_experiment & is_complete]

# Load the data from each entry in the database
data_objects = [json.loads(x) for x in df_sql["datastring"]]


# Create a dataframe
data = []
for participant in range(len(data_objects)):
    data_obj = data_objects[participant]

  # number of trials including attention check
    for j in range(trial_max):
        trialdata = data_obj["data"][j]['trialdata']
        trial = trialdata["id"]
        response = trialdata['response']

        data.append([participant, trial, response])


df_data = pd.DataFrame(data, columns = ["participant", "trial", "response"])

df_data.sort_values(by = ['participant', 'trial'], inplace=True)

# filter out participant that failed attention check
attention_check_fail = df_data[(df_data['trial'] == 30) & (df_data['response'] != 'no_difference')]
excluded_participants = attention_check_fail['participant']

df_data = df_data[~df_data['participant'].isin(excluded_participants)]

# filter out the attention check
df_data = df_data[~(df_data["trial"] == 30)]

vocab = np.array(['cause', 'enable', 'affect', 'no_difference'])
def convert_verb(response):
    return (vocab == response).astype(int)

# Adds a column with a vector representation of the selection for easy tally
# Order of the vector is determined by the vocap array
df_data = df_data.assign(vec_response = list(map(convert_verb, df_data['response'])))

# sum vectors over trial
trial_counts = df_data.groupby(["trial"]).vec_response.apply(np.sum)

trial_counts = np.array(trial_counts.values.tolist()).T
data_averaged = trial_counts/np.sum(trial_counts, axis = 0)


######################
# Fitting Procedures #
######################

# Fitting objectives
# Square error
def compute_error(model_output, trial_set):
    data_set = data_averaged[:, trial_set]
    model_set = model_output[:, trial_set]
    
    sq_err = np.sum((data_set - model_set)**2)
    
    return sq_err

# Data Likelihood
def compute_likelihood(model_output, trial_set):
    
    # Smooth the data so there are no negative infinite logs
    smooth_model = model_output + 0.01
    norm_smooth_model = smooth_model/np.sum(smooth_model, axis=0)
    
    data_counts = trial_counts[:,trial_set]
    model_probs = norm_smooth_model[:,trial_set]
    
    n = np.sum(data_counts, axis=0)[0]
    
    # Compute the log probability
    log_probs = multinomial.logpmf(data_counts.T, n, model_probs.T)
    
    return np.sum(log_probs)


# Computes the semantic values for the No Pragmatics Model
# given a parameter set. Assumes aspects are pre-computed
def compute_meanings(aspects, 
                     nap,
                     sta_soft,
                     unique,
                     caused_version,
                     enabled_version="or_ws",
                     alternative_aspect_values=None,
                     affected_version="or_whs"):
    meanings = []
    for word in ["caused", "enabled", "affected", "didn't affect"]:
        meanings.append(rsa.meaning(word, 
                                    aspects,
                                    caused_version,
                                    enabled_version,
                                    nap,
                                    sta_soft,
                                    unique_softener=unique,
                                    alternative_aspect_values=alternative_aspect_values,
                                    affected_version=affected_version))
        
    meanings = np.vstack(meanings)
    return meanings


# Subroutine for fitting the fine tune paramater (speaker optimality
# for full model, beta param for no pragmatics model)
# Takes a pre-determined parameter set along with a fine_tune parameter
# range to sweep across. Also requires the performance dictionary to add
# model performance values to.
def fit_fine_tune(fine_tune_range, 
                  perf_dict,
                  lesion_rsa,
                  aspects,
                  unoise,
                  nap,
                  sta_soft,
                  unique,
                  caused_version="and_hmu_or_ws",
                  enabled_version="or_ws",
                  alternative_aspects=None,
                  speaker_level=2,
                  affected_version="or_whs",
                  trial_set=np.arange(30),
                  error_type="sq_err"):
    
    if lesion_rsa:
        
        meanings = compute_meanings(aspects,
                                    nap,
                                    sta_soft,
                                    unique,
                                    caused_version,
                                    enabled_version=enabled_version,
                                    alternative_aspect_values=alternative_aspects,
                                    affected_version=affected_version)
        
        for beta in fine_tune_range:
            
            semantic_values = rsa.softmax(meanings, 0, beta=beta)
            if error_type == "sq_err":
                err = compute_error(semantic_values, trial_set)
            elif error_type == "log_like":
                err = compute_likelihood(semantic_values, trial_set)
            else:
                raise Exception("Error type {} not implemented".format(error_type))
                
            perf_dict['unoise'].append(unoise)
            perf_dict['not_affect_param'].append(nap)
            if "m" in caused_version:
                perf_dict['sta_soft'].append(sta_soft)
            if "u" in caused_version:
                perf_dict['unique'].append(unique)
            perf_dict['beta'].append(beta)
            perf_dict['error'].append(err)
            
    else:
        
        for so in fine_tune_range:
            
            if speaker_level == 2:
                model_output = rsa.s2(aspects,
                                      caused_version,
                                      enabled_version,
                                      nap, 
                                      sta_soft,
                                      so,
                                      unique_softener=unique,
                                      alternative_aspect_values=alternative_aspects,
                                      affected_version=affected_version)
            else:
                model_output = rsa.s1(aspects,
                                     caused_version,
                                     enabled_version,
                                     nap,
                                     sta_soft,
                                     so,
                                     unique_softener=unique,
                                     alternative_aspect_values=alternative_aspects,
                                     affected_version=affected_version)
                
            if error_type == "sq_err":
                err = compute_error(model_output, trial_set)
            elif error_type == "log_like":
                err = compute_likelihood(model_output, trial_set)
            
            perf_dict['unoise'].append(unoise)
            perf_dict['not_affect_param'].append(nap)
            if "m" in caused_version:
                perf_dict['sta_soft'].append(sta_soft)
            if "u" in caused_version:
                perf_dict['unique'].append(unique)
            perf_dict['speaker_opt'].append(so)
            perf_dict['error'].append(err)
                
    return perf_dict



# Grid search procedure
# Requires a boolean indicating full model or no pragmatics model
# as well as parameter ranges for uncertainty noise, not affect parameter,
# and also the fine tune parameter, optionally includes ranges for moving 
# and unique softeners. Also includes options for verb definitions
# level of the pramgatic speaker, set of trials to consider, type of objective
# to evaluate, and whether or not to let stationary and unique softern to
# vary indpendently

# Also allows two different output types. Summary returns all parameter settings
# with their values. Opt just returns the optimal parameter set.
def grid_search(lesion_rsa,
                unoise_range,
                not_affect_param_range,
                fine_tune_range,
                caused_version="and_hmu_or_ws",
                enabled_version="or_ws",
                sta_soft_range=None,
                unique_range=None,
                speaker_level=2,
                affected_version="or_whs",
                combine_softeners=True,
                trial_set=np.arange(30),
                output_type="opt",
                error_type="log_like"):
    
    fine_tune = "beta" if lesion_rsa else "speaker_opt"
    
    perf_dict = {
        'unoise': [],
        'not_affect_param': [],
        fine_tune: [],
        'error': []
    }
    
    if not (sta_soft_range is None):
        perf_dict["sta_soft"] = []
        
    if not (unique_range is None):
        perf_dict["unique"] = []
    
    for unoise in unoise_range:
        aspects, alternative_aspects = rsa.load_aspects(unoise)
        
        for nap in not_affect_param_range:
            
            if (sta_soft_range is None) and (unique_range is None):
                
                perf_dict = fit_fine_tune(fine_tune_range,
                                          perf_dict,
                                          lesion_rsa,
                                          aspects,
                                          unoise,
                                          nap,
                                          0,
                                          0,
                                          caused_version,
                                          enabled_version,
                                          alternative_aspects=alternative_aspects,
                                          speaker_level=speaker_level,
                                          affected_version=affected_version,
                                          trial_set=trial_set,
                                          error_type=error_type)
            
            elif (not (sta_soft_range is None)) and (unique_range is None):
                
                assert "m" in caused_version
                  
                for sta_soft in sta_soft_range:
                    perf_dict = fit_fine_tune(fine_tune_range,
                                              perf_dict,
                                              lesion_rsa,
                                              aspects,
                                              unoise,
                                              nap,
                                              sta_soft,
                                              0,
                                              caused_version,
                                              enabled_version,
                                              alternative_aspects=alternative_aspects,
                                              speaker_level=speaker_level,
                                              affected_version=affected_version,
                                              trial_set=trial_set,
                                              error_type=error_type)
                        
            elif (sta_soft_range is None) and (not (unique_range is None)):
                assert "u" in unique_range
                
                for unique in unique_range:
                  
                      perf_dict = fit_fine_tune(fine_tune_range,
                                                perf_dict,
                                                lesion_rsa,
                                                aspects,
                                                unoise,
                                                nap,
                                                0,
                                                unique,
                                                caused_version,
                                                enabled_version,
                                                alternative_aspects = alternative_aspects,
                                                speaker_level=speaker_level,
                                                affected_version=affected_version,
                                                trial_set=trial_set,
                                                error_type=error_type)
                    
                    
            elif (not (sta_soft_range is None)) and (not (unique_range is None)):
                
                assert "u" in caused_version
                assert "m" in caused_version
                
                if combine_softeners:
                    
                    for sta_soft in sta_soft_range:
                        
                        perf_dict = fit_fine_tune(fine_tune_range,
                                                 perf_dict,
                                                 lesion_rsa,
                                                 aspects,
                                                 unoise,
                                                 nap,
                                                 sta_soft,
                                                 sta_soft,
                                                 caused_version,
                                                 enabled_version,
                                                 alternative_aspects=alternative_aspects,
                                                 speaker_level=speaker_level,
                                                 trial_set=trial_set,
                                                 error_type=error_type)
                        
                else:
                
                    for sta_soft in sta_soft_range:

                        for unique in unique_range:

                            perf_dict = fit_fine_tune(fine_tune_range,
                                                      perf_dict,
                                                      lesion_rsa,
                                                      aspects,
                                                      unoise,
                                                      nap,
                                                      sta_soft,
                                                      unique,
                                                      caused_version,
                                                      enabled_version,
                                                      alternative_aspects=alternative_aspects,
                                                      speaker_level=speaker_level,
                                                      affected_version=affected_version,
                                                      trial_set=trial_set,
                                                      error_type=error_type)
                        
            else:
                raise Exception("Missing stationary softener or uniqueness range")
                
    if output_type == "summary": 
        return pd.DataFrame(perf_dict)
    elif output_type == "opt":
        df_perf = pd.DataFrame(perf_dict)
        
        sorted_perf = df_perf.sort_values(by="error",
                                          ignore_index=True,
                                          ascending=error_type=="sq_err")
        
        unoise = sorted_perf['unoise'][0]
        nap = sorted_perf['not_affect_param'][0]
        fine_tune = sorted_perf['beta'][0] if lesion_rsa else sorted_perf['speaker_opt'][0]
        
        sta_soft = sorted_perf['sta_soft'][0] if not (sta_soft_range is None) else None
        unique = sorted_perf['unique'][0] if not (unique_range is None) else None
        
        return {
            "unoise": unoise,
            "not_affect_param": nap,
            "sta_soft": sta_soft,
            "unique": unique,
            "fine_tune": fine_tune
        }
    
    else:
        raise Exception("Output type {} not implemented".format(output_type))


# Cross validation procedure
# Takes a set of trial splits, lesion pragmatics indicator as well as
# ranges for uncertainty noise, not affect param, and fine tune parameters
# optionally requires ranges for stationary softern and unique softener.
# Also optionally requires definitions for the three verbs and error type
def cross_validation(splits,
                    lesion_rsa,
                    unoise_range,
                    not_affect_param_range,
                    fine_tune_range,
                    sta_soft_range=None,
                    unique_range=None,
                    caused_version="and_hmu_or_ws",
                    enabled_version="or_ws",
                    affected_version="or_whs",
                    error_type="log_like"):
    
    start_time = time.time()
    
    perf_dict = {
        "split": [],
        "model": [],
        "caused_version": [],
        "enabled_version": [],
        "affected_version": [],
        "model_params": [],
        "trial": [],
        "verb": [],
        "model_pred": [],
        "data_val":[],
        "use": []
    }
        
    for i in range(len(splits)):
        print("Split", str(i))
            
        train, test = splits[i]
    
        params = grid_search(lesion_rsa,
                            unoise_range,
                            not_affect_param_range,
                            fine_tune_range,
                            caused_version,
                            enabled_version=enabled_version,
                            sta_soft_range=sta_soft_range,
                            unique_range=unique_range,
                            speaker_level=2,
                            affected_version=affected_version,
                            combine_softeners=True,
                            trial_set=train,
                            output_type="opt",
                            error_type="log_like")

        unoise = params['unoise']
        aspects, _ = rsa.load_aspects(params['unoise'])
        nap = params['not_affect_param']
        sta_soft = params['sta_soft']
        unique = params['unique']
        fine_tune = params['fine_tune']

        if not lesion_rsa:
            model_output = rsa.s2(aspects,
                                 caused_version,
                                 enabled_version,
                                 nap,
                                 sta_soft,
                                 fine_tune,
                                 unique_softener=unique,
                                 affected_version=affected_version)
        else:
            model_output = rsa.lesion_model(aspects,
                                           caused_version,
                                           enabled_version,
                                           nap,
                                           sta_soft,
                                           fine_tune,
                                           unique_softener=unique,
                                           affected_version=affected_version)

        train_model = model_output[:, train]
        train_data = data_averaged[:, train]
        test_model = model_output[:, test]
        test_data = data_averaged[:, test]

        assert test_model.shape[1] == train_model.shape[1]

        for j in range(train_model.shape[1]):
            train_trial = train[j]
            test_trial = test[j]

            for k in range(len(vocabulary)):
                verb = vocabulary[k]

                perf_dict['split'].append(i)
                perf_dict['model'].append("semantics" if lesion_rsa else "full")
                perf_dict['caused_version'].append(caused_version)
                perf_dict['enabled_version'].append(enabled_version)
                perf_dict['affected_version'].append(affected_version)
                perf_dict['model_params'].append([unoise, nap, sta_soft, unique] +
                                                 ([fine_tune, None] if not lesion_rsa else [None, fine_tune]))
                perf_dict['trial'].append(train_trial)
                perf_dict['verb'].append(verb)
                perf_dict['model_pred'].append(train_model[k,j])
                perf_dict['data_val'].append(train_data[k,j])
                perf_dict['use'].append('train')

                perf_dict['split'].append(i)
                perf_dict['model'].append("semantics" if lesion_rsa else "full")
                perf_dict['caused_version'].append(caused_version)
                perf_dict['enabled_version'].append(enabled_version)
                perf_dict['affected_version'].append(affected_version)
                perf_dict['model_params'].append([unoise, nap, sta_soft, unique] +
                                                 ([fine_tune, None] if not lesion_rsa else [None, fine_tune]))
                perf_dict['trial'].append(test_trial)
                perf_dict['verb'].append(verb)
                perf_dict['model_pred'].append(test_model[k,j])
                perf_dict['data_val'].append(test_data[k,j])
                perf_dict['use'].append('test')
                
    df_perf = pd.DataFrame(perf_dict)
    filename = "useful_csvs/cross_validation_" + ("full_model.csv" if not lesion_rsa else "lesion_model.csv")
    
    model = "semantics" if lesion_rsa else "full"
    
    filename = "model_performance/cv_{}_model.csv".format(model)
    
    df_perf.to_csv(filename)
    
    print("Runtime:", time.time() - start_time)
    return df_perf


def make_model_df(model_perf):
    
    if model_perf.shape != (32,4):
        model_perf = model_perf.T
        
    assert model_perf.shape == (32,4)
    
    model_perf = model_perf[:30,:]
    
    r,c = model_perf.shape
    
    model_dict = {
        "trial": [],
        "response": [],
        "model_y": []
    }
    
    for tr in range(r):
        
        for i, exp in [(2, "affect"), (0, "cause"), (1, "enable"), (3, "no_difference")]:
            
            model_dict["trial"].append(tr)
            model_dict["response"].append(exp)
            model_dict["model_y"].append(model_perf[tr, i])
            
    return pd.DataFrame(model_dict)

