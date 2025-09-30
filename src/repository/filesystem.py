"""
File system-based repository implementation.

This module provides a simple file system storage backend for BRD/PRD documents,
using JSON files for persistence.
"""

import json
import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
import os

from .base import BaseRepository
from ..core.models import (
    BRDDocument,
    PRDDocument,
    GenerationRequest,
    GenerationResponse,
    DocumentType,
    ValidationResult
)
from ..core.exceptions import (
    DocumentNotFoundError,
    DocumentAlreadyExistsError,
    StorageError
)

logger = logging.getLogger(__name__)


class FileSystemRepository(BaseRepository):
    """File system-based document repository."""

    def __init__(self, base_path: str = "./data/documents"):
        """
        Initialize file system repository.

        Args:
            base_path: Base directory path for document storage
        """
        self.base_path = Path(base_path)
        self._initialize_directories()

    def _initialize_directories(self):
        """Create necessary directory structure."""
        directories = [
            self.base_path / "brds",
            self.base_path / "prds",
            self.base_path / "history",
            self.base_path / "validations",
            self.base_path / "cache"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _get_document_path(self, document_type: str, document_id: str) -> Path:
        """Get file path for a document."""
        return self.base_path / f"{document_type}s" / f"{document_id}.json"

    async def _read_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Read JSON file asynchronously."""
        try:
            async with aiofiles.open(file_path, mode='r') as f:
                content = await f.read()
                return json.loads(content)
        except FileNotFoundError:
            raise DocumentNotFoundError(f"Document not found at {file_path}")
        except json.JSONDecodeError as e:
            raise StorageError(f"Failed to parse JSON file: {e}")
        except Exception as e:
            raise StorageError(f"Failed to read file: {e}")

    async def _write_json_file(self, file_path: Path, data: Dict[str, Any]):
        """Write JSON file asynchronously."""
        try:
            # Convert to JSON string with pretty formatting
            json_content = json.dumps(data, indent=2, default=str)

            # Write atomically by writing to temp file first
            temp_path = file_path.with_suffix('.tmp')
            async with aiofiles.open(temp_path, mode='w') as f:
                await f.write(json_content)

            # Rename temp file to final path (atomic operation)
            temp_path.rename(file_path)

        except Exception as e:
            raise StorageError(f"Failed to write file: {e}")

    async def save_brd(self, document: BRDDocument) -> str:
        """Save a BRD document."""
        file_path = self._get_document_path("brd", document.document_id)

        # Check if document already exists
        if file_path.exists():
            raise DocumentAlreadyExistsError(
                f"BRD document {document.document_id} already exists"
            )

        # Convert to dictionary and save
        document_dict = document.model_dump()
        await self._write_json_file(file_path, document_dict)

        logger.info(f"Saved BRD document: {document.document_id}")
        return document.document_id

    async def save_prd(self, document: PRDDocument) -> str:
        """Save a PRD document."""
        file_path = self._get_document_path("prd", document.document_id)

        # Check if document already exists
        if file_path.exists():
            raise DocumentAlreadyExistsError(
                f"PRD document {document.document_id} already exists"
            )

        # Convert to dictionary and save
        document_dict = document.model_dump()
        await self._write_json_file(file_path, document_dict)

        logger.info(f"Saved PRD document: {document.document_id}")
        return document.document_id

    async def get_brd(self, document_id: str) -> BRDDocument:
        """Retrieve a BRD document by ID."""
        file_path = self._get_document_path("brd", document_id)
        document_dict = await self._read_json_file(file_path)
        return BRDDocument(**document_dict)

    async def get_prd(self, document_id: str) -> PRDDocument:
        """Retrieve a PRD document by ID."""
        file_path = self._get_document_path("prd", document_id)
        document_dict = await self._read_json_file(file_path)
        return PRDDocument(**document_dict)

    async def list_brds(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters
    ) -> List[BRDDocument]:
        """List BRD documents with optional filtering."""
        brd_dir = self.base_path / "brds"
        documents = []

        try:
            # Get all BRD files
            files = sorted(brd_dir.glob("BRD-*.json"))

            # Apply pagination
            files = files[offset:offset + limit]

            # Load documents
            for file_path in files:
                try:
                    document_dict = await self._read_json_file(file_path)
                    document = BRDDocument(**document_dict)

                    # Apply filters
                    if self._match_filters(document_dict, filters):
                        documents.append(document)
                except Exception as e:
                    logger.warning(f"Failed to load BRD {file_path}: {e}")

            return documents

        except Exception as e:
            raise StorageError(f"Failed to list BRD documents: {e}")

    async def list_prds(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters
    ) -> List[PRDDocument]:
        """List PRD documents with optional filtering."""
        prd_dir = self.base_path / "prds"
        documents = []

        try:
            # Get all PRD files
            files = sorted(prd_dir.glob("PRD-*.json"))

            # Apply pagination
            files = files[offset:offset + limit]

            # Load documents
            for file_path in files:
                try:
                    document_dict = await self._read_json_file(file_path)
                    document = PRDDocument(**document_dict)

                    # Apply filters
                    if self._match_filters(document_dict, filters):
                        documents.append(document)
                except Exception as e:
                    logger.warning(f"Failed to load PRD {file_path}: {e}")

            return documents

        except Exception as e:
            raise StorageError(f"Failed to list PRD documents: {e}")

    def _match_filters(self, document: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document matches filter criteria."""
        for key, value in filters.items():
            # Handle nested keys (e.g., "scope.in_scope")
            keys = key.split('.')
            doc_value = document

            for k in keys:
                if isinstance(doc_value, dict):
                    doc_value = doc_value.get(k)
                else:
                    doc_value = None
                    break

            # Check if values match
            if doc_value != value:
                return False

        return True

    async def update_brd(
        self,
        document_id: str,
        updates: Dict[str, Any]
    ) -> BRDDocument:
        """Update a BRD document."""
        # Get existing document
        document = await self.get_brd(document_id)

        # Apply updates
        document_dict = document.model_dump()
        document_dict.update(updates)
        document_dict["updated_at"] = datetime.now().isoformat()

        # Create updated document
        updated_document = BRDDocument(**document_dict)

        # Save back to file
        file_path = self._get_document_path("brd", document_id)
        await self._write_json_file(file_path, updated_document.model_dump())

        logger.info(f"Updated BRD document: {document_id}")
        return updated_document

    async def update_prd(
        self,
        document_id: str,
        updates: Dict[str, Any]
    ) -> PRDDocument:
        """Update a PRD document."""
        # Get existing document
        document = await self.get_prd(document_id)

        # Apply updates
        document_dict = document.model_dump()
        document_dict.update(updates)
        document_dict["updated_at"] = datetime.now().isoformat()

        # Create updated document
        updated_document = PRDDocument(**document_dict)

        # Save back to file
        file_path = self._get_document_path("prd", document_id)
        await self._write_json_file(file_path, updated_document.model_dump())

        logger.info(f"Updated PRD document: {document_id}")
        return updated_document

    async def delete_brd(self, document_id: str) -> bool:
        """Delete a BRD document."""
        file_path = self._get_document_path("brd", document_id)

        if not file_path.exists():
            raise DocumentNotFoundError(f"BRD document {document_id} not found")

        try:
            # Move to archive instead of deleting
            archive_dir = self.base_path / "archive" / "brds"
            archive_dir.mkdir(parents=True, exist_ok=True)

            archive_path = archive_dir / f"{document_id}_{datetime.now().isoformat()}.json"
            file_path.rename(archive_path)

            logger.info(f"Archived BRD document: {document_id}")
            return True

        except Exception as e:
            raise StorageError(f"Failed to delete BRD document: {e}")

    async def delete_prd(self, document_id: str) -> bool:
        """Delete a PRD document."""
        file_path = self._get_document_path("prd", document_id)

        if not file_path.exists():
            raise DocumentNotFoundError(f"PRD document {document_id} not found")

        try:
            # Move to archive instead of deleting
            archive_dir = self.base_path / "archive" / "prds"
            archive_dir.mkdir(parents=True, exist_ok=True)

            archive_path = archive_dir / f"{document_id}_{datetime.now().isoformat()}.json"
            file_path.rename(archive_path)

            logger.info(f"Archived PRD document: {document_id}")
            return True

        except Exception as e:
            raise StorageError(f"Failed to delete PRD document: {e}")

    async def search(
        self,
        query: str,
        document_type: Optional[DocumentType] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for documents by text query."""
        results = []
        query_lower = query.lower()

        # Determine which directories to search
        if document_type == DocumentType.BRD:
            search_dirs = [("brd", self.base_path / "brds")]
        elif document_type == DocumentType.PRD:
            search_dirs = [("prd", self.base_path / "prds")]
        else:
            search_dirs = [
                ("brd", self.base_path / "brds"),
                ("prd", self.base_path / "prds")
            ]

        # Search in each directory
        for doc_type, directory in search_dirs:
            for file_path in directory.glob(f"{doc_type.upper()}-*.json"):
                try:
                    document_dict = await self._read_json_file(file_path)

                    # Simple text search in document content
                    document_str = json.dumps(document_dict).lower()
                    if query_lower in document_str:
                        results.append({
                            "document_id": document_dict.get("document_id"),
                            "document_type": doc_type,
                            "title": document_dict.get("title") or document_dict.get("product_name"),
                            "created_at": document_dict.get("created_at"),
                            "match_preview": self._get_match_preview(document_str, query_lower)
                        })

                        if len(results) >= limit:
                            return results

                except Exception as e:
                    logger.warning(f"Failed to search in {file_path}: {e}")

        return results

    def _get_match_preview(self, text: str, query: str, context_length: int = 100) -> str:
        """Get a preview of text around the match."""
        index = text.find(query)
        if index == -1:
            return ""

        start = max(0, index - context_length)
        end = min(len(text), index + len(query) + context_length)

        preview = text[start:end]
        if start > 0:
            preview = "..." + preview
        if end < len(text):
            preview = preview + "..."

        return preview

    async def save_generation_history(
        self,
        request: GenerationRequest,
        response: GenerationResponse
    ) -> str:
        """Save generation request/response history."""
        history_id = f"GEN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        history_path = self.base_path / "history" / f"{history_id}.json"

        history_entry = {
            "history_id": history_id,
            "timestamp": datetime.now().isoformat(),
            "request": request.model_dump(),
            "response": response.model_dump()
        }

        await self._write_json_file(history_path, history_entry)

        logger.info(f"Saved generation history: {history_id}")
        return history_id

    async def save_validation_result(
        self,
        result: ValidationResult
    ) -> str:
        """Save validation result for a document."""
        validation_id = f"VAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        validation_path = self.base_path / "validations" / f"{validation_id}.json"

        validation_entry = {
            "validation_id": validation_id,
            "timestamp": datetime.now().isoformat(),
            "result": result.model_dump()
        }

        await self._write_json_file(validation_path, validation_entry)

        logger.info(f"Saved validation result: {validation_id}")
        return validation_id

    async def get_document_history(
        self,
        document_id: str
    ) -> List[Dict[str, Any]]:
        """Get version history for a document."""
        history = []
        history_dir = self.base_path / "history"

        # Search for history entries related to this document
        for file_path in history_dir.glob("GEN-*.json"):
            try:
                history_entry = await self._read_json_file(file_path)

                # Check if this history entry relates to the document
                response = history_entry.get("response", {})
                if response.get("brd_document", {}).get("document_id") == document_id or \
                   response.get("prd_document", {}).get("document_id") == document_id:
                    history.append({
                        "history_id": history_entry.get("history_id"),
                        "timestamp": history_entry.get("timestamp"),
                        "request_type": history_entry.get("request", {}).get("document_type"),
                        "cost_metadata": response.get("cost_metadata")
                    })

            except Exception as e:
                logger.warning(f"Failed to load history {file_path}: {e}")

        # Sort by timestamp
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return history

    async def cleanup_old_documents(
        self,
        days_old: int = 30
    ) -> int:
        """Clean up old documents and history."""
        count = 0
        cutoff_date = datetime.now() - timedelta(days=days_old)

        # Clean up archived documents
        archive_dir = self.base_path / "archive"
        if archive_dir.exists():
            for file_path in archive_dir.rglob("*.json"):
                try:
                    # Check file modification time
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff_date:
                        file_path.unlink()
                        count += 1
                except Exception as e:
                    logger.warning(f"Failed to clean up {file_path}: {e}")

        # Clean up old history
        history_dir = self.base_path / "history"
        for file_path in history_dir.glob("GEN-*.json"):
            try:
                history_entry = await self._read_json_file(file_path)
                timestamp = datetime.fromisoformat(
                    history_entry.get("timestamp", datetime.now().isoformat())
                )
                if timestamp < cutoff_date:
                    file_path.unlink()
                    count += 1
            except Exception as e:
                logger.warning(f"Failed to clean up history {file_path}: {e}")

        logger.info(f"Cleaned up {count} old documents/history entries")
        return count