# Load PDF files
from langchain_community.document_loaders import PyPDFLoader
# Split documents into chunks
from langchain_text_splitters import RecursiveCharacterTextSplitter
# BM25 keyword search
from rank_bm25 import BM25Okapi
import re
# Embedding model
from sentence_transformers import SentenceTransformer
# Vector database
from langchain_community.vectorstores import FAISS
# Embedding base class
from langchain.embeddings.base import Embeddings
# Local LLM through Ollama
from langchain_community.llms import Ollama

# Embedding wrapper
class LocalEmbeddings(Embeddings):
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
    def embed_documents(self, texts):
        return self.model.encode(texts).tolist()
    def embed_query(self, text):
        return self.model.encode([text])[0].tolist()

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

# Build BM25 index
chunk_texts = [doc.page_content for doc in chunks]
tokenized_chunks = [re.findall(r'\b\w+\b', text.lower()) for text in chunk_texts]
bm25 = BM25Okapi(tokenized_chunks)

# Build FAISS index
embedding = LocalEmbeddings()
vectorstore = FAISS.from_documents(
    chunks,
    embedding
)

# Load local LLM
llm = Ollama(model="phi3:mini")

print("Hybrid RAG ready!")

# Chat loop
while True:
    query = input("\nAsk: ")

    if query.lower() == "exit":
        break
    # Vector retrieval
    vector_results = vectorstore.similarity_search(
        query,
        k=5
    )

    # BM25 retrieval
    query_tokens = re.findall(r'\b\w+\b', query.lower())
    scores = bm25.get_scores(query_tokens)
    top_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:5]

    keyword_results = [chunks[i] for i in top_indices]

    # Merge results and remove duplicates
    combined_results = []
    seen = set()

    for doc in vector_results + keyword_results:
        text = doc.page_content
        if text not in seen:
            seen.add(text)
            combined_results.append(doc)

    # Build context
    context = "\n\n".join(
        [doc.page_content for doc in combined_results[:5]]
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