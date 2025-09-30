"""
Base repository interface for document storage.

This module provides the abstract base class for all repository implementations,
defining the interface for storing and retrieving BRD/PRD documents.
"""

import abc
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

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


class BaseRepository(abc.ABC):
    """Abstract base class for document repositories."""

    @abc.abstractmethod
    async def save_brd(self, document: BRDDocument) -> str:
        """
        Save a BRD document.

        Args:
            document: The BRD document to save

        Returns:
            The document ID

        Raises:
            DocumentAlreadyExistsError: If document with same ID exists
            StorageError: If storage operation fails
        """
        pass

    @abc.abstractmethod
    async def save_prd(self, document: PRDDocument) -> str:
        """
        Save a PRD document.

        Args:
            document: The PRD document to save

        Returns:
            The document ID

        Raises:
            DocumentAlreadyExistsError: If document with same ID exists
            StorageError: If storage operation fails
        """
        pass

    @abc.abstractmethod
    async def get_brd(self, document_id: str) -> BRDDocument:
        """
        Retrieve a BRD document by ID.

        Args:
            document_id: The document ID

        Returns:
            The BRD document

        Raises:
            DocumentNotFoundError: If document not found
            StorageError: If retrieval fails
        """
        pass

    @abc.abstractmethod
    async def get_prd(self, document_id: str) -> PRDDocument:
        """
        Retrieve a PRD document by ID.

        Args:
            document_id: The document ID

        Returns:
            The PRD document

        Raises:
            DocumentNotFoundError: If document not found
            StorageError: If retrieval fails
        """
        pass

    @abc.abstractmethod
    async def list_brds(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters
    ) -> List[BRDDocument]:
        """
        List BRD documents with optional filtering.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            **filters: Additional filter criteria

        Returns:
            List of BRD documents

        Raises:
            StorageError: If query fails
        """
        pass

    @abc.abstractmethod
    async def list_prds(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters
    ) -> List[PRDDocument]:
        """
        List PRD documents with optional filtering.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            **filters: Additional filter criteria

        Returns:
            List of PRD documents

        Raises:
            StorageError: If query fails
        """
        pass

    @abc.abstractmethod
    async def update_brd(
        self,
        document_id: str,
        updates: Dict[str, Any]
    ) -> BRDDocument:
        """
        Update a BRD document.

        Args:
            document_id: The document ID
            updates: Dictionary of fields to update

        Returns:
            Updated BRD document

        Raises:
            DocumentNotFoundError: If document not found
            StorageError: If update fails
        """
        pass

    @abc.abstractmethod
    async def update_prd(
        self,
        document_id: str,
        updates: Dict[str, Any]
    ) -> PRDDocument:
        """
        Update a PRD document.

        Args:
            document_id: The document ID
            updates: Dictionary of fields to update

        Returns:
            Updated PRD document

        Raises:
            DocumentNotFoundError: If document not found
            StorageError: If update fails
        """
        pass

    @abc.abstractmethod
    async def delete_brd(self, document_id: str) -> bool:
        """
        Delete a BRD document.

        Args:
            document_id: The document ID

        Returns:
            True if deleted successfully

        Raises:
            DocumentNotFoundError: If document not found
            StorageError: If deletion fails
        """
        pass

    @abc.abstractmethod
    async def delete_prd(self, document_id: str) -> bool:
        """
        Delete a PRD document.

        Args:
            document_id: The document ID

        Returns:
            True if deleted successfully

        Raises:
            DocumentNotFoundError: If document not found
            StorageError: If deletion fails
        """
        pass

    @abc.abstractmethod
    async def search(
        self,
        query: str,
        document_type: Optional[DocumentType] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for documents by text query.

        Args:
            query: Search query string
            document_type: Optional filter by document type
            limit: Maximum results to return

        Returns:
            List of matching documents with metadata

        Raises:
            StorageError: If search fails
        """
        pass

    @abc.abstractmethod
    async def save_generation_history(
        self,
        request: GenerationRequest,
        response: GenerationResponse
    ) -> str:
        """
        Save generation request/response history.

        Args:
            request: The generation request
            response: The generation response

        Returns:
            History entry ID

        Raises:
            StorageError: If save fails
        """
        pass

    @abc.abstractmethod
    async def save_validation_result(
        self,
        result: ValidationResult
    ) -> str:
        """
        Save validation result for a document.

        Args:
            result: The validation result

        Returns:
            Validation result ID

        Raises:
            StorageError: If save fails
        """
        pass

    @abc.abstractmethod
    async def get_document_history(
        self,
        document_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get version history for a document.

        Args:
            document_id: The document ID

        Returns:
            List of version history entries

        Raises:
            DocumentNotFoundError: If document not found
            StorageError: If retrieval fails
        """
        pass

    @abc.abstractmethod
    async def cleanup_old_documents(
        self,
        days_old: int = 30
    ) -> int:
        """
        Clean up old documents and history.

        Args:
            days_old: Delete documents older than this many days

        Returns:
            Number of documents deleted

        Raises:
            StorageError: If cleanup fails
        """
        pass

    # Helper methods that can be implemented by base class

    async def exists_brd(self, document_id: str) -> bool:
        """Check if a BRD document exists."""
        try:
            await self.get_brd(document_id)
            return True
        except DocumentNotFoundError:
            return False

    async def exists_prd(self, document_id: str) -> bool:
        """Check if a PRD document exists."""
        try:
            await self.get_prd(document_id)
            return True
        except DocumentNotFoundError:
            return False

    async def get_linked_documents(
        self,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Get BRD and its linked PRD or vice versa.

        Args:
            document_id: The document ID (BRD or PRD)

        Returns:
            Dictionary with 'brd' and 'prd' keys

        Raises:
            DocumentNotFoundError: If document not found
        """
        result = {"brd": None, "prd": None}

        # Try as BRD first
        if document_id.startswith("BRD-"):
            try:
                brd = await self.get_brd(document_id)
                result["brd"] = brd

                # Find related PRDs
                prds = await self.list_prds(related_brd_id=document_id)
                if prds:
                    result["prd"] = prds[0]  # Take first matching PRD
            except DocumentNotFoundError:
                pass

        # Try as PRD
        elif document_id.startswith("PRD-"):
            try:
                prd = await self.get_prd(document_id)
                result["prd"] = prd

                # Get related BRD
                if prd.related_brd_id:
                    try:
                        result["brd"] = await self.get_brd(prd.related_brd_id)
                    except DocumentNotFoundError:
                        pass
            except DocumentNotFoundError:
                pass

        if not result["brd"] and not result["prd"]:
            raise DocumentNotFoundError(f"Document {document_id} not found")

        return result