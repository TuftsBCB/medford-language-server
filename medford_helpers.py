"""medford_helpers.py

By: Liam Strand
On: June 2022

Provides a LSP-compatable interface into the medford parser. Only currently
supports reporting on syntax errors.

# TODO line 216
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

# Type annotations are super helpful, but we need to be 3.8 compatable, so
# we use the typing versions of the types instead of the builtin ones.
from typing import List, Tuple

SYNTAX_ERR_UNEXPECTED_MACRO = "unexpected_macro"
SYNTAX_ERR_DUPLICATED_MACRO = "duplicated_macro"
SYNTAX_ERR_REMAINING_TEMPLATE = "remaining_template"
SYNTAX_ERR_NO_DESCRIPTION = "no_desc"
SYNTAX_ERR_WRONG_MACRO_TOKEN = "wrong_macro_token"

def validate_syntax(
    text_doc: Document,
) -> Tuple[List[medford_detail.detail], List[Diagnostic]]:
    """ Evaluates the syntax of a medford file and generates a token list and
    diagnostic list
    Parameters: A text document reference
    Returns: A tuple containing the tokens and the diagnostics
    Effects: None
    """
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

    # Convert the medford parser format errors into LSP format Diagnostics
    for row in err_mngr._syntax_err_coll.values():
        for e in row:
            diagnostics.append(_medford_syntax_error_to_diagnostic(e, source, text_doc.uri))

    # Return both the tokenized file, and the diagnostics.
    return (details, diagnostics)


def _medford_syntax_error_to_diagnostic(
    error: medford_error_mngr.mfd_syntax_err, source: List[str], uri: str
) -> Diagnostic:
    """Converts a medford parser format syntax error to a LSP diagnostic
    Parameters: A medford syntax error, the source document, and the document's uri
       Returns: A LSP diagnostic containing the information in the syntax error
       Effects: None
    """
    # Extract critical information we are likely to use later
    line_number = error.lineno - 1
    error_type = error.errtype
    line_text = source[line_number]
    error_message = error.msg

    # For each error, we need to extract some information from the error message
    # generated by the medford parser. We use a regular expression to extract this,
    # then we generate another regular expression that parses the erronious line
    # and finds exactly where in that line the error originates.

    # The Diagnostic object is fairly complicated, documentation is in the LSP
    # specification at microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#diagnostic
    # and the actual python definition is at pygls/lsp/types/basic_structures.py on line 268.
    # Both of those resources have links to their nested objects.

    # If we were using python 3.10, we would us a match, but we need to support
    # 3.8+, so we use a big if elif block.

    # The other branches are very similar to this first one, so only this first 
    # branch will be heavily documented. Other branches will be documented in their
    # novelty relative to this first branch
    if error_type == SYNTAX_ERR_UNEXPECTED_MACRO:

        # Scan through the error message, looking for the macro name
        macro = re.search("Unexpected macro '(\\S+)' on line", error_message)[1]

        # Scan through the erronious line, looking for the macro's position
        match = re.search(f"`@{macro}", line_text)

        # Start generating the Diagnostic
        return Diagnostic(

            # The first member, the range, describes the location of the syntax
            # error. It is comprised of two Positions, which are line:character
            # locations in a file.
            range=Range( 

                # The +2 offset is to exclude the `@ from the error squiggle
                start=Position(line=line_number, character=match.start() + 2),
                end=Position(line=line_number, character=match.end()),
            ),

            # The severity for all of the messages are Error because they
            # make the MEDFORD file invalid.
            severity=DiagnosticSeverity.Error,

            # The error code is the same as the error_type because it is a unique
            # identifier to this kind of error.
            code=error_type,

            # The source tells the user where the error is coming from. In this
            # case, the error is coming from the MEDFORDness of the file.
            source="MEDFORD",

            # The error message is passed through to be presented to the user.
            message=error_message,
        )
    elif error_type == SYNTAX_ERR_UNEXPECTED_MACRO:
        match = re.search("Duplicated macro '(\\S+)' on lines (\\d+)", error_message)
        macro = match[1]
        first_occourance = int(match[2]) - 1

        # For this error, we also look for the othe occourance of the macro,
        # so that we can reference it in the Diagnostic.
        first_match = re.search(f"`@{macro}", source[first_occourance])
        second_match = re.search(f"`@{macro}", line_text)

        return Diagnostic(
            range=Range(
                start=Position(
                    line=first_occourance, character=first_match.start() + 2
                ),
                end=Position(line=first_occourance, character=first_match.end()),
            ),
            severity=DiagnosticSeverity.Error,
            code=error_type,
            source="MEDFORD",
            message=error_message,

            # The related information points to the prior "probably correct"
            # macro definition.
            related_information=[
                DiagnosticRelatedInformation(
                    location=Location(
                        uri=uri,
                        range=Range(
                            start=Position(line=line_number, character=second_match.start()),
                            end=Position(line=line_number, character=second_match.end()),
                        ),
                    ),
                    message=f"Earlier definition of macro",
                )
            ],
        )
    elif error_type == SYNTAX_ERR_REMAINING_TEMPLATE:

        # This scan is much simpler because we only need to look for this
        # sequence of characters in the erronious line.
        match = re.search("\[..\]", line_text)
        return Diagnostic(
            range=Range(
                start=Position(line=line_number, character=match.start()),
                end=Position(line=line_number, character=match.end()),
            ),
            severity=DiagnosticSeverity.Error,
            code=error_type,
            source="MEDFORD",
            message=error_message,
        )
    elif error_type == SYNTAX_ERR_NO_DESCRIPTION:
        macro = re.search("Novel token @(\\S+)", error_message)[1]
        match = re.search(f"@{macro}", line_text)
        return Diagnostic(
            range=Range(
                start=Position(line=line_number, character=match.start() + 1),
                end=Position(line=line_number, character=match.end()),
            ),
            severity=DiagnosticSeverity.Error,
            code=error_type,
            source="MEDFORD",
            message=error_message,
        )
    elif error_type == SYNTAX_ERR_WRONG_MACRO_TOKEN:

        # This error doesn't even need a scan because it always occours
        # in the first two characters of the erronious line. 
        # TODO: This isn't actually true...whoops! We need to scan for this.
        return Diagnostic(
            range=Range(
                start=Position(line=line_number, character=0),
                end=Position(line=line_number, character=2),
            ),
            severity=DiagnosticSeverity.Error,
            code=error_type,
            source="MEDFORD",
            message=error_message,
        )
    else:
        # For all non-specific syntax errors (I don't think there are any) we
        # mark the entire line as an error.
        return Diagnostic(
            range=Range(
                start=Position(line=line_number, character=0),
                end=Position(line=line_number + 1, character=0),
            ),
            severity=DiagnosticSeverity.Error,
            code=error_type,
            source="MEDFORD",
            message=error_message,
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
