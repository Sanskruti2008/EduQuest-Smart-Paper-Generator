/**
 * Enhanced Paper Generation Logic
 * Intelligently generates papers based on curriculum structure, chapter weightages,
 * RUA levels, and exam patterns
 */

export interface Question {
  id: number | string;
  text: string;
  chapter: string;
  topic?: string;
  marks: number;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  bloomLevel?: 'Remember' | 'Understand' | 'Apply' | 'Analyze' | 'Evaluate' | 'Create';
  co?: string;
  type: string;
  subject: string;
  grade: string;
  year?: string;
  tags?: string[];
  image?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface ChapterWeightage {
  chapter: string;
  weightage: number; // percentage
  priority: 'Very High' | 'High' | 'Medium' | 'Low';
}

export interface PaperConfig {
  totalMarks: number;
  sections: SectionConfig[];
  difficultyDistribution?: {
    easy: number;    // percentage
    medium: number;
    hard: number;
  };
  bloomDistribution?: {
    remember: number; // percentage
    understand: number;
    apply: number;
    higherOrder: number; // analyze, evaluate, create
  };
}

export interface SectionConfig {
  name: string;
  marksPercentage: number;
  questionType: string;
  marksPerQuestion: number;
  numQuestions?: number;
  requiredQuestions?: number; // For "attempt any X" scenarios
  difficulty?: 'Easy' | 'Medium' | 'Hard' | 'Mixed';
  bloomLevels?: string[];
}

export interface GeneratedSection {
  name: string;
  instructions: string;
  questions: Question[];
  totalMarks: number;
  requiredQuestions?: number;
}

/**
 * Assign default Bloom level to questions that don't have one
 */
function assignDefaultBloomLevel(question: Question): Question {
  if (question.bloomLevel) return question;
  
  // Assign based on marks and difficulty
  let bloomLevel: Question['bloomLevel'];
  
  if (question.marks <= 2) {
    bloomLevel = 'Remember';
  } else if (question.marks <= 4) {
    bloomLevel = question.difficulty === 'Easy' ? 'Understand' : 'Apply';
  } else if (question.marks <= 6) {
    bloomLevel = question.difficulty === 'Hard' ? 'Analyze' : 'Apply';
  } else {
    bloomLevel = question.difficulty === 'Hard' ? 'Evaluate' : 'Analyze';
  }
  
  return { ...question, bloomLevel };
}

/**
 * Calculate how many questions needed from each chapter based on weightage
 */
export function calculateChapterDistribution(
  chapterWeightages: ChapterWeightage[],
  totalQuestions: number
): Map<string, number> {
  const distribution = new Map<string, number>();
  
  // Sort by priority and weightage
  const sortedChapters = [...chapterWeightages].sort((a, b) => {
    const priorityOrder = { 'Very High': 4, 'High': 3, 'Medium': 2, 'Low': 1 };
    const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
    if (priorityDiff !== 0) return priorityDiff;
    return b.weightage - a.weightage;
  });
  
  // Calculate base distribution
  let remaining = totalQuestions;
  let totalWeightage = chapterWeightages.reduce((sum, ch) => sum + ch.weightage, 0);
  
  sortedChapters.forEach((chapter, index) => {
    if (index === sortedChapters.length - 1) {
      // Last chapter gets remaining questions
      distribution.set(chapter.chapter, remaining);
    } else {
      const count = Math.max(1, Math.round((chapter.weightage / totalWeightage) * totalQuestions));
      distribution.set(chapter.chapter, count);
      remaining -= count;
    }
  });
  
  return distribution;
}

/**
 * Distribute marks across Bloom's taxonomy levels
 */
export function calculateBloomDistribution(
  totalMarks: number,
  config?: PaperConfig['bloomDistribution']
): Map<string, number> {
  const defaults = config || {
    remember: 20,      // 20% Remember level
    understand: 35,    // 35% Understand level
    apply: 30,         // 30% Apply level
    higherOrder: 15    // 15% Analyze/Evaluate/Create
  };
  
  return new Map([
    ['Remember', Math.round((totalMarks * defaults.remember) / 100)],
    ['Understand', Math.round((totalMarks * defaults.understand) / 100)],
    ['Apply', Math.round((totalMarks * defaults.apply) / 100)],
    ['Analyze', Math.round((totalMarks * defaults.higherOrder) / 200)],
    ['Evaluate', Math.round((totalMarks * defaults.higherOrder) / 300)],
    ['Create', Math.round((totalMarks * defaults.higherOrder) / 300)],
  ]);
}

/**
 * Filter questions intelligently based on multiple criteria
 */
export function filterQuestions(
  allQuestions: Question[],
  criteria: {
    chapter?: string;
    chapters?: string[];
    difficulty?: string;
    bloomLevel?: string;
    marksRange?: { min: number; max: number };
    questionType?: string;
    excludeIds?: (string | number)[];
  }
): Question[] {
  return allQuestions.filter(q => {
    if (criteria.excludeIds && criteria.excludeIds.includes(q.id)) return false;
    if (criteria.chapter && q.chapter !== criteria.chapter) return false;
    if (criteria.chapters && !criteria.chapters.includes(q.chapter)) return false;
    if (criteria.difficulty && q.difficulty !== criteria.difficulty) return false;
    if (criteria.bloomLevel && q.bloomLevel !== criteria.bloomLevel) return false;
    
    if (criteria.marksRange) {
      if (q.marks < criteria.marksRange.min || q.marks > criteria.marksRange.max) return false;
    }
    
    if (criteria.questionType) {
      const typeMatch = q.type.toLowerCase().includes(criteria.questionType.toLowerCase()) ||
                        q.marks === parseInt(criteria.questionType);
      if (!typeMatch) return false;
    }
    
    return true;
  });
}

/**
 * Score a question based on how well it fits the requirements
 */
function scoreQuestion(
  question: Question,
  criteria: {
    targetMarks?: number;
    preferredDifficulty?: string;
    preferredBloom?: string;
    chapterPriority?: number;
    avoidOverUsedChapters?: Map<string, number>;
  }
): number {
  let score = 100;
  
  // Mark matching
  if (criteria.targetMarks) {
    const markDiff = Math.abs(question.marks - criteria.targetMarks);
    score -= markDiff * 5;
  }
  
  // Difficulty matching
  if (criteria.preferredDifficulty && question.difficulty === criteria.preferredDifficulty) {
    score += 20;
  }
  
  // Bloom level matching
  if (criteria.preferredBloom && question.bloomLevel === criteria.preferredBloom) {
    score += 15;
  }
  
  // Chapter priority
  if (criteria.chapterPriority) {
    score += criteria.chapterPriority * 10;
  }
  
  // Avoid overused chapters
  if (criteria.avoidOverUsedChapters) {
    const usage = criteria.avoidOverUsedChapters.get(question.chapter) || 0;
    score -= usage * 10;
  }
  
  return score;
}

/**
 * Select best questions using intelligent scoring
 */
export function selectBestQuestions(
  availableQuestions: Question[],
  count: number,
  criteria: Parameters<typeof scoreQuestion>[1]
): Question[] {
  // Score all questions
  const scoredQuestions = availableQuestions.map(q => ({
    question: q,
    score: scoreQuestion(q, criteria)
  }));
  
  // Sort by score and select top N
  return scoredQuestions
    .sort((a, b) => b.score - a.score)
    .slice(0, count)
    .map(sq => sq.question)
    .sort(() => Math.random() - 0.5); // Randomize final order
}

/**
 * Main function to generate a complete paper
 */
export function generatePaper(
  allQuestions: Question[],
  paperConfig: PaperConfig,
  chapterWeightages: ChapterWeightage[]
): {
  sections: GeneratedSection[];
  totalMarks: number;
  chapterDistribution: Map<string, number>;
  bloomDistribution: Map<string, number>;
  difficultyDistribution: Map<string, number>;
} {
  // Normalize questions by assigning default Bloom levels where missing
  const normalizedQuestions = allQuestions.map(assignDefaultBloomLevel);
  
  console.log('🎯 Paper Generation Started');
  console.log('   Total questions available:', normalizedQuestions.length);
  console.log('   Target total marks:', paperConfig.totalMarks);
  console.log('   Sections to generate:', paperConfig.sections.length);
  
  const usedQuestionIds = new Set<string | number>();
  const chapterUsage = new Map<string, number>();
  const sections: GeneratedSection[] = [];
  
  // Calculate Bloom's distribution
  const targetBloomMarks = calculateBloomDistribution(
    paperConfig.totalMarks,
    paperConfig.bloomDistribution
  );
  
  const currentBloomMarks = new Map<string, number>(
    Array.from(targetBloomMarks.keys()).map(k => [k, 0])
  );
  
  // Process each section
  for (const sectionConfig of paperConfig.sections) {
    console.log(`\n📝 Generating: ${sectionConfig.name}`);
    console.log(`   Need: ${sectionConfig.numQuestions} questions × ${sectionConfig.marksPerQuestion} marks each`);
    
    const sectionMarks = Math.round((paperConfig.totalMarks * sectionConfig.marksPercentage) / 100);
    const numQuestions = sectionConfig.numQuestions || 
                        Math.ceil(sectionMarks / sectionConfig.marksPerQuestion);
    
    // Calculate chapter distribution for this section
    const sectionChapterDist = calculateChapterDistribution(chapterWeightages, numQuestions);
    
    const sectionQuestions: Question[] = [];
    
    // Select questions chapter by chapter
    for (const [chapter, count] of sectionChapterDist.entries()) {
      // Determine which Bloom levels we need
      const neededBlooms = sectionConfig.bloomLevels || ['Remember', 'Understand', 'Apply'];
      
      for (let i = 0; i < count; i++) {
        // Find least-used Bloom level
        const bloomLevel = neededBlooms.reduce((least, current) => {
          const leastMarks = currentBloomMarks.get(least) || 0;
          const currentMarks = currentBloomMarks.get(current) || 0;
          const leastTarget = targetBloomMarks.get(least) || 1;
          const currentTarget = targetBloomMarks.get(current) || 1;
          
          return (leastMarks / leastTarget) < (currentMarks / currentTarget) ? least : current;
        });
        
        // Filter available questions (strict marks matching)
        const candidates = filterQuestions(normalizedQuestions, {
          chapter,
          marksRange: { 
            min: sectionConfig.marksPerQuestion, 
            max: sectionConfig.marksPerQuestion 
          },
          difficulty: sectionConfig.difficulty !== 'Mixed' ? sectionConfig.difficulty : undefined,
          bloomLevel,
          excludeIds: Array.from(usedQuestionIds)
        });
        
        if (candidates.length === 0) {
          // Relax constraints if no questions found (still strict on marks)
          const relaxedCandidates = filterQuestions(normalizedQuestions, {
            chapters: Array.from(sectionChapterDist.keys()),
            marksRange: { 
              min: sectionConfig.marksPerQuestion, 
              max: sectionConfig.marksPerQuestion 
            },
            excludeIds: Array.from(usedQuestionIds)
          });
          
          if (relaxedCandidates.length > 0) {
            const selected = selectBestQuestions(relaxedCandidates, 1, {
              targetMarks: sectionConfig.marksPerQuestion,
              preferredBloom: bloomLevel,
              avoidOverUsedChapters: chapterUsage
            })[0];
            
            // Validate marks before adding
            if (selected && selected.marks === sectionConfig.marksPerQuestion) {
              console.log(`   ✅ Added: ${selected.text.substring(0, 50)}... (${selected.marks} marks)`);
              sectionQuestions.push(selected);
              usedQuestionIds.add(selected.id);
              chapterUsage.set(selected.chapter, (chapterUsage.get(selected.chapter) || 0) + 1);
              
              const qBloom = selected.bloomLevel || 'Understand';
              currentBloomMarks.set(qBloom, (currentBloomMarks.get(qBloom) || 0) + selected.marks);
            } else if (selected) {
              console.log(`   ❌ Rejected: ${selected.text.substring(0, 50)}... (${selected.marks} marks - need ${sectionConfig.marksPerQuestion})`);
            }
          }
        } else {
          // Select best question from candidates
          const selected = selectBestQuestions(candidates, 1, {
            targetMarks: sectionConfig.marksPerQuestion,
            preferredBloom: bloomLevel,
            chapterPriority: chapterWeightages.find(cw => cw.chapter === chapter)?.weightage || 0,
            avoidOverUsedChapters: chapterUsage
          })[0];
          
          // Validate marks before adding
          if (selected && selected.marks === sectionConfig.marksPerQuestion) {
            console.log(`   ✅ Added: ${selected.text.substring(0, 50)}... (${selected.marks} marks)`);
            sectionQuestions.push(selected);
            usedQuestionIds.add(selected.id);
            chapterUsage.set(selected.chapter, (chapterUsage.get(selected.chapter) || 0) + 1);
            
            const qBloom = selected.bloomLevel || 'Understand';
            currentBloomMarks.set(qBloom, (currentBloomMarks.get(qBloom) || 0) + selected.marks);
          } else if (selected) {
            console.log(`   ❌ Rejected: ${selected.text.substring(0, 50)}... (${selected.marks} marks - need ${sectionConfig.marksPerQuestion})`);
          }
        }
      }
    }
    
    // Create section with instructions
    const totalSectionMarks = sectionQuestions.reduce((sum, q) => sum + q.marks, 0);
    const requiredQuestions = sectionConfig.requiredQuestions || sectionQuestions.length;
    
    let instructions = `${sectionConfig.name}\n`;
    if (sectionQuestions.length > requiredQuestions) {
      instructions += `Attempt any ${requiredQuestions} out of ${sectionQuestions.length} questions. `;
    } else {
      instructions += `Answer all questions. `;
    }
    instructions += `Each question carries ${sectionConfig.marksPerQuestion} mark(s).`;
    
    sections.push({
      name: sectionConfig.name,
      instructions,
      questions: sectionQuestions.map((q, idx) => ({ ...q, questionNumber: idx + 1 })),
      totalMarks: totalSectionMarks,
      requiredQuestions
    });
    
    console.log(`   Section complete: ${sectionQuestions.length} questions, ${totalSectionMarks} marks`);
  }
  
  // Calculate final statistics
  const allPaperQuestions = sections.flatMap(s => s.questions);
  
  console.log('\n✅ Paper Generation Complete');
  console.log(`   Total questions: ${allPaperQuestions.length}`);
  console.log(`   Total marks: ${sections.reduce((sum, s) => sum + s.totalMarks, 0)}`);
  
  // Log marks distribution
  const marksDist = allPaperQuestions.reduce((acc, q) => {
    acc[q.marks] = (acc[q.marks] || 0) + 1;
    return acc;
  }, {} as Record<number, number>);
  console.log('   Questions by marks:', marksDist);
  
  const difficultyDist = new Map<string, number>();
  allPaperQuestions.forEach(q => {
    difficultyDist.set(q.difficulty, (difficultyDist.get(q.difficulty) || 0) + 1);
  });
  
  return {
    sections,
    totalMarks: sections.reduce((sum, s) => sum + s.totalMarks, 0),
    chapterDistribution: chapterUsage,
    bloomDistribution: currentBloomMarks,
    difficultyDistribution: difficultyDist
  };
}

/**
 * Generate MSBTE format paper (70 marks standard)
 */
export function generateMSBTEPaper(
  allQuestions: Question[],
  chapterWeightages: ChapterWeightage[]
): ReturnType<typeof generatePaper> {
  const msbteConfig: PaperConfig = {
    totalMarks: 70,
    sections: [
      {
        name: 'Q.1 - Objective Questions (Attempt ANY FIVE)',
        marksPercentage: 14.3, // 10 marks
        questionType: 'Objective',
        marksPerQuestion: 2,
        numQuestions: 7,
        requiredQuestions: 5,
        difficulty: 'Mixed',
        bloomLevels: ['Remember', 'Understand']
      },
      {
        name: 'Q.2 - Short Answer Questions (Attempt ANY THREE)',
        marksPercentage: 17.1, // 12 marks
        questionType: 'Short Answer',
        marksPerQuestion: 4,
        numQuestions: 4,
        requiredQuestions: 3,
        difficulty: 'Mixed',
        bloomLevels: ['Understand', 'Apply']
      },
      {
        name: 'Q.3 - Short Answer Questions (Attempt ANY THREE)',
        marksPercentage: 17.1, // 12 marks
        questionType: 'Short Answer',
        marksPerQuestion: 4,
        numQuestions: 4,
        requiredQuestions: 3,
        difficulty: 'Mixed',
        bloomLevels: ['Understand', 'Apply']
      },
      {
        name: 'Q.4 - Short Answer Questions (Attempt ANY THREE)',
        marksPercentage: 17.1, // 12 marks
        questionType: 'Short Answer',
        marksPerQuestion: 4,
        numQuestions: 4,
        requiredQuestions: 3,
        difficulty: 'Mixed',
        bloomLevels: ['Apply', 'Analyze']
      },
      {
        name: 'Q.5 - Short Answer Questions (Attempt ANY THREE)',
        marksPercentage: 17.1, // 12 marks
        questionType: 'Short Answer',
        marksPerQuestion: 4,
        numQuestions: 4,
        requiredQuestions: 3,
        difficulty: 'Mixed',
        bloomLevels: ['Apply', 'Analyze']
      },
      {
        name: 'Q.6 - Short Answer Questions (Attempt ANY THREE)',
        marksPercentage: 17.1, // 12 marks
        questionType: 'Short Answer',
        marksPerQuestion: 4,
        numQuestions: 4,
        requiredQuestions: 3,
        difficulty: 'Mixed',
        bloomLevels: ['Analyze', 'Evaluate']
      }
    ],
    difficultyDistribution: {
      easy: 25,
      medium: 50,
      hard: 25
    },
    bloomDistribution: {
      remember: 15,
      understand: 30,
      apply: 35,
      higherOrder: 20
    }
  };
  
  return generatePaper(allQuestions, msbteConfig, chapterWeightages);
}
