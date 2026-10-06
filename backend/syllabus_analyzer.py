"""
Syllabus Analysis and RUA Mapping Utility Module
Provides comprehensive functions for analyzing syllabus compliance with RUA requirements
"""

import json
from typing import Dict, List, Any, Tuple
from datetime import datetime


class SyllabusAnalyzer:
    """Analyzes syllabus data and provides RUA compliance reports"""
    
    def __init__(self, syllabus_file_path: str):
        """Initialize with syllabus data file"""
        with open(syllabus_file_path, 'r', encoding='utf-8') as f:
            self.syllabus_data = json.load(f)
    
    def get_all_subjects(self) -> List[Dict]:
        """Get list of all subjects in syllabus"""
        return self.syllabus_data.get('subjects', [])
    
    def get_subject_by_id(self, subject_id: str) -> Dict:
        """Get specific subject details by ID"""
        for subject in self.syllabus_data.get('subjects', []):
            if subject['subject_id'] == subject_id:
                return subject
        return None
    
    def get_chapter_details(self, subject_id: str, chapter_number: int) -> Dict:
        """Get detailed chapter information"""
        subject = self.get_subject_by_id(subject_id)
        if not subject:
            return None
        
        for chapter in subject.get('chapters', []):
            if chapter['chapter_number'] == chapter_number:
                return chapter
        return None
    
    def analyze_rua_compliance(self, subject_id: str) -> Dict:
        """Comprehensive RUA compliance analysis for a subject"""
        subject = self.get_subject_by_id(subject_id)
        if not subject:
            return {"error": "Subject not found"}
        
        analysis = {
            "subject_name": subject['subject_name'],
            "subject_id": subject_id,
            "total_chapters": len(subject['chapters']),
            "chapters_analysis": [],
            "overall_compliance": {
                "remember": {"covered": 0, "partial": 0, "not_covered": 0},
                "understand": {"covered": 0, "partial": 0, "not_covered": 0},
                "apply": {"covered": 0, "partial": 0, "not_covered": 0}
            },
            "recommendations": [],
            "critical_gaps": [],
            "exam_priorities": {
                "very_high": [],
                "high": [],
                "medium": [],
                "low": []
            }
        }
        
        # Analyze each chapter
        for chapter in subject['chapters']:
            chapter_analysis = self._analyze_chapter_rua(chapter)
            analysis['chapters_analysis'].append(chapter_analysis)
            
            # Update overall compliance
            rua_summary = chapter.get('rua_summary', {})
            for rua_level in ['remember', 'understand', 'apply']:
                coverage_key = f"{rua_level}_coverage"
                coverage = rua_summary.get(coverage_key, "Not covered")
                
                if coverage == "Fully Covered":
                    analysis['overall_compliance'][rua_level]['covered'] += 1
                elif coverage == "Partially Covered":
                    analysis['overall_compliance'][rua_level]['partial'] += 1
                else:
                    analysis['overall_compliance'][rua_level]['not_covered'] += 1
            
            # Collect exam priorities
            for topic in chapter.get('topics', []):
                rua_mapping = topic.get('rua_mapping', {})
                for rua_level, rua_data in rua_mapping.items():
                    priority = rua_data.get('exam_priority', 'Medium')
                    topic_info = {
                        "chapter": chapter['chapter_name'],
                        "topic": topic['topic_name'],
                        "rua_level": rua_level.capitalize(),
                        "marks": rua_data.get('typical_marks', 'N/A')
                    }
                    
                    if priority == "Very High":
                        analysis['exam_priorities']['very_high'].append(topic_info)
                    elif priority == "High":
                        analysis['exam_priorities']['high'].append(topic_info)
                    elif priority == "Medium":
                        analysis['exam_priorities']['medium'].append(topic_info)
                    else:
                        analysis['exam_priorities']['low'].append(topic_info)
        
        # Add overall recommendations
        if 'overall_rua_analysis' in subject:
            analysis['overall_strategy'] = subject['overall_rua_analysis'].get('exam_strategy', [])
            analysis['critical_chapters'] = subject['overall_rua_analysis'].get('critical_chapters', [])
        
        return analysis
    
    def _analyze_chapter_rua(self, chapter: Dict) -> Dict:
        """Analyze RUA compliance for a single chapter"""
        return {
            "chapter_number": chapter['chapter_number'],
            "chapter_name": chapter['chapter_name'],
            "hours_allocated": chapter.get('hours_allocated', 0),
            "weightage": chapter.get('weightage_percentage', 0),
            "learning_objectives": chapter.get('learning_objectives', []),
            "topics_count": len(chapter.get('topics', [])),
            "rua_summary": chapter.get('rua_summary', {}),
            "focus_type": self._determine_chapter_focus(chapter)
        }
    
    def _determine_chapter_focus(self, chapter: Dict) -> str:
        """Determine if chapter is theoretical, practical, or mixed"""
        focus_types = []
        for topic in chapter.get('topics', []):
            focus_types.append(topic.get('focus_type', 'Theoretical'))
        
        if not focus_types:
            return "Unknown"
        
        practical_count = sum(1 for f in focus_types if 'Practical' in f)
        theoretical_count = sum(1 for f in focus_types if 'Theoretical' in f and 'Practical' not in f)
        
        if practical_count > theoretical_count:
            return "Primarily Practical"
        elif theoretical_count > practical_count:
            return "Primarily Theoretical"
        else:
            return "Balanced (Theory + Practice)"
    
    def get_exam_preparation_guide(self, subject_id: str) -> Dict:
        """Generate exam preparation guide based on RUA analysis"""
        subject = self.get_subject_by_id(subject_id)
        if not subject:
            return {"error": "Subject not found"}
        
        guide = {
            "subject": subject['subject_name'],
            "total_marks_distribution": subject.get('exam_weightage', {}),
            "preparation_phases": []
        }
        
        # Phase 1: Remember (Foundation)
        remember_topics = []
        for chapter in subject['chapters']:
            for topic in chapter.get('topics', []):
                rua = topic.get('rua_mapping', {}).get('remember', {})
                if rua.get('depth') in ['High', 'Very High']:
                    remember_topics.append({
                        "chapter": chapter['chapter_name'],
                        "topic": topic['topic_name'],
                        "concepts": rua.get('concepts', []),
                        "marks": rua.get('typical_marks', 'N/A')
                    })
        
        guide['preparation_phases'].append({
            "phase": "Phase 1: Build Foundation (Remember)",
            "duration": "Week 1-2",
            "focus": "Memorize definitions, lists, and basic concepts",
            "topics": remember_topics[:10]  # Top 10 for brevity
        })
        
        # Phase 2: Understand (Concepts)
        understand_topics = []
        for chapter in subject['chapters']:
            for topic in chapter.get('topics', []):
                rua = topic.get('rua_mapping', {}).get('understand', {})
                if rua.get('depth') in ['High', 'Very High']:
                    understand_topics.append({
                        "chapter": chapter['chapter_name'],
                        "topic": topic['topic_name'],
                        "concepts": rua.get('concepts', []),
                        "marks": rua.get('typical_marks', 'N/A')
                    })
        
        guide['preparation_phases'].append({
            "phase": "Phase 2: Deep Understanding",
            "duration": "Week 3-4",
            "focus": "Explain, compare, and interpret concepts",
            "topics": understand_topics[:10]
        })
        
        # Phase 3: Apply (Practice)
        apply_topics = []
        for chapter in subject['chapters']:
            for topic in chapter.get('topics', []):
                rua = topic.get('rua_mapping', {}).get('apply', {})
                if rua.get('depth') in ['High', 'Very High']:
                    apply_topics.append({
                        "chapter": chapter['chapter_name'],
                        "topic": topic['topic_name'],
                        "concepts": rua.get('concepts', []),
                        "marks": rua.get('typical_marks', 'N/A'),
                        "priority": rua.get('exam_priority', 'Medium')
                    })
        
        guide['preparation_phases'].append({
            "phase": "Phase 3: Problem Solving (Apply)",
            "duration": "Week 5-6",
            "focus": "Solve problems, write code/queries, design solutions",
            "topics": apply_topics[:15]  # More apply topics as they're crucial
        })
        
        # Final revision
        guide['preparation_phases'].append({
            "phase": "Phase 4: Revision & Mock Tests",
            "duration": "Week 7-8",
            "focus": "Review all chapters, solve previous papers, timed practice",
            "critical_areas": subject.get('overall_rua_analysis', {}).get('critical_chapters', [])
        })
        
        return guide
    
    def get_weightage_distribution(self, subject_id: str) -> Dict:
        """Get chapter-wise and RUA-wise weightage distribution"""
        subject = self.get_subject_by_id(subject_id)
        if not subject:
            return {"error": "Subject not found"}
        
        distribution = {
            "subject": subject['subject_name'],
            "chapter_weightage": [],
            "rua_weightage": {
                "remember": 0,
                "understand": 0,
                "apply": 0
            },
            "focus_distribution": {
                "theoretical": 0,
                "practical": 0,
                "mixed": 0
            }
        }
        
        for chapter in subject['chapters']:
            chapter_info = {
                "chapter": chapter['chapter_name'],
                "weightage": chapter.get('weightage_percentage', 0),
                "hours": chapter.get('hours_allocated', 0),
                "importance": "Critical" if chapter.get('weightage_percentage', 0) >= 20 else
                            "High" if chapter.get('weightage_percentage', 0) >= 15 else
                            "Moderate" if chapter.get('weightage_percentage', 0) >= 10 else
                            "Standard"
            }
            distribution['chapter_weightage'].append(chapter_info)
        
        # Calculate RUA weightage from overall analysis
        if 'overall_rua_analysis' in subject:
            rua_dist = subject['overall_rua_analysis']
            distribution['rua_weightage']['remember'] = rua_dist.get('remember_distribution', '0%')
            distribution['rua_weightage']['understand'] = rua_dist.get('understand_distribution', '0%')
            distribution['rua_weightage']['apply'] = rua_dist.get('apply_distribution', '0%')
        
        return distribution
    
    def generate_chapter_study_plan(self, subject_id: str, chapter_number: int) -> Dict:
        """Generate detailed study plan for a specific chapter"""
        chapter = self.get_chapter_details(subject_id, chapter_number)
        if not chapter:
            return {"error": "Chapter not found"}
        
        study_plan = {
            "chapter": chapter['chapter_name'],
            "total_hours": chapter.get('hours_allocated', 0),
            "weightage": chapter.get('weightage_percentage', 0),
            "learning_objectives": chapter.get('learning_objectives', []),
            "topic_breakdown": [],
            "practice_requirements": []
        }
        
        for topic in chapter.get('topics', []):
            topic_plan = {
                "topic": topic['topic_name'],
                "subtopics": topic.get('subtopics', []),
                "study_phases": []
            }
            
            rua_mapping = topic.get('rua_mapping', {})
            
            # Remember phase
            if 'remember' in rua_mapping:
                topic_plan['study_phases'].append({
                    "phase": "Remember",
                    "concepts": rua_mapping['remember'].get('concepts', []),
                    "depth": rua_mapping['remember'].get('depth', 'N/A'),
                    "question_types": rua_mapping['remember'].get('question_types', [])
                })
            
            # Understand phase
            if 'understand' in rua_mapping:
                topic_plan['study_phases'].append({
                    "phase": "Understand",
                    "concepts": rua_mapping['understand'].get('concepts', []),
                    "depth": rua_mapping['understand'].get('depth', 'N/A'),
                    "question_types": rua_mapping['understand'].get('question_types', [])
                })
            
            # Apply phase
            if 'apply' in rua_mapping:
                topic_plan['study_phases'].append({
                    "phase": "Apply",
                    "concepts": rua_mapping['apply'].get('concepts', []),
                    "depth": rua_mapping['apply'].get('depth', 'N/A'),
                    "question_types": rua_mapping['apply'].get('question_types', [])
                })
                
                # Add to practice requirements
                study_plan['practice_requirements'].append({
                    "topic": topic['topic_name'],
                    "practice_type": topic.get('focus_type', 'Theoretical'),
                    "concepts": rua_mapping['apply'].get('concepts', [])
                })
            
            study_plan['topic_breakdown'].append(topic_plan)
        
        # Add recommendations
        study_plan['recommendations'] = chapter.get('rua_summary', {}).get('recommendations', [])
        
        return study_plan
    
    def find_missing_ruas(self, subject_id: str) -> Dict:
        """Identify chapters/topics with missing or incomplete RUA mappings"""
        subject = self.get_subject_by_id(subject_id)
        if not subject:
            return {"error": "Subject not found"}
        
        missing_analysis = {
            "subject": subject['subject_name'],
            "incomplete_chapters": [],
            "missing_rua_levels": {
                "remember": [],
                "understand": [],
                "apply": []
            },
            "low_depth_topics": []
        }
        
        for chapter in subject['chapters']:
            chapter_issues = []
            
            for topic in chapter.get('topics', []):
                rua_mapping = topic.get('rua_mapping', {})
                
                # Check for missing RUA levels
                if 'remember' not in rua_mapping:
                    missing_analysis['missing_rua_levels']['remember'].append({
                        "chapter": chapter['chapter_name'],
                        "topic": topic['topic_name']
                    })
                    chapter_issues.append(f"Missing 'Remember' RUA for {topic['topic_name']}")
                
                if 'understand' not in rua_mapping:
                    missing_analysis['missing_rua_levels']['understand'].append({
                        "chapter": chapter['chapter_name'],
                        "topic": topic['topic_name']
                    })
                    chapter_issues.append(f"Missing 'Understand' RUA for {topic['topic_name']}")
                
                if 'apply' not in rua_mapping:
                    missing_analysis['missing_rua_levels']['apply'].append({
                        "chapter": chapter['chapter_name'],
                        "topic": topic['topic_name']
                    })
                    chapter_issues.append(f"Missing 'Apply' RUA for {topic['topic_name']}")
                
                # Check for low depth
                for rua_level, rua_data in rua_mapping.items():
                    if rua_data.get('depth') == 'Low':
                        missing_analysis['low_depth_topics'].append({
                            "chapter": chapter['chapter_name'],
                            "topic": topic['topic_name'],
                            "rua_level": rua_level,
                            "current_depth": "Low"
                        })
            
            if chapter_issues:
                missing_analysis['incomplete_chapters'].append({
                    "chapter": chapter['chapter_name'],
                    "issues": chapter_issues
                })
        
        return missing_analysis
    
    def compare_chapters(self, subject_id: str, chapter1: int, chapter2: int) -> Dict:
        """Compare RUA mappings between two chapters"""
        ch1 = self.get_chapter_details(subject_id, chapter1)
        ch2 = self.get_chapter_details(subject_id, chapter2)
        
        if not ch1 or not ch2:
            return {"error": "One or both chapters not found"}
        
        comparison = {
            "chapter1": {
                "name": ch1['chapter_name'],
                "weightage": ch1.get('weightage_percentage', 0),
                "hours": ch1.get('hours_allocated', 0),
                "topics": len(ch1.get('topics', [])),
                "rua_summary": ch1.get('rua_summary', {})
            },
            "chapter2": {
                "name": ch2['chapter_name'],
                "weightage": ch2.get('weightage_percentage', 0),
                "hours": ch2.get('hours_allocated', 0),
                "topics": len(ch2.get('topics', [])),
                "rua_summary": ch2.get('rua_summary', {})
            },
            "comparison_insights": []
        }
        
        # Compare weightage
        if ch1.get('weightage_percentage', 0) > ch2.get('weightage_percentage', 0):
            comparison['comparison_insights'].append(
                f"{ch1['chapter_name']} has higher exam weightage ({ch1.get('weightage_percentage')}% vs {ch2.get('weightage_percentage')}%)"
            )
        elif ch2.get('weightage_percentage', 0) > ch1.get('weightage_percentage', 0):
            comparison['comparison_insights'].append(
                f"{ch2['chapter_name']} has higher exam weightage ({ch2.get('weightage_percentage')}% vs {ch1.get('weightage_percentage')}%)"
            )
        
        # Compare RUA coverage
        ch1_rua = ch1.get('rua_summary', {})
        ch2_rua = ch2.get('rua_summary', {})
        
        for rua_level in ['remember', 'understand', 'apply']:
            coverage_key = f"{rua_level}_coverage"
            ch1_coverage = ch1_rua.get(coverage_key, "Not covered")
            ch2_coverage = ch2_rua.get(coverage_key, "Not covered")
            
            if ch1_coverage != ch2_coverage:
                comparison['comparison_insights'].append(
                    f"{rua_level.capitalize()}: {ch1['chapter_name']} = {ch1_coverage}, {ch2['chapter_name']} = {ch2_coverage}"
                )
        
        return comparison
    
    def export_analysis_report(self, subject_id: str, output_format: str = 'json') -> str:
        """Export comprehensive analysis report"""
        analysis = self.analyze_rua_compliance(subject_id)
        
        if output_format == 'json':
            return json.dumps(analysis, indent=2, ensure_ascii=False)
        
        # Add more formats if needed (PDF, Excel, etc.)
        return json.dumps({"error": "Format not supported"})


# Standalone utility functions
def calculate_bloom_level_from_rua(rua_level: str) -> str:
    """Map RUA levels to Bloom's Taxonomy levels"""
    mapping = {
        'remember': 'Remember',
        'understand': 'Understand',
        'apply': 'Apply'
    }
    return mapping.get(rua_level.lower(), 'Unknown')


def get_question_type_for_rua(rua_level: str, marks: int) -> List[str]:
    """Suggest question types based on RUA level and marks"""
    if rua_level.lower() == 'remember':
        if marks <= 2:
            return ['MCQ', 'Fill in the blanks', 'True/False', 'One-word answers']
        else:
            return ['Short definitions', 'List items', 'State facts']
    
    elif rua_level.lower() == 'understand':
        if marks <= 4:
            return ['Short answer', 'Explain briefly', 'Describe']
        else:
            return ['Detailed explanation', 'Compare and contrast', 'Discuss']
    
    elif rua_level.lower() == 'apply':
        if marks <= 7:
            return ['Solve problems', 'Apply concepts', 'Calculate', 'Demonstrate']
        else:
            return ['Complex problem-solving', 'Design solutions', 'Create implementations', 'Comprehensive case studies']
    
    return ['General questions']


if __name__ == "__main__":
    # Example usage
    analyzer = SyllabusAnalyzer('syllabus_data.json')
    
    # Get RUA compliance analysis
    analysis = analyzer.analyze_rua_compliance('CS_DBMS')
    print(json.dumps(analysis, indent=2))
    
    # Get exam preparation guide
    guide = analyzer.get_exam_preparation_guide('CS_DBMS')
    print(json.dumps(guide, indent=2))
