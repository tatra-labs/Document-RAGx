import os 
import re
from uuid import uuid4

from openai import OpenAI 
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document 

import instructor 
from pydantic import BaseModel, Field 
from typing import List

from preprocess.snapshot import * 
from engine.prompts import * 
from engine.retriever import * 
import settings 

class KeywordsSchema(BaseModel):
    keywords: List[str] = Field(description="Extracted Keywords")

def display_file_structure(data_dir, indent=0):
    """Recursively display the file structure of the given directory."""
    try:
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            
            if os.path.isdir(item_path):
                print('    ' * indent + f'📁 {item}')
                display_file_structure(item_path, indent + 1)
            else:
                print('    ' * indent + f'📄 {item}')
    except PermissionError:
        print('    ' * indent + '⚠️ [Access Denied]')

def load_documents(snapshot, mode="page"):
    """Load documents from the specified directory."""
    doc_elements = []
    for file_path in snapshot:
        try:
            loader = PyMuPDF4LLMLoader(
                file_path, 
                mode="page",) 
            data = loader.load() 
            if data:
                doc_elements.append(data)
                print(f"Loaded {len(data)} pages from {file_path}")
            else:
                print(f"No data found in {file_path}")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    return doc_elements

def sanitize_documents(
        documents, 
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    ):
    """A simple custom splitter that splits pages into chunks."""
    # New Document structure 
    # Document(
    #     metadata={
    #         "file_path": "file_path",  # Replace with actual source path
    #         "page_number": 1,  # Page number or other relevant metadata
    #         "keywords": ["keyword1", "keyword2"],  # Example keywords
    #     },
    #     page_content="This is the content of the document page."
    # )

    def extract_filename_and_parent(path):
        # Normalize the path for consistent separators
        path = os.path.normpath(path)
        
        # Extract file name without extension
        filename = os.path.splitext(os.path.basename(path))[0]
        
        # Extract the parent directory name
        parent_dir = os.path.basename(os.path.dirname(path))
        
        return [filename, parent_dir]

    def refine_keywords(original_keywords: str):
        tokens = re.split(r'[-_.,/:\s]+', original_keywords) 
        return " ".join(tokens)
    
    new_documents = []
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "\t"],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    for document in documents:
        for page in document:
            file_path = page.metadata.get("source", "unknown_source") 
            page_number = page.metadata.get("page", "unknown_page")
            page_content = page.page_content.strip()
            
            chunks = splitter.split_text(page_content)
            for _, chunk in enumerate(chunks):
                keywords = extract_keywords(chunk)

                # Add category detail to keywords, e.g. 'CF-700 Remote Control', 'CF-700_4L3964_CE'
                category_detail = extract_filename_and_parent(file_path) 
                keywords.extend(category_detail)
                keywords = set(keywords)

                metadata = {
                    "document_id": str(uuid4()),
                    "file_path": file_path,
                    "page_number": page_number,
                    "keywords": refine_keywords(" ".join(list(keywords)))
                }
                new_documents.append(Document(
                    page_content="This is the content that belongs to " + " ".join(category_detail) + chunk, 
                    metadata=metadata))

    return new_documents

def extract_keywords(content: str, model=settings.LLM_MODEL):
    from openai.types.chat import ChatCompletionMessageParam

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": EXTRACT_KEYWORDS_SYSTEM_PROMPT},
        {"role": "user", "content": content}
    ]
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
        response_model=KeywordsSchema,
    )

    return response.keywords

def preprocess(data_dir, mode):
    print(f"Preprocessing documents in {data_dir} using naive strategy now...")

    # Display the file structure of the data directory 
    display_file_structure(data_dir)

    # Load pages from the documents 
    if mode == "new":
        snapshot = take_snapshot(root_dir=data_dir)
        save_snapshot(snapshot=snapshot)
        initial_documents = load_documents(snapshot)
    elif mode == "add":
        new_snapshot = take_snapshot(root_dir=data_dir) 
        old_snapshot = load_snapshot()
        changed_snapshot = find_new_files(old_snapshot, new_snapshot) 
        initial_documents = load_documents(changed_snapshot)

    if not initial_documents:
        print("No documents found to preprocess.")
        return

    print(len(initial_documents), "documents loaded for preprocessing.") 
    
    # Split the pages into chunks 
    chunks = sanitize_documents(initial_documents)

    print(len(chunks), "chunks created from the documents.")

    # Vector Store  
    ## Persistence
    uuids = [str(uuid4()) for _ in range(len(chunks))]
    vector_store.add_documents(
        documents=chunks,
        ids=uuids
    )
    
    if mode == "add":
        save_snapshot(new_snapshot)