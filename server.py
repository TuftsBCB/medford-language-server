"""server.py

By: Liam Strand
On: June 2022

A server implementing the Language Server Protocol for the MEDFORD metadata
markup language. Validation is provided by Polina Shpilker's parser. LSP
bindings are provided by the pygls library.

"""
from sys import stderr, stdout
from timeit import default_timer
import typing
from pprint import pformat

from pygls.lsp.methods import TEXT_DOCUMENT_DID_CHANGE, TEXT_DOCUMENT_DID_OPEN
from pygls.lsp.types import (
    Diagnostic,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
)
from pygls.server import LanguageServer


import MEDFORD.medford as medford
import MEDFORD.medford_detailparser as medford_detailparser
import MEDFORD.medford_detail as medford_detail
import MEDFORD.medford_models as medford_models

# import MEDFORD.medford_BagIt as medford_BagIt
import MEDFORD.medford_error_mngr as medford_error_mngr

# The INFO logging level shows most messages passed between the server
# and the client
import logging

logging.basicConfig(filename="pygls.log", filemode="w", level=logging.INFO)


class MEDFORDLanguageServer(LanguageServer):
    def __init__(self):
        super().__init__()


medford_server = MEDFORDLanguageServer()


def _validate(
    ls: MEDFORDLanguageServer,
    params: DidOpenTextDocumentParams | DidChangeTextDocumentParams,
) -> None:
    """Wrapper around validation function to request and display Diagnostics
    Parameters: the Language Server, textDocument parameters
       Returns: none
       Effects: Displays diagnostics
    """

    # We start the timer because I was currious how long this whole process took
    ls.show_message_log("Validating MEDFORD!")
    start = default_timer()

    # Get the current document from the text editor
    text_doc = ls.workspace.get_document(params.text_document.uri)
    source = text_doc.source.splitlines()

    # Get diagnostics on the document
    diagnostics = _validate_medford(ls, source)

    # Display diagnostics
    ls.publish_diagnostics(text_doc.uri, diagnostics)

    # Stop the timer and log
    end = default_timer()
    ls.show_message_log(end - start)


def _validate_medford(ls: MEDFORDLanguageServer, source: list[str]) -> list[Diagnostic]:
    """Validates a MEDFORD file and generates diagnostics
    Parameters: The language server and a list of lines comprising the text
                of the document
       Returns: A list of Diagnostics
       Effects: none

    TODO: Parse the parser errors and convert to LSP diagnostics
    """
    diagnostics = []
    details = []

    # The medford parser's macro dict is not reset or reinitilized
    # when the parser starts, so we take care of that here.
    medford_detail.detail.macro_dictionary = {}

    # Set up the error manager
    err_mngr = medford_error_mngr.error_mngr("ALL", "LINES")

    # Tokenize the document
    dr = None
    for i, line in enumerate(source):
        if line.strip() != "":
            dr = medford_detail.detail.FromLine(line, i + 1, dr, err_mngr)
            if isinstance(dr, medford_detail.detail_return):
                if dr.is_novel:
                    details.append(dr.detail)

    # If something really went wrong, don't attempt to parse, just log the
    # the syntax errors
    if err_mngr.has_major_parsing:
        ls.show_message_log(pformat(err_mngr._syntax_err_coll))

    # If the tokenization went okay, then validate the document and report errors
    # to the client log (not the server log)
    else:
        parser = medford_detailparser.detailparser(details, err_mngr)
        final_dict = parser.export()
        p = {}
        try:
            p = medford_models.Entity(**final_dict)
        except medford.ValidationError as e:
            helper = stdout
            stdout = stderr
            parser.parse_pydantic_errors(e, final_dict)
            stdout = helper
            ls.show_message_log(pformat(parser.err_mngr._error_collection))
        else:
            # This shows a cute little popup
            ls.show_message("No errors found.")

    return diagnostics


@medford_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: MEDFORDLanguageServer, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    _validate(ls, params)


@medford_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: MEDFORDLanguageServer, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    _validate(ls, params)
