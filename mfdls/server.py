"""server.py

By: Liam Strand
On: June 2022

A server implementing the Language Server Protocol for the MEDFORD metadata
markup language. Validation is provided by Polina Shpilker's parser. LSP
bindings are provided by the pygls library.

"""
import logging
from typing import Union, Optional

from pygls.lsp.methods import (  # TEXT_DOCUMENT_DID_SAVE,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    COMPLETION,
)
from pygls.lsp.types import (
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams,
    MessageType,
    CompletionItem,
    CompletionList,
    CompletionParams,
    CompletionOptions
)
from pygls.server import LanguageServer

from mfdls.medford_syntax import validate_syntax
from mfdls.medford_validation import ValidationMode, validate_data
from mfdls.pip_helpers import pip_install, pip_uninstall, pip_upgrade
from mfdls.medford_tokens import get_available_tokens, _get_minor_tokens, _extract_minors_from_def

# Set up logging to pygls.log
logging.basicConfig(filename="pygls.log", filemode="w", level=logging.INFO)


class MEDFORDLanguageServer(LanguageServer):
    """An object we can pass around that contains the connection to the text
    editor.
    """

    #### COMMANDS ####

    CMD_INSTALL_MFDLS = "installMFDLS"
    CMD_UPDATE_MFDLS = "updateMFDLS"
    CMD_UNINSTALL_MFDLS = "uninstallMFDLS"

    #### LS CONSTANTS ####

    CONFIGURATION_SECTION = "medfordServer"

    def __init__(self):
        self.validation_mode = ValidationMode.OTHER
        self.macros = {}
        super().__init__()


medford_server = MEDFORDLanguageServer()


#### #### #### LSP METHODS #### #### ####


@medford_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: MEDFORDLanguageServer, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    _generate_syntactic_diagnostics(ls, params)


@medford_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: MEDFORDLanguageServer, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    _generate_syntactic_diagnostics(ls, params)

#For now doesn't return user-defined macros or minor tags.
@medford_server.feature(COMPLETION, CompletionOptions(trigger_characters=['@']))
def completions(params: Optional[CompletionParams] = None) -> CompletionList:
    """Returns completion items."""
    tokens = get_available_tokens()
    return tokens.keys()


#### #### #### HELPERS #### #### ####


def _generate_syntactic_diagnostics(
    ls: MEDFORDLanguageServer,
    params: Union[DidOpenTextDocumentParams, DidChangeTextDocumentParams],
) -> None:
    """Wrapper around validation function to request and display Diagnostics
    Parameters: the Language Server, textDocument parameters
       Returns: none
       Effects: Displays diagnostics
    """

    # Get the current document from the text editor
    doc = ls.workspace.get_document(params.text_document.uri)

    # Get diagnostics on the document
    (_, diagnostics) = validate_syntax(doc)

    # Publish those diagnostics
    ls.publish_diagnostics(doc.uri, diagnostics)