"""
Tests for backend/utils/memory_guard.py
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from utils.memory_guard import MemoryGuard, secure_delete


class TestSecureDelete:
    def test_bytearray_zeroed(self):
        data = bytearray(b"sensitive key material 0123456789")
        secure_delete(data)
        assert all(b == 0 for b in data), "All bytes should be zeroed"

    def test_bytearray_length_unchanged(self):
        data = bytearray(b"hello")
        original_len = len(data)
        secure_delete(data)
        assert len(data) == original_len

    def test_dict_cleared(self):
        data = {
            "key": bytearray(b"secret"),
            "iv": bytearray(b"nonce123"),
        }
        secure_delete(data)
        assert len(data) == 0 or all(v is None for v in data.values())

    def test_list_cleared(self):
        data = [bytearray(b"a"), bytearray(b"b"), bytearray(b"c")]
        secure_delete(data)
        assert len(data) == 0 or all(v is None for v in data)

    def test_empty_bytearray(self):
        data = bytearray()
        secure_delete(data)  # should not raise
        assert len(data) == 0

    def test_nested_dict(self):
        data = {
            "session_key": bytearray(b"key_bytes_here_32_bytes_xxxxxxxxx"),
            "tag": bytearray(b"auth_tag_16_bytes"),
        }
        secure_delete(data)
        # After wipe all inner bytearrays should be zeroed or None
        for v in data.values():
            if isinstance(v, bytearray):
                assert all(b == 0 for b in v)
            else:
                assert v is None

    def test_bytes_type_does_not_raise(self):
        # bytes is immutable — secure_delete should handle gracefully
        data = b"immutable bytes"
        secure_delete(data)  # should not raise


class TestMemoryGuard:
    def test_context_manager_entry(self):
        with MemoryGuard() as guard:
            assert guard is not None

    def test_track_returns_same_object(self):
        with MemoryGuard() as guard:
            data = bytearray(b"test data")
            result = guard.track(data)
            assert result is data

    def test_tracked_bytearray_wiped_on_exit(self):
        data = bytearray(b"secret session key 0123456789abc")
        with MemoryGuard() as guard:
            guard.track(data)
            assert data == bytearray(b"secret session key 0123456789abc")
        # After context exit, data should be zeroed
        assert all(b == 0 for b in data)

    def test_multiple_tracked_objects_all_wiped(self):
        key = bytearray(b"key_material_32_bytes_xxxxxxxxxxx")
        iv = bytearray(b"iv_12_bytes!")
        tag = bytearray(b"auth_tag_16b!")

        with MemoryGuard() as guard:
            guard.track(key)
            guard.track(iv)
            guard.track(tag)

        assert all(b == 0 for b in key)
        assert all(b == 0 for b in iv)
        assert all(b == 0 for b in tag)

    def test_exception_still_wipes(self):
        data = bytearray(b"must be wiped even on exception")
        try:
            with MemoryGuard() as guard:
                guard.track(data)
                raise ValueError("simulated error")
        except ValueError:
            pass
        # Should still be wiped
        assert all(b == 0 for b in data)

    def test_exception_propagates(self):
        with pytest.raises(ValueError, match="test error"):
            with MemoryGuard() as guard:
                guard.track(bytearray(b"data"))
                raise ValueError("test error")

    def test_empty_guard_no_error(self):
        with MemoryGuard() as guard:
            pass  # nothing tracked, should be fine

    def test_track_non_bytearray(self):
        # Tracking non-sensitive objects should not crash
        with MemoryGuard() as guard:
            guard.track("plain string")
            guard.track({"key": "value"})
            guard.track([1, 2, 3])
        # Should complete without error

    def test_nested_guards(self):
        outer_data = bytearray(b"outer secret key")
        inner_data = bytearray(b"inner secret key")

        with MemoryGuard() as outer_guard:
            outer_guard.track(outer_data)
            with MemoryGuard() as inner_guard:
                inner_guard.track(inner_data)
            # inner_data wiped after inner context
            assert all(b == 0 for b in inner_data)
            # outer_data still alive inside outer context
        # outer_data wiped after outer context
        assert all(b == 0 for b in outer_data)
