import json
from typing import Optional

import pytest
from mock import Mock
from pygls.lsp.types import (
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    TextDocumentIdentifier,
    TextDocumentItem,
)
from pygls.workspace import Document, Workspace

from ...server import completions, did_close, did_open


class FakeServer:
    """We don't need real server to unit test features."""

    publish_diagnostics = None
    show_message = None
    show_message_log = None

    def __init__(self):
        self.workspace = Workspace("", None)


fake_document_uri = "file://fake_doc.txt"
fake_document_content = "text"
fake_document = Document(fake_document_uri, fake_document_content)


server = FakeServer()
server.publish_diagnostics = Mock()
server.show_message = Mock()
server.show_message_log = Mock()
server.workspace.get_document = Mock(return_value=fake_document)


def _reset_mocks():
    server.publish_diagnostics.reset_mock()
    server.show_message.reset_mock()
    server.show_message_log.reset_mock()


def test_completions():
    completion_list = completions()
    labels = [i.label for i in completion_list.items]

    assert '"' in labels
    assert "[" in labels
    assert "]" in labels
    assert "{" in labels
    assert "}" in labels


def test_did_close():
    _reset_mocks()

    params = DidCloseTextDocumentParams(
        text_document=TextDocumentIdentifier(uri=fake_document_uri)
    )

    did_close(server, params)

    # Check if show message is called
    server.show_message.assert_called_once()


@pytest.mark.asyncio
async def test_did_open():
    _reset_mocks()

    expected_msg = None

    # Get expected error message
    try:
        json.loads(fake_document_content)
    except json.JSONDecodeError as err:
        expected_msg = err.msg

    params = DidOpenTextDocumentParams(
        text_document=TextDocumentItem(
            uri=fake_document_uri,
            language_id="json",
            version=1,
            text=fake_document_content,
        )
    )

    await did_open(server, params)

    # Check publish diagnostics is called
    server.publish_diagnostics.assert_called_once()

    # Check publish diagnostics args message
    args = server.publish_diagnostics.call_args
    assert args[0][1][0].message is expected_msg

    # Check other methods are called
    server.show_message.assert_called_once()
    server.show_message_log.assert_called_once()
