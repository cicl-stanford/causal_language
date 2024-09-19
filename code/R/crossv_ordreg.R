library(brms)
library(tidyverse)

start = proc.time()

df_splits = read.csv("crossv_splits.csv")
df_aspects = read.csv("aspects/aspect_dataframe.csv")

df_splits = df_splits %>%
  mutate(train = strsplit(gsub("\\[|\\]", "", as.character(train)), "\\s+"),
         train = map(.x = train, .f = as.numeric),
         train = map(.x = train, .f = ~.[!is.na(.)])) %>% 
  mutate(test = strsplit(gsub("\\[|\\]", "", as.character(test)), "\\s+"),
         test = map(.x = test, .f = as.numeric),
         test = map(.x = train, .f = ~.[!is.na(.)]))

list_train = df_splits$train
list_test = df_splits$test

# unoise_range = c(0.5, 0.6, 7.0)
unoise_range = c(0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6)

file_args = commandArgs(trailingOnly = TRUE)
split_num = as.numeric(file_args[[1]])


if (length(file_args > 1)) {
  save_models = as.logical(as.numeric(file_args[[2]]))
} else {
  save_models = F
}


train_trials = list_train[[split_num]]
test_trials = list_test[[split_num]]

model_list = list()

top_unoise = -1
top_reg = NA
likelihood = -Inf

for (i in seq(1,length(unoise_range))) {
  unoise = unoise_range[[i]]


  if (unoise == 1) {
    unoise = "1.0"
  }

  data = read.csv(paste("aspects/noise_", unoise, ".csv", sep = "")) %>% 
    mutate(response = factor(response,
                             levels = c("no_difference", "affect", "enable", "cause"),
                             ordered = TRUE))

  train_data = data %>% filter(trial %in% train_trials)

  if (save_models) {
    filename = paste("splits/split", str_pad(split_num, 3, side = "left", pad = "0"), "/ord_reg_noise_", unoise, ".rds", sep = "")
  } else {
    filename = NULL
  }
  
  reg = brm(formula = response ~ whether + how + sufficient + moving + unique +
              (1 + whether + how + sufficient + moving + unique|participant),
            data = train_data,
            family = "cumulative",
            save_all_pars = F,
            file = filename,
            seed = 1)
  
  model_ll = sum(log_lik(reg))
  
  if (model_ll > likelihood) {
    top_reg = reg
    likelihood = model_ll
    top_unoise = as.numeric(unoise)
  }

}

df_top_aspects = df_aspects %>% 
  filter(uncertainty_noise == top_unoise)

reg_pred = as.data.frame(fitted(top_reg,
                                newdata = df_top_aspects,
                                re_formula = NA)[1:30,1,]) %>%
  rename(no_difference = 1,
         affect = 2,
         enable = 3,
         cause = 4) %>%
  mutate(trial = seq(0,29)) %>%
  pivot_longer(cols = c("no_difference", "affect", "enable", "cause"), names_to = "response", values_to = "model_y") %>%
  mutate(response = factor(response, levels = c("no_difference", "affect", "enable", "cause"), ordered = TRUE),
         half = ifelse(trial %in% train_trials, "train", "test"))

df_data = read.csv("../../data/experiment2/participant_means.csv")

df_model_v_data = left_join(reg_pred,
                            df_data,
                            by = c("trial",
                                   "response")) %>% 
  select(-c(data_ymax, data_ymin, X)) %>% 
  mutate(unoise = top_unoise)

filename = paste("splits/split", str_pad(split_num, 3, side = "left", pad = "0"), ".csv", sep = "")

write.csv(df_model_v_data, filename)

print("Time elapsed:")
print(proc.time() - start)
