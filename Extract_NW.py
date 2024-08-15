from chatbot import ask_question, format_bot
from auxiliary import save_row

from dotenv import load_dotenv
import os
import csv

import pandas as pd
import glob
from unidecode import unidecode
import re
from auxiliary import full_text,add_rand_string, text_match, read_first_entries
 
load_dotenv()

restart_index = 0
max_paper = "ALL"
n_agents = 2
proj_location = "NW_Shelf"
pdf_location = 'Extraction_Input/pdfs'
pdf_location = proj_location + '/' + pdf_location

all_papers = glob.glob(pdf_location + "/*.pdf")
all_papers.sort(reverse=True)

directory_path = proj_location + '/Extraction_Output'

# Compile list of paper names
citations =[x.split('.pdf')[0] for x in [x.split('\\')[-1] for x in all_papers]]

# Load Questions, Papers, and Prepare Data Output
topic = "What are the impacts of deep-sea mining on different ecological groups?"

question_parms = pd.read_csv(proj_location + '/Extraction_Input/ExtractionQuestions.csv', index_col=False)
all_questions = question_parms['Question'].tolist()
# all_formats = question_parms['Response Format'].tolist()
all_coding_notes = question_parms['Coding Notes'].tolist()

# data_format = {'Quantitative': 'Return either a single value with any associated units. Or if multiple values are reported, return a list of all possible matching values found in the search results.', 
#                'Qualitative': 'Return a comprehensive response of up to three sentences.', 
#                'Categorical': 'Return a short phrase or single word only. Be as concise as possible. Do not explain or elaborate.',
#                'Theme': 'Return either a single item or a list where each element is at most three words.',
#                'Multiple-Choice': 'Return only the applicable choices from the list provided in the Query without elaboration.'}

# identities
identities = ["OPENAI",
              "CLAUDE",
              #"GOOGLE"
              ]

def create_prompt(question):      
   
    if os.environ.get("RAND_SEED"):
        new_question = add_rand_string(question)
    else:
        new_question = question

    prompt = """ You have recently published a scientific paper.  
    Your task is to provide a comprehensive, clear, and accurate answer to a question about the case studies in your paper accompanied by the most relevant passage copied from the paper. 
    When responding, keep the following guidelines in mind:
    - You should answer using similar language as the question.
    - Your responses should only come from the relevant content of this paper, which will be provided to you 
    in the following. 
    - Make sure the Data is correct and don't output false content.
    - Be as concise as possible.
    - Your paper may include multiple case studies, you will need to provide responses for each case study. 
    Response Format: 
    '{"Case Study Name":"[Answer] *** [Relevant Passage]","Case Study Name":"[Answer] *** [Relevant Passage]"}'

    Tip: If there is no relevant answer to the question based on the context, simply return "NO DATA".
    Question: 
    """
    prompt += new_question
    prompt += """Here are the contents of the paper, please answer the question and provide the Relevant Passage.
    
    """
    
    return prompt


header = ['Citation'] + all_questions

# Initialize embedder


output_dir = proj_location + "/Extraction_Output"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

all_data_df = pd.DataFrame()

# Iterate through papers

for paper_num,paper in enumerate(range(restart_index,len(all_papers[:]))):
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    print(paper_num)
    # End interation early according to variables in '.env'
    try:
        max_paper = int(max_paper)
        if paper_num >= max_paper:
            break
    except:
        print("Extracting All")

    # Set current paper
    paper = all_papers[paper_num].replace('\\', '/')
    print(paper)
    # KG_csv = paper.replace('pdfs',"KG").replace('.pdf','.csv')
    # memory = []
    # entities = set()
    
    try:
        contents = full_text(paper)
        unreadable_pdf = False
    except:
        unreadable_pdf = True
        print("Unreadable PDF")




    # Initialize lists to receive data
    all_responses = []
    all_data = []
    all_context = []
    all_summaries = []
    
    # Iterate through each question in '/ExtractionQuestions.csv'
    for q_num, question in enumerate(all_questions):
        # End interation early according to variables in '.env'
        try:
            max_question = int(os.environ.get("N_QUESTIONS"))
            if q_num >= int(os.environ.get("N_QUESTIONS")):
                break
        except:
            print("Extracting All Questions")

        print("\n\n" + question + "\n\n")

        # Initialize lists for each question to accommodate multiple AI agents. Set number in .env 'N_AGENTS'
        responses = []
        data = []
        contexts = []
        question_notes = question + ' '+ all_coding_notes[q_num]
        prompt = create_prompt(question_notes)
        # Query the LLM multiple times
        for identity in identities:
            print(f"My identity is: {identity}")
            
            save_row(identity,header,output_dir)
            # save_row(identity + '_single',header,output_dir)

            for agent in range(n_agents):
                print(f"Agent {agent + 1}")
                            # If the paper is unreadable, this try block allows the code to continue so that placeholder data can be recorded below.
                if unreadable_pdf:
                    datum,context = 2*['UNREADABLE PDF']
                else:
                    response_text = ask_question(prompt,contents,identity)
                split_attempts = 0
                while split_attempts < 3:
                    try:

                        parts = response_text.split("***")
                        datum, context = parts[0],"".join(parts[1:])
                        # context_check = text_match(context,contents)
                        # if context_check:
                        #     print("***\nContext Verified\n***")
                        split_attempts = 999
                    except:
                        print("LLM SPLITTING....")
                        response_text = ask_question("The following text should have two parts. The first is a response to a question and the second is a verbatim excerpt from a document that should support the first. Without altering the text in anyway, insert a delimiter '***' between the two parts of text. If the response includes 'NO DATA', return 'NO DATA *** NO CONTEXT'. Only return the text as requested. Do not provide a preamble. ",response_text, identity)
                        split_attempts += 1
                        datum,context = "BAD-PARSING: " + response_text,"BAD-PARSING: " + response_text
                        # context_check = True
                # if context_check:
                #     context_check_count = 99
            #  print(context)
                # Append results to lists
                data.append(datum)
                contexts.append(context)
                    
                

            # Gather all agent responses to be summarised in the desired format. 
            # Formats are specified in '/ExtractionQuestions.csv'
            # They are defined in 'chatbot.format_bot'
            # format = all_formats[q_num]
            print("\n\n")
            print("Summary Bot\n\n")

            if unreadable_pdf:
                summary = "UNREADABLE PDF"
            # elif irrelevant_paper:
                # summary = "IRRELEVANT PAPER"

            # Call LLM to gather agent responses
            else:
                synthesis_prompt = f"""
                    You are a formatting and synthesis algorithm and have been given the following Responses from several scientists about a paper, some of whom have not read the whole paper. 
                    Your task is to provide a truthful answer to the question provided based on the Responses from the scientists about their study according to the following Formatting Requirements.
                    When answering, re-state the question as the answer and return text that complies with the formatting requirements. If all responses say "NO DATA", return "NO DATA" only. Do not report any uncertainties.
                    Tip: If something is unclear, you don't need to express that. Finish your response with '***'.
                    
                    Question: {question} 
                    """
                summary = ask_question(synthesis_prompt, '; '.join(data), identity)
                # if 'NO DATA' not in summary:
                #     graph = KG_chain(summary,KG_csv,entities)
                #     memory.append(graph['tuples1'])
                #     print(summary)
                #     print("\n\n")

            # Append data to lists
            all_summaries.append(summary)
            all_responses.append(responses)
            all_data.append(data)
            all_context.append(contexts)


        
        # Save single agent data, row-by-row
        citation = [citations[paper_num]]
        single_data =  ["Response: " + tuple[0] for tuple in all_data]
        single_context =  ["\nContext: " + tuple[0] for tuple in all_context]
        single_response = [str1 + str2 for str1, str2 in zip(single_data, single_context)]
        save_row(identity + '_single', citation + single_response,output_dir)
        # Save paper data, row-by-row
        all_context_combined = ['; '.join(tuple) for tuple in all_context]
        combined_data = ["Response: " + str1 + " Context: " + str2 for str1, str2 in zip(all_summaries, all_context_combined)]

        save_row(identity,citation + combined_data,output_dir)
        paper_num += 1




## Refine Questions from Joe's updates


