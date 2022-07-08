"""medford_validation.py

By: Liam Strand
On: June 2022

Provides a LSP-compatable interface into the semantic validation aspects of the
MEDFORD parser. Currently does not generate Diagnostic objects, only prints
to the server's output.
TODO: Parse medford errors into Diagnostics.
"""
import sys
from typing import List, Tuple

from MEDFORD.medford import MFDMode as ValidationMode
from MEDFORD.medford import ValidationError
from MEDFORD.medford_BagIt import BagIt
from MEDFORD.medford_detail import detail
from MEDFORD.medford_detailparser import detailparser
from MEDFORD.medford_error_mngr import error_mngr, mfd_err
from MEDFORD.medford_models import BCODMO, Entity
from pygls.lsp.types.basic_structures import (
    Diagnostic,
    DiagnosticSeverity,
    Position,
    Range,
)
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
    # to parse it
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

    errors = parser.err_mngr.return_errors()

    diagnostics = []

    for error_list in errors.values():
        for error in error_list:
            diagnostics.append(_parse_medford_error(error))


    return ([], diagnostics)


def _parse_medford_error(err: mfd_err) -> Diagnostic:

    line_number = err.line - 1
    error_message = err.msg
    error_type = err.errtype

    # pylint: disable-next=R0801
    diag = Diagnostic(
        range=Range(
            start=Position(line=line_number, character=0),
            end=Position(line=line_number + 1, character=0),
        ),
        severity=DiagnosticSeverity.Error,
        code=error_type,
        source="MEDFORD",
        message=error_message,
    )

    return diag
