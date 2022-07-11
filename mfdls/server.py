"""server.py

By: Liam Strand
On: June 2022

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
)
from pygls.lsp.types import (
    CompletionItem,
    CompletionList,
    CompletionOptions,
    CompletionParams,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams,
    MessageType,
)
from pygls.server import LanguageServer

from mfdls.medford_syntax import validate_syntax
from mfdls.medford_tokens import get_available_tokens
from mfdls.medford_validation import ValidationMode, validate_data

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
        super().__init__()


# Here we can generate all of the tokens once on compilation to increase performance
def _generate_completion_list() -> CompletionList:
    tokens = get_available_tokens()

    clist = []
    for token, minors in tokens.items():
        clist.append(CompletionItem(label=token))
        for value in minors:
            clist.append(CompletionItem(label=token + "-" + value))
    return CompletionList(is_incomplete=False, items=clist)


medford_server = MEDFORDLanguageServer()
completion_list = _generate_completion_list()

#### #### #### LSP METHODS #### #### ####


@medford_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: MEDFORDLanguageServer, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    _generate_semantic_diagnostics(ls, params)


@medford_server.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: MEDFORDLanguageServer, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    _generate_semantic_diagnostics(ls, params)


@medford_server.feature(COMPLETION, CompletionOptions(trigger_characters=["@"]))
def completions(_params: Optional[CompletionParams] = None) -> CompletionList:
    """Returns completion items."""
    # Since we gathered the tokens on launch, we can just refer our completions to those.
    return completion_list


@medford_server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(ls: MEDFORDLanguageServer, params: DidSaveTextDocumentParams):
    """Text document did save notification."""
    _generate_semantic_diagnostics(ls, params)


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
    except(ValueError):
        ls.show_message("There was an error parsing the file. Review your recent changes.", MessageType.Warning)
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
        (_, diagnostics) = validate_data(doc, ls.validation_mode)
    except(ValueError):
        ls.show_message("There was an error parsing the file. Review your recent changes.", MessageType.Warning)
        return

    ls.publish_diagnostics(doc.uri, diagnostics)
