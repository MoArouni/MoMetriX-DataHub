import json
from typing import Dict, List, Any, Optional

class DataToolFactory:
    """
    Factory class for creating and managing data tool schemas.
    This class is responsible for building schema definitions based on user input.
    """
    
    @staticmethod
    def create_schema(field_definitions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a schema definition based on field definitions
        
        Args:
            field_definitions: List of field definition dictionaries
                Each definition should have:
                - name: field name
                - type: data type (string, number, integer, boolean, date)
                - required: if the field is required
                - constraints: optional dict of constraints
        
        Returns:
            Dict containing the schema definition
        """
        schema = {
            "fields": [],
            "primaryKey": [],
            "required_fields": []
        }
        
        for field_def in field_definitions:
            field = {
                "name": field_def["name"],
                "type": field_def["type"]
            }
            
            # Add constraints if present
            if "constraints" in field_def:
                field["constraints"] = field_def["constraints"]
                
            # Add to schema
            schema["fields"].append(field)
            
            # Add to required fields if needed
            if field_def.get("required", False):
                schema["required_fields"].append(field_def["name"])
                
            # If primary key, add to primary key list
            if field_def.get("primary_key", False):
                schema["primaryKey"].append(field_def["name"])
        
        return schema
        
    @staticmethod
    def get_field_names(schema: Dict[str, Any]) -> List[str]:
        """
        Extract field names from a schema
        
        Args:
            schema: Schema dictionary
            
        Returns:
            List of field names
        """
        if not schema or "fields" not in schema:
            return []
            
        return [field["name"] for field in schema["fields"]]
        
    @staticmethod
    def get_field_types(schema: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract field types from a schema
        
        Args:
            schema: Schema dictionary
            
        Returns:
            Dictionary mapping field names to their types
        """
        if not schema or "fields" not in schema:
            return {}
            
        return {field["name"]: field["type"] for field in schema["fields"]}
        
    @staticmethod
    def get_required_fields(schema: Dict[str, Any]) -> List[str]:
        """
        Get list of required fields from schema
        
        Args:
            schema: Schema dictionary
            
        Returns:
            List of required field names
        """
        if not schema or "required_fields" not in schema:
            return []
            
        return schema["required_fields"]
        
    @staticmethod
    def to_json(schema: Dict[str, Any]) -> str:
        """
        Convert schema to JSON string
        
        Args:
            schema: Schema dictionary
            
        Returns:
            JSON string representation of the schema
        """
        return json.dumps(schema)
        
    @staticmethod
    def from_json(json_str: str) -> Dict[str, Any]:
        """
        Create schema from JSON string
        
        Args:
            json_str: JSON string representation of the schema
            
        Returns:
            Schema dictionary
        """
        if not json_str:
            return {}
            
        return json.loads(json_str) 