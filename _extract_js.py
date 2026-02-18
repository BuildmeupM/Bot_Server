"""Extract JS from auditcheck.html into separate file"""
import os

html_path = r'c:\Users\USER\Desktop\github\Bot_Server\templates\auditcheck.html'
js_path = r'c:\Users\USER\Desktop\github\Bot_Server\static\js\auditcheck.js'

# Ensure directory exists
os.makedirs(os.path.dirname(js_path), exist_ok=True)

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Lines 1575-9931 (1-indexed) = indices 1574-9930 (0-indexed)
# Line 1574 is "<script>" and line 9932 is "</script>"
# We want the content BETWEEN the tags: lines 1575-9931 (content only)
js_lines = lines[1574:9931]  # 0-indexed: 1574 = line 1575, 9930 = line 9931

with open(js_path, 'w', encoding='utf-8') as f:
    f.writelines(js_lines)

print(f"Extracted {len(js_lines)} lines to {js_path}")
print(f"First line: {js_lines[0].strip()[:80]}")
print(f"Last line: {js_lines[-1].strip()[:80]}")
