import pytest
from mock import Mock
from pygls.lsp.types import (
    DidChangeConfigurationParams,
    DidOpenTextDocumentParams,
    TextDocumentIdentifier,
    TextDocumentItem,
)
from pygls.workspace import Document, Workspace

from ...server import did_change, did_open

# We want this empty class instance because its helpful.
# pylint: disable-next=R0903
class FakeServer:
    """We don't need real server to unit test features."""

    publish_diagnostics = None
    show_message = None
    show_message_log = None

    def __init__(self):
        self.workspace = Workspace("", None)


FAKE_DOCUMENT_URI = "file://fake_doc.txt"
FAKE_DOCUMENT_CONTENT = "text"
fake_document = Document(FAKE_DOCUMENT_URI, FAKE_DOCUMENT_CONTENT)


server = FakeServer()
server.publish_diagnostics = Mock()
server.show_message = Mock()
server.show_message_log = Mock()
server.workspace.get_document = Mock(return_value=fake_document)


def _reset_mocks():
    server.publish_diagnostics.reset_mock()
    server.show_message.reset_mock()
    server.show_message_log.reset_mock()


def test_did_change():
    _reset_mocks()
    params = DidChangeConfigurationParams(
        text_document=TextDocumentIdentifier(uri=FAKE_DOCUMENT_URI)
    )

    did_change(server, params)


@pytest.mark.asyncio
async def test_did_open():
    _reset_mocks()

    params = DidOpenTextDocumentParams(
        text_document=TextDocumentItem(
            uri=FAKE_DOCUMENT_URI,
            language_id="json",
            version=1,
            text=FAKE_DOCUMENT_CONTENT,
        )
    )

    await did_open(server, params)

    # Check publish diagnostics is called
    server.publish_diagnostics.assert_called_once()
