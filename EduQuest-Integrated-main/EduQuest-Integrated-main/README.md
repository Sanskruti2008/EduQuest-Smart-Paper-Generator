# EduQuest AI Engine

## Overview

EduQuest is an AI-powered Educational Question Intelligence System designed to generate high-quality, balanced, and non-repetitive question papers.

The core objective is to transform a raw question bank into an intelligent knowledge base capable of:

* Detecting duplicate and paraphrased questions
* Organizing questions into canonical concepts
* Building a unique question bank
* Supporting intelligent question paper generation
* Enforcing academic constraints such as CO, RUA, Difficulty, Unit, and Concept coverage

---

# Current Progress

## 1. Dataset Layer ✅

Created Communication Skills V2 Dataset.

### Dataset Statistics

* Total Questions: 300
* Concepts: 19
* Metadata Included:

  * Course Outcome (CO)
  * RUA Level
  * Difficulty
  * Unit
  * Concept

Example:

```json
{
  "question_number": 1,
  "question_text": "Define communication.",
  "course_outcome": "CO1",
  "rua_level": "R",
  "difficulty": "Easy",
  "unit": "Unit-I",
  "concept": "Communication"
}
```

---

## 2. Embedding Layer ✅

Implemented EmbeddingService using:

* Sentence Transformers
* Model: all-MiniLM-L6-v2

Features:

* Converts questions into vector embeddings
* Embedding Length: 384

Purpose:

* Semantic understanding of questions
* Similarity comparison
* Duplicate detection

---

## 3. Vector Database Layer ✅

Integrated ChromaDB.

Collection:

```text
communication_skills_v2_questions
```

Stored:

* Question Text
* Metadata
* Embeddings

Benefits:

* Fast semantic retrieval
* Vector similarity search

---

## 4. Semantic Search Engine ✅

Implemented SearchService.

Capabilities:

* Retrieve semantically similar questions
* Meaning-based search instead of keyword matching

Example:

Input:

```text
What is communication?
```

Output:

```text
Define communication.
```

---

## 5. Duplicate Detection Engine ✅

Implemented SimilarityService and DuplicateDetectionService.

Features:

* Semantic similarity calculation
* Duplicate detection
* Paraphrase identification

Example:

```text
Define communication.
What is meant by communication?
```

Similarity:

```text
0.90+
```

Result:

```text
Duplicate = True
```

---

## 6. Canonical Assignment Engine ✅

Implemented CanonicalAssignmentService.

Purpose:

* Assign incoming questions to canonical concepts
* Prevent duplicate knowledge storage
* Support concept-level organization

Example:

```text
Define communication.
What is communication?
State the meaning of communication.
```

Mapped to:

```text
CAN_001
```

---

## 7. Canonical Repository ✅

Created repository structure for canonical questions.

Example:

```json
{
  "canonical_id": "CAN_001",
  "canonical_question": "Define communication"
}
```

Purpose:

* Central storage of unique concepts
* Foundation for unique question bank creation

---

## 8. Automatic Canonical Builder ✅

Implemented CanonicalBuilderService.

Purpose:

* Automatically group semantically similar questions
* Create canonical concepts

Workflow:

```text
Question
    ↓
Similarity Check
    ↓
Canonical Assignment
    ↓
Canonical Group Creation
```

---

## 9. Unique Question Bank (V1) ✅

Generated first version of Unique Question Bank.

Results:

```text
Input Questions: 300
Generated Canonicals: 122
```

Output File:

```text
data/processed/canonical_questions_v2.json
```

Example:

```json
{
  "canonical_id": "CAN_001",
  "canonical_question": "Define communication.",
  "questions": [
    "Define communication.",
    "What is communication?",
    "State the meaning of communication."
  ]
}
```

Purpose:

* Remove semantic duplicates
* Organize knowledge by concept
* Enable intelligent question selection

---

# Current Architecture

```text
Dataset
   ↓
Embedding Service
   ↓
ChromaDB
   ↓
Semantic Search
   ↓
Duplicate Detection
   ↓
Canonical Assignment
   ↓
Canonical Builder
   ↓
Unique Question Bank
```

---

# Project Status

## Completed Modules

* Dataset Loader ✅
* Embedding Service ✅
* ChromaDB Integration ✅
* Semantic Search ✅
* Similarity Service ✅
* Duplicate Detection ✅
* Canonical Assignment ✅
* Canonical Repository ✅
* Automatic Canonical Builder ✅
* Unique Question Bank (V1) ✅

---

## Upcoming Modules

* Question Selection Engine ⏳
* PostgreSQL Integration ⏳
* RUA Classifier ⏳
* Difficulty Classifier ⏳
* Question Generator ⏳
* Paper Generation Engine ⏳
* Faculty Validation Layer ⏳

---

# Long-Term Vision

EduQuest aims to become an intelligent assessment platform capable of:

* Multi-subject question bank management
* AI-assisted paper generation
* Duplicate-free assessments
* Outcome-based education support
* Difficulty balancing
* Concept coverage optimization
* Multi-college deployment

---

# Current Milestone Achieved

Successfully transformed:

```text
300 Raw Questions
```

into

```text
122 Canonical Concepts
```

forming the first operational version of the EduQuest Unique Question Bank.
