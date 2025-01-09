import numpy as np
import pandas as pd
import json
import sqlite3

trial_max = 31

# Code to load the data from the sql file
database_path = "../../data/experiment2/speaker_experiment_anonymized.db"
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

df_data.to_csv("../../data/experiment2/speaker_task_preclean.csv", index=False)

# filter out participant that failed attention check
attention_check_fail = df_data[(df_data['trial'] == 30) & (df_data['response'] != 'no_difference')]
excluded_participants = attention_check_fail['participant']

df_data = df_data[~df_data['participant'].isin(excluded_participants)]

# filter out the attention check
df_data = df_data[~(df_data["trial"] == 30)]

df_data.to_csv("../../data/experiment2/speaker_task_clean.csv", index=False)