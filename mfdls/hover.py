from typing import List, Dict
from pygls.lsp.types.language_features import Hover, Position, Range

from mfdls.medford_tokens import get_available_tokens

NO_HOVER: Hover = Hover(contents = [])

def resolve_hover(line: str, line_no: int) -> Hover:
    """
    Handles a Hover request and produces necessary output.
        Parameters: The current line as a str and the current line number
        Returns: A Hover
        Effects: None
    """

    token_dict = get_available_tokens()
    if line.find(' ') == -1:
        return NO_HOVER
    if line[0] == '@':
        whitespace = line.find(' ')
        token = line[1:whitespace]
        if token.find('-') == -1:
            if token_dict.get(token, "Failed") == "Failed":
                return NO_HOVER
            else:
                return Hover(
                    contents=create_contents_major(token, token_dict),
                    range = Range(
                        start=Position(line=line_no, character=0),
                        end=Position(line=line_no, character=whitespace)
                        )
                )
        else:
            if token_dict.get(token[:token.find('-')], "Failed") == "Failed":
                return NO_HOVER
            else:
                return Hover(
                    contents=create_contents_minor(token, token_dict),
                    range = Range(
                        start=Position(line=line_no, character=0),
                        end=Position(line=line_no, character=whitespace)
                        )
                )
    else:
        return NO_HOVER

def create_contents_major(token: str, tokens_dict: Dict[str, List[str]]) -> List[str]:
    """
    Generates a contents property for the requested Hover of a Major Token.
        Parameters: The token to create the contents for and the token dictionary
        Returns: A formatted contents property
        Effects: None
    """
    minors = tokens_dict.get(token, "Failed")
    content_string = ["Major Token: @" + token, "Associated Minor Tokens: "]
    for minor in minors:
        if minors.index(minor) == len(minors) - 1:
            content_string[1] += minor
        else:
            content_string[1] += f"{minor}, "
    return content_string

def create_contents_minor(token: str, tokens_dict: Dict[str, List[str]]) -> str:
    """
    Generates a contents property for the requested Hover of a Minor Token.
        Parameters: The token to create the contents for and the token dictionary
        Returns: A formatted contents property
        Effects: None
    """
    major = token[0:token.find('-')]
    minors = tokens_dict.get(major, "Failed")
    content_string = f"Other minor tokens of @{major}: "

    if minors is None:
        return "Hover Resolve Issue"
    for minor in minors:
        if minors.index(minor) == len(minors) - 1:
            content_string += minor
        else:
            content_string += f"{minor}, "
    return content_string
