library(tidyverse)
library(readxl)
library(dplyr)
library(xlsx)

#### set-up ####
file_path = 'Extraction_ai.xlsx'
sheets = excel_sheets(file_path)
ai_extractions <- sheets %>% lapply(function(x) read_excel(file_path, sheet = x) %>% as_tibble() %>% 
    mutate(across(everything(), function(x) x %>% str_replace("Response: ",""))) %>%
    separate_wider_delim(-Citation, delim = "Context: ", names = c('Response','Context'), names_sep = '***',too_few = "align_start")) %>% 
  setNames(sheets)

GPT4x1 <- ai_extractions[['OPENAI_single']] %>% mutate(Citation = substr(Citation, 1,35))
GPT4x3 <- ai_extractions[['OPENAI']] %>% mutate(Citation = substr(Citation, 1,35))
Elicit <- ai_extractions[['ELICIT']] %>% mutate(Citation = substr(Citation, 1,35))

human_extraction = "Human_Extraction_Cleaned.xlsx" %>% 
  read_excel(sheet = 'Human') %>%
  dplyr::select(-5, -(seq(8, ncol(.), by = 3))) %>%
  slice(-(1:2))
human_extraction <- human_extraction[,c(2:24, 1, 25)]
names(human_extraction) <- names(GPT4x1)
colnames(human_extraction)[24] <- "Human"
colnames(human_extraction)[25] <- "Notes"

human <- subset(human_extraction, select = -c(Human, Notes))
human <- human %>% mutate(Citation = substr(Citation, 1,35))

#### long form and merging data ####
human_long <- human  %>% 
  pivot_longer(cols = -Citation, 
               names_to = "Question",
               values_to = "Answer") %>% 
  mutate(Source="human") %>%
  select(Citation, Question, Source, Answer)

GPT4_long <- GPT4x1 %>% 
  pivot_longer(cols = -Citation, 
               names_to = "Question",
               values_to = "Answer") %>% 
  mutate(Source="GPT4") %>%
  select(Citation, Question, Source, Answer)

GPT4x3_long <- GPT4x3  %>% 
  pivot_longer(cols = -Citation, 
               names_to = "Question",
               values_to = "Answer") %>% 
  mutate(Source="GPT4x3") %>%  
  select(Citation, Question, Source, Answer)

Elicit_long <- Elicit  %>% 
  pivot_longer(cols = -Citation, 
               names_to = "Question",
               values_to = "Answer") %>% 
  mutate(Source="Elicit") %>%  
  select(Citation, Question, Source, Answer)

fulldf <- bind_rows(human_long, GPT4_long, GPT4x3_long, Elicit_long)
widedf <- fulldf %>% pivot_wider(names_from = 'Source', values_from = 'Answer')


#### comparing NA values ####
widedf[] <- lapply(widedf, trimws)
df <- widedf %>% 
  mutate_all(~ifelse(. == "NA", NA, .)) %>% 
  mutate_all(~ifelse(. == "NA***", NA, .)) %>% 
  mutate_all(~ifelse(. == "NA; NA; NA", NA, .)) %>% 
  mutate_all(~ifelse(. == "NO DATA", NA, .)) %>%
  mutate_all(~ifelse(. == "NO CONTEXT;  NO CONTEXT;  NO CONTEXT", NA, .)) %>% 
  mutate_all(~ifelse(. == "NO CONTEXT;  NO CONTEXT; NO DATA", NA, .)) %>%
  mutate_all(~ifelse(. == "NO DATA;  NO CONTEXT;  NO CONTEXT", NA, .))

r.hum_vs_GPT4x1<- df %>% filter(is.na(human) & !is.na(GPT4)) #110 instances where GPT4x1had response and human responded with NA
r.GPT4_vs_hum <- df %>% filter(is.na(GPT4) & !is.na(human)) #154 instances where human had response and GPT4x1responded with NA

r.hum_vs_GPT4x3 <- df %>% filter(is.na(human) & !is.na(GPT4x3)) #137 instances where GPT4x3 had response and human responded with NA
r.GPT4x3_vs_hum <- df %>% filter(is.na(GPT4x3) & !is.na(human)) #111 instances where human had response and GPT4x3 responded with NA

r.hum_vs_Elicit <- df %>% filter(is.na(human) & !is.na(Elicit)) #191 instances where Elicit had response and human responded with NA
r.Elicit_vs_hum <- df %>% filter(is.na(Elicit) & !is.na(human)) #1 instance where human had response and Elicit responded with NA


#### separate response/context ####
newdf <- df %>% mutate(Category = ifelse(grepl("Response", Question,), "response", "context"))
response <- newdf %>% filter(Category == "response")
context <- newdf %>% filter(Category == "context")

## for responses ##
r.hum_vs_GPT4x1<- response %>% filter(is.na(human) & !is.na(GPT4)) #54 instances where GPT4x1had response and human responded with NA
r.GPT4_vs_hum <- response %>% filter(is.na(GPT4) & !is.na(human)) #76 instances where human had response and GPT4x1responded with NA

r.hum_vs_GPT4x3 <- response %>% filter(is.na(human) & !is.na(GPT4x3)) #68 instances where GPT4x3 had response and human responded with NA
r.GPT4x3_vs_hum <- response %>% filter(is.na(GPT4x3) & !is.na(human)) #55 instances where human had response and GPT4x3 responded with NA

r.hum_vs_Elicit <- response %>% filter(is.na(human) & !is.na(Elicit)) #94 instances where Elicit had response and human responded with NA
r.Elicit_vs_hum <- response %>% filter(is.na(Elicit) & !is.na(human)) #0 instance where human had response and Elicit responded with NA

r.na.humGPT4x1<- response %>% filter(is.na(human) & is.na(GPT4)) #40 instances where both returned NA
r.na.humgtp4x3 <- response %>% filter(is.na(human) & is.na(GPT4x3)) #26 instances where both returned NA
r.na.humelicit <- response %>% filter(is.na(human) & is.na(Elicit)) #0 instances where both returned NA

r.ans.humgtp4 <- response %>% filter(!is.na(human) & !is.na(GPT4)) #193 instances where both returned answers
r.ans.humgtp4x3 <- response %>% filter(!is.na(human) & !is.na(GPT4x3)) #214 instances where both returned answers
r.ans.humelicit <- response %>% filter(!is.na(human) & !is.na(Elicit)) #269 instances where both returned answers


## for context ##
c.hum_vs_GPT4x1<- context %>% filter(is.na(human) & !is.na(GPT4)) #56 instances where GPT4x1had response and human responded with NA
c.GPT4_vs_hum <- context %>% filter(is.na(GPT4) & !is.na(human)) #78 instances where human had response and GPT4x1responded with NA

c.hum_vs_GPT4x3 <- context %>% filter(is.na(human) & !is.na(GPT4x3)) #69 instances where GPT4x3 had response and human responded with NA
c.GPT4x3_vs_hum <- context %>% filter(is.na(GPT4x3) & !is.na(human)) #56 instances where human had response and GPT4x3 responded with NA

c.hum_vs_Elicit <- context %>% filter(is.na(human) & !is.na(Elicit)) #97 instances where Elicit had response and human responded with NA
c.Elicit_vs_hum <- context %>% filter(is.na(Elicit) & !is.na(human)) #1 instance where human had response and Elicit responded with NA

c.na.humGPT4x1<- context %>% filter(is.na(human) & is.na(GPT4)) #41 instances where both returned NA
c.na.humgtp4x3 <- context %>% filter(is.na(human) & is.na(GPT4x3)) #28 instances where both returned NA
c.na.humelicit <- context %>% filter(is.na(human) & is.na(Elicit)) #0 instances where both returned NA

c.ans.humgtp4 <- context %>% filter(!is.na(human) & !is.na(GPT4)) #188 instances where both returned answers
c.ans.humgtp4x3 <- context %>% filter(!is.na(human) & !is.na(GPT4x3)) #210 instances where both returned answers
c.ans.humelicit <- context %>% filter(!is.na(human) & !is.na(Elicit)) #265 instances where both returned answers


## creating confusion matrix from the data
pal = c("#a6611a",
        "#dfc27d",
        "#80cdc1",
        "#018571")

(newdfx <- newdf %>% filter(Category == 'response') %>% pivot_longer(c(GPT4, GPT4x3, Elicit), names_to = "AI", values_to = "value") %>% 
    mutate(human_data = ifelse(is.na(human),"No Data","Data"),
           ai_data = ifelse(is.na(value),"No Data","Data")) %>% 
    mutate(human_data = factor(human_data,levels = c('Data',"No Data")),
           ai_data = factor(ai_data, levels = c("Data","No Data") %>% rev)) %>% 
  #   
  # mutate(error_type = case_when(is.na(human) & is.na(value) ~ "4", 
  #                               is.na(human) & !is.na(value) ~ "extras",
  #                               !is.na(human) & is.na(value) ~ "misses",
  #                               !is.na(human) & !is.na(value) ~"finds",
  #                               TRUE ~ "0")) %>% 
  #   
  # mutate(human = factor(ifelse(str_detect(error_type,"misses|finds"),"Data","No Data"),levels = c("Data","No Data")),
  #        ai = factor(ifelse(str_detect(error_type,"extras|finds"),"Data","No Data"),levels = c("Data","No Data") %>% rev)) %>% 
  #  
    group_by(AI,human_data,ai_data,Category) %>% 
    summarise(value =  signif(n()/363, digits = 2)) %>% as_tibble() %>% 
    complete(AI,human_data,ai_data,Category, fill = list(value = 0)) %>% 
    ungroup() %>% 
    mutate(display_value = ifelse(value >= 0.01 | value == 0, value,"<0.01")) %>% 
  ggplot() +
  geom_tile(aes(x = human_data, y = ai_data, fill = interaction(human_data,ai_data))) +
  geom_text(aes(x = human_data, y = ai_data, label = display_value)) +
  xlab("Human") +
  ylab("AI") +
   scale_fill_manual(values = pal[c(1,4,4,2)]) + #c("tan2","forestgreen","darksalmon","forestgreen")) +
  # scale_x_discrete(position = "top") +
  facet_wrap(~ AI) +
  theme_classic() +
  theme(legend.position = "none"))

ggsave("Figures/confusion_matrix.png", width = 7, height = 3, device = "png")



## list of false postives
FPdatax <- newdf %>% pivot_longer(c(GPT4, GPT4x3, Elicit), names_to = "AI", values_to = "value") %>% 
          mutate(human_data = ifelse(is.na(human),"No Data","Data"),
          ai_data = ifelse(is.na(value),"No Data","Data")) %>% 
          mutate(human_data = factor(human_data,levels = c('Data',"No Data")),
          ai_data = factor(ai_data, levels = c("Data","No Data") %>% rev))

FPdata <- FPdatax %>% filter(human_data == "No Data" & ai_data == "Data", Category == "context")

write.csv(FPdata, file = "falsepos_data.csv", row.names = FALSE)











  