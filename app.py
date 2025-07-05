import chainlit as cl 
import logging 

from engine.assistant import add_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s") 


async def create_pdf_element(file_path, page_number):
    file_name = file_path.split("/")[-1]  # Extract the file name from the path
    pdf_element = cl.Pdf(
        name=file_name,
        path=file_path,
        display="inline",  # Options: 'inline', 'side', 'page'
        page=page_number
    )
    return pdf_element

@cl.on_chat_start 
async def on_chat_start():
    """Initialize the chat session.""" 
    cl.user_session.set(
        "messages",
        [
            {
                "role": "system",
                "content": "You are a helpful assistant that answers questions based on the provided documents.",
            }
        ],
    )
    await cl.Message(
        author="assistant", 
        content="Hi, how can I help you today?"
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Continue the chat session, return AI Message."""
    human_message = message.content 
    messages = cl.user_session.get("messages", [
            {
                "role": "system",
                "content": "You are a helpful assistant that answers questions based on the provided documents.",
            }
        ]) 
    messages.append(
        {
            "role": "user",
            "content": human_message,
        }
    )


    ### TODO: Get the response from the pipeline 


    ai_message, file_path, page_number = add_message(human_message)
    pdf_element = await create_pdf_element(file_path, page_number)

    messages.append(
        {
            "role": "assistant",
            "content": ai_message,
        }
    )
    cl.user_session.set("messages", messages)

    response_msg = cl.Message(content=ai_message, elements=[pdf_element])
    
    await response_msg.send()

