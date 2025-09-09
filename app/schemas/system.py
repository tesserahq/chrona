from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class ValidationStatus(str, Enum):
    OK = "ok"
    ERROR = "error"


class ValidationStep(BaseModel):
    """Represents a single validation step in the system setup process."""

    name: str
    status: ValidationStatus
    message: str


class SystemSetupResponse(BaseModel):
    """Response model for system setup operations."""

    success: bool
    message: str
    details: List[ValidationStep]


class AppGroup(BaseModel):
    name: str
    environment: str
    log_level: str
    disable_auth: bool
    port: int


class GeneralGroup(BaseModel):
    is_production: bool


class DatabaseGroup(BaseModel):
    database_host: Optional[str]
    database_driver: Optional[str]
    pool_size: int
    max_overflow: int


class TelemetryGroup(BaseModel):
    otel_enabled: bool
    otel_exporter_otlp_endpoint: str
    otel_service_name: str


class RedisGroup(BaseModel):
    host: str
    port: int
    namespace: str


class ExternalServicesGroup(BaseModel):
    vaulta_api_url: str
    identies_host: Optional[str]


class SystemSettingsGrouped(BaseModel):
    app: AppGroup
    database: DatabaseGroup
    general: GeneralGroup
    telemetry: TelemetryGroup
    redis: RedisGroup
    services: ExternalServicesGroup
