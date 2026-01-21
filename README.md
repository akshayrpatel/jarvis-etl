# **Jarvis ETL Data Pipeline**

The **Jarvis ETL Data Pipeline** is the backend ingestion system for my AI-powered personal assistant - Jarvis. Its job is to process all the documents that describe my work, projects, and background, and convert them into embeddings that power semantic search on my portfolio.

> [!NOTE]
> This project was developed using an **AI-augmented workflow**, leveraging LLMs to reason about architecture, validate system design ideas, and refine documentation. The project consists of code that was written with AI-assisted suggestions, but fully reviewed, validated, and owned by the developer.

## **Motivation & Purpose**

I built this ETL pipeline as part of my journey to understand how production grade AI systems manage data behind the scenes. I wanted visitors on my portfolio to **ask questions about me**, and for the system to respond with knowledge back by real documents.

I needed a way to:

* Automatically load all my project files, notes, and documents
* Split them into meaningful chunks
* Convert them into embeddings
* Store them in a vector database for fast semantic search

This project gave me hands-on experience with **threading, queues, vector search, document chunking, embeddings, RAG principles, and service orchestration**.

---

## **Pipeline Components**

This system is built using clean, modular services, each responsible for one part of the ETL flow.

### **DocumentService**

* Loads files from disk
* Determines valid formats (PDFs, text, markdown, HTML, etc.)
* Splits them into semantic chunks

### **DocumentWorker**

* Runs on a background thread
* Gets chunks from DocumentService and pushes onto the document queue
* Emits a sentinel to signal completion

### **DocumentService**

* Loads files from disk
* Determines valid formats (PDFs, text, markdown, HTML, etc.)
* Splits them into semantic chunks

### **EmbeddingWorker**

* Pulls document chunks in batches from the document queue
* Generates embeddings using the EmbeddingService
* Pushes embedding batches into the embedding queue
* Reacts to sentinel from document worker to exit gracefully
* Emits a sentinel to signal completion

### **EmbeddingService**

* Loads files from disk
* Determines valid formats (PDFs, text, markdown, HTML, etc.)
* Splits them into semantic chunks

### **VectorDBWorker**

* Pulls embeddings in batches from the embedding queue
* Stores them into the vector database (Chroma or other backend)
* Stops when it receives the sentinel

### **RedisBufferQueue**

* A simple Redis-backed queue
* Supports pushing/popping batches
* Handles a sentinel (“**SENTINEL**”) to signal pipeline completion

### **Pipeline Orchestrator**

* Starts all workers
* Waits for the final completion event
* Stops all threads cleanly

Together, these components form a complete **document → embedding → vector database ETL pipeline**.

---

## **Flow Overview**

When the pipeline is started:

1. **DocumentWorker**

   * Loads files from disk
   * Splits them into chunks
   * Pushes each batch into the document queue
   * Signals “DONE” via sentinel

2. **EmbeddingWorker**

   * Pulls chunk batches
   * Generates embeddings
   * Pushes batches into embedding queue
   * Forwards sentinel

3. **VectorDBWorker**

   * Pulls embedding batches
   * Inserts embeddings into the vector database
   * Stops once sentinel is reached

4. **Pipeline Orchestrator**

   * Waits for the entire process to finish
   * Shuts down all workers cleanly

This produces a complete, searchable embedding index of all documents used by my AI assistant.

---

## **Architecture**

The system uses a lightweight, service-oriented architecture with clear separation of concerns:

* **Workers** are responsible for background execution
* **Queues** act as buffers between stages (Document → Embedding → VectorDB)
* **Services** encapsulate the logic (loading, embedding, indexing)
* **Pipeline** manages lifecycle and coordination
* **Events + Sentinels** provide clean shutdown signaling

A diagram will be added later to visualize the full flow.

---

## **Technologies & Concepts**

### **Core Tools**

* **Python 3**
* **FastAPI** (backend server for my RAG assistant)
* **Uvicorn** (ASGI server)
* **Redis** (queueing backend)
* **ChromaDB** (vector database)
* **SentenceTransformers / FastEmbed Embedding Models**

### **Concepts Used**

* **RAG (Retrieval-Augmented Generation)**
  The foundation of the portfolio assistant
* **Document loaders & chunking**
  Splitting content into semantic units
* **Embeddings**
  Turning text chunks into vector representations
* **Producer–Consumer pipelines**
  With Redis queues as buffers
* **Sentinels + Events**
  For clean worker shutdown
* **Threading**
  Running workers in parallel
* **Service-oriented architecture**
  Each piece modular and testable

---

## **How I Built It & Challenges**

I built this pipeline while learning about real-world RAG systems and vector search. The process included:

### Learning the foundations

* Took courses on LangChain, RAG, embeddings, vector databases
* Studied LLM system design and pipeline orchestration

### Designing the pipeline

* Broke the system into independently testable services
* Designed a threaded worker model with Redis queues
* Used sentinels & events for proper shutdown
* Implemented serializer/deserializer systems for document & embedding payloads

### Challenges I faced

* Handling parallelism and thread coordination
* Ensuring workers exit cleanly without hanging
* Designing batch-based ingestion
* Figuring out sentinel propagation between queues
* Redis connection handling & retries
* File loader inconsistencies (PDF parsing, etc.)
* Embedding model performance 

---

## **Key Learnings**

This project taught me a wide range of skills that directly map to real-world AI engineering:

### **LLM & RAG Engineering**

* How RAG pipelines actually work under the hood
* Why vector search is needed and how embeddings are indexed
* How to chunk text optimally for retrieval
* How embeddings are generated and compared
* How to store and retrieve vectors efficiently

### **Backend & Systems Engineering**

* Threading
* Producer/consumer models
* Pipeline orchestration
* Queue coordination
* Event-driven shutdown
* Error handling and retries

### **Architecture & Clean Code**

* Writing testable, modular services
* Clear separation of concerns
* Designing predictable worker behavior
* Maintaining clean boundaries between stages

---
