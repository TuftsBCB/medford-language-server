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
    MessageType,
)
from pygls.server import LanguageServer

from mfdls.medford_syntax import validate_syntax
from mfdls.medford_tokens import get_available_tokens
from mfdls.medford_validation import ValidationMode, validate_data
from mfdls.pip_helpers import pip_install, pip_uninstall, pip_upgrade

# Set up logging to pygls.log
logging.basicConfig(filename="pygls.log", filemode="w", level=logging.WARNING)


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
        self.tokens = get_available_tokens()
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
    ls.show_message("hello world")
    _generate_syntactic_diagnostics(ls, params)


# Does not work yet, commenting out for a merge
@medford_server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(ls: MEDFORDLanguageServer, params: DidSaveTextDocumentParams):
    """Text document did save notification."""
    _generate_syntactic_diagnostics(ls, params)


#### #### #### CUSTOM COMMANDS #### #### ####


@medford_server.command(MEDFORDLanguageServer.CMD_INSTALL_MFDLS)
async def install_mfdls(ls: MEDFORDLanguageServer, *_args):
    """Command to install mfdls"""
    if pip_install():
        ls.show_message("Successfully installed mfdls", MessageType.Info)
    else:
        ls.show_message("Unable to install mfdls", MessageType.Warning)


@medford_server.command(MEDFORDLanguageServer.CMD_UPDATE_MFDLS)
async def update_mfdls(ls: MEDFORDLanguageServer, *_args):
    """Command to update mfdls"""
    if pip_upgrade():
        ls.show_message("Successfully upgraded mfdls", MessageType.Info)
    else:
        ls.show_message("Unable to upgrade mfdls", MessageType.Warning)


@medford_server.command(MEDFORDLanguageServer.CMD_UNINSTALL_MFDLS)
async def uninstall_mfdls(ls: MEDFORDLanguageServer, *_args):
    """Command to uninstall mfdls"""
    if pip_uninstall():
        ls.show_message("Successfully uninstalled mfdls", MessageType.Info)
    else:
        ls.show_message("Unable to uninstall mfdls", MessageType.Warning)


#### #### #### HELPERS #### #### ####


def _generate_syntactic_diagnostics(
    ls: MEDFORDLanguageServer,
    params: Union[
        DidSaveTextDocumentParams,
        DidOpenTextDocumentParams,
        DidChangeTextDocumentParams,
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
    (details, diagnostics) = validate_syntax(doc)

    # Publish the diagnostics
    ls.publish_diagnostics(doc.uri, diagnostics)

    # Store the defined macros in the languge server, if we successfully parse the file
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

    (_, diagnostics) = validate_data(doc, ls.validation_mode)

    ls.publish_diagnostics(doc.uri, diagnostics)
