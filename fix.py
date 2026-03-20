import sys
content = open('client/src/roadbook/cli.py', 'r', encoding='utf-8').read()
content = content.replace('run_parser.add_argument("--inputs-file", help="JSON inputs file path")', 'run_parser.add_argument("--inputs-file", help="JSON inputs file path")\n    run_parser.add_argument("--guide", action="store_true", help="Force Semantic Guide Mode instead of running script")')
open('client/src/roadbook/cli.py', 'w', encoding='utf-8').write(content)
