import rsa
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.stats import pearsonr

vocabulary_dataset = ["cause", "enable", "affect", "no_difference"]
vocabulary = ["caused", "enabled", "affected", "no_difference"]
w, h, s, m, u, o = (0,1,2,3,4,5)

participant_means = pd.read_csv("../../data/experiment3/participant_means.csv").drop(columns="Unnamed: 0")
trial_comparison_indices = participant_means[["video_a", "video_b"]].to_numpy()
trial_utterance_values = participant_means[["utterance"]].to_numpy()

def softmax_normalize(arr, beta=1): return rsa.softmax(arr, ax=0, beta=beta)

def convert_utterance(arr): 
    convert_dict = {"caused": 0, "enabled": 1, "affected": 2, "no_difference": 3}
    return np.array([convert_dict[utt[0]] for utt in arr])

trial_utterance_values = convert_utterance(trial_utterance_values)
scaled_human_responses = participant_means.Mean.to_numpy()

###############
# Grid Search #
###############

def compute_softmax_predictions(beta, listener_dist, trial_comparison_indices, trial_utterance_values):
    
    output_array = []
    
    for i in range(len(trial_utterance_values)):
        clip_numbers = trial_comparison_indices[i,:]
        utterance = trial_utterance_values[i]        
        
        listener_values = listener_dist[clip_numbers, utterance]
        
        softmax_predictions = softmax_normalize(listener_values, beta=beta)
        
        output_array.append(softmax_predictions)
        
    return np.array(output_array)



def compute_square_error(beta, human_response, listener_dist, trial_comparison_indices, trial_utterance_values):
    softmax_predictions = compute_softmax_predictions(beta, listener_dist, trial_comparison_indices, trial_utterance_values)
    compare_values = softmax_predictions[:,1]
    
    return np.sum((human_response - compare_values)**2)



def fit_and_compute_softmax(listener_params, human_response, model_type, trial_comparison_indices=trial_comparison_indices, trial_utterance_values=trial_utterance_values, trial_indices=np.arange(36, dtype=int)):
    
    uncertainty_noise = listener_params["uncertainty_noise"]
    how_not_affect_param = listener_params["how_not_affect_param"]
    stationary_softener = listener_params["stationary_softener"]
    fine_tune = listener_params["fine_tune"]
    unique_softener = listener_params["unique_softener"]
    caused_version = listener_params["caused_version"]
    enabled_version = listener_params["enabled_version"]
    affected_version = listener_params["affected_version"]

    primary_aspect_values, _ = rsa.load_aspects(uncertainty_noise)
    
    human_response = human_response[trial_indices]
    
    if model_type == "full":

        listener_dist = rsa.l1(primary_aspect_values, caused_version, enabled_version, how_not_affect_param, stationary_softener, fine_tune, unique_softener=unique_softener, affected_version=affected_version)
        optimal_beta = minimize_scalar(compute_square_error, args=(human_response, listener_dist, trial_comparison_indices, trial_utterance_values))['x']
        model_predictions = compute_softmax_predictions(optimal_beta, listener_dist, trial_comparison_indices, trial_utterance_values)
        
    elif model_type == "no_pragmatics":
        listener_dist = rsa.l0(primary_aspect_values, caused_version, enabled_version, how_not_affect_param, stationary_softener, unique_softener=unique_softener, affected_version=affected_version)
        optimal_beta = minimize_scalar(compute_square_error, args=(human_response, listener_dist, trial_comparison_indices, trial_utterance_values))['x']
        model_predictions = compute_softmax_predictions(optimal_beta, listener_dist, trial_comparison_indices, trial_utterance_values)
        
    else:
        raise Exception("Model Version {} not implemented.".format(model_type))
        
    return model_predictions, optimal_beta


def get_trial_pairings(model_df, trial_comparison_indices, trial_utterance_values, model_type="regression"):
    
    trial_pairings = np.zeros((2, len(trial_utterance_values)))

    if model_type == "regression":
        value = "model_y"
    elif model_type == "participant":
        value = "data_y"
    else:
        raise Exception("Model Type {} not implemented.".format(model_type))
    
    for trial in range(len(trial_utterance_values)):
        video_a, video_b = trial_comparison_indices[trial,:]
        utterance = vocabulary_dataset[trial_utterance_values[trial]]

        video_a_prob = model_df[(model_df["trial"] == video_a) &
                                (model_df["response"] == utterance)][value].to_numpy()[0]

        video_b_prob = model_df[(model_df["trial"] == video_b) &
                                (model_df["response"] == utterance)][value].to_numpy()[0]

        trial_pairings[:,trial] = [video_a_prob, video_b_prob]
        
    return trial_pairings


def fit_square_error(beta, model_pairings, human_means, trial_ind=np.arange(36, dtype=int)):
    
    human_means = human_means[trial_ind]
    
    normalized_scores = softmax_normalize(model_pairings, beta=beta)
    return np.sum((normalized_scores[1,:]-human_means)**2)

def reg_square_error(beta, regression_pairings, human_means, trial_ind=np.arange(36, dtype=int)):
    
    human_means = human_means[trial_ind]
    
    normalized_scores = softmax_normalize(regression_pairings, beta=beta)
    return np.sum((normalized_scores[1,:]-human_means)**2)

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

####################
# Cross Validation #
####################


def cross_validate(train,
                  test,
                  model_type,
                  model_params,
                  trial_comparison_indices=trial_comparison_indices,
                  trial_utterance_values=trial_utterance_values,
                  human_responses=scaled_human_responses):
    

    if model_type == "full":

        primary_aspect_values, _ = rsa.load_aspects(model_params["uncertainty_noise"])
        
        listener_dist = rsa.l1(
            primary_aspect_values = primary_aspect_values,
            caused_version = model_params["caused_version"],
            enabled_version = model_params["enabled_version"],
            how_not_affect_param = model_params["how_not_affect_param"],
            stationary_softener = model_params["stationary_softener"],
            speaker_optimality = model_params["fine_tune"],
            unique_softener = model_params["unique_softener"],
            affected_version = model_params["affected_version"]
        )
        
    elif model_type == "no_pragmatics":

        primary_aspect_values, _ = rsa.load_aspects(model_params["uncertainty_noise"])
        
        listener_dist = rsa.l0(
            primary_aspect_values = primary_aspect_values,
            caused_version = model_params["caused_version"],
            enabled_version = model_params["enabled_version"],
            how_not_affect_param = model_params["how_not_affect_param"],
            stationary_softener = model_params["stationary_softener"],
            unique_softener = model_params["unique_softener"],
            affected_version = model_params["affected_version"]
        )
        
        
    elif model_type == "regression":
        
        speaker_regression = pd.read_csv("model_performance/speaker_regression_predictions.csv")
        
    else:
        raise Exception("Model type {} not implemented".format(model_type))
        
    model_performance = {
        "split": [],
        "model": [],
        "beta": [],
        "trial": [],
        "verb": [],
        "model_pred": [],
        "data_val": [],
        "use": []
    }
        
    for split in range(100):
        
        train_ind = train[:,split]
        train_tci = trial_comparison_indices[train_ind, :]
        train_tuv = trial_utterance_values[train_ind]
        
        test_ind = test[:,split]
        test_tci = trial_comparison_indices[test_ind, :]
        test_tuv = trial_utterance_values[test_ind]

        print("Split:", split)
        print("Train Indices")
        print(train_ind)
        print("Test Indices")
        print(test_ind)
        print()
        
        assert len(np.intersect1d(train_ind, test_ind)) == 0
        
        if model_type != "regression":

            model_train, optimal_beta = fit_and_compute_softmax(model_params,
                                                      human_responses,
                                                      model_type,
                                                      trial_comparison_indices=train_tci,
                                                      trial_utterance_values=train_tuv,
                                                      trial_indices=train_ind)

            model_test = compute_softmax_predictions(optimal_beta,
                                                    listener_dist,
                                                    trial_comparison_indices=test_tci,
                                                    trial_utterance_values=test_tuv)
            
        else:
            
            train_pairings = get_trial_pairings(speaker_regression, train_tci, train_tuv)
            test_pairings = get_trial_pairings(speaker_regression, test_tci, test_tuv)
            
            optimal_beta = minimize_scalar(reg_square_error, args=(train_pairings, scaled_human_responses, train_ind))["x"]
            
            model_train = softmax_normalize(train_pairings, optimal_beta).T
            model_test = softmax_normalize(test_pairings, optimal_beta).T


        for tr_ind, trial in enumerate(train_ind):

            model_performance["split"].append(split)
            model_performance["model"].append(model_type)
            model_performance["beta"].append(optimal_beta)
            model_performance["trial"].append(trial)
            model_performance["verb"].append(vocabulary[train_tuv[tr_ind]])
            model_performance["model_pred"].append(model_train[tr_ind, 1])
            model_performance["data_val"].append(scaled_human_responses[trial])
            model_performance["use"].append("train")


        for tr_ind, trial in enumerate(test_ind):

            model_performance["split"].append(split)
            model_performance["model"].append(model_type)
            model_performance["beta"].append(optimal_beta)
            model_performance["trial"].append(trial)
            model_performance["verb"].append(vocabulary[test_tuv[tr_ind]])
            model_performance["model_pred"].append(model_test[tr_ind, 1])
            model_performance["data_val"].append(scaled_human_responses[trial])
            model_performance["use"].append("test")
            
    return pd.DataFrame(model_performance)
