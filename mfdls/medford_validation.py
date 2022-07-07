"""medford_validation.py

By: Liam Strand
On: June 2022

Provides a LSP-compatable interface into the semantic validation aspects of the
MEDFORD parser. Currently does not generate Diagnostic objects, only prints
to the server's output.
TODO: Parse medford errors into Diagnostics.
"""
import logging
import sys
from typing import List, Tuple

from MEDFORD.medford import MFDMode as ValidationMode
from MEDFORD.medford import ValidationError
from MEDFORD.medford_BagIt import BagIt
from MEDFORD.medford_detail import detail
from MEDFORD.medford_detailparser import detailparser
from MEDFORD.medford_error_mngr import error_mngr
from MEDFORD.medford_models import BCODMO, Entity
from pygls.lsp.types.basic_structures import Diagnostic
from pygls.workspace import Document

from mfdls.medford_syntax import validate_syntax


def validate_data(
    text_doc: Document, mode: ValidationMode
) -> Tuple[List[detail], List[Diagnostic]]:
    """Performs a semantic (and syntactic) validation on a text document
    Parameters: A text document to verify, and the mode to validate in
       Returns: A tuple containing the tokenized syntax, and a list of any
                Diagnostics that should be sent to the client
       Effects: Can optionally send Diagnostics to the client, or show a
                "success" notification.
    """
    (details, diagnostics) = validate_syntax(text_doc)

    if not details:
        return (details, diagnostics)

    err_mngr = error_mngr("ALL", "LINE")
    parser = detailparser(details, err_mngr)
    final_dict = parser.export()

    # Pydantic is going to spew out an error here, it's the parser's job
    # to parser it
    try:
        if mode == ValidationMode.BCODMO:
            _ = BCODMO(**final_dict)
        elif mode == ValidationMode.BAGIT:
            _ = BagIt(**final_dict)
        else:
            _ = Entity(**final_dict)

    # We have to do the stdout/stderr song and dance because parse_pydantic_errors
    # prints to stdout and we need to keep that channel clear of non-LSP
    # communication. parse_pydantic_errors loads the error manager's
    # _error_collection with the errors it finds.
    except ValidationError as err:
        _helper = sys.stdout
        sys.stdout = sys.stderr
        parser.parse_pydantic_errors(err, final_dict)
        sys.stdout = _helper
    else:
        return (details, [])

    # Also, there is no other way to get this collection right now so disable
    # the check until the API is changed.
    # pylint: disable-next=W0212
    errors = parser.err_mngr.return_errors()

    for error in errors:
        _parse_medford_error(error)

    return ([], [])

def _parse_medford_error(error: ValidationError):
    logging.critical(repr(error))
