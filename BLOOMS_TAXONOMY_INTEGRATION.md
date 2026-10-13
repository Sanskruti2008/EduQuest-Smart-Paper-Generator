# Bloom's Taxonomy Integration in EduQuest Smart Paper generation System

## Overview

EduQuest Smart Paper generation System now automatically classifies all generated questions according to **Bloom's Taxonomy**, a hierarchical framework for categorizing educational learning objectives based on cognitive complexity.

## Bloom's Taxonomy Levels

The system uses all six levels of Bloom's Taxonomy (revised version):

### 1. **Remember** (Lowest Cognitive Level)
- **Description**: Recall facts and basic concepts
- **Keywords**: Define, List, Name, State, Identify, Label, Recall, Recognize
- **Typical Marks**: 1-2 marks
- **Example**: "Define photosynthesis."

### 2. **Understand**
- **Description**: Explain ideas or concepts
- **Keywords**: Explain, Describe, Summarize, Interpret, Classify, Compare, Discuss
- **Typical Marks**: 3-4 marks
- **Example**: "Explain the process of photosynthesis."

### 3. **Apply**
- **Description**: Use information in new situations
- **Keywords**: Apply, Demonstrate, Illustrate, Solve, Use, Calculate, Implement
- **Typical Marks**: 5-6 marks
- **Example**: "Calculate the rate of photosynthesis given specific light intensities."

### 4. **Analyze**
- **Description**: Draw connections among ideas
- **Keywords**: Analyze, Examine, Investigate, Differentiate, Compare and contrast, Organize
- **Typical Marks**: 7-8 marks
- **Example**: "Analyze the factors affecting the rate of photosynthesis."

### 5. **Evaluate**
- **Description**: Justify a decision or course of action
- **Keywords**: Evaluate, Assess, Judge, Critique, Justify, Argue, Defend
- **Typical Marks**: 9 marks
- **Example**: "Evaluate the importance of photosynthesis in maintaining Earth's atmosphere."

### 6. **Create** (Highest Cognitive Level)
- **Description**: Produce new or original work
- **Keywords**: Create, Design, Construct, Develop, Formulate, Plan, Produce, Invent
- **Typical Marks**: 10 marks
- **Example**: "Design an experiment to demonstrate the effect of CO₂ concentration on photosynthesis."

## Features Implemented

### 1. Automatic Classification
- The AI automatically assigns a Bloom's level to each generated question
- If the AI doesn't assign a level, the system uses an automatic fallback based on:
  - Question keywords (verb analysis)
  - Mark allocation
  - Question complexity

### 2. Visual Indicators
- **Paper Builder**: Each question displays its Bloom's level in an emerald-colored badge with a 🎓 icon
- **Review Page**: Complete breakdown showing count of questions at each Bloom's level
- **Export (PDF/DOCX)**: Bloom's level appears next to each question in green text

### 3. Statistics & Analytics
- The Review page now includes a dedicated "Bloom's Taxonomy" card
- Shows distribution across all six levels
- Helps ensure balanced cognitive complexity in the paper

### 4. Smart Assignment Logic
The system uses intelligent rules to assign Bloom's levels:

```
Marks 1-2  → Remember
Marks 3-4  → Understand
Marks 5-6  → Apply
Marks 7-8  → Analyze
Marks 9    → Evaluate
Marks 10+  → Create
```

Additionally, keyword analysis takes precedence over mark-based assignment.

## Benefits for Educators

1. **Balanced Assessment**: Ensure your question paper covers all cognitive levels
2. **Learning Objectives**: Align questions with specific learning outcomes
3. **Differentiation**: Easily identify lower-order and higher-order thinking questions
4. **Quality Assurance**: Verify that mark allocation matches cognitive complexity
5. **Professional Standards**: Meet educational standards requiring Bloom's Taxonomy alignment

## PT Exam Pattern

For PT (Periodic Test) exams, questions are automatically aligned with appropriate Bloom's levels:

- **Q.1 (2 marks each)**: Remember & Understand
- **Q.2 (4 marks each)**: Understand & Apply
- **Q.3 (4 marks each)**: Apply, Analyze & Evaluate

## Regular Exam Pattern

For regular exams, the distribution is based on:
- Overall difficulty setting (Easy/Medium/Hard/Mixed)
- Mark allocation for each question
- Question type and complexity

## API Response

The AI generation endpoint now returns Bloom's Taxonomy statistics:

```json
{
  "success": true,
  "questions": [...],
  "sections": [...],
  "stats": {
    "totalQuestions": 14,
    "totalMarks": 30,
    "distribution": {
      "Easy": 5,
      "Medium": 5,
      "Hard": 4
    },
    "bloomDistribution": {
      "Remember": 3,
      "Understand": 4,
      "Apply": 3,
      "Analyze": 3,
      "Evaluate": 1,
      "Create": 0
    }
  }
}
```

## Future Enhancements

Potential future improvements could include:
1. User-specified Bloom's level distribution (e.g., "30% Remember, 40% Understand, 30% Apply")
2. Bloom's level filtering in question bank search
3. Historical analysis of Bloom's distribution across generated papers
4. Recommendations for improving cognitive diversity

## Technical Implementation

### Backend (server.py)
- `auto_assign_bloom_level()`: Function to automatically assign Bloom's levels
- Updated AI prompts to explicitly request Bloom's classification
- Added Bloom's statistics to API responses
- Modified PDF/DOCX generation to display Bloom's levels

### Frontend (React)
- Updated PaperBuilder.tsx to display Bloom's badges
- Enhanced Review.tsx with Bloom's distribution card
- Modified question rendering to show Bloom's level consistently

## Best Practices

1. **Lower-Order Thinking** (Remember, Understand): 30-40% of questions
2. **Higher-Order Thinking** (Apply, Analyze, Evaluate, Create): 60-70% of questions
3. **Balanced Distribution**: Avoid having all questions at one level
4. **Progressive Difficulty**: Structure sections from lower to higher cognitive levels

---

**Note**: The Bloom's Taxonomy classification is automatically applied to all newly generated questions. Existing questions in the question bank can be manually tagged with Bloom's levels for consistency.
