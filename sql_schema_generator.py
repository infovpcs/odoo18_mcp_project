import pandas as pd
import sqlparse
import json
from typing import Dict, List, Optional
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OdooDBConnector:
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Connect to Odoo PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(
                dbname=os.getenv("ODOO_DB", "llmdb17"),
                user=os.getenv("DB_USER", "odoo"),
                password=os.getenv("DB_PASSWORD", "odoo"),
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5435")
            )
            self.connection.autocommit = True  # Prevent transaction issues
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            print("Successfully connected to Odoo database")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a query with proper error handling."""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            self.connection.rollback()  # Rollback on error
            return []
        except Exception as e:
            print(f"Error executing query: {e}")
            return []

    def get_field_info(self, table_name: str) -> Dict:
        """Get field information for a given table from Odoo database."""
        # First check if table exists
        table_check_query = """
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_name = %s 
                AND table_schema = 'public'
            );
        """
        result = self.execute_query(table_check_query, (table_name,))
        if not result or not result[0]['exists']:
            return {}

        # Get basic field info
        field_query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                col_description(pgc.oid, pga.attnum) as column_comment
            FROM information_schema.columns c
            JOIN pg_class pgc ON pgc.relname = c.table_name
            JOIN pg_attribute pga ON pga.attrelid = pgc.oid 
                AND pga.attname = c.column_name
            WHERE c.table_name = %s
            AND c.table_schema = 'public'
        """
        fields = {}
        for row in self.execute_query(field_query, (table_name,)):
            fields[row['column_name']] = {
                'type': self.map_pg_to_odoo_type(row['data_type']),
                'required': row['is_nullable'] == 'NO',
                'default': row['column_default'],
                'help': row['column_comment'],
                'string': self.get_field_string(table_name, row['column_name'])
            }
            
            # Add selection options for fields that have them
            if fields[row['column_name']]['type'] == 'selection':
                fields[row['column_name']]['selection'] = self.get_field_selection(table_name, row['column_name'])
                
        return fields
    
    def get_field_string(self, table_name: str, field_name: str) -> str:
        """Get the display name of a field from ir_model_fields if available."""
        query = """
            SELECT field_description 
            FROM ir_model_fields 
            WHERE model = %s AND name = %s 
            LIMIT 1
        """
        try:
            result = self.execute_query(query, (table_name.replace('_', '.'), field_name))
            return result[0]['field_description'] if result else field_name.replace('_', ' ').title()
        except Exception:
            return field_name.replace('_', ' ').title()
    
    def get_field_selection(self, table_name: str, field_name: str) -> List[tuple]:
        """Get selection options for a field if it's a selection field."""
        query = """
            SELECT selection_json 
            FROM ir_model_fields 
            WHERE model = %s AND name = %s AND ttype = 'selection'
            LIMIT 1
        """
        try:
            result = self.execute_query(query, (table_name.replace('_', '.'), field_name))
            if result and result[0]['selection_json']:
                return json.loads(result[0]['selection_json'])
        except Exception:
            pass
        return []
    
    def get_model_info(self, table_name: str) -> Dict:
        """Get model description and other metadata from ir_model."""
        query = """
            SELECT 
                name,
                model,
                transient,
                state
            FROM ir_model 
            WHERE model = %s 
            LIMIT 1
        """
        try:
            result = self.execute_query(query, (table_name.replace('_', '.'),))
            if result:
                return {
                    'name': result[0]['name'],
                    'model': result[0]['model'],
                    'transient': result[0]['transient'],
                    'state': result[0]['state']
                }
        except Exception as e:
            print(f"Error getting model info: {e}")
            pass
            
        # Fallback to basic info if model not found in ir_model
        return {
            'name': table_name.replace('_', ' ').title(),
            'model': table_name.replace('_', '.'),
            'transient': False,
            'state': 'base'
        }

    def is_valid_table(self, table_name: str) -> bool:
        """Check if a table name represents a valid Odoo model table."""
        # Common Odoo model prefixes
        odoo_prefixes = ['ir_', 'res_', 'product_', 'sale_', 'purchase_', 'stock_', 'account_', 'mrp_']
        
        # Check if it's a real table
        query = """
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_name = %s 
                AND table_schema = 'public'
            );
        """
        result = self.execute_query(query, (table_name,))
        exists = result[0]['exists'] if result else False
        
        # Check if it follows Odoo naming convention
        has_odoo_prefix = any(table_name.startswith(prefix) for prefix in odoo_prefixes)
        
        return exists and (has_odoo_prefix or table_name in ['res_partner', 'res_users'])

    def map_pg_to_odoo_type(self, pg_type: str) -> str:
        """Map PostgreSQL data types to Odoo field types."""
        type_mapping = {
            'integer': 'integer',
            'character varying': 'char',
            'text': 'text',
            'boolean': 'boolean',
            'timestamp without time zone': 'datetime',
            'date': 'date',
            'numeric': 'float',
            'double precision': 'float',
            'jsonb': 'json',
            'bytea': 'binary'
        }
        return type_mapping.get(pg_type.lower(), 'char')
    
    def get_model_relations(self, table_name: str) -> List[Dict]:
        """Get foreign key relationships for a table."""
        query = """
            SELECT
                tc.table_schema, 
                tc.constraint_name, 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
        """
        result = self.execute_query(query, (table_name,))
        relations = []
        for row in result:
            relations.append({
                'field': row['column_name'],
                'relation': row['foreign_table_name'],
                'type': 'many2one'
            })
        return relations

class SQLSchemaGenerator:
    def __init__(self):
        self.model_schema = {}
        self.db_connector = OdooDBConnector()
        self.db_connector.connect()
        
    def __del__(self):
        """Cleanup database connection."""
        if hasattr(self, 'db_connector'):
            self.db_connector.disconnect()
        
    def extract_tables_from_query(self, query: str) -> List[str]:
        """Extract actual table names from SQL query, resolving aliases."""
        parsed = sqlparse.parse(query)[0]
        tables = set()
        aliases = {}
        
        for token in parsed.tokens:
            if isinstance(token, sqlparse.sql.Identifier):
                if 'FROM' in str(token.parent) or 'JOIN' in str(token.parent):
                    parts = str(token).split(' ')
                    table_name = parts[0].strip()
                    if self.db_connector.is_valid_table(table_name):
                        tables.add(table_name)
                        if len(parts) > 1:  # Has alias
                            aliases[parts[-1].strip()] = table_name
        
        return list(tables)
    
    def extract_fields_from_query(self, query: str) -> Dict[str, List[str]]:
        """Extract actual fields (not aliases) from SQL query."""
        if not query:
            return {}
            
        try:
            parsed = sqlparse.parse(query)[0]
        except Exception as e:
            print(f"Error parsing SQL query: {e}")
            return {}
            
        fields = {}
        table_aliases = {}
        
        # First pass: collect all table aliases
        try:
            for token in parsed.tokens:
                if isinstance(token, sqlparse.sql.Identifier):
                    if 'FROM' in str(token.parent) or 'JOIN' in str(token.parent):
                        parts = str(token).split(' ')
                        if len(parts) > 1:  # Has alias
                            real_table = parts[0].strip()
                            alias = parts[-1].strip()
                            if self.db_connector.is_valid_table(real_table):
                                table_aliases[alias] = real_table
                                
            # Add original tables to aliases dictionary
            real_tables = set(table_aliases.values())
            for table in real_tables:
                table_aliases[table] = table
                
            # Second pass: extract fields with their actual table names
            select_seen = False
            for token in parsed.tokens:
                if token.is_group and not select_seen:
                    if 'SELECT' in str(token):
                        select_seen = True
                        for item in token.tokens:
                            if isinstance(item, sqlparse.sql.Identifier):
                                field_parts = str(item).split('.')
                                if len(field_parts) == 2:  # Has table prefix
                                    table_alias = field_parts[0].strip()
                                    field_name = field_parts[1].strip()
                                    if table_alias in table_aliases:
                                        real_table = table_aliases[table_alias]
                                        if real_table not in fields:
                                            fields[real_table] = []
                                        # Remove any alias from the field name
                                        actual_field = field_name.split(' ')[0].strip()
                                        if actual_field not in fields[real_table]:
                                            fields[real_table].append(actual_field)
        except Exception as e:
            print(f"Error processing SQL query: {e}")
            return {}
            
        return fields
    
    def process_sql_dataset(self, csv_path: str) -> Dict:
        """Process SQL queries from CSV and generate Odoo schema."""
        df = pd.read_csv(csv_path)
        
        for _, row in df.iterrows():
            query = row['output']
            tables = self.extract_tables_from_query(query)
            fields = self.extract_fields_from_query(query)
            
            for table in tables:
                if table not in self.model_schema and self.db_connector.is_valid_table(table):
                    # Get model metadata
                    model_info = self.db_connector.get_model_info(table)
                    
                    # Get field information from database
                    db_fields = self.db_connector.get_field_info(table)
                    relations = self.db_connector.get_model_relations(table)
                    
                    self.model_schema[table] = {
                        'name': model_info['name'],
                        'model': model_info['model'],
                        'transient': model_info['transient'],
                        'state': model_info['state'],
                        'fields': db_fields,
                        'relations': relations
                    }
                
                # Add any fields from the query that are in the database
                if table in fields:
                    for field in fields[table]:
                        db_info = self.db_connector.get_field_info(table).get(field)
                        if db_info and field not in self.model_schema[table]['fields']:
                            self.model_schema[table]['fields'][field] = db_info
        
        # Remove any remaining invalid tables or computed fields
        self.model_schema = {k: v for k, v in self.model_schema.items() 
                           if self.db_connector.is_valid_table(k) and v['fields']}
        
        return self.model_schema
    
    def infer_field_type(self, field_name: str) -> str:
        """Infer field type based on field name."""
        if 'id' in field_name.lower():
            return 'many2one'
        elif 'date' in field_name.lower():
            return 'datetime'
        elif 'price' in field_name.lower() or 'amount' in field_name.lower():
            return 'float'
        elif 'qty' in field_name.lower() or 'quantity' in field_name.lower():
            return 'float'
        elif 'name' in field_name.lower():
            return 'char'
        else:
            return 'char'
    
    def save_schema(self, output_path: str):
        """Save the generated schema to a JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.model_schema, f, indent=2)
    
    def generate_schema_summary(self, tables: List[str], fields: Dict[str, List[str]]) -> str:
        """Generate a detailed summary of the schema used in the query."""
        summary_parts = []
        
        # Add introduction
        summary_parts.append("This query interacts with the following Odoo models and their fields:")
        
        for table in tables:
            if table not in self.model_schema:
                continue
                
            model_info = self.model_schema[table]
            model_fields = fields.get(table, [])
            
            # Add model description
            summary_parts.append(f"\n{model_info['name']} ({model_info['model']}):")
            
            # Add fields used in the query
            if model_fields:
                summary_parts.append("Fields used:")
                for field_name in model_fields:
                    if field_name in model_info['fields']:
                        field_info = model_info['fields'][field_name]
                        field_desc = f"- {field_info['string']}"
                        if field_info['help']:
                            field_desc += f": {field_info['help']}"
                        if field_info['type'] == 'selection' and 'selection' in field_info:
                            options = [f"'{k}': {v}" for k, v in field_info['selection']]
                            field_desc += f" (Options: {', '.join(options)})"
                        summary_parts.append(field_desc)
            
            # Add relationships
            if model_info['relations']:
                summary_parts.append("\nRelationships:")
                for relation in model_info['relations']:
                    if relation['relation'] in self.model_schema:
                        related_model = self.model_schema[relation['relation']]['name']
                        summary_parts.append(f"- Links to {related_model} through {relation['field']}")
        
        return "\n".join(summary_parts)
    
    def create_training_dataset(self, input_csv: str, output_csv: str):
        """Create a training dataset with enhanced schema information."""
        df = pd.read_csv(input_csv)
        enhanced_rows = []
        
        for _, row in df.iterrows():
            query = row['output']
            tables = self.extract_tables_from_query(query)
            fields = self.extract_fields_from_query(query)
            
            # Generate schema summary
            schema_summary = self.generate_schema_summary(tables, fields)
            
            # Combine original instruction with schema summary
            instruction = row['instruction'].strip()
            enhanced_instruction = f"{instruction}\n\nSchema Information:\n{schema_summary}\n"
            
            enhanced_rows.append({
                'input': row['input'],
                'instruction': enhanced_instruction,
                'output': query
            })
        
        # Create enhanced dataset
        enhanced_df = pd.DataFrame(enhanced_rows)
        enhanced_df.to_csv(output_csv, index=False)
        print(f"Enhanced dataset saved to {output_csv}")

def main():
    generator = SQLSchemaGenerator()
    
    # First process the SQL dataset to build the schema
    schema = generator.process_sql_dataset('data/SQL_Query_DS.csv')
    generator.save_schema('data/odoo_sql_query_df_cleaned.json')
    print("Schema generation completed. Check odoo_sql_query_df_cleaned.json")
    
    # Then create the enhanced training dataset
    generator.create_training_dataset(
        'data/SQL_Query_DS.csv',
        'data/enhanced_SQL_Query_DS.csv'
    )
    print("Enhanced training dataset created. Check enhanced_SQL_Query_DS.csv")

if __name__ == "__main__":
    main()