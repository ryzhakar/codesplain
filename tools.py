
"""Simple callback functions for Treeverse."""
import anthropic
from treeverse import FileNode

_MODEL = "claude-3-5-sonnet-20240620"
_TEMP = 0.6
_TOKENS = 3021

client = anthropic.Anthropic()

with open('prompts/single_file_analysis.md', 'r') as promptfile:
    single_file_prompt = promptfile.read()

def llm_analysis(node: FileNode) -> dict:
    """Add line count to the node's custom data."""
    if not node.file_info.is_text_file:
        return {}
    with open(node.file_info.full_path, 'r') as file:
        file_content = file.read()
    file_metadata = node.file_info.to_yaml()
    metadata_block = f'```yaml\n{file_metadata}\n```'
    code_block = f'```python\n{file_content}\n```'
    payload = f'{metadata_block}\n{code_block}'
    message = client.messages.create(
        model=_MODEL,
        max_tokens=_TOKENS,
        temperature=_TEMP,
        system=single_file_prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": payload,
                    }
                ]
            }
        ]
    )
    message = message.content[0].text
    return {'analysis': message}


# def reduce_total_lines(node: FileNode) -> dict:
#     """Calculate total line count in the tree."""
#     parent_lines = node.custom_data.get('lines', 0)
#     children_lines = sum(
#         child.custom_data.get('lines', 0)
#         for child in node.child_nodes
#     )
#     return {'custom_data': {'lines': parent_lines + children_lines}}
