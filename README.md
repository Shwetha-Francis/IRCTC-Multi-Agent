# IRCTC Multi-Agent System

An AI-powered railway assistance application built using **LangChain, LangGraph, Groq LLM, and Streamlit**. The project uses multiple specialized agents to handle different railway-related tasks through a single conversational interface.

## Project Overview

The IRCTC Multi-Agent System is designed to simulate a railway assistance platform where users can search for trains, collect ticket booking details, book food, manage user profiles, track trains, and ask railway-related questions.

Instead of handling every request through one large program, the application uses multiple specialized agents. LangGraph manages the workflow and routes user requests to the appropriate agent.

**Note:** This is an educational simulation project. Ticket booking and related transactions are not connected to the official IRCTC booking system.

## Key Features

The application consists of six specialized agents:

1. **Train Search Agent**
   - Searches for railway stations using station names or codes.
   - Searches for trains based on journey details.
   - Handles ambiguous station selections.

2. **Ticket Booking Agent**
   - Collects passenger and journey details.
   - Handles simulated ticket booking information.
   - Prepares booking details for the booking workflow.

3. **Food Booking Agent**
   - Collects food preferences and order details.
   - Supports simulated food ordering during a train journey.

4. **Profile and Account Agent**
   - Supports user registration and login.
   - Stores user account information in SQLite.
   - Maintains booking history.

5. **Railway FAQ Agent**
   - Answers railway-related questions using Retrieval-Augmented Generation (RAG).
   - Retrieves relevant information from railway PDF documents.
   - Uses ChromaDB for document retrieval and Groq for response generation.

6. **Live Tracking Agent**
   - Retrieves train running information through an external railway API.
   - Provides train tracking information when API data is available.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| LangChain | LLM application integration |
| LangGraph | Multi-agent workflow orchestration |
| Groq | Large Language Model API |
| Streamlit | User interface |
| ChromaDB | Vector database for RAG |
| Sentence Transformers | Text embedding generation |
| SQLite | User and booking data storage |
| PyPDF | PDF document processing |
| Python-dotenv | Environment variable management |
| Requests | External API communication |

## RAG Implementation

The Railway FAQ Agent uses Retrieval-Augmented Generation (RAG) to answer questions from railway documents.

The workflow:

1. Railway PDF documents are loaded.
2. Document content is extracted and divided into smaller chunks.
3. Sentence Transformers generates embeddings for the text chunks.
4. ChromaDB stores the embeddings and document information.
5. When a user asks a question, the system retrieves relevant document chunks.
6. The retrieved information is passed to the Groq LLM to generate an answer.

This helps the application answer railway questions using the provided reference documents rather than relying only on the LLM's general knowledge.

## Multi-Agent Architecture

The application uses LangGraph to manage the conversation workflow.

The general workflow is:

User Input → Intent Detection → Agent Routing → Specialized Agent → Response to User

Each agent is responsible for a specific task. This modular architecture makes the application easier to maintain and extend.

## Project Structure

```text
IRCTC-Multi-Agent/
│
├── agents/
│   ├── food_booking_agent.py
│   ├── live_tracking_agent.py
│   ├── profile_agent.py
│   ├── railway_faq_agent.py
│   ├── ticket_booking_agent.py
│   └── train_search_agent.py
│
├── data/
│   └── railway_docs/
│
├── rag/
│   └── railway_rag.py
│
├── tools/
│   └── train_tools.py
│
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Shwetha-Francis/IRCTC-Multi-Agent.git
```

### 2. Navigate to the project directory

```bash
cd IRCTC-Multi-Agent
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

Windows:

```bash
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment variables

Create a `.env` file in the project root directory and add the required API credentials.

Example:

```env
GROQ_API_KEY=your_groq_api_key
RAILRADAR_API_KEY=your_railradar_api_key
```

Use the actual variable names expected by the project code. Never upload your real API keys to GitHub.

### 7. Run the application

```bash
streamlit run app.py
```

## Important Notes

- This project is developed for learning and demonstration purposes.
- Ticket and food booking workflows are simulated.
- Live train tracking depends on external API availability and valid API credentials.
- Railway FAQ responses depend on the available reference documents.
- The SQLite database and personal railway tickets are not included in the public repository.

## Future Improvements

- Improve agent coordination and conversation memory.
- Add more railway-related tools and services.
- Improve booking confirmation and transaction handling.
- Enhance error handling and API reliability.
- Add more railway documents to the RAG knowledge base.

## Author

**Shwetha Francis**

B.Tech – Artificial Intelligence and Data Science

GitHub: [Shwetha-Francis](https://github.com/Shwetha-Francis)
