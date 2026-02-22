from pydantic import BaseModel, field_validator


class PostCreate(BaseModel):
    title: str
    body_markdown: str
    category: str = "improvement"
    is_published: bool = False

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1:
            raise ValueError("Title is required")
        if len(v) > 300:
            raise ValueError("Title must be at most 300 characters")
        return v

    @field_validator("body_markdown")
    @classmethod
    def validate_body(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Post body is required")
        return v


class PostUpdate(BaseModel):
    title: str | None = None
    body_markdown: str | None = None
    category: str | None = None


class PostResponse(BaseModel):
    id: str
    title: str
    slug: str
    body_markdown: str
    body_html: str
    category: str
    is_published: bool
    view_count: int
    project_id: str

    model_config = {"from_attributes": True}
