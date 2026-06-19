import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

log_path = r'C:\Users\tmanh\.gemini\antigravity\brain\b76bd65b-74f9-46a9-a0de-d2d425de4e96\.system_generated\logs\overview.txt'

with open(log_path, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        if 'render_erd.py' in line and 'write_to_file' in line:
            print(f"--- MATCH AT LINE {line_num} ---")
            try:
                data = json.loads(line)
                # Find the write_to_file tool call args
                for tc in data.get('tool_calls', []):
                    if tc.get('name') == 'write_to_file':
                        args = tc.get('args', {})
                        # If args is a string, load it
                        if isinstance(args, str):
                            args = json.loads(args)
                        print("TargetFile:", args.get('TargetFile'))
                        print("CodeContent:")
                        print(args.get('CodeContent'))
            except Exception as e:
                print("Error:", e)
