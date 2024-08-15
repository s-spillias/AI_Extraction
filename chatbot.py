
from langchain.chains import LLMChain, SequentialChain,RetrievalQA
from langchain.prompts import PromptTemplate


import pathlib
import textwrap

import json
import os



from auxiliary import get_llm, configure_azure_support

# Configure Claude
import boto3
session = boto3.Session(profile_name='default')
brt = boto3.client(service_name='bedrock-runtime')
import openai
openai.api_key = os.environ.get("OPENAI_API_KEY")
 
modelId = 'anthropic.claude-v2'
accept = 'application/json'
contentType = 'application/json'

#Configure Google


# def pretty_print_docs(docs):
#     return f"".join([f"%%%" + d.page_content for i, d in enumerate(docs)])

# def embed_paper(paper_path,embedding):
#     pdf_location = os.environ.get("PROJ_LOCATION") + '/' + os.environ.get('PDF_LOCATION')
#     try:
#         paper_embed = (paper_path.replace(pdf_location + "/","")).replace(".pdf","")
#     except:
#         print("PDF is not read-able. Attempting OCR...")
#         os.system('ocrmypdf "' + paper_path + '" "' + paper_path + '" --force-ocr')
#         paper_embed = (paper_path.replace(pdf_location + "/","")).replace(".pdf","")
#     embedding.load_n_process_document(paper_path)
#     vectorstore = embedding.create_vectorstore(paper=paper_embed)
#     return vectorstore

# def semantic_search(vectorstore,question,search_type,model_name):
#     engine = os.environ.get("EMBEDDING_ENGINE")
#     if engine == 'OpenAI':
#         llm = get_llm()
#         # embeddings = get_embedding_model()
#         # embeddings_filter = EmbeddingsFilter(embeddings=embeddings, similarity_threshold=0.76)

#     else:
#         raise KeyError("Currently unsupported chat model type!")

#     relevant_docs = RetrievalQA.from_chain_type(llm=llm,
#                                                  chain_type="stuff", 
#                                                  retriever=vectorstore.as_retriever(#search_type=search_type, 
#                                                                                     search_kwargs={#'score_threshold': 0.8, 
#                                                                                                 #   'fetch_k': 30,
#                                                                                                    'k': int(os.environ.get("N_CHUNKS"))}
#                                                                                                 ), 
#                                                                                                 return_source_documents=True
#                                                                                                    )
#     return relevant_docs
      



# # Helper function for printing docs



def ask_question(prompt,contents,identity):
    n_attempts = 0
    while n_attempts < 3:
        try:
            # Author bot answers
            if identity == "OPENAI":
               # configure_azure_support()
                # prompt = create_prompt(question)
                response_raw = openai.ChatCompletion.create(
                    model = "gpt-4-0125-preview",
                    #engine = "gpt-4-1106-preview",# used 1106 for extraction
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": contents},
                    ]
                    )
                response_text = response_raw.choices[0].message.content

            elif identity == "CLAUDE":

                body = json.dumps({
                    "prompt": "Human:" + prompt + contents + "Assistant:",
                    "max_tokens_to_sample": 1000,
                    "temperature": 0.0,
                    "top_p": 1.0,
                })
                response_raw = brt.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
                content_bytes = response_raw.get('body').read()
                response_text = json.loads(content_bytes)['completion']
            elif identity == "GOOGLE":
                response_raw = model.generate_content(prompt + contents)
                response_text = response_raw.text
            n_attempts = 999
        except:
            n_attempts += 1
            response_text = "NO DATA"
    # print("Response" + '\n' + response + '\n')
    # if not context == '':
    #     print("Context" + '\n' + context + '\n')
    print(response_text)
    return response_text


def force_format_ask(author,paper,question,q_num):
    n_attempts = 0
    n_retries = int(os.environ.get("N_RETRIES"))
    while n_attempts < n_retries: # Force a correctly formatted response.
        try:
            response = ask_question(author,paper,question,q_num,identity)
            if '%%' in response:
                data, context = response.split("%%")[:2]
            else:
                data, context = response.split("Context")[:2]
            n_attempts = n_retries + 1
        except:
                print("Bad Parsing...Trying again...")
                n_attempts += 1
    return response, data, context


# Dictionary of prompt types; numbers are the number of chunks sent to LLM


def format_bot(response,format,question):
    llm = get_llm()

    data_format = {'Quantitative': 'Return either a single value with any associated units. Or if multiple values are reported, return a list of all possible matching values found in the search results.', 
               'Qualitative': 'Return a comprehensive response of up to three sentences.', 
               'Categorical': 'Return a short phrase or single word only. Be as concise as possible. Do not explain or elaborate.',
               'Theme': 'Return either a single item or a list where each element is at most three words.',
               'Multiple-Choice': 'Return only the applicable choices from the list provided in the Query without elaboration.'}

    format_description = data_format[format]
    print("\n" + format_description + "\n")

   # first step in chain
    template_format = """
        You are a formatting and synthesis algorithm and have been given the following Responses and Contexts from several scientists about a paper, some of whom have not read the whole paper. 
        Your task is to provide a truthful answer to the question provided based on the Responses and Contexts from the scientists about their study according to the following Formatting Requirements.
        When answering, re-state the question as the answer and return text that complies with the formatting requirements along with the Context verbatim as provided by the scientists. If all responses say "NO DATA", return "NO DATA" only. Do not report any uncertainties.
        Tip: If something is unclear, you don't need to express that.
        Formatting Requirements: [{format_description}/Context] 
        Question: {question} 
        Responses: {response} 
        """
    prompt_format = PromptTemplate(

        input_variables=["response","format_description","question"],

        template=template_format)

    chain_format = LLMChain(llm = llm, prompt = prompt_format, output_key = "formatted_data", verbose = False)

# Combine the first and the second chain

    overall_chain = SequentialChain(chains=[#chain_author,
                                            chain_format                                                                      
                                            ], verbose=False, input_variables = ['response','format_description',"question"],
                                            output_variables= ["formatted_data"])



    out = overall_chain({"response":response, "format_description": format_description,"question": question})
    return out


#response = """Data: The unintended consequence of increased water consumption due to 
#the installation of water-efficient showerheads in households was caused by the rebound effect. This effect occurs when water-efficient technologies lead to a decrease in the cost of water use, which in turn leads to an increase in water consumption.%%Context: "The rebound effect occurs when water-efficient technologies lead to a decrease in the cost of water use, which in turn leads to an increase in water consumption. This effect has been observed in a number of studies on water-efficient technologies, including showerheads (Gleick, 2003; Kenway et al., 2008; 
#Lipchin et al., 2011)." (p. 87)%%"""