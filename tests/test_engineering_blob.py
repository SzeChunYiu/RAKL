from hashlib import sha256

import pytest

from rakl.engineering_blob import CanonicalPayloadStoreAdapter, LocalFilesystemBlobStore
from rakl.engineering_store import EngineeringIntegrityError


def test_local_blob_store_put_reuse_and_tamper_detection(tmp_path):
    store = LocalFilesystemBlobStore(tmp_path / "blobs")
    payload = b"exact evidence bytes"
    digest = store.put_if_absent(payload)
    assert digest == sha256(payload).hexdigest()
    assert store.put_if_absent(payload) == digest
    assert store.get_verified(digest) == payload
    assert store.exists_verified(digest)
    assert store.stat(digest)["raw_bytes"] == len(payload)

    path = store._path(digest)
    path.write_bytes(b"tampered")
    with pytest.raises(EngineeringIntegrityError, match="digest mismatch"):
        store.get_verified(digest)
    assert not store.exists_verified(digest)


class Stored:
    def __init__(self, digest):
        self.sha256 = digest


class FakeIncumbentStore:
    def __init__(self, root):
        self.root = root
        self.data = {}

    def put_bytes(self, payload):
        digest = sha256(payload).hexdigest()
        self.data[digest] = payload
        return Stored(digest)

    def read_bytes(self, digest):
        return self.data[digest]

    def verify(self, digest):
        return digest in self.data and sha256(self.data[digest]).hexdigest() == digest

    def path_for(self, digest):
        return self.root / digest


def test_incumbent_canonical_payload_adapter_preserves_digest(tmp_path):
    incumbent = FakeIncumbentStore(tmp_path)
    adapter = CanonicalPayloadStoreAdapter(incumbent)
    digest = adapter.put_if_absent(b"abc")
    assert adapter.get_verified(digest) == b"abc"
    assert adapter.exists_verified(digest)
    assert adapter.stat(digest)["backend"] == "INCUMBENT_CANONICAL_PAYLOAD_STORE"
