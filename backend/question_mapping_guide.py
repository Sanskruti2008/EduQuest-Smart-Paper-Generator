"""
Visual guide to understand question mapping
"""

print("=" * 70)
print("QUESTION MAPPING GUIDE")
print("=" * 70)

print("\nThe template has a specific structure:")
print("\n┌─────────────────────────────────────────┐")
print("│  SECTION 1 (Q1): 7 questions (A-G)     │")
print("│  • Position 1-7 → Q1_A to Q1_G         │")
print("│  • Typically 2 marks each               │")
print("└─────────────────────────────────────────┘")

print("\n┌─────────────────────────────────────────┐")
print("│  SECTIONS 2-6 (Q2-Q6): 4 questions each│")
print("│  • Q2: Position 8-11 → Q2_A to Q2_D    │")
print("│  • Q3: Position 12-15 → Q3_A to Q3_D   │")
print("│  • Q4: Position 16-19 → Q4_A to Q4_D   │")
print("│  • Q5: Position 20-23 → Q5_A to Q5_D   │")
print("│  • Q6: Position 24-27 → Q6_A to Q6_D   │")
print("│  • Typically 4 marks each               │")
print("└─────────────────────────────────────────┘")

print("\n" + "=" * 70)
print("EXAMPLES:")
print("=" * 70)

examples = [
    (5, ["Q1: 5 rows (A-E)", "Empty sections removed"]),
    (7, ["Q1: 7 rows (A-G complete)", "Empty sections removed"]),
    (10, ["Q1: 7 rows (A-G)", "Q2: 3 rows (A-C)", "Q3-Q6 removed"]),
    (15, ["Q1: 7 rows", "Q2: 4 rows", "Q3: 4 rows", "Q4-Q6 removed"]),
    (27, ["Q1: 7 rows", "Q2-Q6: 4 rows each", "All sections filled"]),
]

for count, result in examples:
    print(f"\n📝 If you have {count} questions:")
    for line in result:
        print(f"   → {line}")

print("\n" + "=" * 70)
print("HOW TO VERIFY:")
print("=" * 70)
print("""
1. Open your frontend and go to Review page
2. Check the "Total Questions" count
3. Export with "Professional Template" format
4. Check the terminal/console output - it will show:
   - How many questions were received
   - The mapping (Q1 → Q1_A, Q2 → Q1_B, etc.)
   - Final document statistics
   
5. Open the exported Word document and count:
   - How many sections are visible (Q.1, Q.2, etc.)
   - How many question rows in each section
   - Total should match your question count
""")

print("\n" + "=" * 70)
print("COMMON ISSUES:")
print("=" * 70)
print("""
❌ Document has fewer questions than expected
   → Check browser console (F12) to see what's being sent
   → Open inspect_data.html to see localStorage content
   
❌ Questions seem duplicated
   → Check if questions have duplicate text
   → Review the question order in Paper Builder
   
❌ Some questions are missing
   → Check if all questions were added to the paper
   → Verify questions array in localStorage
""")

print("\n" + "=" * 70)
