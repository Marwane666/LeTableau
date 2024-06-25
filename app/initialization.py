import os
import logging
import sys
import nest_asyncio
from dotenv import load_dotenv
from llama_index.core import SummaryIndex, Settings
from llama_index.core import SimpleDirectoryReader
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core import StorageContext, load_index_from_storage
import openai

nest_asyncio.apply()
load_dotenv()
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

def initialize_and_persist_vectorstore(pdf_path, persist_dir):
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        7
    
    openai.api_key = api_key

    if not os.path.exists(persist_dir):
        os.makedirs(persist_dir)

    if os.listdir(persist_dir):
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        summary_index = load_index_from_storage(storage_context)
    else:
        reader = SimpleDirectoryReader(input_files=[pdf_path])
        documents = reader.load_data()

        Settings.llm = OpenAI(max_tokens=3000)
        Settings.embed_model = OpenAIEmbedding(
            model_name="text-embedding-3-large", 
            api_key=api_key
        )

        summary_index = SummaryIndex.from_documents(documents)
        summary_index.storage_context.persist(persist_dir=persist_dir)

    Settings.llm = OpenAI(max_tokens=3000, model="gpt-4o")
    chat_engine = summary_index.as_chat_engine(chat_mode="simple", max_tokens=3000)

    return chat_engine
