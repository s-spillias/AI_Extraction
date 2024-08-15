#from embedding_engine import Embedder
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

restart_index = 11
max_paper = "ALL"
n_agents = 3
proj_location = "CBFM"
pdf_location = 'Extraction_Input/pdfs'
pdf_location = proj_location + '/' + pdf_location

all_papers = glob.glob(pdf_location + "/*.pdf")
all_papers.sort(reverse=True)

directory_path = proj_location + '/Extraction_Output'
paper_human = []

# Read the CSV file and extract values from the first column
with open(directory_path + '/paper_names.csv', 'r', encoding = 'utf-8') as csv_file:
    csv_reader = csv.reader(csv_file)
    
    # Assuming the first column is at index 0
    for row in csv_reader:
        if row:  # Check if the row is not empty
            paper_human.append(row[0])

paper_human = paper_human[1:]

paper_ai = []
with open(proj_location + '/Extraction_Output' + '/Extraction_ai.csv', 'r', encoding = 'utf-8') as csv_file:
    csv_reader = csv.reader(csv_file)
    
    # Assuming the first column is at index 0
    for row in csv_reader:
        if row:  # Check if the row is not empty
            paper_ai.append(row[0])

paper_ai = paper_ai[1:]
paper_ai = [element.replace('CBFM/Extraction_Input/pdfs/', '') for element in paper_ai]
paper_human = paper_human[1:]
paper_human = [element.replace('.pdf', '') for element in paper_human]
all_papers = [pdf_location + '/' + s for s in paper_human]

unique_to_paper_human = set(paper_human) - set(paper_ai)

# Identify strings present in paper_ai but not in paper_human
unique_to_paper_ai = set(paper_ai) - set(paper_human)

# Convert the results back to lists if needed
unique_to_paper_human = list(unique_to_paper_human)
unique_to_paper_ai = list(unique_to_paper_ai)


# # Clean paper names; remove quotations, UTF characters, and trailing spaces.
# for paper in all_papers:
#     os.rename(paper, unidecode((re.sub('[“”"]', '',paper)).replace(' .pdf','.pdf')))

# Compile list of paper names
citations =[x.split('.pdf')[0] for x in [x.split('\\')[-1] for x in all_papers]]

# Load Questions, Papers, and Prepare Data Output
topic = os.environ.get("TOPIC")

question_parms = pd.read_csv(proj_location + '/Extraction_Input/ExtractionQuestions.csv', index_col=False)
all_questions = question_parms['Question'].tolist()
all_formats = question_parms['Response Format'].tolist()
all_coding_notes = question_parms['Coding Notes'].tolist()

data_format = {'Quantitative': 'Return either a single value with any associated units. Or if multiple values are reported, return a list of all possible matching values found in the search results.', 
               'Qualitative': 'Return a comprehensive response of up to three sentences.', 
               'Categorical': 'Return a short phrase or single word only. Be as concise as possible. Do not explain or elaborate.',
               'Theme': 'Return either a single item or a list where each element is at most three words.',
               'Multiple-Choice': 'Return only the applicable choices from the list provided in the Query without elaboration.'}

# identities
identities = ["OPENAI",
              #"CLAUDE",
              #"GOOGLE"
              ]

def create_prompt(question):      
   
    if os.environ.get("RAND_SEED"):
        new_question = add_rand_string(question)
    else:
        new_question = question

    prompt = f""" You have recently published a scientific paper.  
    Your task is to provide a comprehensive, clear, and accurate answer to questions about your paper accompanied by the most relevant passage copied from the paper. 
    When responding, keep the following guidelines in mind:
    - You should answer using similar language as the question.
    - Your responses should only come from the relevant content of this paper, which will be provided to you 
    in the following. 
    - Make sure the Data is correct and don't output false content.
    - Be as concise as possible.
    Response Format: 
    '[Answer] *** [Relevant Passage]'

    Tip: If there is no relevant answer to the question based on the context, simply return "NO DATA" and nothing else.
    Question: {new_question}
    """
    
    prompt += """Here are the contents of the paper, please answer the question and provide the Relevant Passage.
    
    {contents}"""
    
    return prompt


header = ['Citation'] + all_questions

# Initialize embedder


output_dir = proj_location + "/Extraction_Output"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

all_data_df = pd.DataFrame()

# Iterate through papers
for identity in identities:
    print(f"My identity is: {identity}")
    
    save_row(identity,header,output_dir)
    save_row(identity + '_single',header,output_dir)
    for paper_num in range(restart_index,len(all_papers[:])):
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
        if paper.replace("CBFM/Extraction_Input/pdfs/","").replace(".pdf","") not in unique_to_paper_human:
            print("Skipping")
            continue
        # KG_csv = paper.replace('pdfs',"KG").replace('.pdf','.csv')
        # memory = []
        # entities = set()
        
        try:
            contents = full_text(paper + '.pdf')
            unreadable_pdf = False
        except:
            unreadable_pdf = True
            print("Unreadable PDF")

        q_num = 0

  
        # Initialize lists to receive data
        all_responses = []
        all_data = []
        all_context = []
        all_summaries = []
        
        # Iterate through each question in '/ExtractionQuestions.csv'
        for question in all_questions:
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
            question_notes = question + all_coding_notes[q_num]
            prompt = create_prompt(question_notes)
            # Query the LLM multiple times
            for agent in range(n_agents):
                print(f"Agent {agent + 1}")
                            # If the paper is unreadable, this try block allows the code to continue so that placeholder data can be recorded below.
               # print(relevant_docs)
                # Write place-holder data if pdf is 'unreadable' or 'irrelevant'
                context_check = False
                context_check_count = 0
                while context_check_count < 3: 
                    context_check_count += 1
                    print('Attempting...')
                    if unreadable_pdf:
                        datum,context = 2*['UNREADABLE PDF']
                        context_check = True
                    # elif irrelevant_paper:
                    #     data,context = 2*['IRRELEVANT PAPER']
                    # Otherwise query LLM with context from the vectorstore and the relevant question.
                    else:
                        response_text = ask_question(prompt,contents,identity)
                    split_attempts = 0
                    while split_attempts < 3:
                        context_check = False
                        try:

                            parts = response_text.split("***")
                            datum, context = parts[0],"".join(parts[1:])
                            context_check = text_match(context,contents)
                            if context_check:
                                print("***\nContext Verified\n***")
                            split_attempts = 999
                        except:
                            print("LLM SPLITTING....")
                            response_text = ask_question("The following text should have two parts. The first is a response to a question and the second is a verbatim excerpt from a document that should support the first. Without altering the text in anyway, insert a delimiter '***' between the two parts of text. If the response includes 'NO DATA', return 'NO DATA *** NO CONTEXT'. Only return the text as requested. Do not provide a preamble. ",response_text, identity)
                            split_attempts += 1
                            datum,context = "BAD-PARSING: " + response_text,"BAD-PARSING: " + response_text
                            context_check = True
                    if context_check:
                        context_check_count = 99
                #  print(context)
                    # Append results to lists
                    data.append(datum)
                    contexts.append(context)
                    
                

            # Gather all agent responses to be summarised in the desired format. 
            # Formats are specified in '/ExtractionQuestions.csv'
            # They are defined in 'chatbot.format_bot'
            format = all_formats[q_num]
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
                    Formatting Requirements: {data_format[format]}***
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

            # Increase question counter
            q_num += 1
        
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


