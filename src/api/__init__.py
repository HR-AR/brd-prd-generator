"""
API module for BRD/PRD Generator.
"""

from .endpoints import router
from .dependencies import (
    get_document_generator,
    get_repository_instance,
    get_llm_factory_instance,
    verify_api_key,
    check_rate_limit,
    ws_manager,
    GeneratorDep,
    RepositoryDep,
    ClientIdDep,
    ValidatorDep
)

__all__ = [
    'router',
    'get_document_generator',
    'get_repository_instance',
    'get_llm_factory_instance',
    'verify_api_key',
    'check_rate_limit',
    'ws_manager',
    'GeneratorDep',
    'RepositoryDep',
    'ClientIdDep',
    'ValidatorDep'
]