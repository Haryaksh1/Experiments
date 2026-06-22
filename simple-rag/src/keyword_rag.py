# Load PDF files
from langchain_community.document_loaders import PyPDFLoader
# Split documents into chunks
from langchain_text_splitters import RecursiveCharacterTextSplitter
# BM25 keyword search
from rank_bm25 import BM25Okapi
import re
# Local LLM through Ollama
from langchain_community.llms import Ollama

# Store all PDF pages
docs = []

# PDF paths
pdf_files = [
    "pdfs/bns.pdf",
    "pdfs/bnss.pdf",
    "pdfs/bsa.pdf"
]

# Load PDFs
for pdf in pdf_files:
    loader = PyPDFLoader(pdf)
    docs.extend(loader.load())

# Split into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = splitter.split_documents(docs)

# Convert chunks into plain text
chunk_texts = [doc.page_content for doc in chunks]

# Tokenize chunks for BM25
tokenized_chunks = [re.findall(r'\b\w+\b', text.lower()) for text in chunk_texts]

# Build BM25 index
bm25 = BM25Okapi(tokenized_chunks)

# Load local LLM
llm = Ollama(model="phi3:mini")

print("Keyword RAG ready!")

# Chat loop
while True:
    query = input("\nAsk: ")

    if query.lower() == "exit":
        break

    # Tokenize query
    query_tokens = re.findall(r'\b\w+\b', query.lower())

    # Score all chunks
    scores = bm25.get_scores(query_tokens)

    # Get top 5 chunks
    top_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:5]

    # Retrieve chunks
    results = [chunks[i] for i in top_indices]

    # Build context
    context = "\n\n".join(
        [doc.page_content for doc in results]
    )

    # Prompt
    prompt = f"""
Answer ONLY from the provided legal context.
If the answer is not present, say:
'Information not found in provided documents.'

Context:
{context}

Question:
{query}
"""

    # Generate answer
    response = llm.invoke(prompt)

    print("\nAnswer:\n")
    print(response)