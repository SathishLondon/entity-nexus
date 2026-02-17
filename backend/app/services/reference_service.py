import os
import json
import pandas as pd
from typing import List, Dict, Optional
from glob import glob

REFERENCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "dnb_references")

class ReferenceService:
    def __init__(self):
        self.base_dir = REFERENCES_DIR

    def get_modules(self) -> List[Dict[str, str]]:
        """
        Scans the references directory and returns a list of available data modules.
        A module is defined by a common prefix for _DataDictionary.xlsm, _Sample.json, etc.
        """
        modules = {}
        
        # Find all Data Dictionary files as the source of truth for modules
        # Pattern: *_DataDictionary.xlsm
        dict_files = glob(os.path.join(self.base_dir, "*_DataDictionary.xlsm"))
        
        for f in dict_files:
            filename = os.path.basename(f)
            # Remove suffix to get module ID
            module_id = filename.replace("_DataDictionary.xlsm", "")
            
            modules[module_id] = {
                "id": module_id,
                "name": module_id.replace("_", " "), # Human readable(ish)
                "has_dictionary": True,
                "has_sample": os.path.exists(os.path.join(self.base_dir, f"{module_id}_Sample.json")) or os.path.exists(os.path.join(self.base_dir, f"{module_id}_JSON.json")),
                "has_pdf": os.path.exists(os.path.join(self.base_dir, f"{module_id}_PDF.pdf"))
            }
            
        return list(modules.values())

    def get_data_dictionary(self, module_id: str) -> List[Dict]:
        """
        Parses the Excel Data Dictionary for a given module.
        Returns a list of fields with metadata.
        """
        file_path = os.path.join(self.base_dir, f"{module_id}_DataDictionary.xlsm")
        if not os.path.exists(file_path):
            return []

        try:
            # Read the Excel file. Usually the first sheet contains the definitions.
            # We might need to adjust header row if it's not 0.
            df = pd.read_excel(file_path)
            
            # clean up column names (strip whitespace, lower case)
            df.columns = [str(c).strip() for c in df.columns]
            
            # Convert to list of dicts
            # Replace NaN with None/Empty string for JSON serialization
            return df.fillna("").to_dict(orient="records")
        except Exception as e:
            print(f"Error parsing dictionary for {module_id}: {e}")
            return []

    def get_sample(self, module_id: str) -> Optional[Dict]:
        """
        Returns the sample JSON for a given module.
        """
        # Try common suffixes
        candidates = [
            f"{module_id}_Sample.json",
            f"{module_id}_JSON.json"
        ]
        
        for suffix in candidates:
            file_path = os.path.join(self.base_dir, suffix)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"Error reading sample for {module_id}: {e}")
                    return None
                    
        return None

    # ========== Phase 1: Module Categorization & Excel Enhancements ==========
    
    def get_module_category(self, module_id: str) -> str:
        """
        Determine the category of a module based on its ID prefix.
        Categories: Standard, Additional, Side, Add-on
        """
        if module_id.startswith("Standard_DB_"):
            return "Standard"
        elif module_id.startswith("Additional_DB_"):
            return "Additional"
        elif module_id.startswith("Side_DB_"):
            return "Side"
        elif module_id.startswith("addon_") or module_id.startswith("Addon_"):
            return "Add-on"
        else:
            return "Unknown"
    
    def get_modules_by_category(self) -> Dict[str, List[Dict]]:
        """
        Group modules by category (Standard, Additional, Side, Add-on).
        Returns:
        {
            'Standard': [...],
            'Additional': [...],
            'Side': [...],
            'Add-on': [...]
        }
        """
        modules = self.get_modules()
        categorized = {
            'Standard': [],
            'Additional': [],
            'Side': [],
            'Add-on': [],
            'Unknown': []
        }
        
        for module in modules:
            category = self.get_module_category(module['id'])
            module['category'] = category
            categorized[category].append(module)
        
        return categorized
    
    def get_data_dictionary_from_excel(self, module_id: str) -> List[Dict[str, any]]:
        """
        Parse the 'Business Dictionary' sheet from Excel Data Dictionary.
        This provides richer field definitions than the default sheet.
        
        Returns list of:
        - Data Block: The block name
        - Data Name: Field name
        - Data Definition: Field description
        - Data Type: Data type
        - Monitorable: Y/N
        - Batch Applicable: Y/N
        """
        file_path = os.path.join(self.base_dir, f"{module_id}_DataDictionary.xlsm")
        if not os.path.exists(file_path):
            return []
        
        try:
            # Try to read "Business Dictionary" sheet
            try:
                df = pd.read_excel(file_path, sheet_name='Business Dictionary')
            except ValueError:
                # Sheet doesn't exist, fall back to first sheet
                df = pd.read_excel(file_path, sheet_name=0)
            
            # Clean up column names
            df.columns = [str(c).strip() for c in df.columns]
            
            # Filter to relevant blocks (if module name appears in block name)
            # This handles the case where one Excel file contains multiple blocks
            if 'Data Block' in df.columns:
                # Extract key parts of module_id for filtering
                # e.g., "Standard_DB_companyinfo_L1" -> look for blocks containing "companyinfo" and "L1"
                module_parts = module_id.replace("Standard_DB_", "").replace("Additional_DB_", "").replace("Side_DB_", "").split("_")
                
                # Filter blocks that contain any of the module parts
                mask = df['Data Block'].str.contains('|'.join(module_parts), case=False, na=False)
                df_filtered = df[mask]
                
                # If filtering removed everything, return all (better than nothing)
                if df_filtered.empty:
                    print(f"Warning: No matching blocks found for {module_id}, returning all blocks")
                    return df.fillna("").to_dict(orient="records")
                
                return df_filtered.fillna("").to_dict(orient="records")
            
            # If no "Data Block" column, return all
            return df.fillna("").to_dict(orient="records")
            
        except Exception as e:
            print(f"Error parsing Excel dictionary for {module_id}: {e}")
            return []
    
    def get_available_blocks(self, module_id: str) -> List[str]:
        """
        Get list of unique data block names from the Excel dictionary.
        Useful for filtering UI.
        """
        file_path = os.path.join(self.base_dir, f"{module_id}_DataDictionary.xlsm")
        if not os.path.exists(file_path):
            return []
        
        try:
            df = pd.read_excel(file_path, sheet_name='Business Dictionary')
            df.columns = [str(c).strip() for c in df.columns]
            
            if 'Data Block' in df.columns:
                blocks = df['Data Block'].dropna().unique().tolist()
                return sorted(blocks)
            
            return []
        except Exception as e:
            print(f"Error getting blocks for {module_id}: {e}")
            return []
    
    def filter_dictionary_by_block(self, module_id: str, block_names: List[str]) -> List[Dict]:
        """
        Filter dictionary entries by specific block names.
        Useful for showing only relevant blocks (e.g., only 'companyinfo_L1_v1')
        """
        all_data = self.get_data_dictionary_from_excel(module_id)
        
        if not block_names:
            return all_data
        
        # Filter to selected blocks
        filtered = [row for row in all_data if row.get('Data Block') in block_names]
        return filtered

    # ========== Phase 2: Analysis & Compare Features ==========
    
    def extract_json_paths(self, module_id: str) -> List[str]:
        """
        Extract all JSON paths from the sample JSON.
        Returns list of paths like: organization.primaryName, organization.primaryAddress.streetAddress
        """
        sample = self.get_sample(module_id)
        if not sample:
            return []
        
        paths = []
        
        def extract_paths(obj, prefix=""):
            """Recursively extract paths from nested JSON"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{prefix}.{key}" if prefix else key
                    paths.append(current_path)
                    if isinstance(value, (dict, list)):
                        extract_paths(value, current_path)
            elif isinstance(obj, list) and obj:
                # For arrays, explore the first item
                extract_paths(obj[0], prefix)
        
        extract_paths(sample)
        return sorted(set(paths))
    
    def analyze_module(self, module_id: str) -> Dict[str, any]:
        """
        Comprehensive analysis of a module.
        Returns:
        - field_count: Total number of fields
        - data_types: Distribution of data types
        - blocks: List of unique blocks
        - complexity_score: 1-10 rating based on field count and nesting
        - json_paths: All JSON paths in sample
        """
        # Get Excel data
        excel_data = self.get_data_dictionary_from_excel(module_id)
        blocks = self.get_available_blocks(module_id)
        json_paths = self.extract_json_paths(module_id)
        
        # Analyze data types
        data_types = {}
        for entry in excel_data:
            dtype = entry.get('Data Type', 'unknown')
            data_types[dtype] = data_types.get(dtype, 0) + 1
        
        # Calculate complexity score (1-10)
        field_count = len(excel_data)
        block_count = len(blocks)
        max_nesting = max([path.count('.') for path in json_paths]) if json_paths else 0
        
        # Scoring formula
        complexity = min(10, (
            (field_count / 1000) * 3 +  # Field count contribution (max 3 points)
            (block_count / 10) * 3 +     # Block count contribution (max 3 points)
            (max_nesting / 5) * 4        # Nesting depth contribution (max 4 points)
        ))
        
        return {
            'module_id': module_id,
            'field_count': field_count,
            'block_count': block_count,
            'data_types': data_types,
            'blocks': blocks,
            'json_paths_count': len(json_paths),
            'max_nesting_depth': max_nesting,
            'complexity_score': round(complexity, 1),
            'complexity_label': self._get_complexity_label(complexity)
        }
    
    def _get_complexity_label(self, score: float) -> str:
        """Convert complexity score to label"""
        if score <= 3:
            return "Simple"
        elif score <= 6:
            return "Moderate"
        elif score <= 8:
            return "Complex"
        else:
            return "Very Complex"
    
    def compare_modules(self, module_id_1: str, module_id_2: str) -> Dict[str, any]:
        """
        Compare two modules and identify differences.
        Returns:
        - common_fields: Fields present in both
        - only_in_module1: Fields only in first module
        - only_in_module2: Fields only in second module
        - type_differences: Fields with different data types
        - coverage_comparison: Which module has more comprehensive data
        """
        # Get data for both modules
        data1 = self.get_data_dictionary_from_excel(module_id_1)
        data2 = self.get_data_dictionary_from_excel(module_id_2)
        
        # Extract field names
        fields1 = set([entry.get('Data Name', '') for entry in data1])
        fields2 = set([entry.get('Data Name', '') for entry in data2])
        
        # Find common and unique fields
        common_fields = fields1 & fields2
        only_in_1 = fields1 - fields2
        only_in_2 = fields2 - fields1
        
        # Check for type differences in common fields
        type_differences = []
        field_map1 = {entry.get('Data Name'): entry.get('Data Type') for entry in data1}
        field_map2 = {entry.get('Data Name'): entry.get('Data Type') for entry in data2}
        
        for field in common_fields:
            type1 = field_map1.get(field, 'unknown')
            type2 = field_map2.get(field, 'unknown')
            if type1 != type2:
                type_differences.append({
                    'field': field,
                    'type_in_module1': type1,
                    'type_in_module2': type2
                })
        
        # Coverage comparison
        coverage_pct_1 = (len(common_fields) / len(fields1) * 100) if fields1 else 0
        coverage_pct_2 = (len(common_fields) / len(fields2) * 100) if fields2 else 0
        
        return {
            'module1': {
                'id': module_id_1,
                'total_fields': len(fields1),
                'coverage_percentage': round(coverage_pct_1, 1)
            },
            'module2': {
                'id': module_id_2,
                'total_fields': len(fields2),
                'coverage_percentage': round(coverage_pct_2, 1)
            },
            'comparison': {
                'common_fields_count': len(common_fields),
                'only_in_module1_count': len(only_in_1),
                'only_in_module2_count': len(only_in_2),
                'type_differences_count': len(type_differences),
                'common_fields': sorted(list(common_fields))[:50],  # First 50
                'only_in_module1': sorted(list(only_in_1))[:50],
                'only_in_module2': sorted(list(only_in_2))[:50],
                'type_differences': type_differences[:20]  # First 20
            },
            'recommendation': self._get_comparison_recommendation(
                len(fields1), len(fields2), len(common_fields)
            )
        }
    
    def _get_comparison_recommendation(self, count1: int, count2: int, common: int) -> str:
        """Generate recommendation based on comparison"""
        if common / max(count1, count2) > 0.8:
            return "Modules are very similar. Consider using the more comprehensive one."
        elif common / max(count1, count2) > 0.5:
            return "Modules have significant overlap but also unique fields. Review differences carefully."
        else:
            return "Modules are quite different. They likely serve different use cases."

    # ========== Phase 3: Field Mapping Feature ==========
    
    def _get_canonical_schema(self) -> Dict[str, List[Dict]]:
        """
        Get the canonical schema definition.
        In production, this would come from a database or config file.
        For now, we'll use a simplified version based on the existing models.
        """
        return {
            'core_fields': [
                {'field': 'name', 'type': 'string', 'description': 'Primary business name'},
                {'field': 'legal_name', 'type': 'string', 'description': 'Legal registered name'},
                {'field': 'registration_number', 'type': 'string', 'description': 'Company registration number'},
                {'field': 'jurisdiction_code', 'type': 'string', 'description': 'ISO country code'},
                {'field': 'duns', 'type': 'string', 'description': 'D&B DUNS number'},
            ],
            'address_fields': [
                {'field': 'street_address', 'type': 'string', 'description': 'Street address'},
                {'field': 'city', 'type': 'string', 'description': 'City name'},
                {'field': 'postal_code', 'type': 'string', 'description': 'Postal/ZIP code'},
                {'field': 'country_code', 'type': 'string', 'description': 'ISO country code'},
                {'field': 'region', 'type': 'string', 'description': 'State/province/region'},
            ],
            'financial_fields': [
                {'field': 'revenue_usd', 'type': 'float', 'description': 'Annual revenue in USD'},
                {'field': 'employee_count', 'type': 'integer', 'description': 'Number of employees'},
                {'field': 'year_started', 'type': 'integer', 'description': 'Year business started'},
            ],
            'hierarchy_fields': [
                {'field': 'parent_duns', 'type': 'string', 'description': 'Parent company DUNS'},
                {'field': 'ultimate_parent_duns', 'type': 'string', 'description': 'Ultimate parent DUNS'},
                {'field': 'ownership_percentage', 'type': 'float', 'description': 'Ownership percentage'},
            ]
        }
    
    def _get_field_aliases(self) -> Dict[str, List[str]]:
        """
        Get common aliases for canonical fields.
        Used for fuzzy matching.
        """
        return {
            'name': ['business_name', 'company_name', 'organization_name', 'primary_name', 'trade_name'],
            'legal_name': ['registered_name', 'legal_business_name', 'official_name'],
            'registration_number': ['company_number', 'reg_number', 'registration_id', 'company_id'],
            'duns': ['duns_number', 'd_u_n_s', 'dunsNumber'],
            'street_address': ['address_line_1', 'street', 'address', 'street_name'],
            'city': ['town', 'locality', 'city_name'],
            'postal_code': ['zip_code', 'postcode', 'zip', 'postal'],
            'country_code': ['country', 'country_iso', 'iso_country'],
            'revenue_usd': ['annual_revenue', 'revenue', 'sales', 'turnover'],
            'employee_count': ['employees', 'headcount', 'staff_count', 'number_of_employees'],
        }
    
    def suggest_field_mappings(self, module_id: str) -> Dict[str, List[Dict]]:
        """
        Suggest mappings from D&B fields to canonical model.
        Uses exact matching, fuzzy matching, and semantic matching.
        
        Returns suggestions grouped by confidence level:
        - exact: 100% confidence (exact match)
        - high: 90-99% confidence (fuzzy match with high score)
        - medium: 80-89% confidence (fuzzy match with medium score)
        - low: < 80% confidence (semantic match)
        """
        from fuzzywuzzy import fuzz
        
        # Get D&B fields
        dnb_fields = self.get_data_dictionary_from_excel(module_id)
        
        # Get canonical schema and aliases
        canonical_schema = self._get_canonical_schema()
        aliases = self._get_field_aliases()
        
        # Flatten canonical fields
        all_canonical_fields = []
        for category, fields in canonical_schema.items():
            for field in fields:
                field['category'] = category
                all_canonical_fields.append(field)
        
        # Store suggestions by confidence level
        suggestions = {
            'exact': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        # Process each D&B field
        for dnb_field in dnb_fields:
            dnb_name = dnb_field.get('Data Name', '').lower().strip()
            if not dnb_name:
                continue
            
            best_match = None
            best_score = 0
            match_type = None
            
            # Try exact matching first
            for canonical_field in all_canonical_fields:
                canonical_name = canonical_field['field'].lower()
                
                # Check exact match
                if dnb_name == canonical_name:
                    best_match = canonical_field
                    best_score = 100
                    match_type = 'exact'
                    break
                
                # Check aliases
                field_aliases = aliases.get(canonical_field['field'], [])
                for alias in field_aliases:
                    if dnb_name == alias.lower():
                        best_match = canonical_field
                        best_score = 100
                        match_type = 'exact_alias'
                        break
                
                if best_score == 100:
                    break
            
            # If no exact match, try fuzzy matching
            if best_score < 100:
                for canonical_field in all_canonical_fields:
                    canonical_name = canonical_field['field'].lower()
                    
                    # Fuzzy match against field name
                    score = fuzz.ratio(dnb_name, canonical_name)
                    
                    # Also check against aliases
                    field_aliases = aliases.get(canonical_field['field'], [])
                    for alias in field_aliases:
                        alias_score = fuzz.ratio(dnb_name, alias.lower())
                        score = max(score, alias_score)
                    
                    if score > best_score:
                        best_score = score
                        best_match = canonical_field
                        match_type = 'fuzzy'
            
            # Only include matches above 75% confidence
            if best_match and best_score >= 75:
                suggestion = {
                    'dnb_field': dnb_field.get('Data Name'),
                    'dnb_type': dnb_field.get('Data Type'),
                    'dnb_definition': dnb_field.get('Data Definition', '')[:200],  # Truncate
                    'canonical_field': best_match['field'],
                    'canonical_type': best_match['type'],
                    'canonical_description': best_match['description'],
                    'category': best_match['category'],
                    'confidence_score': best_score,
                    'match_type': match_type
                }
                
                # Categorize by confidence
                if best_score == 100:
                    suggestions['exact'].append(suggestion)
                elif best_score >= 90:
                    suggestions['high'].append(suggestion)
                elif best_score >= 80:
                    suggestions['medium'].append(suggestion)
                else:
                    suggestions['low'].append(suggestion)
        
        # Sort each category by confidence score (descending)
        for category in suggestions:
            suggestions[category].sort(key=lambda x: x['confidence_score'], reverse=True)
        
        # Add summary statistics
        total_dnb_fields = len(dnb_fields)
        total_suggestions = sum(len(suggestions[cat]) for cat in suggestions)
        
        return {
            'module_id': module_id,
            'summary': {
                'total_dnb_fields': total_dnb_fields,
                'total_suggestions': total_suggestions,
                'coverage_percentage': round((total_suggestions / total_dnb_fields * 100), 1) if total_dnb_fields > 0 else 0,
                'exact_matches': len(suggestions['exact']),
                'high_confidence': len(suggestions['high']),
                'medium_confidence': len(suggestions['medium']),
                'low_confidence': len(suggestions['low'])
            },
            'suggestions': suggestions
        }
    
    def get_canonical_schema_endpoint(self) -> Dict[str, List[Dict]]:
        """
        Endpoint to get the canonical schema.
        Used by the frontend to display canonical fields.
        """
        return self._get_canonical_schema()
    
    # ========== Phase 4: Hierarchy Visualization ==========
    
    def extract_hierarchy_structure(self, module_id: str) -> Dict[str, any]:
        """
        Extract hierarchy structure from D&B sample JSON.
        Looks for common hierarchy patterns in the JSON.
        
        Returns:
        - nodes: List of entities in the hierarchy
        - relationships: List of parent-child relationships
        - root_node: The top-level entity
        - visualization_data: D3.js compatible format
        """
        sample = self.get_sample(module_id)
        if not sample:
            return {
                'error': 'No sample JSON available',
                'nodes': [],
                'relationships': [],
                'root_node': None
            }
        
        nodes = []
        relationships = []
        
        # Extract organization info (root node)
        org = sample.get('organization', {})
        if org:
            root_duns = org.get('duns') or sample.get('inquiryDetail', {}).get('duns')
            root_name = org.get('primaryName') or org.get('organizationName', {}).get('name', 'Unknown')
            
            if root_duns:
                nodes.append({
                    'id': root_duns,
                    'name': root_name,
                    'type': 'subject',
                    'level': 0
                })
        
        # Look for hierarchy data in common locations
        hierarchy_paths = [
            'organization.corporateLinkage',
            'organization.hierarchyConnections',
            'familyTreeMembers',
            'corporateLinkage',
            'hierarchies'
        ]
        
        for path in hierarchy_paths:
            data = self._get_nested_value(sample, path)
            if data:
                extracted = self._extract_hierarchy_from_data(data, nodes, relationships)
                nodes.extend(extracted['nodes'])
                relationships.extend(extracted['relationships'])
        
        # Build tree structure for visualization
        tree_data = self._build_tree_structure(nodes, relationships)
        
        return {
            'module_id': module_id,
            'nodes': nodes,
            'relationships': relationships,
            'root_node': nodes[0] if nodes else None,
            'tree_data': tree_data,
            'summary': {
                'total_nodes': len(nodes),
                'total_relationships': len(relationships),
                'max_depth': self._calculate_max_depth(tree_data)
            }
        }
    
    def _get_nested_value(self, obj: Dict, path: str) -> any:
        """Get nested value from dict using dot notation path"""
        keys = path.split('.')
        current = obj
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return None
            else:
                return None
        return current
    
    def _extract_hierarchy_from_data(self, data: any, existing_nodes: List, existing_relationships: List) -> Dict:
        """Extract hierarchy nodes and relationships from data"""
        nodes = []
        relationships = []
        
        if isinstance(data, dict):
            # Check for parent information
            parent = data.get('parent') or data.get('parentOrganization')
            if parent:
                parent_duns = parent.get('duns')
                parent_name = parent.get('primaryName') or parent.get('name', 'Unknown Parent')
                if parent_duns:
                    nodes.append({
                        'id': parent_duns,
                        'name': parent_name,
                        'type': 'parent',
                        'level': -1
                    })
            
            # Check for ultimate parent
            ultimate = data.get('ultimateParent') or data.get('globalUltimate')
            if ultimate:
                ultimate_duns = ultimate.get('duns')
                ultimate_name = ultimate.get('primaryName') or ultimate.get('name', 'Unknown Ultimate')
                if ultimate_duns:
                    nodes.append({
                        'id': ultimate_duns,
                        'name': ultimate_name,
                        'type': 'ultimate_parent',
                        'level': -2
                    })
            
            # Check for subsidiaries/children
            subsidiaries = data.get('subsidiaries') or data.get('children') or data.get('familyTreeMembersDownward')
            if isinstance(subsidiaries, list):
                for idx, sub in enumerate(subsidiaries):
                    if isinstance(sub, dict):
                        sub_duns = sub.get('duns')
                        sub_name = sub.get('primaryName') or sub.get('name', f'Subsidiary {idx+1}')
                        if sub_duns:
                            nodes.append({
                                'id': sub_duns,
                                'name': sub_name,
                                'type': 'subsidiary',
                                'level': 1
                            })
        
        elif isinstance(data, list):
            # Process array of hierarchy members
            for item in data:
                if isinstance(item, dict):
                    extracted = self._extract_hierarchy_from_data(item, existing_nodes, existing_relationships)
                    nodes.extend(extracted['nodes'])
                    relationships.extend(extracted['relationships'])
        
        return {'nodes': nodes, 'relationships': relationships}
    
    def _build_tree_structure(self, nodes: List[Dict], relationships: List[Dict]) -> Dict:
        """Build D3.js compatible tree structure"""
        if not nodes:
            return {}
        
        # Find root (subject entity)
        root = next((n for n in nodes if n.get('type') == 'subject'), nodes[0])
        
        # Build tree recursively
        def build_node(node_id: str, visited: set) -> Dict:
            if node_id in visited:
                return None
            visited.add(node_id)
            
            node = next((n for n in nodes if n['id'] == node_id), None)
            if not node:
                return None
            
            tree_node = {
                'id': node['id'],
                'name': node['name'],
                'type': node.get('type', 'unknown'),
                'children': []
            }
            
            # Find children
            child_rels = [r for r in relationships if r.get('parent_id') == node_id]
            for rel in child_rels:
                child = build_node(rel['child_id'], visited)
                if child:
                    tree_node['children'].append(child)
            
            return tree_node
        
        return build_node(root['id'], set()) or {}
    
    def _calculate_max_depth(self, tree: Dict, current_depth: int = 0) -> int:
        """Calculate maximum depth of tree"""
        if not tree or not tree.get('children'):
            return current_depth
        
        max_child_depth = current_depth
        for child in tree.get('children', []):
            child_depth = self._calculate_max_depth(child, current_depth + 1)
            max_child_depth = max(max_child_depth, child_depth)
        
        return max_child_depth
    
    def get_hierarchy_summary(self) -> Dict[str, any]:
        """
        Get summary of hierarchy capabilities across all modules.
        Shows which modules have hierarchy data.
        """
        modules = self.get_modules()
        hierarchy_modules = []
        
        for module in modules:
            module_id = module['id']
            
            # Check if module name suggests hierarchy data
            hierarchy_keywords = ['hierarchy', 'linkage', 'family', 'tree', 'ownership', 'parent']
            has_hierarchy_name = any(keyword in module_id.lower() for keyword in hierarchy_keywords)
            
            if has_hierarchy_name:
                # Try to extract hierarchy
                structure = self.extract_hierarchy_structure(module_id)
                if structure.get('nodes'):
                    hierarchy_modules.append({
                        'module_id': module_id,
                        'module_name': module.get('name'),
                        'node_count': len(structure['nodes']),
                        'relationship_count': len(structure['relationships'])
                    })
        
        return {
            'total_modules': len(modules),
            'hierarchy_modules': len(hierarchy_modules),
            'modules': hierarchy_modules
        }
