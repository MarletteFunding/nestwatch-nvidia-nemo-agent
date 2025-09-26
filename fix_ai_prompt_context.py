#!/usr/bin/env python3
"""
Fix AI_PROMPT_CONTEXT.md specific issues
"""

def fix_ai_prompt_context():
    """Fix AI_PROMPT_CONTEXT.md file."""
    filepath = '/Users/stephen.kerns/Desktop/sre-tools/NeMo-Agent-Toolkit-develop/AI_PROMPT_CONTEXT.md'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Remove trailing spaces
        line = line.rstrip()
        
        # Fix specific issues
        if line == '### **Frontend (Next.js)**' and i < len(lines) - 1 and lines[i+1].strip() == '':
            fixed_lines.append(line)
            fixed_lines.append('')
            # Skip the extra blank line
            continue
        elif line == '### **Backend (Python FastAPI)**' and i < len(lines) - 1 and lines[i+1].strip() == '':
            fixed_lines.append(line)
            fixed_lines.append('')
            # Skip the extra blank line
            continue
        elif line == '### **Data Sources**' and i < len(lines) - 1 and lines[i+1].strip() == '':
            fixed_lines.append(line)
            fixed_lines.append('')
            # Skip the extra blank line
            continue
        elif line.startswith('```') and not line.startswith('```text') and not line.startswith('```python') and not line.startswith('```bash'):
            # Add language to fenced code blocks
            if line == '```':
                fixed_lines.append('```text')
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    
    print("✅ Fixed AI_PROMPT_CONTEXT.md")

if __name__ == '__main__':
    fix_ai_prompt_context()
