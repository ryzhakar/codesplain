from rich.panel import Panel
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.syntax import Syntax
from treeverse import FileNode
import re


def manual_analysis(node: FileNode) -> dict:
    console = Console()
    
    if not node.file_info.is_text_file:
        return {}
    
    if node.file_name.startswith('__'):
        return {}
    
    with open(node.file_info.full_path, 'r') as file:
        file_content = file.read()
    
    file_metadata = node.file_info.to_yaml()
    
    is_empty = re.match(r'^\s*$', file_content)
    if is_empty:
        return {}
    
    instructions = """
    # Manually Analyze Code
    
    - Review the file metadata and content below
    - Enter your analysis on multiple lines
    - Press Enter for a new line
    - To finish, press Ctrl+D (Unix) or Ctrl+Z (Windows)
    - Your input will be displayed for confirmation
    """
    
    console.print(Panel(Markdown(instructions), title="Instructions", expand=False))
    
    # Display file metadata
    console.print(Panel(Syntax(file_metadata, "yaml"), title="File Metadata", expand=False))
    
    # Display file content
    console.print(Panel(Syntax(file_content, "python"), title="File Content", expand=False))
    
    lines = []
    try:
        while True:
            line = Prompt.ask("Enter your analysis", console=console)
            lines.append(line)
    except EOFError:
        pass
    
    user_analysis = "\n".join(lines).strip()
    
    if user_analysis:
        console.print("\nYour analysis:", style="bold green")
        console.print(Panel(user_analysis, title="User Analysis", expand=False))
        
        confirm = Prompt.ask("Is this analysis correct? [y/n]")
        if confirm.lower() != 'y':
            return manual_analysis(node)  # Recursively call the function if not confirmed
    else:
        console.print("No analysis provided. Please try again.", style="bold red")
        return manual_analysis(node)  # Recursively call the function if no input
    
    return {'analysis': user_analysis}
