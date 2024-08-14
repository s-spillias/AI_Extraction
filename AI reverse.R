#reverse script
library(dplyr)
library(tidyverse)
library(readxl)
library(beyonce)
library(ggpubr)
library(lme4)
library(lmerTest)
options(max.print = 999999)

# open files - create dataframes #
file_path = 'output_assessment_AI_reverse.xlsx'
validate_path = list.files('Raw_Team_Assessment', pattern = 'validate', full.names = TRUE)
figure_folder = '../Manuscript/Figures'
# firstcontact-gpt4-32k
# January 29, ran Elicit and GPT4-32k
sheet_names <- excel_sheets(file_path)

all_data_list <- lapply(sheet_names, function(sheet) {
  read_excel(file_path, sheet = sheet) %>% 
    mutate(AI = sheet)})

do_stats = function(x){
  x %>% 
    summarise(mean = mean(value),
              standard_error = sd(value, na.rm = TRUE) / sqrt(n()),
              st_dev = sd(value),
              difficulty_mean = mean(Difficulty, na.rm = TRUE),
              st_dev_difficulty = sd(Difficulty, na.rm = TRUE),
              standard_error_difficulty = sd(Difficulty, na.rm = TRUE) / sqrt(n()),
    )}

difficulty <- read_excel("Extraction_Human_Difficulty.xlsx") %>% as_tibble() %>% 
  pivot_longer(-Question) %>% 
  setNames(c('Citation','Question','Difficulty')) %>% 
  mutate(Difficulty = case_match(Difficulty, 'Easy' ~ 1, 'Medium' ~ 2, 'Hard' ~ 3))

file_path = 'Extraction_ai.xlsx'
sheets = excel_sheets(file_path)
ai_extractions <- sheets %>% lapply(function(x) read_excel(file_path, sheet = x) %>% as_tibble() %>% 
                                      mutate(across(everything(), function(x) x %>% str_replace("Response: ",""))) %>%
                                      separate_wider_delim(-Citation, delim = "Context:", names = c('Response','Context'), names_sep = '***',too_few = "align_start") %>% 
                                      mutate(across(-Citation, nchar))) %>% setNames(sheets)

human_extraction = "Human_Extraction_Cleaned.xlsx" %>% 
  read_excel(sheet = 'Human') %>%
  dplyr::select(-5, -(seq(8, ncol(.), by = 3))) %>%
  dplyr::select(-1) %>% 
  dplyr::slice(-(1:2)) %>% 
  mutate(across(-Question, nchar)) %>% 
  dplyr::select(-last_col())

verbosity_ratios = sheets %>% lapply(function(x) bind_cols(human_extraction$Question, (ai_extractions[[x]] %>% select(-1))/(human_extraction %>% select(-1))))

reviewers = c(
  'R1', "Which country was the study conducted in?",
  'R1',"Provide some background as to the drivers and/or motivators of community-based fisheries management.",
  'R2',"What management mechanisms are used?",
  'R3',"Which groups of people are involved in the management as part of the CBFM case-studies? Choices: Community-members, Researchers, Practitioners, Government, NGOs, Other",
  'R4',"What benefits of Community-Based Fisheries Management are reported in this case study?",
  'R4',"What are the indicators of success of CBFM?",
  'R1',"How was the data on benefits collected?",
  'R3',"What are the reported barriers to success of Community-Based Fisheries Management?",
  'R2',"Guidelines for future implementation of CBFM?",
  'R3',"How does the community monitor the system they are managing?",
  'R4',"How does the community make decisions?")

extractor <- "Human_Extraction_Cleaned.xlsx" %>% 
  read_excel(sheet = 'Human') %>%
  dplyr::select(-5, -(seq(8, ncol(.), by = 3))) %>%
  #dplyr::select(-1) %>% 
  dplyr::slice(-(1:2)) %>% 
  mutate(across(-Question, nchar)) %>% 
  dplyr::select(-last_col()) %>% 
  select(-3:-24) %>% 
  mutate(short_cit = substr(Question, 1,35)) #no idea why citation column is actually the question column in this instance
colnames(extractor)[1] <- "Extractor"
colnames(extractor)[2] <- "Citation"
colnames(extractor)[3] <- "short_cit"

reviewers_id <- matrix(reviewers, nrow = length(reviewers) / 2, byrow = TRUE) %>% as_tibble() %>% 
  setNames(c("Reviewer","Question"))

df_description = all_data_list %>% bind_rows() %>% 
  pivot_longer(-c('Citation','AI')) %>% 
  separate(value, sep = ':::', into = c("value", "description")) %>% 
  separate(value, sep = "\\|", into = paste0("rep",1:5)) %>% 
  separate(description, sep = "\\|", into = paste0("Description",1:5)) %>% 
  pivot_longer(starts_with('rep'), names_to = 'Agent') 

ai_df <- df_description %>% 
  dplyr::select(-starts_with('Description')) %>% 
  separate(value, sep = ';', into = paste0('Crit', 1:4)) %>% 
  pivot_longer(starts_with('Crit'), names_to = 'Criteria')

team_path = "output_assessment_TEAM.xlsx" #original file with unedited flag values = output_assessment_TEAM_OG.xlsx

sheet_names <- excel_sheets(team_path)

team_data_list <- lapply(sheet_names, function(sheet) {
  read_excel(team_path, sheet = sheet) %>% 
    mutate(AI = sheet)
})

df_validate = validate_path %>% 
  lapply(function(x) sheet_names %>% lapply(function(y)    read_excel(x, sheet = y) %>% 
                                              mutate(AI = y, Reviewer = x %>% str_remove("Raw_Team_Assessment/validate_assessment_") %>% str_remove('.xlsx')) %>% 
                                              bind_rows())
  ) %>% bind_rows() %>% 
  pivot_longer(-c('Citation','AI','Reviewer'), names_to = 'Question',values_to = 'Value') %>% 
  filter(!(Value %>% str_detect("Response|Context"))) %>% 
  pivot_wider(names_from = 'Reviewer', values_from = 'Value') %>% 
  filter(!is.na(SCOTT)) %>% 
  pivot_longer(-c('Citation','AI','Question'), names_to = 'Reviewer',values_to = 'Value') %>% 
  separate(Value, sep = ';', into = paste0('Crit',1:4)) %>% 
  pivot_longer(starts_with('crit'),values_to = 'value', names_to = 'Criteria') %>% 
  mutate(value = as.numeric(value)) %>% 
  mutate(Reviewer = recode(Reviewer, 'MATT' = 'R1',
                           'FABIO' = 'R2',
                           'SCOTT' = 'R3',
                           'ROWAN' = 'R4'))

stat_summary <- team_data_list %>% bind_rows() %>% 
  pivot_longer(-c("Citation","AI")) %>% 
  separate(value, sep = ';', into = paste0('Crit',1:4)) %>% 
  pivot_longer(starts_with("Crit"), names_to = 'Criteria') %>% 
  mutate(Agent = 'Human') %>% 
  bind_rows(ai_df) %>% 
  mutate(Flag = ifelse(Criteria == 'Crit4' & value > 1, "FLAG",NA),
         group_agent = ifelse(str_detect(Agent, "Human"), "Human Assessor", "GPT4-Turbo Assessor"),
         value = as.integer(value)) %>% 
  {flag_df <<- .} %>% 
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
                         'OPENAI_single' ~ 'GPT4')) %>% 
  mutate(Question = factor(str_split_fixed(Question, '\\?',2)[,1],levels = str_split_fixed(reviewers_id$Question, '\\?',2)[,1])) %>% 
  {full_df <<- .} %>% 
  group_by(group_agent, AI,Criteria) %>% 
  do_stats()

question_df <- full_df %>% 
  group_by(Reviewer, AI, Criteria, Question) %>% 
  do_stats()

paper_df <- full_df %>% 
  group_by(group_agent, AI, Criteria, Citation) %>% 
  do_stats()

reviewer_df <- full_df %>% 
  group_by(Reviewer, Criteria) %>% 
  do_stats()

flag_df <- flag_df %>% filter(!is.na(Flag))

### Make Plots ####
crit_pal = beyonce_palette(127)[-1]
## Overall
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

humandf <- full_df %>% filter(Agent == "Human") %>% select(-short_cit)
aidf <- full_df %>% filter(Agent != "Human")
aidf2 <- aidf %>% group_by(Citation, AI, Question, Criteria, Flag, group_agent, Reviewer, Difficulty) %>% 
  summarise(value = median(value)) %>% mutate(Agent = "AI") %>% 
  select(Citation, AI, Question, Criteria, Agent, Flag, group_agent, value, Reviewer, Difficulty)
statdf <- rbind(humandf, aidf2)
statdf2 <- statdf %>% filter(Reviewer != "GPT4-Turbo")
statdfx <- statdf %>% filter(Agent == "Human")
statdfy <- statdf %>% filter(Agent == "AI")

# stat tests
ttest <- statdfy %>%  group_by(AI, Criteria) %>%  summarise(t_value = t.test(value, mu = 2, alternative = "less")$statistic, p_value = t.test(value, mu = 2, alternative = "less")$p.value)
print(ttest)
tplot <- ggplot(ttest, aes(x = Criteria, y = t_value, fill = AI)) +
  geom_bar(stat = "identity", position = "dodge") +
  geom_hline(yintercept = 0, linetype = "dashed", color = "red") +
  geom_text(aes(label = ifelse(p_value < 0.05, "*", "")), position = position_dodge(width = 0.9), vjust = -0.5) +
  labs(title = "Comparison to Mean of 2",
       x = "Criteria",
       y = "t-value") +
  theme_minimal()
plot(tplot)


fullai_crit <- lmer(value ~ Agent*AI + (1|Reviewer) + (1|Citation), data = statdf)
anova(fullai_crit)
fullai_crit_emmeans <- emmeans(fullai_crit, ~ Agent)
fullai_crit_cont <- pairs(fullai_crit_emmeans, adjust = "tukey")
print(fullai_crit_cont)
#interaction between agent and AI so looking at agents seperately

agent_hum <- lmer(value ~ AI + (1|Reviewer) + (1|Citation), data = statdfx)
anova(agent_hum)
agent_hum_emmeans <- emmeans(agent_hum, ~ AI)
agent_hum_cont <- pairs(agent_hum_emmeans, adjust = "tukey")
print(agent_hum_cont)

agent_ai <- lmer(value ~ AI*Criteria + (1|Citation), data = statdfy)
anova(agent_ai)
agent_ai_emmeans <- emmeans(agent_ai, ~AI*Criteria)
agent_ai_cont <- pairs (agent_ai_emmeans, adjust = "tukey")
print(agent_ai_cont)

agent_ai <- lmer(value ~ AI + (1|Citation), 
                 data = filter(statdfy, Criteria == "Context to Question"))
anova(agent_ai)
agent_ai_emmeans <- emmeans(agent_ai, ~AI)
agent_ai_cont <- pairs (agent_ai_emmeans, adjust = "tukey")
print(agent_ai_cont)

#statdf <- statdf_rev

original <- lmer(value ~ AI + (1|Reviewer) + (1|Citation), data = statdf)
reverse <- lmer(value ~ AI + (1|Reviewer) + (1|Citation), data = statdf_rev)
anova(original, reverse)
