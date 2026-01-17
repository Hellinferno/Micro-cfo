"""
Configuration module for MicroCFO Integration Server
"""

import os
from typing import List
from pydantic import BaseModel


class ServerConfig(BaseModel):
    """Server configuration settings"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    reload: bool = False
    # Timeout settings for large file uploads and processing
    request_timeout: int = 300  # 5 minutes
    keepalive_timeout: int = 65  # 65 seconds


class CORSConfig(BaseModel):
    """CORS configuration settings"""
    frontend_url: str = "http://localhost:5173"
    allowed_origins: List[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]
    allow_credentials: bool = True
    allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers: List[str] = ["*"]


class SecurityConfig(BaseModel):
    """Security configuration settings"""
    trusted_hosts: List[str] = ["localhost", "127.0.0.1", "0.0.0.0", "testserver"]
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24


class APIConfig(BaseModel):
    """API configuration settings"""
    v1_prefix: str = "/api/v1"
    title: str = "MicroCFO Integration API"
    description: str = "FastAPI integration layer for MicroCFO MCP Server"
    version: str = "1.0.0"


class Config:
    """Main configuration class"""
    
    def __init__(self):
        # Load from environment variables
        self.server = ServerConfig(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            reload=os.getenv("RELOAD", "false").lower() == "true",
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "300")),
            keepalive_timeout=int(os.getenv("KEEPALIVE_TIMEOUT", "65"))
        )
        
        # CORS configuration
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        allowed_origins = [frontend_url]
        
        # Add default development origins
        default_origins = [
            "http://localhost:5173",
            "http://localhost:3000", 
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000"
        ]
        
        for origin in default_origins:
            if origin not in allowed_origins:
                allowed_origins.append(origin)
        
        self.cors = CORSConfig(
            frontend_url=frontend_url,
            allowed_origins=allowed_origins
        )
        
        # Security configuration
        self.security = SecurityConfig(
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expiration_hours=int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
        )
        
        # API configuration
        self.api = APIConfig(
            v1_prefix=os.getenv("API_V1_PREFIX", "/api/v1")
        )
        
        # Add debug hosts in development
        if self.server.debug:
            self.security.trusted_hosts.append("*")


# Global configuration instance
config = Config()