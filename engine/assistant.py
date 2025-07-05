from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

from engine.retriever import *
from engine.prompts import ANSWER_GENERATION_SYSTEM_PROMPT_TEMPLATE
import settings 

llm = ChatOllama(model=str(settings.LLM_MODEL), base_url=str(settings.LLM_PROVIDER))


def add_message(human_message: str):
    # Extracting keyword 
    result = naive_retrieve(human_message)
    main_context = result[0][0].page_content
    sub_context = result[1][0].page_content 

    file_path = result[0][0].metadata["file_path"]
    page_number = result[0][0].metadata["page_number"]

    try: 
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", ANSWER_GENERATION_SYSTEM_PROMPT_TEMPLATE.format(context=main_context + '\n\n' + sub_context)),
                MessagesPlaceholder("human_message")
            ]
        )

        qa_chain = qa_prompt | llm
        response = qa_chain.invoke({"human_message": [HumanMessage(content=human_message)]})
    except:
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", ANSWER_GENERATION_SYSTEM_PROMPT_TEMPLATE.format(context=main_context)),
                MessagesPlaceholder("human_message")
            ]
        )

        qa_chain = qa_prompt | llm
        response = qa_chain.invoke({"human_message": [HumanMessage(content=human_message)]})
    

    return [response.content, file_path, page_number]