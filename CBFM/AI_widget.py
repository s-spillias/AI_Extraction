#####
your_name_here = "CHATGPT" # or 'Rowan', 'Fabio', 'Matt'
####

bespoke_columns = {"CHATGPT":range(2,13),"Scott":[5,9,11],"Rowan":[6,7,12],'Fabio':[4,10],'Matt':[2,3,8]}
# Context: Pull out the relevant bit of the paper. Did they pull out something relevant to the question
# Response: Given that context, is the response relevant/justified. Just rate the AI
# How similar are the two answers that have been extracted?
# we assume that there is 

import pandas as pd
from tkinter import *
from tkinter import ttk
import openpyxl
import shutil
import os
import random
from chatbot import ask_question
import glob
from auxiliary import full_text, text_match, ask_AI

project_directory = "CBFM/"
input_directory = project_directory + 'Extraction_Output/'
output_path = project_directory + 'Assessment_Output/output_assessment_AI_reverse.xlsx'

# Load the Excel spreadsheet
xls_human = openpyxl.load_workbook(input_directory +'Extraction_Human.xlsx')

# Load the Excel file using openpyxl
xls_ai = openpyxl.load_workbook(input_directory +'Extraction_ai.xlsx')


n_agents = 5

global resume
# Check if 'CBFM/output_assessment.xlsx' exists, if not, copy 'CBFM/Extraction_ai.xlsx' to 'CBFM/output_assessment.xlsx'
if not os.path.exists(output_path):
    print("copying source file")
    shutil.copyfile(input_directory +'Extraction_ai.xlsx', output_path)
    resume = False
else:
    print(output_path + " exists")
    resume = True


# Extract the questions from the 'CBFM/criteria.csv' file
questions = ['Context2Question',"Response2Context","AI2Human"]

ratings = "1 - Poor \n2 - Fair \n3 - Good"

def sanitize_text(text):
    # Trim leading and trailing whitespace
    sanitized = text.strip()
    
    # Replace single quotes with double quotes
    sanitized = sanitized.replace("'", '"')


    # Replace newline characters with a space
    #sanitized = sanitized.replace('\n', ' ')

    # Remove extra internal whitespace by splitting and rejoining
    sanitized = ' '.join(sanitized.split())
    sanitized = sanitized.replace("Context:", '\n\nContext:\n')
    #print(sanitized)
    return sanitized

global suppress
suppress = False
# Function to yield one set of cells at a time, along with the current sheet name and cell position
def cell_generator():
    newline = "\n\n"
    sheet_name = "ALL"
    human_sheet = xls_human[sheet_name]
    max_column_human = human_sheet.max_column
    column_names = [human_sheet.cell(row=1, column=col).value for col in range(1, max_column_human + 1)]
    for col in bespoke_columns[your_name_here]:
        for row in range(2, human_sheet.max_row + 1): 
            ai_sheetnames = xls_ai.sheetnames
            random.shuffle(ai_sheetnames)
            # import paper text
            paper_name = human_sheet.cell(row=row,column = 1).value
            contents = full_text(project_directory + 'Extraction_input/pdfs/Human_Kept/' + paper_name)

            for sheet_name_ai in ai_sheetnames:
                sheet_ai = xls_ai[sheet_name_ai]

                col_name = column_names[col-1] + newline
            
                cell_value_ai = sheet_ai.cell(row=row, column=col).value
                ai_text = sanitize_text(cell_value_ai)
                ai_context = ai_text.split('Context:')[1]
                # prompt = "hello"
                # ask_AI(prompt, 'azure-gpt-4-turbo')
                # ai_context,contents


                #print(ai_text)
                human_text = human_sheet.cell(row=row, column=col).value
                human_text = sanitize_text(human_text)
                if ai_text is not None:
                    #print(cell_value_ai[:10])
                    #print(human_text[:10])
                    wb = openpyxl.load_workbook(output_path)
                    sheet = wb[sheet_name_ai]
                    cell = sheet.cell(row=row, column=col)
                    #print(cell)
                    global resume
                    global suppress
                    if len(cell.value.split("|")) == 5:
                        print(str(row) + str(col))
                        resume = True
                    else:
                        print(str(row) + str(col))
                        suppress = True
                        resume = False
                    #print("New cell.")
                    yield f'Response: {human_text} && {newline}    {ai_text}', sheet_name_ai, (row, col),col_name
# Create a generator object
cell_gen = cell_generator()
working = True
while working:
    try:
        try:
            cell_values, sheet_name_ai, cell_position,col_name = next(cell_gen)
        except:
            working = False
        if resume:
            raise(KeyError)
        wb = openpyxl.load_workbook(output_path)
        sheet = wb[sheet_name_ai]
        # Unpack the tuple
        row_number , column_number = cell_position
        cell = sheet.cell(row=row_number, column = column_number)
        prompt = f"""You are a very critical reviewer. You are meticulous and demanding, but fair. If you can find fault you will. You are assessing the quality of answer to the following Question: {col_name} You will be given answers from two separate responders. You are evaluating only the first answer. Each answer will have two parts, a Response and Context. For three criteria, you will rate on a scale from 1 to 3, where {ratings}. The criteria are as follows:
         1) how well does the Context in the first answer apply to the Question. 2) how well does the Context in the first answer support the Response and 3) how does the Response and Context in the first answer compare to the Response and Context in the second answer - if the first answer is better score 3, if it is worse score 1, if similar score 2.
         Return exactly one sentence explanation for each of the three ratings.
         Your response should be formatted as follows. :::Expanation1.Explanation2.Explanation3::: ; ***X;X;X***, where 'X' is the rating for the applicable criterion.  Here are the answers:"""
        contents = cell_values
        n_agents_counter = 0
        out_list = []
        explanation_list = []
        while n_agents_counter < n_agents:
            try:
                output = ask_question(prompt, contents,"OPENAI")
                out = output.split('***')[1] 
                explanation = output.split(':::')[1]

                if not len(out) == 5:
                    raise(ValueError)
                out_list.append(out)
                explanation_list.append(explanation)
                n_agents_counter += 1
            except:
                print("Retrying...")
        explanations = "|".join(explanation_list)
        cell.value = "|".join(out_list) + ':::' + explanations
        # Save the DataFrame back to the Excel file
        wb.save(output_path)
        print("Data written to " + output_path)
    except:
        print('catching up')

