"""Document management API routes."""

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.api.auth_deps import get_current_user
from app.core.deps import UnitOfWork, get_uow
from app.db.models.user import User
from app.schemas.documents import (
    DocumentContentResponse,
    DocumentListResponse,
    DocumentResponse,
    MessageResponse,
    UrlIngestRequest,
)
from app.services.documents import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=list[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def upload_documents(
    files: list[UploadFile] = File(...),
    organization_id: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[DocumentResponse]:
    """Upload one or more documents for ingestion."""
    documents = await DocumentService(uow).upload_files(
        current_user,
        files,
        organization_id=organization_id,
    )
    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.post("/url", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def ingest_url(
    payload: UrlIngestRequest,
    organization_id: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DocumentResponse:
    """Ingest a public web page by URL."""
    document = await DocumentService(uow).ingest_url(
        current_user,
        payload,
        organization_id=organization_id,
    )
    return DocumentResponse.model_validate(document)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    organization_id: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DocumentListResponse:
    """List personal documents or an organization's shared library."""
    items, total = await DocumentService(uow).list_documents(
        current_user,
        page=page,
        page_size=page_size,
        organization_id=organization_id,
    )
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(doc) for doc in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DocumentResponse:
    document = await DocumentService(uow).get_document(current_user, document_id)
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/file")
async def download_document_file(
    document_id: str,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> FileResponse:
    """Download the original uploaded file for in-app viewing."""
    document, path = await DocumentService(uow).get_document_file(current_user, document_id)
    return FileResponse(
        path,
        filename=document.original_filename,
        media_type=document.content_type or "application/octet-stream",
    )


@router.get("/{document_id}/content", response_model=DocumentContentResponse)
async def get_document_content(
    document_id: str,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DocumentContentResponse:
    document, text = await DocumentService(uow).get_document_content(current_user, document_id)
    return DocumentContentResponse(
        document_id=document.id,
        text=text,
        page_count=document.page_count,
        chunk_count=document.chunk_count,
    )


@router.delete("/{document_id}", response_model=MessageResponse)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> MessageResponse:
    await DocumentService(uow).delete_document(current_user, document_id)
    return MessageResponse(message="Document deleted.")
