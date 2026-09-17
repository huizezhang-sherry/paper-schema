library(VGAMdata)
library(VGAM)
library(dplyr)

data("smqP", package = "VGAMdata")

cols <- c('TC30', 'TCquit', 'SCA', 'educ', 'marital',
          'SIA', 'SEQN', 'age', 'gender', 'race2',
          "passiveSmoke_job", "passiveSmoke_rest",
          "passiveSmoke_bar", "passiveSmoke_car",
          "passiveSmoke_home", "passiveSmoke_other", 
          "passiveSmoke_ecigarettes")
df <- smqP |> select(all_of(cols))

cols_require_complete <- setdiff(cols, c("TC30", "TCquit", "SCA"))
df_complete <- df |> 
  filter(complete.cases(pick(all_of(cols_require_complete))))

df_age_restricted <- df_complete |> filter(age < 80)

df_age_restricted <- df_age_restricted |> 
  mutate(
    SCA_corrected = if_else(!is.na(SCA) & !is.na(SIA) & (SCA - SIA < 0), NA_integer_, SCA),
    SIA_corrected = if_else(!is.na(SCA) & !is.na(SIA) & (SCA - SIA < 0), NA_integer_, SIA)
  )

df_age_restricted <- df_age_restricted |>
  mutate(
    marital_imputed = if_else(age < 20, "Never married", as.character(marital))
  )

df_age_restricted <- df_age_restricted |>
  mutate(
    educ_imputed = case_when(
      age < 14 ~ "< 9th grade",
      age >= 14 & age <= 16 ~ "9-11th grade",
      age >= 17 & age <= 19 ~ "High school",
      TRUE ~ as.character(educ)
    )
  )

df_ever_smokers <- df_age_restricted |> 
  filter(
    !is.na(SIA_corrected) & 
    ((!is.na(SCA_corrected) & !is.na(TCquit)) | (is.na(SCA_corrected) & !is.na(TC30)))
  )

df_ever_smokers <- droplevels(df_ever_smokers)

parent_distribution <- negbinomial

i_mix_spec <- c(12, 13, 14, 19, 20, 21)
i_mlm_spec <- c(15, 16, 17, 18)

a_mix_spec <- NULL
a_mlm_spec <- NULL

d_mix_spec <- NULL
d_mlm_spec <- NULL

truncation_spec <- NULL

covariate_formula <- SIA_corrected ~ race2 + gender + marital_imputed + educ_imputed

fitted_model <- vglm(
  covariate_formula,
  family = gaitdnbinomial(
    i.mix = i_mix_spec, i.mlm = i_mlm_spec,
    a.mix = a_mix_spec, a.mlm = a_mlm_spec,
    d.mix = d_mix_spec, d.mlm = d_mlm_spec,
    truncate = truncation_spec
  ),
  data = df_ever_smokers
)
