from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from app.services.reference_service import ReferenceService

router = APIRouter()
service = ReferenceService()

@router.get("/modules", response_model=List[Dict[str, Any]])
def get_modules():
    """List all available D&B data modules found in the references directory."""
    return service.get_modules()

@router.get("/{module_id}/dictionary", response_model=List[Dict[str, Any]])
def get_dictionary(module_id: str):
    """Get the parsed data dictionary (fields/definitions) for a module."""
    data = service.get_data_dictionary(module_id)
    if not data:
        # It's possible the file exists but parsing failed, or file doesn't exist
        # We'll return empty list if valid module but no dict, or 404 if invalid?
        # For now, just return empty list to avoid breaking UI
        return []
    return data

@router.get("/{module_id}/sample", response_model=Optional[Dict[str, Any]])
def get_sample(module_id: str):
    """Get the sample JSON payload for a module."""
    data = service.get_sample(module_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Sample not found for this module")
    return data

# ========== Phase 1: Enhanced Endpoints ==========

@router.get("/modules/by-category", response_model=Dict[str, List[Dict[str, Any]]])
def get_modules_by_category():
    """Get modules grouped by category (Standard, Additional, Side, Add-on)"""
    return service.get_modules_by_category()

@router.get("/{module_id}/dictionary/excel", response_model=List[Dict[str, Any]])
def get_dictionary_from_excel(module_id: str):
    """Get the Business Dictionary from Excel with richer field definitions"""
    data = service.get_data_dictionary_from_excel(module_id)
    if not data:
        return []
    return data

@router.get("/{module_id}/available-blocks", response_model=List[str])
def get_available_blocks(module_id: str):
    """Get list of available data blocks in the Excel dictionary"""
    return service.get_available_blocks(module_id)

@router.get("/{module_id}/dictionary/filtered", response_model=List[Dict[str, Any]])
def get_filtered_dictionary(module_id: str, blocks: Optional[str] = None):
    """Get dictionary filtered by specific block names (comma-separated)"""
    block_list = blocks.split(',') if blocks else []
    return service.filter_dictionary_by_block(module_id, block_list)

# ========== Phase 2: Analysis & Compare Endpoints ==========

@router.get("/{module_id}/analyze", response_model=Dict[str, Any])
def analyze_module(module_id: str):
    """Get comprehensive analysis of a module including complexity score"""
    return service.analyze_module(module_id)

@router.get("/{module_id}/json-paths", response_model=List[str])
def get_json_paths(module_id: str):
    """Get all JSON paths from the sample JSON"""
    return service.extract_json_paths(module_id)

@router.get("/{module_id}/compare/{other_module_id}", response_model=Dict[str, Any])
def compare_modules(module_id: str, other_module_id: str):
    """Compare two modules and identify differences"""
    return service.compare_modules(module_id, other_module_id)

# ========== Phase 3: Field Mapping Endpoints ==========

@router.get("/canonical-schema", response_model=Dict[str, List[Dict[str, Any]]])
def get_canonical_schema():
    """Get the canonical schema definition"""
    return service.get_canonical_schema_endpoint()

@router.get("/{module_id}/mappings", response_model=Dict[str, Any])
def get_field_mappings(module_id: str):
    """Get suggested field mappings from D&B to canonical model"""
    return service.suggest_field_mappings(module_id)

# ========== Phase 4: Hierarchy Visualization Endpoints ==========

@router.get("/{module_id}/hierarchy", response_model=Dict[str, Any])
def get_hierarchy_structure(module_id: str):
    """Extract and visualize hierarchy structure from module sample"""
    return service.extract_hierarchy_structure(module_id)

@router.get("/hierarchy/summary", response_model=Dict[str, Any])
def get_hierarchy_summary():
    """Get summary of hierarchy capabilities across all modules"""
    return service.get_hierarchy_summary()
