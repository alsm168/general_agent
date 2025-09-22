#!/usr/bin/env python3
"""Script to generate Mermaid syntax and HTML file for researcher agent graph."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from researcher_agent.graph import graph as researcher_agent_graph
from superviser_graph.graph import graph as superviser_agent

def generate_mermaid_syntax(out_name=r'superviser_agent'):
    """Generate and save Mermaid syntax for the researcher agent graph."""
    try:
        # Get the Mermaid syntax
        mermaid_syntax = superviser_agent.get_graph(xray=True).draw_mermaid()
        
        # Save the syntax to a file
        with open(f"/mnt/sdb/lsm/work/project/general_agent/{out_name}.mmd", "w") as f:
            f.write(mermaid_syntax)
        
        print(f"Mermaid syntax saved to {out_name}.mmd")
        print("\nMermaid syntax:")
        print(mermaid_syntax)
        
        # Generate HTML file
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{out_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .mermaid {{
            text-align: center;
            margin: 20px 0;
        }}
        .instructions {{
            background-color: #e9f7fe;
            border-left: 6px solid #2196F3;
            margin-bottom: 15px;
            padding: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{out_name}</h1>
        <div class="instructions">
            <p>This diagram shows the flow of the {out_name} graph. You can also view the raw Mermaid syntax in the <code>{out_name}.mmd</code> file.</p>
        </div>
        <div class="mermaid">
{mermaid_syntax}
        </div>
    </div>
    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
</body>
</html>"""
        
        # Save the HTML to a file
        with open(f"/mnt/sdb/lsm/work/project/general_agent/{out_name}.html", "w") as f:
            f.write(html_content)
        
        print("\nHTML file saved to researcher_agent_graph.html")
        print("You can open this file in a web browser to view the graph.")
        
        return True
    except Exception as e:
        print(f"Error generating Mermaid syntax: {e}")
        return False

if __name__ == "__main__":
    generate_mermaid_syntax()