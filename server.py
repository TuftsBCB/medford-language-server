############################################################################
# Copyright(c) Open Law Library. All rights reserved.                      #
# See ThirdPartyNotices.txt in the project root for additional notices.    #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License")           #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http: // www.apache.org/licenses/LICENSE-2.0                         #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
############################################################################
import asyncio
import re
import sys
from timeit import default_timer
import uuid
from typing import Optional
from pprint import pprint, pformat

from pygls.lsp.methods import (COMPLETION, TEXT_DOCUMENT_DID_CHANGE,
                               TEXT_DOCUMENT_DID_CLOSE, TEXT_DOCUMENT_DID_OPEN, 
                               TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL)
from pygls.lsp.types import (CompletionItem, CompletionList, CompletionOptions,
                             CompletionParams, ConfigurationItem,
                             ConfigurationParams, Diagnostic,
                             DiagnosticSeverity,
                             DidChangeTextDocumentParams,
                             DidCloseTextDocumentParams,
                             DidOpenTextDocumentParams, MessageType, Position,
                             Range, Registration, RegistrationParams,
                             SemanticTokens, SemanticTokensLegend, SemanticTokensParams,
                             Unregistration, UnregistrationParams)
from pygls.lsp.types.basic_structures import (WorkDoneProgressBegin,
                                              WorkDoneProgressEnd,
                                              WorkDoneProgressReport)
from pygls.lsp.types.window import (ShowDocumentCallbackType, 
                                    ShowDocumentClientCapabilities, 
                                    ShowDocumentParams, ShowDocumentResult, URI)
from pygls.server import LanguageServer


import MEDFORD.medford as medford
import MEDFORD.medford_detailparser as medford_detailparser
import MEDFORD.medford_detail as medford_detail
import MEDFORD.medford_models as medford_models
import MEDFORD.medford_BagIt as medford_BagIt
import MEDFORD.medford_error_mngr as medford_error_mngr

import logging

logging.basicConfig(filename="pygls.log", filemode="w", level=logging.INFO)

# COUNT_DOWN_START_IN_SECONDS = 10
# COUNT_DOWN_SLEEP_IN_SECONDS = 1


class MEDFORDLanguageServer(LanguageServer):
    # CMD_COUNT_DOWN_BLOCKING = 'countDownBlocking'
    # CMD_COUNT_DOWN_NON_BLOCKING = 'countDownNonBlocking'
    # CMD_PROGRESS = 'progress'
    # CMD_REGISTER_COMPLETIONS = 'registerCompletions'
    # CMD_SHOW_CONFIGURATION_ASYNC = 'showConfigurationAsync'
    # CMD_SHOW_CONFIGURATION_CALLBACK = 'showConfigurationCallback'
    # CMD_SHOW_CONFIGURATION_THREAD = 'showConfigurationThread'
    # CMD_UNREGISTER_COMPLETIONS = 'unregisterCompletions'
    # CMD_SAY_HI = 'sayHi'

    # CONFIGURATION_SECTION = 'medfordServer'

    def __init__(self):
        super().__init__()


medford_server = MEDFORDLanguageServer()


def _validate(ls: MEDFORDLanguageServer, params):

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


def _validate_medford(ls: MEDFORDLanguageServer, source: list) -> list:
    """Validates MEDFORD file."""
    diagnostics = []
    details = []

    # The medford parser's macro dict is  not reset or reinitilized
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
    else:
        parser = medford_detailparser.detailparser(details, err_mngr)
        final_dict = parser.export()
        p = {}
        try:
            p = medford_models.Entity(**final_dict)
        except medford.ValidationError as e:
            helper = sys.stdout
            sys.stdout = sys.stderr
            parser.parse_pydantic_errors(e, final_dict)
            sys.stdout = helper
            ls.show_message_log(pformat(parser.err_mngr._error_collection))
        else:
            ls.show_message("No errors found.")

    return diagnostics


# @medford_server.feature(COMPLETION, CompletionOptions(trigger_characters=[',']))
# def completions(params: Optional[CompletionParams] = None) -> CompletionList:
#     """Returns completion items."""
#     return CompletionList(
#         is_incomplete=False,
#         items=[
#             CompletionItem(label='"'),
#             CompletionItem(label='['),
#             CompletionItem(label=']'),
#             CompletionItem(label='{'),
#             CompletionItem(label='}'),
#         ]
#     )


# @medford_server.command(MEDFORDLanguageServer.CMD_SAY_HI)
# def say_hi(ls: MEDFORDLanguageServer, *args):
#     ls.show_message("hello world")
#     def _sd_callback(res: ShowDocumentResult):
#         logging.warning(res.__repr__())
#     ls.show_document(ShowDocumentParams(uri=URI("file://Unknown.jpeg"), takeFocus=True), _sd_callback)


# @medford_server.command(MEDFORDLanguageServer.CMD_COUNT_DOWN_BLOCKING)
# def count_down_10_seconds_blocking(ls: MEDFORDLanguageServer, *args):
#     """Starts counting down and showing message synchronously.
#     It will `block` the main thread, which can be tested by trying to show
#     completion items.
#     """
#     for i in range(COUNT_DOWN_START_IN_SECONDS):
#         ls.show_message(f'Counting down... {COUNT_DOWN_START_IN_SECONDS - i}')
#         time.sleep(COUNT_DOWN_SLEEP_IN_SECONDS)


# @medford_server.command(MEDFORDLanguageServer.CMD_COUNT_DOWN_NON_BLOCKING)
# async def count_down_10_seconds_non_blocking(ls: MEDFORDLanguageServer, *args):
#     """Starts counting down and showing message asynchronously.
#     It won't `block` the main thread, which can be tested by trying to show
#     completion items.
#     """
#     for i in range(COUNT_DOWN_START_IN_SECONDS):
#         ls.show_message(f'Counting down... {COUNT_DOWN_START_IN_SECONDS - i}')
#         await asyncio.sleep(COUNT_DOWN_SLEEP_IN_SECONDS)


@medford_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: MEDFORDLanguageServer, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    _validate(ls, params)


# @medford_server.feature(TEXT_DOCUMENT_DID_CLOSE)
# def did_close(server: MEDFORDLanguageServer, params: DidCloseTextDocumentParams):
#     """Text document did close notification."""
#     server.show_message('Text Document Did Close')


@medford_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: MEDFORDLanguageServer, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    _validate(ls, params)


# @medford_server.feature(
#     TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
#     SemanticTokensLegend(
#         token_types = ["operator"],
#         token_modifiers = []
#     )
# )
# def semantic_tokens(ls: MEDFORDLanguageServer, params: SemanticTokensParams):
#     """See https://microsoft.github.io/language-server-protocol/specification#textDocument_semanticTokens
#     for details on how semantic tokens are encoded."""
    
#     TOKENS = re.compile('".*"(?=:)')
    
#     uri = params.text_document.uri
#     doc = ls.workspace.get_document(uri)

#     last_line = 0
#     last_start = 0

#     data = []

#     for lineno, line in enumerate(doc.lines):
#         last_start = 0

#         for match in TOKENS.finditer(line):
#             start, end = match.span()
#             data += [
#                 (lineno - last_line),
#                 (start - last_start),
#                 (end - start),
#                 0, 
#                 0
#             ]

#             last_line = lineno
#             last_start = start

#     return SemanticTokens(data=data)



# @medford_server.command(MEDFORDLanguageServer.CMD_PROGRESS)
# async def progress(ls: MEDFORDLanguageServer, *args):
#     """Create and start the progress on the client."""
#     token = 'token'
#     # Create
#     await ls.progress.create_async(token)
#     # Begin
#     ls.progress.begin(token, WorkDoneProgressBegin(title='Indexing', percentage=0))
#     # Report
#     for i in range(1, 10):
#         ls.progress.report(
#             token,
#             WorkDoneProgressReport(message=f'{i * 10}%', percentage= i * 10),
#         )
#         await asyncio.sleep(2)
#     # End
#     ls.progress.end(token, WorkDoneProgressEnd(message='Finished'))


# @medford_server.command(MEDFORDLanguageServer.CMD_REGISTER_COMPLETIONS)
# async def register_completions(ls: MEDFORDLanguageServer, *args):
#     """Register completions method on the client."""
#     params = RegistrationParams(registrations=[
#                 Registration(
#                     id=str(uuid.uuid4()),
#                     method=COMPLETION,
#                     register_options={"triggerCharacters": "[':']"})
#              ])
#     response = await ls.register_capability_async(params)
#     if response is None:
#         ls.show_message('Successfully registered completions method')
#     else:
#         ls.show_message('Error happened during completions registration.',
#                         MessageType.Error)


# @medford_server.command(MEDFORDLanguageServer.CMD_SHOW_CONFIGURATION_ASYNC)
# async def show_configuration_async(ls: MEDFORDLanguageServer, *args):
#     """Gets exampleConfiguration from the client settings using coroutines."""
#     try:
#         config = await ls.get_configuration_async(
#             ConfigurationParams(items=[
#                 ConfigurationItem(
#                     scope_uri='',
#                     section=MEDFORDLanguageServer.CONFIGURATION_SECTION)
#         ]))

#         example_config = config[0].get('exampleConfiguration')

#         ls.show_message(f'jsonServer.exampleConfiguration value: {example_config}')

#     except Exception as e:
#         ls.show_message_log(f'Error ocurred: {e}')


# @medford_server.command(MEDFORDLanguageServer.CMD_SHOW_CONFIGURATION_CALLBACK)
# def show_configuration_callback(ls: MEDFORDLanguageServer, *args):
#     """Gets exampleConfiguration from the client settings using callback."""
#     def _config_callback(config):
#         try:
#             example_config = config[0].get('exampleConfiguration')

#             ls.show_message(f'jsonServer.exampleConfiguration value: {example_config}')

#         except Exception as e:
#             ls.show_message_log(f'Error ocurred: {e}')

#     ls.get_configuration(ConfigurationParams(items=[
#         ConfigurationItem(
#             scope_uri='',
#             section=MEDFORDLanguageServer.CONFIGURATION_SECTION)
#     ]), _config_callback)


# @medford_server.thread()
# @medford_server.command(MEDFORDLanguageServer.CMD_SHOW_CONFIGURATION_THREAD)
# def show_configuration_thread(ls: MEDFORDLanguageServer, *args):
#     """Gets exampleConfiguration from the client settings using thread pool."""
#     try:
#         config = ls.get_configuration(ConfigurationParams(items=[
#             ConfigurationItem(
#                 scope_uri='',
#                 section=MEDFORDLanguageServer.CONFIGURATION_SECTION)
#         ])).result(2)

#         example_config = config[0].get('exampleConfiguration')

#         ls.show_message(f'jsonServer.exampleConfiguration value: {example_config}')

#     except Exception as e:
#         ls.show_message_log(f'Error ocurred: {e}')


# @medford_server.command(MEDFORDLanguageServer.CMD_UNREGISTER_COMPLETIONS)
# async def unregister_completions(ls: MEDFORDLanguageServer, *args):
#     """Unregister completions method on the client."""
#     params = UnregistrationParams(unregisterations=[
#         Unregistration(id=str(uuid.uuid4()), method=COMPLETION)
#     ])
#     response = await ls.unregister_capability_async(params)
#     if response is None:
#         ls.show_message('Successfully unregistered completions method')
#     else:
#         ls.show_message('Error happened during completions unregistration.',
#                         MessageType.Error)
