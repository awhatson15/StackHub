
from typing import Optional, List
from pydantic import BaseModel, Field, validator

class Edition(BaseModel):
    dist: str = Field("community", description="The edition of the app",examples=["community","enterprise"])
    version: str  = Field(..., description="The version of the app",examples=["1.0.0","latest"])

class appInstall(BaseModel):
    app_name: str = Field(..., description="The name of the app",examples=["wordpress","mysql"])
    edition: Edition = Field(..., description="The edition of the app", example={"dist":"community","version":"1.0.0"})
    app_id: str = Field(..., pattern="^[a-z][a-z0-9]{1,19}$", description="The custom identifier for the application. It must be a combination of 2 to 20 lowercase letters and numbers, and cannot start with a number.", example="wordpress")
    domain_names: Optional[List[str]] = Field(None, description="The domain names for the app, not exceeding 2, one wildcard domain and one custom domain.", example=["wordpress.example.com","mysql.example.com"])
    default_domain: Optional[str] = Field(None, description="The default domain for the app, sourced from domain_names. If not set, the custom domain will be used automatically.", example="wordpress.example.com")
    
    @validator('domain_names', check_fields=False)
    def validate_domain_names(cls, v):
        if v and len(v) > 2:
            raise ValueError('domain_names should not exceed 2.')
        return v

    class Config:
        title = "App Installation"
        description = "App Installation Payload"