
import sys
from pathlib import Path

# Add the project root so Python can find the rag folder.
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

# Import the reusable RAG function.
from rag.railway_rag import ask_railway_question


def railway_faq_agent(question):
    # Send the question to the RAG system and return its answer.
    return ask_railway_question(question)


# Run the FAQ chatbot continuously.
if __name__ == "__main__":

    print("IRCTC Railway FAQ Agent")
    print("Type 'exit' to stop.\n")

    while True:
        question = input("Ask a railway question: ").strip()

        # Stop the chatbot when the user types exit.
        if question.lower() == "exit":
            print("Goodbye!")
            break

        # Avoid processing empty questions.
        if not question:
            print("Please enter a question.\n")
            continue

        try:
            answer = railway_faq_agent(question)
            print("\nRailway FAQ Agent:")
            print(answer)
            print()

        except Exception as error:
            print("Error:", error)
