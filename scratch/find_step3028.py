import json

with open(r'C:\Users\buzunar\.gemini\antigravity-ide\brain\fcfbab7e-5aa1-4945-a84f-f8c3888faae9\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if '"step_index":3028' in line or '"step_index":3027' in line or '"step_index":3026' in line:
            obj = json.loads(line)
            for tc in obj.get('tool_calls', []):
                if 'CodeContent' in tc.get('args', {}):
                    print("File:", tc['args']['TargetFile'])
                    print("Content:\n", tc['args']['CodeContent'])
