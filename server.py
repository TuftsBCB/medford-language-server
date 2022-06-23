"""server.py

By: Liam Strand
On: June 2022

A server implementing the Language Server Protocol for the MEDFORD metadata
markup language. Validation is provided by Polina Shpilker's parser. LSP
bindings are provided by the pygls library.

"""
from typing import Union

from pygls.lsp.methods import TEXT_DOCUMENT_DID_CHANGE, TEXT_DOCUMENT_DID_OPEN
from pygls.lsp.types import (
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
)
from pygls.server import LanguageServer

from .medford_helpers import validate_syntax

# The INFO logging level shows most messages passed between the server
# and the client
import logging

logging.basicConfig(filename="pygls.log", filemode="w", level=logging.INFO)


class MEDFORDLanguageServer(LanguageServer):
    def __init__(self):
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

    (_, diagnostics) = validate_syntax(doc)

    ls.publish_diagnostics(doc.uri, diagnostics)
