import numpy as np
import json


# Different labeling schemes for vocabulary in code base and dataset
vocabulary_dataset = ["cause", "enable", "affect", "no_difference"]
vocabulary = ["caused", "enabled", "affected", "didn't affect"]
w, h, s, m, u, o = (0, 1, 2, 3, 4, 5)

# A global parameter to determine whether the to use the min trick or not
# Elaborated in the meaning function under the cc definition of caused
min_trick = True

# Procedure for loading aspects to be used in semantic and pragmatic computations
# Returns the primary aspect values and a list of the alternative aspect value arrays
# Could generalize to consider any candidate as possible primary. For the moment only
# considers the first. Works for the current setup
def load_aspects(uncertainty_noise, num_samples=1000, aspect_file=None):
  
  if not (aspect_file is None):
    clips_data = json.load(open(aspect_file))
  else:
    clips_data = json.load(open("aspects_paper/aspects_noise_{}_samples_{}.json".format(uncertainty_noise, num_samples)))

  primary_candidate = clips_data[0]
  alternative_candidates = clips_data[1:]

  # Convert representation to numpy array
  primary_aspect_values = np.array([tr['rep'] for tr in primary_candidate])[:,:5]

  alternative_aspect_values = []

  for candidate_aspects in alternative_candidates:
    alternative_aspects = np.array([tr['rep'] for tr in candidate_aspects])[:,:4]
    alternative_aspect_values.append(alternative_aspects)

  return primary_aspect_values, alternative_aspect_values


# The base routine for computing the caused definition
# Essentially all the calculations we do before checking for combined cause
def caused_subroutine(primary_aspect_values, caused_version, stationary_softener, unique_softener):
  # base caused definition or (whether, sufficiency) and how
  suff_or_necc = np.sum(primary_aspect_values[:,[w,s]], axis=1) - np.prod(primary_aspect_values[:,[w,s]], axis=1)
  caused = suff_or_necc * primary_aspect_values[:,h]
  # A clunky check to see if moving "m" is in the definition. Works for the moment
  # but may need revision if we play with caused definitions more
  if "and_hm" in caused_version:
    moving = primary_aspect_values[:,m]
    # soften the moving feature
    soften_moving = (moving + stationary_softener) - (moving * stationary_softener) 
    caused = caused * soften_moving

  if "u" in caused_version:
    assert not (unique_softener is None)
    unique = primary_aspect_values[:, u]
    soften_unique = (unique + unique_softener) - (unique * unique_softener)
    caused = caused * soften_unique

  return caused

# Meaning function. Requires the utterance of interest, the aspect values for the primary cause,
# The caused and enabled semantic versions. The meaning parameters (no difference param and stationary
# softener). Optional parameters for comparison threshold, comparison softener, and alternative aspect
# values. Comparison threshold and softener are only required for dummy versions of combined cause.
# Alternative aspect values are required for both versions of combined cause
def meaning(utterance, primary_aspect_values, caused_version, enabled_version, how_not_affect_param, stationary_softener, unique_softener=None, comparison_threshold=None, comparison_softener=None, alternative_aspect_values = None, affected_version = "h"):
  if utterance == "enabled":
    if enabled_version == "or_ws":
      # or whether, sufficiency
      return np.sum(primary_aspect_values[:,[w,s]], axis=1) - np.prod(primary_aspect_values[:,[w,s]], axis=1)
    elif enabled_version == "or_ws_and_nh":
      # Code for explicit no how version of cause
      or_ws = np.sum(primary_aspect_values[:,[w,s]], axis=1) - np.prod(primary_aspect_values[:,[w,s]], axis=1)
      or_ws_and_nh = or_ws * (1 - primary_aspect_values[:,h])
      return or_ws_and_nh
    else:
      raise Exception("Enabled Version " + enabled_version + " not implemented.")

  elif utterance == "caused":
    if "cc" not in caused_version:
    	# base version no combined cause
      return caused_subroutine(primary_aspect_values, caused_version, stationary_softener, unique_softener)
    elif "dummy" not in caused_version:
      if alternative_aspect_values == None:
        raise Exception("No alternative aspects for computing combined cause")
      # get the meanings scores of the primary candidate
      primary_meaning = caused_subroutine(primary_aspect_values, caused_version, stationary_softener, unique_softener)
      # initialize the aggregator with the scores of the primary candidate
      cause_assessments = np.expand_dims(primary_meaning,0)

      # collect the meanings in an array
      # array dimensions are entity x trial_num
      for alternative in alternative_aspect_values:
        alterative_meaning = np.expand_dims(caused_subroutine(alternative, caused_version, stationary_softener, unique_softener), 0)
        cause_assessments = np.concatenate((cause_assessments, alterative_meaning), 0)

      # Make a copy of the primary meaning
      normalized = primary_meaning.copy()
      # Check for all entities in the array where caused value is nan (i.e entity isn't in the scene)
      # If in a particular column (trial) there is more than one entity that is not a nan
      # then on that index there will be a comparison. Save those indicies for comparison
      comp_indicies = np.argwhere(np.sum(~np.isnan(cause_assessments), axis=0) != 1).T[0]
      # If in a particular column there is only one entity that is not a nan,
      # there is no comparison to be made. Save those indicies for non-comparison
      no_comp_indicies = np.argwhere(np.sum(~np.isnan(cause_assessments), axis=0) == 1).T[0]

      # Sum the causal values of all entities in a given trial (ignoring nans)
      comp_denom = np.nansum(cause_assessments[:, comp_indicies], axis=0)
      # For any where the sum is equal to zero, nothing has causal rating in that trial
      # set denominator to 1 to avoid division by zero. Since primary cause must have zero
      # should not be an issue
      comp_denom[comp_denom == 0] = 1.0
      # Only in the cases that have more than one cause, divide through by the 
      # corresponding denominator value (the sum of all causes)
      normalized[comp_indicies] = normalized[comp_indicies]/comp_denom

      # Take the minimum of the normalized value and the initial primary value
      # to avoid inflating the primary value with the addition of unrelated causes
      # Kind of a hack. We should think about how to make this more principled
      if min_trick:
        normalized = np.minimum(normalized, primary_meaning)

      # return the normalized value
      return normalized
    else:

      # Can't run the dummy version without, alternatve causes, a threshold, and
      # a softener
      if alternative_aspect_values == None:
        raise Exception("No alternative aspects for computing combined cause")
      if comparison_threshold == None:
        raise Exception("No threshold for dummy comparison")
      if comparison_softener == None:
        raise Exception("No softener for dummy comparison")

      primary_meaning = caused_subroutine(primary_aspect_values, caused_version, stationary_softener, unique_softener)

      alternative_cause_assessments = tuple([np.expand_dims(caused_subroutine(alt, caused_version, stationary_softener, unique_softener), 0) for alt in alternative_aspect_values])

      # Convert all nans to 0 (won't affect things because 0s are below threshold)
      alternative_matrix = np.nan_to_num(np.concatenate(alternative_cause_assessments, 0))
      # check where the alternatives are above the threshold
      above_threshold = alternative_matrix > comparison_threshold

      # This simulates an ^~combined conjunct added on the end of the 
      # If there is no comparator the value will be 1 (thus not deflating primary meaning value)
      # If there is a comparator, we take the or with the comparison softener, so the primary
      # meaning value will be deflated by the value of the softener

      # Mark all the cases for which there are no comparison
      no_comparator = ~np.any(above_threshold, axis=0)
      soften_no_comp = (no_comparator + comparison_softener) - (no_comparator * comparison_softener)

      return primary_meaning*soften_no_comp

  elif utterance == "affected":
    if affected_version == "h":
      affected = primary_aspect_values[:,h]
      return affected
    elif affected_version == "or_wh":
      or_wh = np.sum(primary_aspect_values[:,[w,h]], axis=1) - np.prod(primary_aspect_values[:,[w,h]], axis=1)
      return or_wh
    elif affected_version == "or_whs":
      or_wh = np.sum(primary_aspect_values[:,[w,h]], axis=1) - np.prod(primary_aspect_values[:,[w,h]], axis=1)
      or_whs = (primary_aspect_values[:,s] + or_wh) - primary_aspect_values[:,s] * or_wh
      return or_whs
    else:
      raise Exception("Meaning for affected version '{}' not implemented.".format(affected_version))


  elif utterance == "didn't affect":
    # whether_or_suff = (primary_aspect_values[:,w] + primary_aspect_values[:,s]) - (primary_aspect_values[:,w]*primary_aspect_values[:,s])
    # how_and_flip = primary_aspect_values[:,h] * how_not_affect_param
    # - or of all disjuncts is same as not and treating each as a conjunct
    # De Morgan's Law
    # Probability 1 - x is equivalent
    # return 1 - (whether_or_suff + how_and_flip - whether_or_suff*how_and_flip)

    not_wh = 1 - primary_aspect_values[:,w]
    not_suf = 1 - primary_aspect_values[:,s]
    not_how = 1 - primary_aspect_values[:,h]

    soft_not_how = (not_how + how_not_affect_param) - (not_how*how_not_affect_param)

    return not_wh*not_suf*soft_not_how

  else:
    raise Exception("meaning for utterance '{}' not implemented.".format(utterance))

# L0(clip | utterance) \propto P(clip) * P(utterance true | clip)
def l0(primary_aspect_values, caused_version, enabled_version, how_not_affect_param, stationary_softener, unique_softener=None, comparison_threshold=None, comparison_softener=None, alternative_aspect_values = None, affected_version="h", vocabulary=["caused", "enabled", "affected", "didn't affect"]):
  n_worlds = primary_aspect_values.shape[0]
  # assert n_worlds == trial_max
  prior = 1./n_worlds
  # number of utterances X number of worlds
  likelihood = np.array([meaning(utterance, primary_aspect_values, caused_version, enabled_version, how_not_affect_param, stationary_softener, unique_softener=unique_softener, comparison_threshold=comparison_threshold, comparison_softener=comparison_softener, alternative_aspect_values=alternative_aspect_values, affected_version=affected_version) for utterance in vocabulary])
  unnormalized_l0 = prior*likelihood

  # normalize within each utterance to get distribution over worlds
  normalization_constants = np.sum(unnormalized_l0, axis=1)

  # There may be some utterance which is false for all worlds.
  # In that case, we can't make a well-defined probability distribution over worlds.
  # But we will just return 0 for every world in that group.
  # This is fine, because if the utterance is false for all worlds,
  # we want the likelihood of that utterance given each world to be 0.
  numerator = unnormalized_l0.T
  denominator = normalization_constants

  # numerator is only nonzero if well defined normalization constant exists
  well_defined = normalization_constants > 0

  # For any denominator that is not well defined (i.e. equal to zero)
  # Add 1 to it. The normalization will then be each world (value 0) divided by 1
  denominator = denominator + (1 - well_defined)

  # number of worlds X number of utterances
  return numerator / denominator

# S1(utterance | clip) \propto P(utterance) * L0(clip | utterance)^optimality
def s1(primary_aspect_values, caused_version, enabled_version, how_not_affect_param, stationary_softener, speaker_optimality, unique_softener=None, comparison_threshold=None, comparison_softener=None, alternative_aspect_values=None, affected_version="h", vocabulary=["caused", "enabled", "affected", "didn't affect"]):
  prior = 1./len(vocabulary)
  likelihood = l0(primary_aspect_values, caused_version, enabled_version, how_not_affect_param, stationary_softener, unique_softener=unique_softener, comparison_threshold=comparison_threshold, comparison_softener=comparison_softener, alternative_aspect_values=alternative_aspect_values, affected_version=affected_version, vocabulary=vocabulary)
  unnormalized_s1 = prior*likelihood**speaker_optimality

  # normalize within each world to get distribution over utterances
  normalization_constants = np.sum(unnormalized_s1, axis=1)
  numerator = unnormalized_s1.T
  denominator = normalization_constants

  # There may be some worlds for which no utterance is true.
  # In that case, we can't make a well-defined probability distribution over utterances.
  # But we will just return 0 for every utterance in that group.
  # This is fine, because if a world cannot be picked out by any utterance,
  # we want the likelihood of that world given each utterance to be 0
  
  # numerator is only nonzero if well defined normalization constant exists
  well_defined = normalization_constants > 0

  # For any denominator that is not well defined (i.e. equal to zero)
  # Add 1 to it. The normalization will then be each world (value 0) divided by 1
  denominator = denominator + (1 - well_defined)

  return numerator / denominator


# L1(clip | utterance) \propto P(clip) * S1(utterance | clip)
# L1(clip | utterance) =  L1(clip | utterance)
def l1(primary_aspect_values, caused_version, enabled_version, how_not_affect_param, stationary_softener, speaker_optimality, unique_softener=None, comparison_threshold=None, comparison_softener=None, alternative_aspect_values = None, affected_version='h', vocabulary=["caused", "enabled", "affected", "didn't affect"]):
  n_worlds = primary_aspect_values.shape[0]
  # assert n_worlds == trial_max
  # prior over world
  prior = 1./n_worlds
  # 4 utterances X 32 worlds
  # for each world, there's a likelihood of the utterance
  likelihood = s1(primary_aspect_values, caused_version, enabled_version, how_not_affect_param, stationary_softener, speaker_optimality, unique_softener=unique_softener, comparison_threshold=comparison_threshold, comparison_softener=comparison_softener, alternative_aspect_values=alternative_aspect_values, affected_version=affected_version, vocabulary=vocabulary)
  numerator = prior*likelihood

  # normalize within each utterance to get a distribution over  worlds
  denominator = np.sum(numerator, axis=1)
  return numerator.T / denominator


# Full model function. Requires aspect values for primary object and alternatives, (to be passed down to meaning)
# Requires all other model parameters other than uncertainty noise (implicit in the aspect values)
# S2(utterance | clip) \propto P(utterance) * L1(clip | utterance)^optimality
def s2(primary_aspect_values, caused_version, enabled_version, how_not_affect_param, stationary_softener, speaker_optimality, unique_softener=None, comparison_threshold=None, comparison_softener=None, alternative_aspect_values = None, affected_version='h', vocabulary=["caused", "enabled", "affected", "didn't affect"]):
  prior = 1./len(vocabulary)
  likelihood = l1(primary_aspect_values, caused_version, enabled_version, how_not_affect_param, stationary_softener, speaker_optimality, unique_softener=unique_softener, comparison_threshold=comparison_threshold, comparison_softener=comparison_softener, alternative_aspect_values=alternative_aspect_values, affected_version=affected_version, vocabulary=vocabulary)
  unnormalized_s2 = prior*likelihood**speaker_optimality
  # normalize within each world to get distribution over utterances
  return unnormalized_s2.T / np.sum(unnormalized_s2, axis=1)

# Softmax procedure for lesion model
def softmax(arr, ax, beta=1):
  exp_arr = np.exp(beta*arr)
  return exp_arr/np.sum(exp_arr, axis=ax)

# Compute lesion model outputs.
# Requires aspect values for primary object and alternatives, (to be passed down to meaning)
# Requires all other model parameters other than uncertainty noise (implicit in the aspect values)
def lesion_model(primary_aspect_values, caused_version, enabled_version, how_not_affect_param, stationary_softener, beta, unique_softener=None, comparison_threshold=None, comparison_softener=None, alternative_aspect_values=None, affected_version="h"):
  semantic_values = np.vstack([meaning(word, primary_aspect_values, caused_version, enabled_version, how_not_affect_param, stationary_softener, unique_softener, comparison_threshold=comparison_threshold, comparison_softener=comparison_softener, alternative_aspect_values=alternative_aspect_values, affected_version=affected_version) for word in vocabulary])
  semantic_values = softmax(semantic_values, 0, beta=beta)
  return semantic_values