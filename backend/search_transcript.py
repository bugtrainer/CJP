import json

transcript_path = r"C:\Users\raham\.gemini\antigravity\brain\dccbf099-35d3-4d5a-9cd0-c61bd71eb298\.system_generated\logs\transcript.jsonl"

found = False
with open(transcript_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        data = json.loads(line)
        content = str(data.get('content', ''))
        tool_calls = str(data.get('tool_calls', ''))
        full_text = content + " " + tool_calls
        
        if 'railway' in full_text.lower() or 'postgresql' in full_text.lower() or 'database_url' in full_text.lower() or 'cjphub.com' in full_text.lower():
            # Print matching fragments
            for word in full_text.split():
                if any(x in word.lower() for x in ['railway', 'postgresql', 'database', 'cjphub']):
                    print(f"Line {i} match: {word}")
                    found = True

if not found:
    print("No matches found in transcript.")
