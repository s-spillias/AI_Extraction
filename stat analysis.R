library(tidyverse)
library(readxl)
library(beyonce)
library(ggpubr)

#### stats for analysis ####
# stat_analysis dataframe = full_df from process evaluations

stat_analysis <- team_data_list %>% bind_rows() %>% 
  pivot_longer(-c("Citation","AI")) %>% 
  separate(value, sep = ';', into = paste0('Crit',1:4)) %>% 
  pivot_longer(starts_with("Crit"), names_to = 'Criteria') %>% 
  mutate(Agent = 'Human') %>% 
  bind_rows(ai_df) %>% 
  mutate(Flag = ifelse(Criteria == 'Crit4' & value > 1, "FLAG",NA),
         group_agent = ifelse(str_detect(Agent, "Human"), "Human Assessor", "GPT4-Turbo Assessor"),
         value = as.integer(value)) %>% 
  filter(!is.na(value)) %>% 
  filter(Criteria != 'Crit4') %>%
  relocate(value, .after = 'group_agent') %>% 
  mutate(Criteria = case_match(Criteria, 'Crit1' ~ 'Context to Question',
                               'Crit2' ~ 'Response to Context',
                               'Crit3' ~ 'AI Response to Human Response')) %>% 
  rename('Question' = 'name') %>% 
  left_join(reviewers_id, by = 'Question') %>% 
  mutate(Reviewer = ifelse(str_detect(group_agent,'GPT'),'GPT4-Turbo',Reviewer)) %>% 
  mutate(short_cit = substr(Citation, 1,35)) %>% 
  left_join(difficulty %>%  mutate(short_cit = substr(Citation, 1,35)) %>% dplyr::select(-Citation), by = c("Question",'short_cit')) %>%
  mutate(AI = case_match(AI, 'ELICIT' ~ 'Elicit',
                         'OPENAI' ~ 'GPT4x3',
                         'OPENAI_single' ~ 'GPT4'))

# combining median value for the 5 replicates of the AI assessor
humandf <- stat_analysis %>% filter(Agent == "Human") %>% select(-short_cit, -Difficulty)
aidf <- stat_analysis %>% filter(Agent != "Human")
aidf2 <- aidf %>% group_by(Citation, AI, Question, Criteria, Flag, group_agent, Reviewer) %>% 
  summarise(value = median(value)) %>% mutate(Agent = "AI") %>% 
  select(Citation, AI, Question, Criteria, Agent, Flag, group_agent, value, Reviewer)

statdf <- rbind(humandf, aidf2)

# analysis
aiaov <- aov(data = statdf, value ~ AI)
summary(aiaov)
tt <- TukeyHSD(aiaov)
tt

plot(aiaov)


# validating reviewers #
statdf2 <- statdf %>% filter(Reviewer != "GPT4-Turbo")
val <- aov( data = statdf2, value ~ Reviewer*Criteria)
summary(val)
valtt <- TukeyHSD(val)
valtt

df_validate_stats <- df_validate_stats %>% mutate(Criteria = case_match(Criteria, 'Crit1' ~ 'Context to Question',
                                                              'Crit2' ~ 'Response to Context',
                                                              'Crit3' ~ 'AI Response to Human Response'))
valplot <- {ggplot(df_validate_stats, aes(x = Reviewer, y = mean, fill = Criteria, group = Criteria)) +
  geom_hline(yintercept = 2,linetype = 'dashed',alpha = 0.5 ) +
  geom_col(stat = "identity", position = "dodge", color = "black") +
  geom_errorbar(aes(ymin = mean - standard_error, ymax = mean + standard_error),
                position = position_dodge(width = 0.9), width = 0.25) +
  labs(x = "Reviewer", y = "Mean Assessed Quality") +
  theme_classic() +
  coord_cartesian(ylim = c(1, 3)) +
  theme(legend.position = 'bottom') +
  #facet_wrap(~Question) +
  scale_fill_manual(values = crit_pal)} #will need to run process_evaluations_new before to get objects

df_val <- df_validate %>% filter(Criteria != "Crit4") %>% mutate(Criteria = case_match(Criteria, 'Crit1' ~ 'Context to Question',
                                                                        'Crit2' ~ 'Response to Context',
                                                                        'Crit3' ~ 'AI Response to Human Response'))
crit1_mean <- df_val %>% filter(Criteria == "Context to Question") # crit 1 - in red
crit1_mean <- mean(crit1_mean$value)
print(crit1_mean) #mean = 2.458

crit2_mean <- df_val %>% filter(Criteria == "Response to Context") #crit 2 - in green
crit2_mean <- mean(crit2_mean$value)
print(crit2_mean) #mean = 2.533

crit3_mean <- df_val %>% filter(Criteria == "AI Response to Human Response") #crit 3 - in blue
crit3_mean <- mean(crit3_mean$value)
print(crit3_mean) #mean = 2.242

# standardizing reviewers #

# attempting to create 5th "reviewer" which is all combined data - not sure if this is valid for anova
df_val2 <- df_val %>% filter(Criteria != "NA") %>% mutate(Reviewer = "R5")
valbind <- rbind(df_val, df_val2)

valbind_stats = valbind %>% 
  group_by(Criteria, Reviewer) %>% 
  summarise(mean = mean(value),
            standard_error = sd(value, na.rm = TRUE) / sqrt(n()),
            st_dev = sd(value))
valplot2 <- {ggplot(valbind_stats, aes(x = Reviewer, y = mean, fill = Criteria, group = Criteria)) +
    geom_hline(yintercept = 2,linetype = 'dashed',alpha = 0.5 ) +
    geom_col(stat = "identity", position = "dodge", color = "black") +
    geom_errorbar(aes(ymin = mean - standard_error, ymax = mean + standard_error),
                  position = position_dodge(width = 0.9), width = 0.25) +
    labs(x = "Reviewer", y = "Mean Assessed Quality") +
    theme_classic() +
    coord_cartesian(ylim = c(1, 3)) +
    theme(legend.position = 'bottom') +
    #facet_wrap(~Question) +
    scale_fill_manual(values = crit_pal)} # compares individual reviewers (1-4) to the mean of all the values (R5)

valaov <- aov(data = valbind, value ~ Reviewer*Criteria)
summary(valaov)
val_hsd <- TukeyHSD(valaov)
val_hsd 
#only reviewer 1 is sig. diff. from "reviewer 5" (the average of all data) WHEN ALL CRITERIA COMBINED
#no interaction between reviewer*criteria (p = 0.222) - only sig. diff is R1 vs R3 response to context

## LMM analysis ##
library(lme4)
lmm_model <- lmer(value ~ AI + (1|Reviewer), data = statdf)
summary(lmm_model)
lmm_mod_anova <- anova(lmm_model)
TukeyHSD(lmm_mod_anova)

## GLMM analysis ##
library(lme4)
library(emmeans)

glmm_mod <- glmer(value ~ AI + (1|Reviewer), data = statdf, family = poisson) #but is poisson legit? only one that works
summary(glmm_mod)
anova(glmm_mod)
emm <- emmeans(glmm_mod, ~ AI)
contrasts <- pairs(emm, adjust = "tukey")
print(contrasts)

glmm_mod2 <- glmer(value ~ AI*Criteria + (1|Reviewer), data = statdf, family = poisson) #but is poisson legit? only one that works
summary(glmm_mod2)
anova(glmm_mod2)
emm2 <- emmeans(glmm_mod2, ~ AI*Criteria)
contrasts2 <- pairs(emm2, adjust = "tukey")
print(contrasts2)

glmm_mod <- glmer(value ~ group_agent*AI + (1|Reviewer), data = statdf, family = poisson) #but is poisson legit? only one that works
summary(glmm_mod)
anova(glmm_mod)
emm <- emmeans(glmm_mod, ~ group_agent*AI)
contrasts <- pairs(emm, adjust = "tukey")
print(contrasts)

mod_glmm <- glmer(value ~ AI*group_agent + (1|Reviewer), data = statdf, family = poisson)
summary(mod_glmm)
anova(mod_glmm)
emm_glmm <- emmeans(mod_glmm, ~ AI|group_agent)
pairs(emm_glmm)
emm_int_glmm <- emmeans(mod_glmm, pairwise ~ AI:group_agent)
pairs(emm_int_glmm)

# comparing full model with interaction to reduced model without - if p < 0.05, then interaction between AI and group_agent is sig.
mod_red <- glmer(value ~ AI + group_agent + (1|Reviewer), data = statdf, family = poisson)
anova_res <- anova(mod_red, mod_glmm)
print(anova_res)

## full plot ##
ggplot(stat_summary, aes(x = AI, y = mean, fill = Criteria, group = Criteria)) +
  geom_hline(yintercept = 2, linetype = 'dashed',alpha = 0.5 ) +
  geom_col(stat = "identity", position = "dodge", color = "black") +
  geom_errorbar(aes(ymin = mean - standard_error, ymax = mean + standard_error),
                position = position_dodge(width = 0.9), width = 0.25) +
  labs( x = "AI Implementation", y = "Assessed Quality") +
  theme_classic() +
  coord_cartesian(ylim = c(1, 3)) +
  facet_wrap(~group_agent) +
  #scale_y_continuous(    labels = c("Poor","Fair","Good"),breaks = c(1,2,3),) +
  scale_fill_manual(values = crit_pal) +
  theme(legend.position = 'bottom') 
