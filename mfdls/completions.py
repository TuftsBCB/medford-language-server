"""completions.py

By: Liam Strand and Andrew Powers
On: Summer 2022

A server implementing the Language Server Protocol for the MEDFORD metadata
markup language. Validation is provided by Polina Shpilker's parser. LSP
bindings are provided by the pygls library.

"""
from string import whitespace
from typing import Dict, List, Tuple

from pygls.lsp.types.language_features import CompletionItem, CompletionList


def generate_major_token_list(token_dict: Dict[str, List[str]]) -> CompletionList:
    clist = [CompletionItem(label=major) for major in token_dict.keys()]
    return CompletionList(is_incomplete=False, items=clist)


def generate_macro_list(macros: Dict[str, Tuple[int, str]]) -> CompletionList:
    clist = []
    for macro, replacement in macros.items():
        clist.append(CompletionItem(label=macro, detail=replacement[1]))

    return CompletionList(is_incomplete=False, items=clist)


def is_requesting_minor_token(line: str, pos: int) -> bool:
    subline = line[:pos]

    if subline[0] == "@":
        for char in subline[:-1]:
            if char in (whitespace + "-"):
                return False
        return True

    return False


def generate_minor_token_list(
    tokens: Dict[str, List[str]], line: str, pos: int
) -> CompletionList:
    subline = line[1 : pos - 1]

    if subline in tokens.keys():
        clist = [CompletionItem(label=minor) for minor in tokens[subline]]
        return CompletionList(is_incomplete=False, items=clist)
    else:
        return CompletionList(is_incomplete=False, items=[])
