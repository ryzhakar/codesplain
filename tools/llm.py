"""Simple callback functions for Treeverse."""
import anthropic
from treeverse import FileNode
import re
from itertools import chain

# _MODEL = "claude-3-5-sonnet-20240620"
_MODEL = "claude-3-haiku-20240307"
_TEMP = 0.1
_TOKENS = 3000
_NEWLINE = '\n'

client = anthropic.Anthropic(max_retries=10)

with open('prompts/inductive_analysis.md', 'r') as apromptfile:
    analysis_prompt = apromptfile.read()

with open('prompts/abductive_synthesis.md', 'r') as spromptfile:
    synthesis_prompt = spromptfile.read()


def analysis(
    node: FileNode,
    system_prompt: str = analysis_prompt,
) -> dict:
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
    payload = _NEWLINE.join((
        _to_codeblock(file_metadata, lang='yaml'),
        _to_codeblock(file_content, lang='python'),
    ))
    return {
        'analysis': _get_anthropic_answer(
            system_prompt=system_prompt,
            payload=payload,
        )
    }


def synthesis(
    node: FileNode,
    system_prompt: str = synthesis_prompt
) -> dict:
    children_mapping = {
        child.file_name: child
        for child in node.child_nodes
    }
    children_analyses = list(filter(
        lambda pair: pair[-1] is not None,
        (
            (
                child.file_name,
                child.custom_data.get('accumulation_level', 0), 
                child.custom_data.get('analysis'),
            )
            for child in node.child_nodes
        )
    ))
    if not children_analyses:
        return {}
    if len(children_analyses) == 1:
        return node.custom_data
    accumulation_level = max(map(lambda triple: triple[1], children_analyses))
    raw_analysis_items = (
        (
            '====',
            (
                f'Accumulated {level}-level analysis for {filename}:'
                if analysis
                else f'Original analysis for {filename}:'
            ),
            _to_codeblock(children_mapping[filename].to_yaml(), lang='yaml'),
            _to_codeblock(analysis, lang='markdown'),
            _NEWLINE,
        )
        for filename, level, analysis in children_analyses
    )
    analysis_items = _NEWLINE.join(chain.from_iterable(raw_analysis_items))
    directory_item = _NEWLINE.join((
        f'Directory to analyze: {node.file_name}',
        _to_codeblock(node.file_info.to_yaml(), lang='yaml')
    ))
    payload = _NEWLINE.join((
        directory_item,
        _NEWLINE,
        analysis_items,
    ))
    return {'custom_data': {
        'analysis': _get_anthropic_answer(
            system_prompt=system_prompt,
            payload=payload,
        ),
        'accumulation_level': accumulation_level + 1
    }}

def _get_anthropic_answer(
    *,
    system_prompt: str,
    payload: str,
) -> str:
    message = client.messages.create(
        model=_MODEL,
        max_tokens=_TOKENS,
        temperature=_TEMP,
        system=system_prompt,
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
    return message.content[0].text

def _to_codeblock(content: str, lang: str = 'markdown') -> str:
    return f'```{lang}\n{content}\n```'
