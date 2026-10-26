import json

with open(r'C:\Users\buzunar\.gemini\antigravity-ide\brain\fcfbab7e-5aa1-4945-a84f-f8c3888faae9\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if any(f'"step_index":{s}' in line for s in range(3015, 3027)):
            obj = json.loads(line)
            for tc in obj.get('tool_calls', []):
                if 'CodeContent' in tc.get('args', {}):
                    print("File:", tc['args']['TargetFile'])
                    print("Content:\n", tc['args']['CodeContent'])
