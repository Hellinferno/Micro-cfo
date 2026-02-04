"""
Configuration module for MicroCFO Integration Server
Complete configuration for all services and API providers
"""

import os
from typing import List, Optional
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
    encryption_key: Optional[str] = None  # For encrypting sensitive data


class DatabaseConfig(BaseModel):
    """Database configuration"""
    url: str = "postgresql://microcfo:changeme@localhost:5432/microcfo"
    pool_size: int = 10
    max_overflow: int = 20
    pool_pre_ping: bool = True
    pool_recycle: int = 3600  # 1 hour


class RedisConfig(BaseModel):
    """Redis configuration"""
    url: str = "redis://localhost:6379/0"
    max_connections: int = 10
    socket_timeout: int = 5


class LLMConfig(BaseModel):
    """LLM Provider configuration"""
    # Google Gemini (Primary)
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash"
    
    # Groq (Fast inference)
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"
    
    # OpenAI (Fallback)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    
    # OpenRouter (Alternative)
    openrouter_api_key: Optional[str] = None
    
    # Rate limits
    max_tokens_per_request: int = 2000
    requests_per_minute: int = 60


class StorageConfig(BaseModel):
    """Storage configuration (S3/Local)"""
    # AWS S3
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    aws_region: str = "ap-south-1"  # Mumbai
    s3_bucket_name: Optional[str] = None
    
    # Local storage fallback
    local_storage_path: str = "./file_storage"


class EmailConfig(BaseModel):
    """Email service configuration"""
    sendgrid_api_key: Optional[str] = None
    from_email: str = "noreply@microcfo.com"
    from_name: str = "MicroCFO"


class SMSConfig(BaseModel):
    """SMS/OTP service configuration"""
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None


class WhatsAppConfig(BaseModel):
    """WhatsApp Business API configuration"""
    api_key: Optional[str] = None
    phone_number_id: Optional[str] = None
    verify_token: Optional[str] = None


class AccountAggregatorConfig(BaseModel):
    """Account Aggregator framework configuration"""
    provider: str = "sahamati_sandbox"
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    api_url: str = "https://api.sandbox.sahamati.org.in"
    callback_url: Optional[str] = None


class MonitoringConfig(BaseModel):
    """Monitoring and observability configuration"""
    sentry_dsn: Optional[str] = None
    datadog_api_key: Optional[str] = None
    enable_metrics: bool = True
    enable_tracing: bool = True


class FeatureFlagsConfig(BaseModel):
    """Feature flags for gradual rollouts"""
    enable_agent_a: bool = True  # Visual Auditor
    enable_agent_b: bool = True  # Legal Sentinel
    enable_agent_c: bool = True  # Subsidy Hunter
    enable_agent_d: bool = True  # Negotiator
    enable_whatsapp: bool = True
    enable_account_aggregator: bool = False
    enable_etl_scheduler: bool = True


class APIConfig(BaseModel):
    """API configuration settings"""
    v1_prefix: str = "/api/v1"
    title: str = "MicroCFO Integration API"
    description: str = """
The MicroCFO Integration API provides a comprehensive suite of endpoints to power AI-driven financial operations. It acts as a bridge between a frontend application and the backend Model Context Protocol (MCP) server where the intelligent agents (Visual Auditor, Legal Sentinel, etc.) reside.

The API is organized into the following functional areas:

- **Authentication**: Endpoints for user login, profile management, and JWT token handling.
- **Onboarding**: A step-by-step flow for setting up new user and company profiles.
- **Visual Auditor (Agent A)**: Process invoices from URLs or direct file uploads to extract data, detect fraud, and check for compliance issues.
- **Legal Sentinel (Agent B)**: Query the legislative RAG for compliance information and risk assessment.
- **Subsidy Hunter (Agent C)**: Discover applicable government subsidies based on a business sector and capital expenditure.
- **Negotiator (Agent D)**: Generate professional negotiation drafts (emails, WhatsApp messages) for managing payables and receivables.
- **ERP Export**: Export processed invoice data into formats compatible with Tally, Zoho Books, and standard CSV/JSON.
- **Async Tasks**: Submit long-running jobs like document processing and retrieve their status and results asynchronously.
- **Audit Trail**: Query and export comprehensive audit logs for all system activities.
- **WebSocket**: A real-time communication channel for receiving live updates, such as legal notifications and processing statuses.
"""
    version: str = "1.0.0"


class Config:
    """Main configuration class - loads all settings from environment"""
    
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
        
        # CORS configuration - Production ready
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        allowed_origins = [frontend_url]
        
        # Add default development origins
        default_origins = [
            "http://localhost:5173",
            "http://localhost:3000", 
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000"
        ]
        
        # Add production Vercel URL from environment
        vercel_url = os.getenv("VERCEL_URL")
        if vercel_url:
            allowed_origins.append(f"https://{vercel_url}")
        
        # Add custom production frontend URL
        production_frontend = os.getenv("PRODUCTION_FRONTEND_URL")
        if production_frontend:
            allowed_origins.append(production_frontend)
        
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
            jwt_expiration_hours=int(os.getenv("JWT_EXPIRATION_HOURS", "24")),
            encryption_key=os.getenv("ENCRYPTION_KEY")
        )
        
        # Database configuration
        self.database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "postgresql://microcfo:changeme@localhost:5432/microcfo"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20"))
        )
        
        # Redis configuration
        self.redis = RedisConfig(
            url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
        )
        
        # LLM Provider configuration
        self.llm = LLMConfig(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            groq_api_key=os.getenv("GROQ_API_KEY"),
            groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            max_tokens_per_request=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            requests_per_minute=int(os.getenv("LLM_RATE_LIMIT", "60"))
        )
        
        # Storage configuration
        self.storage = StorageConfig(
            aws_access_key=os.getenv("AWS_ACCESS_KEY"),
            aws_secret_key=os.getenv("AWS_SECRET_KEY"),
            aws_region=os.getenv("AWS_REGION", "ap-south-1"),
            s3_bucket_name=os.getenv("S3_BUCKET_NAME"),
            local_storage_path=os.getenv("LOCAL_STORAGE_PATH", "./file_storage")
        )
        
        # Email configuration
        self.email = EmailConfig(
            sendgrid_api_key=os.getenv("SENDGRID_API_KEY"),
            from_email=os.getenv("EMAIL_FROM", "noreply@microcfo.com"),
            from_name=os.getenv("EMAIL_FROM_NAME", "MicroCFO")
        )
        
        # SMS configuration
        self.sms = SMSConfig(
            twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
            twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
            twilio_phone_number=os.getenv("TWILIO_PHONE_NUMBER")
        )
        
        # WhatsApp configuration
        self.whatsapp = WhatsAppConfig(
            api_key=os.getenv("WHATSAPP_API_KEY"),
            phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID"),
            verify_token=os.getenv("WHATSAPP_VERIFY_TOKEN")
        )
        
        # Account Aggregator configuration
        self.account_aggregator = AccountAggregatorConfig(
            provider=os.getenv("AA_PROVIDER", "sahamati_sandbox"),
            client_id=os.getenv("AA_CLIENT_ID"),
            client_secret=os.getenv("AA_CLIENT_SECRET"),
            api_url=os.getenv("AA_API_URL", "https://api.sandbox.sahamati.org.in"),
            callback_url=os.getenv("AA_CALLBACK_URL")
        )
        
        # Monitoring configuration
        self.monitoring = MonitoringConfig(
            sentry_dsn=os.getenv("SENTRY_DSN"),
            datadog_api_key=os.getenv("DATADOG_API_KEY"),
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            enable_tracing=os.getenv("ENABLE_TRACING", "true").lower() == "true"
        )
        
        # Feature flags
        self.features = FeatureFlagsConfig(
            enable_agent_a=os.getenv("ENABLE_AGENT_A", "true").lower() == "true",
            enable_agent_b=os.getenv("ENABLE_AGENT_B", "true").lower() == "true",
            enable_agent_c=os.getenv("ENABLE_AGENT_C", "true").lower() == "true",
            enable_agent_d=os.getenv("ENABLE_AGENT_D", "true").lower() == "true",
            enable_whatsapp=os.getenv("ENABLE_WHATSAPP", "true").lower() == "true",
            enable_account_aggregator=os.getenv("ENABLE_AA", "false").lower() == "true",
            enable_etl_scheduler=os.getenv("ENABLE_ETL", "true").lower() == "true"
        )
        
        # Add Render host to trusted hosts
        render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME")
        if render_host:
            self.security.trusted_hosts.append(render_host)
        
        # Add Heroku host to trusted hosts
        heroku_app_name = os.getenv("HEROKU_APP_NAME")
        if heroku_app_name:
            self.security.trusted_hosts.append(f"{heroku_app_name}.herokuapp.com")
        
        # API configuration
        self.api = APIConfig(
            v1_prefix=os.getenv("API_V1_PREFIX", "/api/v1")
        )
        
        # Add debug hosts in development
        if self.server.debug:
            self.security.trusted_hosts.append("*")
    
    def get_llm_providers_status(self) -> dict:
        """Get status of configured LLM providers"""
        return {
            "gemini": bool(self.llm.gemini_api_key),
            "groq": bool(self.llm.groq_api_key),
            "openai": bool(self.llm.openai_api_key),
            "openrouter": bool(self.llm.openrouter_api_key)
        }
    
    def get_services_status(self) -> dict:
        """Get status of configured external services"""
        return {
            "database": bool(self.database.url),
            "redis": bool(self.redis.url),
            "s3": bool(self.storage.s3_bucket_name),
            "sendgrid": bool(self.email.sendgrid_api_key),
            "twilio": bool(self.sms.twilio_account_sid),
            "whatsapp": bool(self.whatsapp.api_key),
            "account_aggregator": bool(self.account_aggregator.client_id)
        }


# Global configuration instance
config = Config()