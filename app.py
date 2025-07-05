import chainlit as cl 
import logging 

from engine.assistant import add_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s") 

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


    ai_message = add_message(human_message)

    messages.append(
        {
            "role": "assistant",
            "content": ai_message,
        }
    )
    cl.user_session.set("messages", messages)

    response_msg = cl.Message(content=ai_message)
    
    await response_msg.send()

