from docx import Document
import sys
import os
p = os.path.join(os.path.dirname(__file__), 'formatted_paper.docx')
try:
    doc = Document(p)
except Exception as e:
    print('ERROR_LOADING', e)
    sys.exit(1)

paras = [para.text for para in doc.paragraphs if para.text.strip()]
print('PARAGRAPHS_FOUND:', len(paras))
for i, text in enumerate(paras[:30], 1):
    print(f'--- PARA {i} ---')
    print(text)
