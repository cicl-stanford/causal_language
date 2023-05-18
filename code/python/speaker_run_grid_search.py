import speaker_model_fitting as smf
import rsa
from sys import argv

model = argv[1]

unoise_range = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6]
not_affect_param_range = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
softener_range = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
speaker_optimality_range = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3, 3.25, 3.5]
beta_range = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3, 3.25, 3.5]


if model == "full":

	lesion_rsa = 0

	opt_params = smf.grid_search(lesion_rsa,
		unoise_range,
		not_affect_param_range,
		speaker_optimality_range,
		sta_soft_range=softener_range,
		unique_range=softener_range)

	aspects, _ = rsa.load_aspects(opt_params["unoise"])
	model_perf = rsa.s2(aspects,
	 "and_hmu_or_ws",
	 "or_ws",
	 opt_params["not_affect_param"],
	 opt_params["sta_soft"],
	 opt_params["fine_tune"],
	 unique_softener=opt_params["sta_soft"],
	 affected_version="or_whs")

	df_model = smf.make_model_df(model_perf)
	df_model.to_csv("model_performance/speaker_full_model_predictions.csv")

	print()
	print("Optimal Parameters")
	print("Uncertainty Noise:", opt_params["unoise"])
	print("No Difference Softener:", opt_params["not_affect_param"])
	print("Caused Softener:", opt_params["sta_soft"])
	print("Speaker Optimality:", opt_params["fine_tune"])
	print()

elif model == "no_pragmatics":

	lesion_rsa = 1

	opt_params = smf.grid_search(lesion_rsa,
		unoise_range,
		not_affect_param_range,
		beta_range,
		sta_soft_range=softener_range,
		unique_range=softener_range)

	aspects, _ = rsa.load_aspects(opt_params["unoise"])
	model_perf = rsa.lesion_model(aspects,
		caused_version="and_hmu_or_ws",
		enabled_version="or_ws",
		how_not_affect_param=opt_params["not_affect_param"],
		stationary_softener=opt_params["sta_soft"],
		beta=opt_params["fine_tune"],
		unique_softener=opt_params["sta_soft"],
		affected_version="or_whs")

	df_model = smf.make_model_df(model_perf)
	df_model.to_csv("model_performance/speaker_no_pragmatics_predictions.csv")

	print()
	print("Optimal Parameters")
	print("Uncertainty Noise:", opt_params["unoise"])
	print("No Difference Softener:", opt_params["not_affect_param"])
	print("Caused Softener:", opt_params["sta_soft"])
	print("Softmax Beta:", opt_params["fine_tune"])
	print()

else:
	raise Exception("Model version {} not implemented".format(model))