#!/usr/bin/env python3
"""
Simple test to verify pytest setup works
"""

import pytest

def test_simple():
    """Simple test that should pass"""
    assert 1 + 1 == 2

def test_another():
    """Another simple test"""
    assert "hello" == "hello"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])