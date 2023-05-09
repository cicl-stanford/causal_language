import model_fitting as mf
import pickle
from sys import argv

model = argv[1]

unoise_range = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6]
not_affect_param_range = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
softener_range = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
speaker_optimality_range = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3, 3.25, 3.5]
beta_range = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3, 3.25, 3.5]

with open("crossv_splits.pickle", "rb") as f:
	splits = pickle.load(f)


if model == "full":

	print("Cross Validation: Full Model")

	df_perf = mf.cross_validation(splits,
		0,
		unoise_range,
		not_affect_param_range,
		speaker_optimality_range,
		sta_soft_range=softener_range,
		unique_range=softener_range,
		error_type="log_like")

elif model == "no_pragmatics":

	print("Cross Validation: No Pragmatics Model")

	df_perf = mf.cross_validation(splits,
		1,
		unoise_range,
		not_affect_param_range,
		beta_range,
		sta_soft_range=softener_range,
		unique_range=softener_range,
		error_type="log_like")

else:

	raise Exception("Model {} not implemented.".format(model))


