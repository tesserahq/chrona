from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.prompt import Prompt
from app.schemas.prompt import PromptCreate, PromptUpdate
from app.utils.db.filtering import apply_filters
from app.services.soft_delete_service import SoftDeleteService

"""
Module providing the PromptService class for managing Prompt entities.
Includes methods for CRUD operations and dynamic searching with flexible filters.
"""


class PromptService(SoftDeleteService[Prompt]):
    def __init__(self, db: Session):
        super().__init__(db, Prompt)

    def get_prompt(self, prompt_id: UUID) -> Optional[Prompt]:
        """Fetch a single prompt by ID."""
        return self.db.query(Prompt).filter(Prompt.id == prompt_id).first()

    def get_prompt_by_prompt_id(self, prompt_id: str) -> Optional[Prompt]:
        """Fetch a single prompt by prompt_id string."""
        return self.db.query(Prompt).filter(Prompt.prompt_id == prompt_id).first()

    def get_prompt_by_id_or_prompt_id(
        self, identifier: Union[UUID, str]
    ) -> Optional[Prompt]:
        """
        Fetch a single prompt by either UUID ID or prompt_id string.

        Args:
            identifier: Either a UUID (for the id field) or a string (for the prompt_id field)

        Returns:
            Optional[Prompt]: The prompt if found, None otherwise
        """
        if isinstance(identifier, UUID):
            return self.get_prompt(identifier)
        elif isinstance(identifier, str):
            return self.get_prompt_by_prompt_id(identifier)
        else:
            raise ValueError(
                f"Identifier must be UUID or string, got {type(identifier)}"
            )

    def get_prompts(self, skip: int = 0, limit: int = 100) -> List[Prompt]:
        """Fetch a list of prompts with pagination."""
        return self.db.query(Prompt).offset(skip).limit(limit).all()

    def create_prompt(self, prompt: PromptCreate) -> Prompt:
        """Create a new prompt."""
        db_prompt = Prompt(**prompt.model_dump())
        self.db.add(db_prompt)
        self.db.commit()
        self.db.refresh(db_prompt)
        return db_prompt

    def update_prompt(self, prompt_id: UUID, prompt: PromptUpdate) -> Optional[Prompt]:
        """Update an existing prompt."""
        db_prompt = self.db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if db_prompt:
            update_data = prompt.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_prompt, key, value)
            self.db.commit()
            self.db.refresh(db_prompt)
        return db_prompt

    def delete_prompt(self, prompt_id: UUID) -> bool:
        """Soft delete a prompt and return a boolean indicating success."""
        return self.delete_record(prompt_id)

    def search(self, filters: Dict[str, Any]) -> List[Prompt]:
        """
        Search prompts based on provided filters.

        Args:
            filters: Dictionary of filters where key is the field name and value is either:
                - A direct value (uses = operator)
                - A dictionary with 'operator' and 'value', e.g. {"operator": "ilike", "value": "%system%"}

        Returns:
            List[Prompt]: List of prompts matching the filter criteria.

        Example:
            filters = {
                "name": {"operator": "ilike", "value": "%system%"},
                "type": "system",
                "workspace_id": workspace_uuid,
                "created_by_id": user_uuid
            }
        """
        query = self.db.query(Prompt)
        query = apply_filters(query, Prompt, filters)
        return query.all()

    def get_prompts_by_workspace(
        self, workspace_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Prompt]:
        """Get all prompts for a specific workspace."""
        return (
            self.db.query(Prompt)
            .filter(Prompt.workspace_id == workspace_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_prompts_by_type(
        self,
        prompt_type: str,
        workspace_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Prompt]:
        """Get prompts by type, optionally filtered by workspace."""
        query = self.db.query(Prompt).filter(Prompt.type == prompt_type)
        if workspace_id:
            query = query.filter(Prompt.workspace_id == workspace_id)
        return query.offset(skip).limit(limit).all()

    def get_prompts_by_creator(
        self,
        created_by_id: UUID,
        workspace_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Prompt]:
        """Get prompts created by a specific user, optionally filtered by workspace."""
        query = self.db.query(Prompt).filter(Prompt.created_by_id == created_by_id)
        if workspace_id:
            query = query.filter(Prompt.workspace_id == workspace_id)
        return query.offset(skip).limit(limit).all()
