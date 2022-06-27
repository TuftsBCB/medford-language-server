import sys
from typing import List, Tuple

from MEDFORD.medford import MFDMode as ValidationMode
from MEDFORD.medford import ValidationError
from MEDFORD.medford_detailparser import detailparser
from MEDFORD.medford_error_mngr import error_mngr
from MEDFORD.medford_detail import detail
from MEDFORD.medford_models import Entity, BCODMO
from MEDFORD.medford_BagIt import BagIt
from pygls.lsp.types import (
    Diagnostic,
    DiagnosticRelatedInformation,
    DiagnosticSeverity,
    Location,
    Position,
    Range,
)
from pygls.workspace import Document
from mfdls.medford_syntax import validate_syntax
from mfdls.server import logging


def validate_data(
    text_doc: Document, mode: ValidationMode
) -> Tuple[List[detail], List[Diagnostic]]:

    (details, diagnostics) = validate_syntax(text_doc)

    if not details:
        return (details, diagnostics)

    err_mngr = error_mngr("ALL", "LINE")
    parser = detailparser(details, err_mngr)
    final_dict = parser.export()
    try:
        if mode == ValidationMode.BCODMO:
            _ = BCODMO(**final_dict)
        elif mode == ValidationMode.BAGIT:
            _ = BagIt(**final_dict)
        else:
            _ = Entity(**final_dict)

    except ValidationError as e:
        _helper = sys.stdout
        sys.stdout = sys.stderr
        parser.parse_pydantic_errors(e, final_dict)
        sys.stdout = _helper
    else:
        return (details, [])

    logging.critical(parser.err_mngr._error_collection)

    return ([], [])

    #### #### #### #### #### #### #### #### ####
    #### #### #### SAVE FOR LATER #### #### ####
    #### #### #### #### #### #### #### #### ####

    # If the tokenization went okay, then validate the document and report errors
    # to the client log (not the server log)
    # else:
    #     parser = detailparser(details, err_mngr)
    #     final_dict = parser.export()
    #     p = {}
    #     try:
    #         p = Entity(**final_dict)
    # except ValidationError as e:
    #     helper = stdout
    #     stdout = stderr
    #     parser.parse_pydantic_errors(e, final_dict)
    #     stdout = helper
    #     ls.show_message_log(pformat(parser.err_mngr._error_collection))
    # else:
    #     # This shows a cute little popup
    #     ls.show_message("No errors found.")
