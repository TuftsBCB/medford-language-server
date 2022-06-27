"""server.py

By: Liam Strand
On: June 2022

A server implementing the Language Server Protocol for the MEDFORD metadata
markup language. Validation is provided by Polina Shpilker's parser. LSP
bindings are provided by the pygls library.

"""
import logging
from typing import Union

from pygls.lsp.methods import (
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_SAVE,
)
from pygls.lsp.types import (
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams,
)
from pygls.server import LanguageServer

from mfdls.medford_syntax import validate_syntax
from mfdls.medford_validation import ValidationMode, validate_data

# Set up logging to pygls.log
logging.basicConfig(filename="pygls.log", filemode="w", level=logging.WARNING)


class MEDFORDLanguageServer(LanguageServer):
    """An object we can pass around that contains the connection to the text
    editor.

    Eventually, the commands that we register will end up in here.
    """

    def __init__(self):
        self.validation_mode = ValidationMode.BCODMO
        super().__init__()


medford_server = MEDFORDLanguageServer()


#### #### #### LSP METHODS #### #### ####


@medford_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: MEDFORDLanguageServer, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    _generate_syntactic_diagnostics(ls, params)


@medford_server.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: MEDFORDLanguageServer, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    _generate_syntactic_diagnostics(ls, params)


@medford_server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(ls: MEDFORDLanguageServer, params: DidSaveTextDocumentParams):
    """Text document did save notification."""
    _generate_semantic_diagnostics(ls, params)


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


def _generate_semantic_diagnostics(
    ls: MEDFORDLanguageServer,
    params: DidSaveTextDocumentParams,
) -> None:
    """Wrapper around validation function to request and display Diagnostics
    Parameters: the Language Server, DidSaveTextDocument parameters
       Returns: none
       Effects: Displays diagnostics
    """
    doc = ls.workspace.get_document(params.text_document.uri)

    (_, diagnostics) = validate_data(doc, ls.validation_mode)

    ls.publish_diagnostics(doc.uri, diagnostics)
