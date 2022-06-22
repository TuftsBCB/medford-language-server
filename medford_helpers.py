"""medford_helpers.py

By: Liam Strand
On: June 2022



"""

# import MEDFORD.medford as medford
# import MEDFORD.medford_BagIt as medford_BagIt
import MEDFORD.medford_detail as medford_detail

# import MEDFORD.medford_detailparser as medford_detailparser
import MEDFORD.medford_error_mngr as medford_error_mngr

# import MEDFORD.medford_models as medford_models

from pygls.lsp.types import (
    Diagnostic,
    DiagnosticRelatedInformation,
    DiagnosticSeverity,
    Location,
    Position,
    Range,
)
from pygls.workspace import Document

import re

from typing import List, Tuple


def validate_syntax(
    text_doc: Document,
) -> Tuple[List[Diagnostic], List[medford_detail.detail]]:
    source = text_doc.source.splitlines()

    details = []
    diagnostics = []

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

    for row in err_mngr._syntax_err_coll.values():
        for e in row:
            diagnostics.append(_medford_error_to_diagnostic(e, source, text_doc.uri))

    return (details, diagnostics)


def _medford_error_to_diagnostic(
    error: medford_error_mngr.mfd_syntax_err, source: List[str], uri: str
) -> Diagnostic:

    lineno = error.lineno - 1
    etype = error.errtype
    line = source[lineno]
    msg = error.msg

    if etype == "unexpected_macro":
        macro = re.search("Unexpected macro '(\\S+)' on line", msg)[1]
        match = re.search(f"`@{macro}", line)
        return Diagnostic(
            range=Range(
                start=Position(line=lineno, character=match.start() + 2),
                end=Position(line=lineno, character=match.end()),
            ),
            severity=DiagnosticSeverity.Error,
            code=etype,
            source="MEDFORD",
            message=msg,
        )
    elif etype == "duplicated_macro":
        match = re.search("Duplicated macro '(\\S+)' on lines (\\d+)", msg)
        macro = match[1]
        first_occourance = int(match[2]) - 1
        first_match = re.search(f"`@{macro}", source[first_occourance])
        second_match = re.search(f"`@{macro}", line)

        return Diagnostic(
            range=Range(
                start=Position(
                    line=first_occourance, character=first_match.start() + 2
                ),
                end=Position(line=first_occourance, character=first_match.end()),
            ),
            severity=DiagnosticSeverity.Error,
            code=etype,
            source="MEDFORD",
            message=msg,
            related_information=[
                DiagnosticRelatedInformation(
                    location=Location(
                        uri=uri,
                        range=Range(
                            start=Position(line=lineno, character=second_match.start()),
                            end=Position(line=lineno, character=second_match.end()),
                        ),
                    ),
                    message=f"Earlier definition of macro",
                )
            ],
        )
    elif etype == "remaining_template":
        match = re.search("\[..\]", line)
        return Diagnostic(
            range=Range(
                start=Position(line=lineno, character=match.start()),
                end=Position(line=lineno, character=match.end()),
            ),
            severity=DiagnosticSeverity.Error,
            code=etype,
            source="MEDFORD",
            message=msg,
        )
    elif etype == "no_desc":
        macro = re.search("Novel token @(\\S+)", msg)[1]
        match = re.search(f"@{macro}", line)
        return Diagnostic(
            range=Range(
                start=Position(line=lineno, character=match.start() + 1),
                end=Position(line=lineno, character=match.end()),
            ),
            severity=DiagnosticSeverity.Error,
            code=etype,
            source="MEDFORD",
            message=msg,
        )
    elif etype == "wrong_macro_token":
        return Diagnostic(
            range=Range(
                start=Position(line=lineno, character=0),
                end=Position(line=lineno, character=2),
            ),
            severity=DiagnosticSeverity.Error,
            code=etype,
            source="MEDFORD",
            message=msg,
        )
    else:
        return Diagnostic(
            range=Range(
                start=Position(line=lineno, character=0),
                end=Position(line=lineno + 1, character=0),
            ),
            severity=DiagnosticSeverity.Error,
            code=etype,
            source="MEDFORD",
            message=msg,
        )

    #### #### #### #### #### #### #### #### ####
    #### #### #### SAVE FOR LATER #### #### ####
    #### #### #### #### #### #### #### #### ####

    # If the tokenization went okay, then validate the document and report errors
    # to the client log (not the server log)
    # else:
    #     parser = medford_detailparser.detailparser(details, err_mngr)
    #     final_dict = parser.export()
    #     p = {}
    #     try:
    #         p = medford_models.Entity(**final_dict)
    #     except medford.ValidationError as e:
    #         helper = stdout
    #         stdout = stderr
    #         parser.parse_pydantic_errors(e, final_dict)
    #         stdout = helper
    #         ls.show_message_log(pformat(parser.err_mngr._error_collection))
    #     else:
    #         # This shows a cute little popup
    #         ls.show_message("No errors found.")
