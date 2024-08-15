import boto3
import json
import os
import requests
import base64
from groq import Groq,AsyncGroq
from openai import AzureOpenAI,OpenAI,AsyncAzureOpenAI,AsyncOpenAI
#session = boto3.Session(profile_name='bedrockprofile')
#  from dotenv import load_dotenv
import os
# import llama_index.llms.azure_openai 
# import llama_index.embeddings.azure_openai 
# from llama_index.core import StorageContext, VectorStoreIndex, SimpleDirectoryReader, load_index_from_storage
# from llama_index.core import Settings
# initialize settings (set chunk size)

# def ask_AI_doc(prompt,docs,AI_to_use=None):
#     llm = llama_index.llms.azure_openai.AzureOpenAI(azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
#                         api_key=os.environ.get("AZURE_OPENAI_KEY"),
#                         api_version=os.environ.get("AZURE_OPENAI_VERSION"),
#                         azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT"))
#     embed_model = llama_index.embeddings.azure_openai.AzureOpenAIEmbedding(azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
#                         model="text-embedding-ada-002",
#                         api_key=os.environ.get("AZURE_OPENAI_KEY"),
#                         api_version=os.environ.get("AZURE_OPENAI_VERSION"),
#                         azure_deployment=os.environ.get("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"))



#     Settings.llm = llm
#     Settings.embed_model = embed_model
#     # set context window
#     Settings.context_window = 8096
#     # set number of output tokens
#     # Settings.num_output = 256

#     def get_index(directory):
#         index = None
#         documents = SimpleDirectoryReader(directory).load_data()
#         index_name = directory + '_index'
#         if not os.path.exists(index_name):
#             print("building index", index_name)
#             index = VectorStoreIndex.from_documents(documents, show_progress=True)
#             index.storage_context.persist(persist_dir=index_name)
#         else:
#             index = load_index_from_storage(
#                 StorageContext.from_defaults(persist_dir=index_name)
#             )

#         return index
#     documents_index = get_index(docs)
#     documents_engine = documents_index.as_query_engine()
#     output = documents_engine.query(prompt)
#     return output

brt = boto3.client(service_name='bedrock-runtime')
def ask_claude(prompt, max_tokens = 2000):
    newline = "\n\n"
    body = json.dumps({
        "max_tokens": max_tokens,
        "messages": [{"role": "user",
                    "content": f"{newline}Human: {prompt}{newline}Assistant:"}],
        "anthropic_version": "bedrock-2023-05-31"
    })
 
    modelId = 'anthropic.claude-3-sonnet-20240229-v1:0'
    accept = 'application/json'
    contentType = 'application/json'
    
    response = brt.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
    
    response_body = json.loads(response.get("body").read())
    out = response_body.get("content")[0]["text"]
    print(out)
    return out


# ------------------ Create functions ------------------ #
async def ask_AI_async(prompt,AI_to_use):
    n_attempts = 0
    
    if 'claude' in AI_to_use:
        output = ask_claude(prompt)
        return output
    if 'azure' in AI_to_use:
        client = AsyncAzureOpenAI(azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
                     api_key=os.environ.get("AZURE_OPENAI_KEY"),
                     api_version=os.environ.get("AZURE_OPENAI_VERSION"),
                     azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT"))
    elif 'modelbot' in AI_to_use:
        client = AsyncAzureOpenAI(
            azure_endpoint = "https://modelbot.openai.azure.com/", 
            api_key='e9038573691d40cd9b1b17d8f2d6ebc6',  
            api_version="2024-02-15-preview"
            )

    elif 'mixtral' in AI_to_use or 'llama' in AI_to_use:
        client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
    else:
        client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    if 'gpt-4-turbo' in AI_to_use:
        model = 'gpt-4-0125-preview'
    elif 'modelbot' in AI_to_use:
        model="ModelBot-gpt4"
    elif 'mixtral' in AI_to_use:
        model = "mixtral-8x7b-32768"
    elif 'llama' in AI_to_use:
        model = 'llama2-70b-4096'
    else:
        model = 'gpt-3.5-turbo-0125'
    while n_attempts < 5:
        try:
            completion = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
                )
            output = completion.choices[0].message.content
            n_attempts = 999
        except:
            n_attempts += 1
    
    return(output)

def ask_AI(prompt,AI_to_use):
    n_attempts = 0
    if 'claude' in AI_to_use:
        output = ask_claude(prompt)
        return output
    if 'azure' in AI_to_use:
        client = AzureOpenAI(azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
                     api_key=os.environ.get("AZURE_OPENAI_KEY"),
                     api_version=os.environ.get("AZURE_OPENAI_VERSION"),
                     azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT"))
    elif 'modelbot' in AI_to_use:
        client = AzureOpenAI(
            azure_endpoint = "https://modelbot.openai.azure.com/", 
            api_key='e9038573691d40cd9b1b17d8f2d6ebc6',  
            api_version="2024-02-15-preview"
            )

    elif 'mixtral' in AI_to_use or 'llama' in AI_to_use:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    else:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    if 'gpt-4-turbo' in AI_to_use:
        model = 'gpt-4-0125-preview'
    elif 'modelbot' in AI_to_use:
        model="ModelBot-gpt4"
    elif 'mixtral' in AI_to_use:
        model = "mixtral-8x7b-32768"
    elif 'llama' in AI_to_use:
        model = 'llama2-70b-4096'
    else:
        model = 'gpt-3.5-turbo-0125'
    while n_attempts < 5:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
                )
            output = completion.choices[0].message.content
            n_attempts = 999
        except:
            n_attempts += 1
    
    return(output)

 
# Configuration
async def ask_AI_vision(prompt, image_path, AI_to_use = 'azure-gpt-4-turbo'):
        # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
        
    if 'azure' in AI_to_use:
        GPT4V_KEY = os.getenv("AZURE_OPENAI_KEY")
    else:
        print("Unsupported AI, use AI_to_use = 'azure-gpt-4-turbo'")
        raise(KeyError)
    encoded_image = encode_image(image_path)
    headers = {
        "Content-Type": "application/json",
        "api-key": GPT4V_KEY,
    }
    
    # Payload for the request
    payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": prompt
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{encoded_image}"
            }
            }
        ]
        }
    ],
    "max_tokens": 800
    }
    
    GPT4V_ENDPOINT = "https://od232800-openai-gpt4.openai.azure.com/openai/deployments/firstcontact-vision/chat/completions?api-version=2023-07-01-preview"
    
    # Send request
    try:
        response = requests.post(GPT4V_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.RequestException as e:
        raise SystemExit(f"Failed to make the request. Error: {e}")
    
    # Handle the response as needed (e.g., print or process)
    #print(response.json())
    output = response.json()['choices'][0]['message']['content']
    return(output)





