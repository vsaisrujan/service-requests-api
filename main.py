from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from typing import Literal, List
from datetime import datetime, timezone
import uuid

app = FastAPI(title="Service Request API")

# Simple in-memory list to store all requests — resets when the server restarts
requests_store: List[dict] = []


# Return 400 instead of FastAPI's default 422 for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    messages = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"] if loc != "body" and not isinstance(loc, int))
        msg = error["msg"]
        messages.append(f"{field}: {msg}" if field else msg)
    return JSONResponse(
        status_code=400,
        content={"detail": "; ".join(messages)},
    )


# What the request body should look like when creating a new request
class ServiceRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str
    category: Literal["Billing", "Technical", "Other"]
    contactEmail: EmailStr

    # Reject strings that are empty or just spaces
    @field_validator("title", "description")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty or whitespace")
        return v.strip()


# What gets returned to the client after a request is created or fetched
class ServiceRequestResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    contactEmail: str
    createdAt: str


@app.post("/api/requests", response_model=ServiceRequestResponse, status_code=201)
def create_request(payload: ServiceRequestCreate):
    # Build the record and assign a unique ID and timestamp
    record = {
        "id": str(uuid.uuid4()),
        "title": payload.title,
        "description": payload.description,
        "category": payload.category,
        "contactEmail": str(payload.contactEmail),
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    requests_store.append(record)
    return record


@app.get("/api/requests", response_model=List[ServiceRequestResponse])
def list_requests():
    # Return newest first by reversing the list
    return list(reversed(requests_store))


@app.get("/api/requests/{request_id}", response_model=ServiceRequestResponse)
def get_request(request_id: str):
    for req in requests_store:
        if req["id"] == request_id:
            return req
    raise HTTPException(status_code=404, detail="Request not found")
