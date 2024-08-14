library(tidyverse)
library(readxl)
library(beyonce)
library(ggpubr)

file_path = 'output_assessment_CHATGPT_explanation.xlsx'

figure_folder = '../Manuscript/Figures'
# firstcontact-gpt4-32k
# January 29, ran Elicit and GPT4-32k
sheet_names <- excel_sheets(file_path)

all_data_list <- lapply(sheet_names, function(sheet) {
  read_excel(file_path, sheet = sheet) %>% 
    mutate(AI = sheet)
})

do_stats = function(x){
  x %>% 
  summarise(mean = mean(value),
  standard_error = sd(value, na.rm = TRUE) / sqrt(n()),
  st_dev = sd(value),
  difficulty_mean = mean(Difficulty, na.rm = TRUE),
  st_dev_difficulty = sd(Difficulty, na.rm = TRUE),
  standard_error_difficulty = sd(Difficulty, na.rm = TRUE) / sqrt(n()),
  )
}

difficulty <- read_excel("Extraction_Human_Difficulty.xlsx") %>% as_tibble() %>% 
  pivot_longer(-Question) %>% 
  setNames(c('Citation','Question','Difficulty')) %>% 
  mutate(Difficulty = case_match(Difficulty, 'Easy' ~ 1, 'Medium' ~ 2, 'Hard' ~ 3))

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

team_path = "output_assessment_TEAM.xlsx"

sheet_names <- excel_sheets(team_path)

team_data_list <- lapply(sheet_names, function(sheet) {
  read_excel(team_path, sheet = sheet) %>% 
    mutate(AI = sheet)
})

stat_summary <- team_data_list %>% bind_rows() %>% 
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
  #ggsave(file.path(figure_folder,'overall.png'))
  
  
## Questions
question_df %>% filter(!str_detect(Reviewer,'GPT')) %>% ungroup() %>% 
  mutate(
  normalized_difficulty_mean = 1 + 2*((difficulty_mean - min(difficulty_mean,na.rm = TRUE)) / (max(difficulty_mean,na.rm = TRUE) - min(difficulty_mean,na.rm = TRUE))),
  normalized_difficulty_st_dev = st_dev_difficulty / (max(st_dev_difficulty) - min(st_dev_difficulty)),
  normalized_difficulty_standard_error = standard_error_difficulty / (max(standard_error_difficulty) - min(standard_error_difficulty))
) %>% 
  arrange(difficulty_mean) %>% ungroup() %>% 
ggplot() +
  aes(x = AI, y = mean, fill = Criteria, group = Criteria) +
  geom_hline(yintercept = 2, linetype = 'dashed',alpha = 0.5 ) +
  geom_col(stat = "identity", position = "dodge", color = "black") +
  geom_segment(aes(x = 4, y = 1.1, xend = 4, yend = 2.9), col = 'orange') +
  geom_point(aes(x = 4,y = normalized_difficulty_mean), size = 3, col = 'orange', show.legend = FALSE) +
  geom_errorbar(aes(ymin = mean - standard_error, ymax = mean + standard_error),
                position = position_dodge(width = 0.9), width = 0.25) +
  # labs(title = "Mean Values by Group and Criteria", x = "Group", y = "Mean Value") +
  theme_classic() +
  coord_cartesian(ylim = c(1, 3), xlim = c(1,3.7)) +
  facet_wrap(~Question, labeller = label_wrap_gen()) +
  labs(x = '') +
  scale_fill_manual(values = crit_pal) +
  scale_y_continuous(
    name = "Assessed Quality",
    #labels = c("Poor","Fair","Good"),breaks = c(1,2,3),
    sec.axis = sec_axis(~ (. - 1)/2, name = "Question Difficulty", labels = c("Easy","Hard"), breaks = c(0,1)),
  ) +
  theme(axis.text.y.right = element_text(color = "orange"),
        strip.text = element_text(size = 8),
        legend.position = 'bottom',
        ) +
  geom_text(aes(x = 4.2, y = 1.15, label = Reviewer, hjust = 1, vjust = 1), size = 3) 
#ggsave(file.path(figure_folder,'questions_supp.png'), width = 12, height = 7)

# Check for Reviewer Consistency
ggplot(reviewer_df, aes(x = Reviewer, y = mean, fill = Criteria, group = Criteria)) +
  geom_hline(yintercept = 2,linetype = 'dashed',alpha = 0.5 ) +
  geom_col(stat = "identity", position = "dodge", color = "black") +
  geom_errorbar(aes(ymin = mean - standard_error, ymax = mean + standard_error),
                position = position_dodge(width = 0.9), width = 0.25) +
  labs(x = "Reviewer", y = "Mean Assessed Quality") +
  theme_classic() +
  coord_cartesian(ylim = c(1, 3)) +
  theme(legend.position = 'bottom') +
#facet_wrap(~Question) +
  scale_fill_manual(values = crit_pal)  # Set your desired fill colors
#ggsave(file.path(figure_folder,'reviewer_supp.png'), width = 12, height = 7)


full_df %>% filter(!str_detect(Reviewer,'GPT')) %>% 
  group_by(Reviewer,Criteria) %>% 
  ggplot() +
  geom_density(fill = 'skyblue',aes(x = value), adjust = 2.5) +
  facet_grid(Reviewer~ Criteria) +
  theme_classic()


## Impact of Difficulty
ggplot(question_df %>% filter(!str_detect(Reviewer,'GPT')), aes(x = difficulty_mean, y = mean, col = Criteria)) +
  geom_point() +
  geom_smooth(method = "lm", se = FALSE) +  # Use method = "lm" for linear model
  #stat_poly_line() +
  #stat_poly_eq() +
  theme_classic() +
  facet_wrap(~AI) +
  labs(y = 'Mean Assessed Quality', x = 'Mean Question Difficulty') +
  
  theme(legend.position = 'bottom') +
  scale_colour_manual(values = crit_pal)
#ggsave(file.path(figure_folder,'question_difficulty_supp.png'), width = 12, height = 7)


ggplot(paper_df %>% filter(str_detect(group_agent,'Human')), 
       aes(x = difficulty_mean, y = mean, col = Criteria)) +
  geom_point() +
  labs(y = 'Mean Assessed Quality', x = 'Mean Paper Difficulty') +
  
  geom_smooth(method = "lm", se = FALSE) +  # Use method = "lm" for linear model
  theme_classic() +
  theme(legend.position = 'bottom') +
  scale_colour_manual(values = crit_pal) # Set your desired fill colors
  #ggsave(file.path(figure_folder,'paper_difficulty_supp.png'), width = 12, height = 7)


