# Comparative RAG on Indian Legal Documents

A side-by-side implementation of five Retrieval-Augmented Generation (RAG) architectures, applied to the same corpus of Indian legal statutes: **BNS** (Bharatiya Nyaya Sanhita), **BNSS** (Bharatiya Nagarik Suraksha Sanhita), and **BSA** (Bharatiya Sakshya Adhiniyam).

The goal is to compare retrieval strategies, not just answer questions. All five implementations share the same chunking, embedding model, and LLM so that differences in output come from the retrieval method itself.

## RAG variants implemented

| Variant | Retrieval method |
|---|---|
| Vector RAG | Dense embedding similarity search (FAISS) |
| Keyword RAG | BM25 sparse keyword matching |
| Hybrid RAG | Vector + BM25 results merged and deduplicated |
| Tree RAG | Routes query to the correct statute (BNS / BNSS / BSA) before retrieving |
| Graph RAG | BM25 retrieval expanded with neighboring chunks |

## Shared configuration

- **Chunking:** `RecursiveCharacterTextSplitter`, chunk size 1000, overlap 200
- **Embedding model:** `all-MiniLM-L6-v2` (Sentence-Transformers)
- **LLM:** `phi3:mini` via Ollama (local inference)
- **Context window:** k = 5 chunks per query

## Project structure

```
simple-rag/
├── README.md
├── requirements.txt
├── pdfs/                  # Source statutes (not included, see below)
│   ├── bns.pdf
│   ├── bnss.pdf
│   └── bsa.pdf
├── src/
│   ├── vector_rag.py
│   ├── keyword_rag.py
│   ├── hybrid_rag.py
│   ├── tree_rag.py
│   └── graph_rag.py
└── samples/                # Example query/answer screenshots
    ├── vector_rag_sample.png
    ├── keyword_rag_sample.png
    ├── hybrid_rag_sample.png
    ├── tree_rag_sample.png
    └── graph_rag_sample.png
```

## Setup

1. Install [Ollama](https://ollama.com) and pull the model:
   ```
   ollama pull phi3:mini
   ```
2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Place `bns.pdf`, `bnss.pdf`, and `bsa.pdf` in the `pdfs/` directory.

## Usage

Run any variant from the project root:

```
python src/vector_rag.py
```

Type a question at the `Ask:` prompt. Type `exit` to quit.

## Sample output

Each `samples/` screenshot shows the same query, *"What is the punishment for organized crime under BNS?"* run against all five variants, illustrating how retrieval strategy affects the retrieved context and final answer.

## When to use which

Each variant trades off differently on speed, setup cost, and retrieval quality depending on the query type. A detailed write-up with theory and examples is here: <>

## Further reading

A detailed write-up covering how each RAG variant works, their tradeoffs, and when to use which: <>

## Coming in the next update

A quantitative comparison across all five variants using a fixed 50-question test set, with results visualized to make retrieval quality differences easier to compare at a glance.
