#!/usr/bin/env python3
"""
Minimal test for subsidy hunter
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

def test_simple_import():
    """Test that we can import the router"""
    from src.routers.subsidy_hunter import router as subsidy_hunter_router
    assert subsidy_hunter_router is not None

def test_basic_app():
    """Test basic FastAPI app creation"""
    app = FastAPI()
    client = TestClient(app)
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "test"}
    
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "test"}