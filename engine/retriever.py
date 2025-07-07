import re
from collections import defaultdict
from datasketch import MinHash, MinHashLSHForest
from openai import OpenAI
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma 
from langchain_core.documents import Document

import chromadb 
from chromadb.config import Settings

import instructor 
from pydantic import BaseModel, Field 
from typing import List

from engine.prompts import * 
import settings

# Embedding model 
embedding_model = HuggingFaceEmbeddings(
    model_name=settings.EMBEDDING_MODEL,
    model_kwargs={'device': 'cpu'}
)

# Vector store
persistent_client = chromadb.PersistentClient(
    path=str(settings.INDICES), 
    settings=Settings(allow_reset=True)
)
collection = persistent_client.get_or_create_collection(
    name=str(settings.COLLECTION_NAME),
    metadata={
        "hnsw:space": "cosine"
    }
)
vector_store = Chroma(
    client=persistent_client,
    collection_name=collection.name,
    embedding_function=embedding_model
)

# Raw documents 
raw_docs = vector_store.get(include=["documents", "metadatas"])
raw_documents = [
    Document(page_content=doc, metadata=meta)
    for doc, meta in zip(raw_docs["documents"], raw_docs["metadatas"])
]

# Keywords list 
preprocess_func = lambda x: x.split() 
keywords_list = [
    preprocess_func(doc.metadata.get("keywords", [])) 
    for doc in raw_documents
]

# For Keyword Search, set up forest  
forest = MinHashLSHForest(num_perm=int(settings.NUM_PERM))
doc_signatures = [] 
for i, keywords in enumerate(keywords_list):
    m = MinHash(num_perm=int(settings.NUM_PERM)) 
    for kw in keywords:
        m.update(kw.encode('utf8')) 
    doc_signatures.append(m) 
    forest.add(i, m) 

forest.index() 

def extract_keywords_from_query(query: str, model=settings.LLM_MODEL):
    from openai.types.chat import ChatCompletionMessageParam

    class KeywordsSchema(BaseModel):
        keywords: List[str] = Field(description="Extracted Keywords")   

    def refine_keywords(original_keywords: str):
        tokens = re.split(r'[-_.,/:\s]+', original_keywords) 
        return tokens

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": EXTRACT_KEYWORDS_FROM_QUERY_SYSTEM_PROMPT},
        {"role": "user", "content": query}
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
    
    return refine_keywords(" ".join(response.keywords))

def sparse_retrieve(keywords_from_query):
    k = int(settings.k)
    m_query = MinHash(num_perm=int(settings.NUM_PERM)) 
    for kw in keywords_from_query:
        m_query.update(kw.encode('utf8')) 
    
    candidates = forest.query(m_query, k*2)

    scores = []
    for idx in candidates:
        score = m_query.jaccard(doc_signatures[idx])
        scores.append((raw_documents[idx], score)) 

    topk = sorted(scores, key=lambda x: x[1], reverse=True)[:k]
    
    return topk

# class KeywordRetriever(BaseRetriever):
#     """Self-defined keyword retriever"""
#     documents: List[Document]
#     k: int

#     def _get_relevant_documents(
#         self, 
#         query: str,
#         *,
#         run_manager: CallbackManagerForRetrieverRun
#     ):
#         keywords_from_query = extract_keywords_from_query(query) 
#         scores = bm25_vectorizer.get_scores(keywords_from_query)
#         top_idxs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:self.k]
#         retrieved_documents = [(raw_documents[idx], scores[idx]) for idx in top_idxs] 
#         return retrieved_documents

# sparse_retriever = KeywordRetriever(documents=raw_documents, k=int(settings.k))

def naive_retrieve(human_message: str):
    k = int(settings.k)
    weights = [0.1, 0.9]
    
    try:
        keywords_from_query = extract_keywords_from_query(human_message) 
    except Exception as e:
        print("Keywords extraction from query failed...")
        keywords_from_query = [] 

    dense_retriever_result = vector_store.similarity_search_with_score(human_message, k=k)

    if keywords_from_query:
        sparse_retriever_result = sparse_retrieve(keywords_from_query)
    else:
        return dense_retriever_result

    score_dict = defaultdict(float)
    retrieved_documents = {}
    for lst in sparse_retriever_result:
        document, score = lst 
        id = document.metadata["document_id"] 
        score_dict[id] += score * weights[0]
        retrieved_documents[id] = document 
    
    for lst in dense_retriever_result:
        document, score = lst 
        id = document.metadata["document_id"] 
        score_dict[id] += score * weights[1]
        retrieved_documents[id] = document 

    combined = [(retrieved_documents[id], score) for id, score in score_dict.items()]
    sorted_combined = sorted(combined, key=lambda x: x[1], reverse=True)

    return sorted_combined