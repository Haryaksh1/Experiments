from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings
from langchain_community.llms import Ollama

# Embedding wrapper
class LocalEmbeddings(Embeddings):
    def __init__(self):
        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    def embed_documents(self, texts):
        return self.model.encode(texts).tolist()

    def embed_query(self, text):
        return self.model.encode([text])[0].tolist()

# Load PDFs
docs = []

pdf_files = [
    "pdfs/bns.pdf",
    "pdfs/bnss.pdf",
    "pdfs/bsa.pdf"
]

for pdf in pdf_files:
    loader = PyPDFLoader(pdf)
    docs.extend(loader.load())

# Split into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = splitter.split_documents(docs)

# Create embeddings
embedding = LocalEmbeddings()

# Store in FAISS
vectorstore = FAISS.from_documents(
    chunks,
    embedding
)

# Load local LLM
llm = Ollama(model="phi3:mini")

print("Vector RAG ready!")

# Chat loop
while True:
    query = input("\nAsk: ")

    if query.lower() == "exit":
        break

    results = vectorstore.similarity_search(
        query,
        k=5
    )

    context = "\n\n".join(
        [doc.page_content for doc in results]
    )

    prompt = f"""
Answer ONLY using the context below.

Context:
{context}

Question:
{query}
"""

    response = llm.invoke(prompt)

    print("\nAnswer:\n")
    print(response)