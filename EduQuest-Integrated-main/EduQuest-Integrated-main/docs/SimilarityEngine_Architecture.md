# Similarity Engine Architecture

## Project Overview

The Similarity Engine is an independent software module of EduQuest AI responsible for processing extracted question datasets and automatically maintaining a centralized, subject-wise unique question repository.

The engine receives a structured dataset of questions, performs semantic similarity analysis, detects duplicate questions, assigns canonical questions, updates the subject-wise ChromaDB collections, updates the Canonical Repository, generates the Unique Question Bank, and finally returns a detailed processing report.

The engine is completely automated and requires only a single function call for integration with external systems.

---

## Design Goals

- Fully automated processing
- Single function call integration
- Subject independent
- Scalable to multiple departments
- Machine Learning ready
- Production ready architecture
- No manual execution
- No terminal commands
- Easy integration with Question Paper Generation Engine

---

# Folder Structure

```
eduquest/

│
├── src/
│
│   ├── engine/
│   │      ├── __init__.py
│   │      └── similarity_engine.py
│   │
│   ├── processors/
│   │      ├── __init__.py
│   │      ├── dataset_processor.py
│   │      └── question_processor.py
│   │
│   ├── services/
│   │      ├── embedding_service.py
│   │      ├── search_service.py
│   │      ├── chroma_service.py
│   │      ├── duplicate_detection_service.py
│   │      ├── canonical_service.py
│   │      ├── canonical_repository.py
│   │      ├── unique_question_bank_service.py
│   │      ├── similarity_service.py
│   │      └── verb_extraction_service.py
│   │
│   ├── models/
│   │      ├── question.py
│   │      └── processing_result.py
│   │
│   └── utils/
│
├── data/
│      ├── raw/
│      ├── processed/
│      └── canonical_questions.json
│
├── chroma_db/
│
├── tests/
│
├── docs/
│
└── experiments/
```

---

## Responsibility of each folder

### engine/

Contains only the main entry point.

This is the only module another developer should call.

---

### processors/

Contains business workflow.

Processors coordinate the services.

They never store data.

---

### services/

Contains reusable logic.

Examples:

- Embeddings
- ChromaDB
- Duplicate Detection
- Search
- Canonical Assignment

Every service should have a single responsibility.

---

### models/

Contains data models only.

No processing logic.

---

### utils/

General helper functions.

No business logic.

---

### data/

Stores JSON datasets and generated repositories.

---

### chroma_db/

Persistent vector database.

---

### experiments/

Research only.

Nothing inside this folder is used by the production engine.


---

# Engine Contract

## Engine Entry Point

```python
engine = SimilarityEngine()

result = engine.process_dataset(dataset)
```

The Similarity Engine exposes only one public function.

```python
process_dataset(dataset)
```

All internal operations are automatically handled by the engine.

---

## Expected Input

The engine accepts a structured dataset.

Example:

```python
dataset = {

    "subject": "Communication Skills",

    "department": "Computer Engineering",

    "semester": 3,

    "questions": [

        {
            "question_id": "Q001",

            "question_text": "Define Communication.",

            "marks": 2,

            "unit": "Unit-I",

            "difficulty": "Easy",

            "rua": "R",

            "co": "CO1"
        }

    ]
}
```

Only these fields are mandatory:

- subject
- questions
- question_text

All remaining metadata is optional.

The engine preserves all available metadata.

---

## Expected Output

The engine returns a Processing Report.

Example:

```python
{

    "status": "success",

    "subject": "Communication Skills",

    "questions_processed": 300,

    "duplicates_found": 82,

    "new_questions": 218,

    "canonical_questions": 190,

    "processing_time": 8.74,

    "collection": "communication_skills"
}
```

The returned object contains only processing information.

The processed data is automatically stored internally by the engine.

No additional function calls are required.
```

---

# Processing Workflow

The Similarity Engine follows a fixed processing pipeline.

```
Dataset
    │
    ▼
Input Validation
    │
    ▼
Dataset Processor
    │
    ▼
Question Processor
    │
    ▼
Generate Embedding
    │
    ▼
Load Subject Collection
    │
    ▼
Semantic Search
    │
    ▼
Duplicate Detection
    │
    ▼
Canonical Assignment
    │
    ▼
Update ChromaDB
    │
    ▼
Update Canonical Repository
    │
    ▼
Generate Unique Question Bank
    │
    ▼
Generate Processing Report
    │
    ▼
Return Result
```

---

## Workflow Description

### Step 1

The engine validates the incoming dataset.

Invalid datasets are rejected before processing begins.

---

### Step 2

The Dataset Processor iterates through every question.

Each question is independently processed.

---

### Step 3

Question Processor generates the embedding.

Embeddings are generated only once per question.

---

### Step 4

The engine automatically loads the correct ChromaDB collection using the subject name.

If the collection does not exist, it is created automatically.

---

### Step 5

Semantic Search retrieves the Top-K most similar existing questions.

---

### Step 6

Duplicate Detection determines whether the incoming question already exists.

The decision is based on semantic similarity, verb analysis and future Machine Learning models.

---

### Step 7

Canonical Service assigns the canonical question.

If no suitable canonical exists, a new canonical question is created.

---

### Step 8

If the question is unique, it is inserted into ChromaDB.

Duplicate questions are linked to their canonical question.

---

### Step 9

Canonical Repository is updated.

---

### Step 10

Unique Question Bank is regenerated.

---

### Step 11

Processing statistics are collected.

---

### Step 12

A Processing Report is returned to the caller.

---

# ChromaDB Architecture

## Collection Strategy

The Similarity Engine maintains one ChromaDB collection per subject.

Examples:

communication_skills

java

python

operating_system

database_management_system

computer_graphics

software_engineering

Each subject is completely isolated.

---

## Collection Naming Convention

Collection names are automatically generated.

Rules:

- Convert subject to lowercase
- Replace spaces with underscores
- Remove special characters

Example:

Communication Skills

↓

communication_skills

Database Management System

↓

database_management_system

---

## Stored Information

Each ChromaDB record stores:

- Question ID
- Question Text
- Embedding Vector
- Metadata

Metadata includes:

- subject
- department
- semester
- unit
- concept
- marks
- difficulty
- rua
- bloom
- course_outcome
- canonical_id
- upload_date
- source_paper

The engine preserves all available metadata.

---

## Search Strategy

Similarity search is always performed only inside the subject collection.

The engine never compares Java questions with Python questions.

---

## Collection Creation

If a collection does not exist:

The engine automatically creates it.

No manual setup is required.

---

## Embedding Policy

Embeddings are generated exactly once.

Stored permanently.

Never regenerated unless explicitly requested.

---

## Update Policy

Every new unique question is automatically inserted into ChromaDB.

Duplicate questions are linked to an existing canonical question.

No duplicate embeddings are stored.

---

# Canonical Repository Architecture

## Purpose

The Canonical Repository maintains one canonical representation for every unique question.

Duplicate questions never create new canonical entries.

Instead, they are linked to an existing canonical question.

---

## Canonical Record Structure

Each canonical record contains:

- canonical_id
- canonical_question
- subject
- department
- semester
- concept
- unit
- difficulty
- rua
- bloom
- course_outcome

Duplicate Questions

- duplicate_question_ids
- duplicate_question_texts

Statistics

- occurrence_count
- last_updated

---

## Canonical Assignment Policy

If a question is unique:

→ Create a new canonical question.

If a duplicate is detected:

→ Link the duplicate to the existing canonical question.

No duplicate canonical questions are allowed.

---

## Canonical ID Format

Example

CAN_000001

CAN_000002

CAN_000003

The canonical identifier remains permanent.

It never changes even if additional duplicates are discovered later.

---

## Repository Update Policy

The repository is automatically updated after every processed dataset.

No manual execution is required.

---

# Unique Question Bank Architecture

## Purpose

The Unique Question Bank is the final output repository of the Similarity Engine.

It contains only unique canonical questions.

This repository serves as the primary input for the Question Paper Generation Engine.

---

## Record Structure

Each unique question contains:

- canonical_id
- question_text
- subject
- department
- semester
- unit
- concept
- marks
- difficulty
- rua
- bloom
- course_outcome

Additional Metadata

- occurrence_count
- duplicate_count
- created_date
- last_updated

---

## Update Policy

The Unique Question Bank is regenerated automatically after every processed dataset.

No manual execution is required.

---

## Duplicate Policy

Duplicate questions are never stored in the Unique Question Bank.

Only the canonical question is preserved.

---

## Integration Policy

The Question Paper Generation Engine always reads questions from the Unique Question Bank.

It never directly reads ChromaDB.

It never directly reads duplicate questions.

This guarantees that only validated unique questions are used for paper generation.

---

## Future Extensions

The Unique Question Bank should support future additions including:

- Difficulty Prediction
- Bloom Classification
- Topic Classification
- Machine Learning Scores
- Quality Score
- Usage Frequency

---

# Service Interfaces

The Similarity Engine is composed of independent reusable services.

Each service performs one responsibility only.

---

## EmbeddingService

Purpose

Generate semantic embeddings.

Public Interface

generate_embedding(text)

generate_embeddings(texts)

---

## ChromaService

Purpose

Manage ChromaDB collections.

Public Interface

get_collection(subject)

insert_question(question)

search(embedding)

count(subject)

---

## SearchService

Purpose

Retrieve semantically similar questions.

Public Interface

find_similar_questions(
    embedding,
    subject,
    top_k
)

---

## DuplicateDetectionService

Purpose

Determine whether an incoming question is a duplicate.

Public Interface

check_duplicate(
    source_question,
    candidate_question,
    similarity_score
)

---

## CanonicalService

Purpose

Assign canonical questions.

Public Interface

assign_canonical(
    question,
    duplicate_result
)

---

## CanonicalRepository

Purpose

Store canonical knowledge.

Public Interface

find()

insert()

update()

delete()

---

## UniqueQuestionBankService

Purpose

Maintain the unique question repository.

Public Interface

generate_unique_bank()

get_questions()

---

## ProcessingResult

Purpose

Collect processing statistics.

Public Interface

add_processed()

add_duplicate()

add_unique()

generate_report()