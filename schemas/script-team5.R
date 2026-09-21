# Load required libraries
library(readr)
library(dplyr)
library(glmmTMB)

# Load the data
df <- read_csv("data/football.csv")

# Step 1: create_skin_tone_variable
# Average the two ratings of skin-tone and rescale to create avgrate01
# Input: rater1, rater2
# Output: avgrate01
df <- df %>%
  mutate(avgrate01 = (rater1 + rater2) / 2)

# Rescale to 0-1 range
avgrate_min <- min(df$avgrate01, na.rm = TRUE)
avgrate_max <- max(df$avgrate01, na.rm = TRUE)
df <- df %>%
  mutate(avgrate01 = (avgrate01 - avgrate_min) / (avgrate_max - avgrate_min))

# Step 2: handle_missing_data
# Apply listwise deletion for cases missing skin-tone-rating, meanIAT, or meanExp
# Input: avgrate01, meanIAT, meanExp
# Output: df_complete
df_complete <- df %>%
  filter(!is.na(avgrate01) & !is.na(meanIAT) & !is.na(meanExp))

# Step 3: disaggregate_response_variable
# Disaggregate data to one game per row with redCards appearing as 1s in first n rows per player
# Input: df_complete, redCards, games
# Output: df_disaggregated, red_card_binary
df_disaggregated <- df_complete %>%
  filter(games > 0) %>%
  rowwise() %>%
  do({
    row_data <- .
    n_games <- row_data$games
    n_red_cards <- min(row_data$redCards, n_games)  # Ensure red cards don't exceed games
    
    # Create expanded rows
    expanded <- data.frame(
      playerShort = rep(row_data$playerShort, n_games),
      refNum = rep(row_data$refNum, n_games),
      refCountry = rep(row_data$refCountry, n_games),
      avgrate01 = rep(row_data$avgrate01, n_games),
      meanIAT = rep(row_data$meanIAT, n_games),
      meanExp = rep(row_data$meanExp, n_games),
      red_card_binary = c(rep(1, n_red_cards), rep(0, n_games - n_red_cards)),
      stringsAsFactors = FALSE
    )
    expanded
  }) %>%
  ungroup()

# Ensure factor variables for random effects
df_disaggregated <- df_disaggregated %>%
  mutate(
    playerShort = as.factor(playerShort),
    refNum = as.factor(refNum),
    refCountry = as.factor(refCountry)
  )

# Step 4: select_error_distribution
# Use binomial error distribution
# Input: red_card_binary
# Output: distribution_spec
distribution_spec <- binomial(link = "logit")

# Step 5: specify_random_effects_structure
# Add random effects for playerShort, refNum, and skin-tone across referees countries of origin
# Input: df_disaggregated, playerShort, refNum, avgrate01, refCountry
# Output: ranef_spec
ranef_spec <- "(1 | playerShort) + (1 | refNum) + (0 + avgrate01 | refCountry)"

# Step 6: select_covariates
# Do not use any covariates
# Input: df_disaggregated
# Output: covariate_spec
covariate_spec <- NULL

# Step 7: fit_glmm
# Estimate generalized linear mixed models using glmer in R package lme4
# Input: df_disaggregated, red_card_binary, avgrate01, ranef_spec, distribution_spec, covariate_spec
# Output: glmm_model

# Build the formula
# Fixed effect: avgrate01 (skin tone predictor)
# Random effects: as specified in ranef_spec
# No covariates as specified in covariate_spec

formula_string <- paste("red_card_binary ~ avgrate01 +", ranef_spec)
model_formula <- as.formula(formula_string)

# Fit the GLMM
glmm_model <- glmmTMB(
  formula = model_formula,
  data = df_disaggregated,
  family = distribution_spec,
)

# Print model summary
summary(glmm_model)
