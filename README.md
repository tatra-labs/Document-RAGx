# Document-RAGx

## Purpose 

This project aims to provide the end-to-end interface for RAG from documents. 

## Strcuture 

### I structured AI Engine like below.  

1. Data Pipeline 

    - Document Parsing (various types) & Loading 

2. Transforming into Knowledge Base for Retrieval 

    - (Semantic) Splitters 
    - Knowledge Base Architecture 
    - Embedding (Available embedding adapter training)

3. Generation 

    - Re-ranking (dual encoder + cross encoder) 

### Front-End  

1. Document Upload 

2. Chat interface 

    - chainlit 

