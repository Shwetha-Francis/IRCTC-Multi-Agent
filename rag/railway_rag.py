import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from the project root.
PROJECT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_DIR / ".env")

# Point to the ChromaDB database used by your existing rail_chatbot project.
OLD_PROJECT_DIR = Path(r"C:\Users\dell\rail_chatbot")
CHROMA_PATH = OLD_PROJECT_DIR / "chroma_db"

# Connect to the existing collection without re-ingesting the PDFs.
client = chromadb.PersistentClient(path=str(CHROMA_PATH))
collection = client.get_or_create_collection(name="irctc_documents")

# Load the embedding model and Groq client once when this module is imported.
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
groq_client = Groq()


def ask_railway_question(question):
    """Retrieve relevant railway document chunks and generate an answer."""

    # Convert the user's question into an embedding for ChromaDB search.
    question_embedding = model.encode(question)

    # Retrieve the five most relevant document chunks.
    results = collection.query(
        query_embeddings=[question_embedding.tolist()],
        n_results=5
    )
    
    # Debug: display the retrieved document chunks
    print("\n--- Retrieved Documents ---")

    for i, document in enumerate(results["documents"][0]):
        print(f"\nDocument {i + 1}:")
        print(document[:500])  # Display first 500 characters

        print("Metadata:", results["metadatas"][0][i])
        print("Distance:", results["distances"][0][i])

    documents = results["documents"][0]
    metadata = results["metadatas"][0]

    # Build context that includes the source document names.
    context_parts = []

    for document, meta in zip(documents, metadata):
        source = meta.get("source", "Unknown document")
        context_parts.append(f"Source: {source}\nInformation:\n{document}")

    context = "\n\n---\n\n".join(context_parts)

    # Instruct the LLM to answer only from retrieved document information.
    prompt = f"""
You are an IRCTC railway information assistant.

Answer the user's question using only the retrieved information.
Do not invent railway rules or details.
If the information is missing, say:
"I don't have enough information in my documents to answer that."

Retrieved information:
{context}

User question:
{question}

Give a short, direct answer.
"""

    # Ask Groq to generate the answer.
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
