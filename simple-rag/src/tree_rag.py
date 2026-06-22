# Load PDF files
from langchain_community.document_loaders import PyPDFLoader
# Split documents into chunks
from langchain_text_splitters import RecursiveCharacterTextSplitter
# BM25 keyword search
from rank_bm25 import BM25Okapi
# Local LLM
from langchain_community.llms import Ollama
import re

# Load PDFs
bns_docs = PyPDFLoader("pdfs/bns.pdf").load()
bnss_docs = PyPDFLoader("pdfs/bnss.pdf").load()
bsa_docs = PyPDFLoader("pdfs/bsa.pdf").load()

# Splitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

# Create chunks
bns_chunks = splitter.split_documents(bns_docs)
bnss_chunks = splitter.split_documents(bnss_docs)
bsa_chunks = splitter.split_documents(bsa_docs)

# Build BNS BM25
bns_texts = [doc.page_content for doc in bns_chunks]
bns_tokens = [re.findall(r'\b\w+\b', text.lower()) for text in bns_texts]
bns_bm25 = BM25Okapi(bns_tokens)

# Build BNSS BM25
bnss_texts = [doc.page_content for doc in bnss_chunks]
bnss_tokens = [re.findall(r'\b\w+\b', text.lower()) for text in bnss_texts]
bnss_bm25 = BM25Okapi(bnss_tokens)

# Build BSA BM25
bsa_texts = [doc.page_content for doc in bsa_chunks]
bsa_tokens = [re.findall(r'\b\w+\b', text.lower()) for text in bsa_texts]
bsa_bm25 = BM25Okapi(bsa_tokens)

# Load LLM
llm = Ollama(model="phi3:mini")

print("Tree RAG ready!")

# Chat loop
while True:
    query = input("\nAsk: ")

    if query.lower() == "exit":
        break

    query_tokens = re.findall(r'\b\w+\b', query.lower())
    query_upper = query.upper()

    # Explicit routing if user mentions document name
    if "BNS" in query_upper:
        selected = "BNS"
    elif "BNSS" in query_upper:
        selected = "BNSS"
    elif "BSA" in query_upper:
        selected = "BSA"
    else:
        bns_score = max(bns_bm25.get_scores(query_tokens))
        bnss_score = max(bnss_bm25.get_scores(query_tokens))
        bsa_score = max(bsa_bm25.get_scores(query_tokens))

        scores = {
            "BNS": bns_score,
            "BNSS": bnss_score,
            "BSA": bsa_score
        }

        selected = max(scores, key=scores.get)

    print("Selected Document:", selected)

    if selected == "BNS":
        chunks = bns_chunks
        bm25 = bns_bm25
    elif selected == "BNSS":
        chunks = bnss_chunks
        bm25 = bnss_bm25
    else:
        chunks = bsa_chunks
        bm25 = bsa_bm25

    chunk_scores = bm25.get_scores(query_tokens)

    top_indices = sorted(
        range(len(chunk_scores)),
        key=lambda i: chunk_scores[i],
        reverse=True
    )[:5]

    results = [chunks[i] for i in top_indices]

    context = "\n\n".join(
        [doc.page_content for doc in results]
    )

    prompt = f"""
Answer ONLY from the provided legal context.
If the answer is not present, say:
'Information not found in provided documents.'

Document Selected:
{selected}

Context:
{context}

Question:
{query}
"""

    response = llm.invoke(prompt)

    print("\nAnswer:\n")
    print(response)