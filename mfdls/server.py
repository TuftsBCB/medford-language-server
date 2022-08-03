"""server.py

By: Liam Strand and Andrew Powers
On: Summer 2022

A server implementing the Language Server Protocol for the MEDFORD metadata
markup language. Validation is provided by Polina Shpilker's parser. LSP
bindings are provided by the pygls library.

"""
import logging
from typing import Optional, Union

from pygls.lsp.methods import (
    COMPLETION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_SAVE,
    HOVER
)
from pygls.lsp.types import (
    CompletionList,
    CompletionOptions,
    CompletionParams,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams,
    Hover,
    HoverParams
)
from pygls.server import LanguageServer

from mfdls.completions import (
    NO_COMPLETIONS,
    generate_macro_list,
    generate_major_token_list,
    generate_minor_token_list,
    is_requesting_minor_token,
)
from mfdls.medford_syntax import validate_syntax
from mfdls.medford_tokens import get_available_tokens
from mfdls.medford_validation import ValidationMode, validate_data
from mfdls.hover import resolve_hover

# Set up logging to pygls.log
logging.basicConfig(filename="pygls.log", filemode="w", level=logging.WARNING)


class MEDFORDLanguageServer(LanguageServer):
    """An object we can pass around that contains the connection to the text
    editor.
    """

    #### COMMANDS ####

    #### LS CONSTANTS ####

    CONFIGURATION_SECTION = "medfordServer"

    def __init__(self):
        self.validation_mode = ValidationMode.OTHER
        self.macros = {}
        self.tokens = get_available_tokens()
        super().__init__()


medford_server = MEDFORDLanguageServer()

#### #### #### LSP METHODS #### #### ####


@medford_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: MEDFORDLanguageServer, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    _generate_semantic_diagnostics(ls, params)


@medford_server.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: MEDFORDLanguageServer, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    _generate_semantic_diagnostics(ls, params)


@medford_server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(ls: MEDFORDLanguageServer, params: DidSaveTextDocumentParams):
    """Text document did save notification."""
    _generate_semantic_diagnostics(ls, params)


@medford_server.feature(COMPLETION, CompletionOptions(trigger_characters=["@", "-"]))
def completions(ls: MEDFORDLanguageServer, params: CompletionParams) -> CompletionList:
    """Request for completion items"""
    return _generate_completions(ls, params)

@medford_server.feature(HOVER)
def hover(ls: MEDFORDLanguageServer, params: HoverParams) -> Hover:
    return _generate_hover(ls, params)

#### #### #### CUSTOM COMMANDS #### #### ####


#### #### #### HELPERS #### #### ####


def _generate_syntactic_diagnostics(
    ls: MEDFORDLanguageServer,
    params: Union[
        DidChangeTextDocumentParams,
        DidSaveTextDocumentParams,
        DidOpenTextDocumentParams,
    ],
) -> None:
    """Wrapper around validation function to request and display Diagnostics
    Parameters: the Language Server, textDocument parameters
       Returns: none
       Effects: Displays diagnostics
    """

    # Get the current document from the text editor
    doc = ls.workspace.get_document(params.text_document.uri)

    # Get diagnostics on the document
    try:
        (details, diagnostics) = validate_syntax(doc)
    except ValueError as err:
        logging.warning(err)
        return

    # Publish the diagnostics
    ls.publish_diagnostics(doc.uri, diagnostics)

    # Store the defined macros in the languge server
    if details:
        ls.macros = details[0].macro_dictionary


def _generate_semantic_diagnostics(
    ls: MEDFORDLanguageServer,
    params: Union[
        DidSaveTextDocumentParams,
        DidOpenTextDocumentParams,
        DidChangeTextDocumentParams,
    ],
) -> None:
    """Wrapper around validation function to request and display Diagnostics
    Parameters: the Language Server, DidSaveTextDocument parameters
       Returns: none
       Effects: Displays diagnostics
    """
    doc = ls.workspace.get_document(params.text_document.uri)

    try:
        (details, diagnostics) = validate_data(doc, ls.validation_mode)
    except ValueError as err:
        logging.warning(err)
        return

    # Store the defined macros in the languge server
    if details:
        ls.macros = details[0].macro_dictionary

    ls.publish_diagnostics(doc.uri, diagnostics)

def _generate_hover(
    ls: MEDFORDLanguageServer, params: HoverParams
) -> Hover:

    doc = ls.workspace.get_document(params.text_document.uri)
    line = doc.lines[params.position.line]
    line_no = doc.lines.index(line)

    return resolve_hover(line, line_no)

def _generate_completions(
    ls: MEDFORDLanguageServer, params: CompletionParams
) -> CompletionList:
    """Generate a completion list to show to the client, calling different functions
    based on the RPC parameters.
    Parameters: The language server and the commpletion parameters (importantly the
                position of the completion trigger)
       Returns: A list of possible completinos
       Effects: None
    """

    doc = ls.workspace.get_document(params.text_document.uri)
    line = doc.lines[params.position.line]

    clist: Optional[CompletionList] = None

    if line[params.position.character - 1] == "@":
        if params.position.character == 1:
            clist = generate_major_token_list(ls.tokens)
        elif (
            line[params.position.character - 2] == "`" and params.position.character > 2
        ):
            clist = generate_macro_list(ls.macros, params.position.line)
    elif line[params.position.character - 1] == "-" and is_requesting_minor_token(
        line, params.position.character
    ):
        clist = generate_minor_token_list(ls.tokens, line, params.position.character)

    if clist:
        return clist
    else:
        return NO_COMPLETIONS
