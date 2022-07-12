"""completions.py

By: Andrew Powers and Liam Strand
On: Summer 2022

A series of funtions that takes the custom data structures that hold the tokens
and macros found in the document and parser, and reports them to the text editor
as completion lists.

"""
from string import whitespace
from typing import Dict, List, Optional, Tuple

from pygls.lsp.types.language_features import CompletionItem, CompletionList

NO_COMPLETIONS = CompletionList(is_incomplete=False, items=[])


def generate_major_token_list(token_dict: Dict[str, List[str]]) -> CompletionList:
    """Generate a completion list of the defined major tokens
    Parameters: The current token dictionary
       Returns: The token dict's major tokens in CompletionList form
       Effects: None
    """
    clist = [CompletionItem(label=major) for major in token_dict.keys()]
    return CompletionList(is_incomplete=False, items=clist)


def generate_macro_list(macros: Dict[str, Tuple[int, str]]) -> CompletionList:
    """Generate a completion list of defined macros, along with their definitions
    Parameters: The working macro dictionary
       Returns: The macro dictionary in CompletionList form
       Effects: None
    """

    clist = []
    for macro, replacement in macros.items():
        clist.append(CompletionItem(label=macro, detail=replacement[1]))

    return CompletionList(is_incomplete=False, items=clist)


def is_requesting_minor_token(line: str, pos: int) -> bool:
    """Determine if an instance of the "-" character is cause to get minor token completions
    Parameters: The line and position of the querey
       Returns: True if we should emit completions, false otherwise
       Effects: None
    """
    subline = line[:pos]

    if subline[0] == "@":
        for char in subline[:-1]:
            if char in (whitespace + "-"):
                return False
        return True

    return False


def generate_minor_token_list(
    tokens: Dict[str, List[str]], line: str, pos: int
) -> Optional[CompletionList]:
    """Handle a request for the minor tokens associated with a major token
    Parameters: The working token dictionary,
                the line that triggered the completion request,
                and the position in that line where the request was triggered
       Returns: If the major token is defined, a CompletionList with the minor tokens
                None if the major token is user-defined.
       Effects: None
    """
    subline = line[1 : pos - 1]

    if subline in tokens.keys():
        clist = [CompletionItem(label=minor) for minor in tokens[subline]]
        return CompletionList(is_incomplete=False, items=clist)
    else:
        return CompletionList(is_incomplete=False, items=[])
