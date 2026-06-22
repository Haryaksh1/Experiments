from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi
from langchain_community.llms import Ollama
import re

docs = []
pdf_files = [
    "pdfs/bns.pdf",
    "pdfs/bnss.pdf",
    "pdfs/bsa.pdf"
]

for pdf in pdf_files:
    loader = PyPDFLoader(pdf)
    docs.extend(loader.load())

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = splitter.split_documents(docs)

chunk_texts = [doc.page_content for doc in chunks]
tokenized_chunks = [re.findall(r'\b\w+\b', text.lower()) for text in chunk_texts]
bm25 = BM25Okapi(tokenized_chunks)

graph = {}
for i in range(len(chunks)):
    neighbors = []
    if i - 1 >= 0:
        neighbors.append(i - 1)
    if i + 1 < len(chunks):
        neighbors.append(i + 1)
    graph[i] = neighbors

llm = Ollama(model="phi3:mini")
print("Graph RAG ready!")

while True:
    query = input("\nAsk: ")
    if query.lower() == "exit":
        break

    query_tokens = re.findall(r'\b\w+\b', query.lower())
    scores = bm25.get_scores(query_tokens)

    top_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:3]

    retrieved_indices = []
    for idx in top_indices:
        retrieved_indices.append(idx)
        for neighbor in graph[idx]:
            retrieved_indices.append(neighbor)

    unique_indices = []
    seen = set()
    for idx in retrieved_indices:
        if idx not in seen:
            seen.add(idx)
            unique_indices.append(idx)

    unique_indices = unique_indices[:5]
    # graph expansion may pull in more distinct source regions than k=5 implies

    context = "\n\n---\n\n".join(
        [f"[Chunk {i}]\n{chunks[i].page_content}" for i in unique_indices]
    )

    prompt = f"""You are a legal assistant for Indian law (BNS, BNSS, BSA).
Answer the question using the context below.
Mention section numbers and penalties when available.
If the answer is truly not in the context, say 'Information not found in provided documents.'

Context:
{context}

Question: {query}

Answer:"""

    response = llm.invoke(prompt)
    print("\nAnswer:\n")
    print(response)