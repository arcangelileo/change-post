from pydantic import BaseModel, field_validator


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    website_url: str | None = None
    accent_color: str = "#6366f1"

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1:
            raise ValueError("Project name is required")
        if len(v) > 200:
            raise ValueError("Project name must be at most 200 characters")
        return v

    @field_validator("accent_color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith("#") or len(v) != 7:
            raise ValueError("Color must be a valid hex color (e.g. #6366f1)")
        return v


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    website_url: str | None = None
    accent_color: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if len(v) < 1:
                raise ValueError("Project name is required")
            if len(v) > 200:
                raise ValueError("Project name must be at most 200 characters")
        return v


class ProjectResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None
    website_url: str | None
    logo_url: str | None
    accent_color: str
    owner_id: str

    model_config = {"from_attributes": True}
