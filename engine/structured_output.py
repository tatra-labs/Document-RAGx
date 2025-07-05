import instructor 
from openai import OpenAI 
from pydantic import BaseModel 
import json 
import settings 

def get_structured_output(messages, schema: type[BaseModel], model=settings.LLM_MODEL):
    client = instructor.from_openai(
        OpenAI(
            base_url=str(settings.INSTRUCTOR_BASE_URL),
            api_key=str(settings.INSTRUCTOR_API_KEY),  # required, but unused
        ),
        mode=instructor.Mode.JSON,
    )
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_model=schema,
    )
    
    return json.loads(response.model_dump_json())

