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
from pygls.lsp.types import Diagnostic
from pygls.workspace import Document

from mfdls.medford_syntax import validate_syntax


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
    logging.critical(parser.err_mngr._error_collection)

    return ([], [])
