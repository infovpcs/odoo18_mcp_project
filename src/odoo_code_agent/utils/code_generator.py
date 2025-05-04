# src/odoo_code_agent/utils/code_generator.py
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def generate_model_class(
    model_name: str,
    fields: Dict[str, Dict[str, Any]],
    description: Optional[str] = None,
    inherit_model: Optional[str] = None,
    methods: Optional[List[Dict[str, Any]]] = None,
    mail_thread: bool = False,
    mail_activity: bool = False
) -> str:
    """
    Generate Odoo 18 model class code.

    Args:
        model_name: Technical name of the model (e.g., 'custom.model')
        fields: Dictionary of fields with their attributes
        description: Human-readable description of the model
        inherit_model: Model to inherit from (for extending existing models)
        methods: List of methods to include in the model
        mail_thread: Whether to inherit from mail.thread
        mail_activity: Whether to inherit from mail.activity.mixin

    Returns:
        Python code for the model class
    """
    if not description:
        # Convert model_name to a more readable format for description
        description = model_name.replace(".", " ").replace("_", " ").title()

    # Include necessary imports
    imports = ["from odoo import models, fields, api"]

    # Add mail imports if needed
    if mail_thread or mail_activity:
        imports.append("from odoo.addons.mail.models.mail_thread import MailThread")

    code = "\n".join(imports) + "\n\n"

    # Generate class definition
    model_class_name = "".join(part.capitalize() for part in model_name.replace(".", "_").split("_"))

    if inherit_model:
        # This is a model that extends an existing one
        code += f"class {model_class_name}(models.Model):\n"
        code += f"    _inherit = '{inherit_model}'\n\n"
    else:
        # This is a new model
        # Determine parent classes
        parent_classes = ["models.Model"]
        if mail_thread:
            parent_classes.append("models.mail.thread")
        if mail_activity:
            parent_classes.append("models.mail.activity.mixin")

        parent_class_str = ", ".join(parent_classes)

        code += f"class {model_class_name}({parent_class_str}):\n"
        code += f"    _name = '{model_name}'\n"
        code += f"    _description = '{description}'\n"

        # Add mail thread specific settings
        if mail_thread:
            code += "    _inherit = ['mail.thread']\n"
        if mail_activity:
            if mail_thread:
                code += "    _inherit += ['mail.activity.mixin']\n"
            else:
                code += "    _inherit = ['mail.activity.mixin']\n"

        code += "\n"

    # Add fields
    for field_name, field_attrs in fields.items():
        field_type = field_attrs.get("type", "Char")
        field_string = field_attrs.get("string", field_name.replace("_", " ").title())

        field_code = f"    {field_name} = fields.{field_type}("

        # Add field attributes
        attrs = []
        if "string" in field_attrs:
            attrs.append(f"string='{field_attrs['string']}'")
        else:
            attrs.append(f"string='{field_string}'")

        for attr, value in field_attrs.items():
            if attr not in ["type", "string"]:
                if isinstance(value, str):
                    attrs.append(f"{attr}='{value}'")
                else:
                    attrs.append(f"{attr}={value}")

        field_code += ", ".join(attrs) + ")\n"
        code += field_code

    # Add methods
    if methods:
        code += "\n"
        for method in methods:
            method_name = method.get("name", "method")
            method_params = method.get("params", "self")
            method_body = method.get("body", "    pass")
            method_decorator = method.get("decorator")

            if method_decorator:
                code += f"    @{method_decorator}\n"

            code += f"    def {method_name}({method_params}):\n"

            # Add docstring if provided
            if "docstring" in method:
                code += f'        """\n        {method["docstring"]}\n        """\n'

            # Add method body with proper indentation
            for line in method_body.split("\n"):
                code += f"        {line}\n"

            code += "\n"

    return code


def generate_form_view(
    model_name: str,
    fields: List[str],
    view_id: Optional[str] = None,
    view_name: Optional[str] = None,
    groups: Optional[List[Dict[str, List[str]]]] = None,
    include_chatter: bool = True,
    mail_thread_model: bool = False
) -> str:
    """
    Generate Odoo 18 form view XML.

    Args:
        model_name: Technical name of the model
        fields: List of field names to include in the view
        view_id: Optional ID for the view
        view_name: Optional name for the view
        groups: Optional field grouping structure
        include_chatter: Whether to include the chatter component
        mail_thread_model: Whether the model inherits from mail.thread

    Returns:
        XML code for the form view
    """
    if not view_id:
        view_id = f"{model_name.replace('.', '_')}_form_view"

    if not view_name:
        view_name = f"{model_name.replace('.', ' ').replace('_', ' ').title()} Form"

    xml = f"""<record id="{view_id}" model="ir.ui.view">
    <field name="name">{view_name}</field>
    <field name="model">{model_name}</field>
    <field name="arch" type="xml">
        <form>"""

    # Add sheet for content
    xml += """
            <sheet>"""

    if groups:
        # Add fields in groups
        for group in groups:
            xml += "\n                <group>"

            for group_name, group_fields in group.items():
                xml += f'\n                    <group string="{group_name}">'

                for field in group_fields:
                    xml += f'\n                        <field name="{field}"/>'

                xml += '\n                    </group>'

            xml += '\n                </group>'
    else:
        # Add fields without grouping
        xml += '\n                <group>'

        for field in fields:
            xml += f'\n                    <field name="{field}"/>'

        xml += '\n                </group>'

    xml += """
            </sheet>"""

    # Add chatter if requested (Odoo 18 uses a single <chatter/> tag)
    if include_chatter and mail_thread_model:
        xml += """
            <chatter/>"""

    xml += """
        </form>
    </field>
</record>"""

    return xml


def generate_list_view(
    model_name: str,
    fields: List[str],
    view_id: Optional[str] = None,
    view_name: Optional[str] = None
) -> str:
    """
    Generate Odoo list view XML (replaces tree view in Odoo 18).

    Args:
        model_name: Technical name of the model
        fields: List of field names to include in the view
        view_id: Optional ID for the view
        view_name: Optional name for the view

    Returns:
        XML code for the list view
    """
    if not view_id:
        view_id = f"{model_name.replace('.', '_')}_list_view"

    if not view_name:
        view_name = f"{model_name.replace('.', ' ').replace('_', ' ').title()} List"

    xml = f"""<record id="{view_id}" model="ir.ui.view">
    <field name="name">{view_name}</field>
    <field name="model">{model_name}</field>
    <field name="arch" type="xml">
        <list>"""

    for field in fields:
        xml += f'\n            <field name="{field}"/>'

    xml += """
        </list>
    </field>
</record>"""

    return xml


def generate_search_view(
    model_name: str,
    fields: List[str],
    view_id: Optional[str] = None,
    view_name: Optional[str] = None,
    filters: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Generate Odoo search view XML.

    Args:
        model_name: Technical name of the model
        fields: List of field names to include in the view
        view_id: Optional ID for the view
        view_name: Optional name for the view
        filters: Optional list of filters to include

    Returns:
        XML code for the search view
    """
    if not view_id:
        view_id = f"{model_name.replace('.', '_')}_search_view"

    if not view_name:
        view_name = f"{model_name.replace('.', ' ').replace('_', ' ').title()} Search"

    xml = f"""<record id="{view_id}" model="ir.ui.view">
    <field name="name">{view_name}</field>
    <field name="model">{model_name}</field>
    <field name="arch" type="xml">
        <search string="{view_name}">"""

    for field in fields:
        xml += f'\n            <field name="{field}"/>'

    if filters:
        xml += '\n            <filter string="Filters">'

        for filter_def in filters:
            filter_name = filter_def.get("name", "filter")
            filter_domain = filter_def.get("domain", "[]")
            filter_string = filter_def.get("string", filter_name.replace("_", " ").title())

            xml += f'\n                <filter name="{filter_name}" string="{filter_string}" domain="{filter_domain}"/>'

        xml += '\n            </filter>'

    xml += """
        </search>
    </field>
</record>"""

    return xml


def generate_action_window(
    model_name: str,
    action_id: Optional[str] = None,
    action_name: Optional[str] = None,
    view_mode: str = "list,form"
) -> str:
    """
    Generate Odoo 18 action window XML.

    Args:
        model_name: Technical name of the model
        action_id: Optional ID for the action
        action_name: Optional name for the action
        view_mode: Comma-separated list of view modes (default: "list,form" for Odoo 18)

    Returns:
        XML code for the action window
    """
    if not action_id:
        action_id = f"action_{model_name.replace('.', '_')}"

    if not action_name:
        action_name = f"{model_name.replace('.', ' ').replace('_', ' ').title()}"

    xml = f"""<record id="{action_id}" model="ir.actions.act_window">
    <field name="name">{action_name}</field>
    <field name="type">ir.actions.act_window</field>
    <field name="res_model">{model_name}</field>
    <field name="view_mode">{view_mode}</field>
    <field name="help" type="html">
        <p class="o_view_nocontent_smiling_face">
            Create your first {action_name.lower()}
        </p>
    </field>
</record>"""

    return xml


def generate_menu_item(
    menu_id: str,
    menu_name: str,
    action_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    sequence: int = 10
) -> str:
    """
    Generate Odoo menu item XML.

    Args:
        menu_id: ID for the menu item
        menu_name: Name for the menu item
        action_id: Optional ID of the action to execute
        parent_id: Optional ID of the parent menu
        sequence: Sequence number for ordering

    Returns:
        XML code for the menu item
    """
    xml = f"""<menuitem id="{menu_id}"
          name="{menu_name}"""

    if parent_id:
        xml += f'\n          parent="{parent_id}"'

    if action_id:
        xml += f'\n          action="{action_id}"'

    xml += f'\n          sequence="{sequence}"/>'

    return xml


def generate_access_rights(
    model_name: str,
    groups: Dict[str, Dict[str, bool]]
) -> str:
    """
    Generate Odoo access rights CSV content.

    Args:
        model_name: Technical name of the model
        groups: Dictionary mapping group names to their permissions

    Returns:
        CSV content for ir.model.access.csv
    """
    model_id = model_name.replace(".", "_")
    csv_content = "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink\n"

    for group_name, permissions in groups.items():
        access_id = f"access_{model_id}_{group_name.replace('.', '_')}"
        access_name = f"access.{model_name}.{group_name}"
        group_id = group_name

        perm_read = "1" if permissions.get("read", True) else "0"
        perm_write = "1" if permissions.get("write", False) else "0"
        perm_create = "1" if permissions.get("create", False) else "0"
        perm_unlink = "1" if permissions.get("unlink", False) else "0"

        csv_content += f"{access_id},{access_name},model_{model_id},{group_id},{perm_read},{perm_write},{perm_create},{perm_unlink}\n"

    return csv_content


def generate_controller(
    module_name: str,
    controller_name: Optional[str] = None,
    routes: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Generate Odoo controller code.

    Args:
        module_name: Name of the module
        controller_name: Optional name for the controller class
        routes: Optional list of routes to include

    Returns:
        Python code for the controller
    """
    if not controller_name:
        controller_name = f"{module_name.replace('_', ' ').title().replace(' ', '')}Controller"

    code = """from odoo import http
from odoo.http import request

"""

    code += f"class {controller_name}(http.Controller):\n"

    if routes:
        for route in routes:
            route_path = route.get("path", f"/{module_name}")
            route_auth = route.get("auth", "public")
            route_type = route.get("type", "http")
            route_methods = route.get("methods", ["GET"])
            route_methods_str = ", ".join([f'"{m}"' for m in route_methods])

            method_name = route.get("name", "index")
            method_params = route.get("params", "self")
            method_body = route.get("body", "    return 'Hello, world!'")

            code += f"""    @http.route('{route_path}', auth='{route_auth}', type='{route_type}', methods=[{route_methods_str}])
    def {method_name}({method_params}):
"""

            # Add docstring if provided
            if "docstring" in route:
                code += f'        """\n        {route["docstring"]}\n        """\n'

            # Add method body with proper indentation
            for line in method_body.split("\n"):
                code += f"        {line}\n"

            code += "\n"
    else:
        # Add a default index route
        code += f"""    @http.route('/{module_name}', auth='public')
    def index(self, **kw):
        return "Hello, world!"
"""

    return code


def generate_complete_views(
    model_name: str,
    fields: List[str],
    form_fields: Optional[List[str]] = None,
    list_fields: Optional[List[str]] = None,
    search_fields: Optional[List[str]] = None,
    filters: Optional[List[Dict[str, Any]]] = None,
    groups: Optional[List[Dict[str, List[str]]]] = None,
    mail_thread_model: bool = False
) -> str:
    """
    Generate complete views XML for a model following Odoo 18 guidelines.

    Args:
        model_name: Technical name of the model
        fields: List of all field names
        form_fields: Optional list of fields for form view (defaults to all fields)
        list_fields: Optional list of fields for list view (defaults to subset of fields)
        search_fields: Optional list of fields for search view (defaults to subset of fields)
        filters: Optional list of filters for search view
        groups: Optional field grouping structure for form view
        mail_thread_model: Whether the model inherits from mail.thread

    Returns:
        Complete XML for all views
    """
    # Default field selections if not provided
    if not form_fields:
        form_fields = fields

    if not list_fields:
        # For list view, use a subset of fields (max 5) if there are many
        list_fields = fields[:min(5, len(fields))]

    if not search_fields:
        # For search view, use a subset of fields (max 3) if there are many
        search_fields = fields[:min(3, len(fields))]

    # Generate the views
    form_view = generate_form_view(
        model_name,
        form_fields,
        groups=groups,
        include_chatter=True,
        mail_thread_model=mail_thread_model
    )
    list_view = generate_list_view(model_name, list_fields)
    search_view = generate_search_view(model_name, search_fields, filters=filters)
    action = generate_action_window(model_name, view_mode="list,form")

    # Combine all views
    xml = """<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Form View -->
"""
    xml += "\n    ".join(form_view.split("\n"))

    xml += """

    <!-- List View -->
"""
    xml += "\n    ".join(list_view.split("\n"))

    xml += """

    <!-- Search View -->
"""
    xml += "\n    ".join(search_view.split("\n"))

    xml += """

    <!-- Action Window -->
"""
    xml += "\n    ".join(action.split("\n"))

    xml += """
</odoo>"""

    return xml


def generate_module_files(
    module_name: str,
    models: List[Dict[str, Any]],
    base_path: str = "."
) -> Dict[str, str]:
    """
    Generate all files for an Odoo module.

    Args:
        module_name: Name of the module
        models: List of model definitions
        base_path: Base path where the module should be created

    Returns:
        Dictionary mapping file paths to their content
    """
    from src.odoo_code_agent.utils.module_structure import generate_manifest

    files = {}
    module_path = os.path.join(base_path, module_name)

    # Create basic module structure
    files[os.path.join(module_path, "__init__.py")] = "from . import models\n"
    files[os.path.join(module_path, "__manifest__.py")] = generate_manifest(module_name)
    files[os.path.join(module_path, "models", "__init__.py")] = ""

    # Process models
    model_imports = []
    security_content = "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink\n"

    for model_def in models:
        model_name = model_def.get("name")
        model_file = model_def.get("file", model_name.replace(".", "_"))
        model_fields = model_def.get("fields", {})
        model_methods = model_def.get("methods", [])
        model_inherit = model_def.get("inherit")
        model_description = model_def.get("description")

        # Generate model file
        model_code = generate_model_class(
            model_name=model_name,
            fields=model_fields,
            methods=model_methods,
            inherit_model=model_inherit,
            description=model_description
        )

        files[os.path.join(module_path, "models", f"{model_file}.py")] = model_code
        model_imports.append(f"from . import {model_file}")

        # Generate views if this is not an inherited model
        if not model_inherit:
            field_names = list(model_fields.keys())
            views_xml = generate_complete_views(
                model_name=model_name,
                fields=field_names,
                filters=model_def.get("filters"),
                groups=model_def.get("groups")
            )

            files[os.path.join(module_path, "views", f"{model_file}_views.xml")] = views_xml

            # Generate security
            groups = model_def.get("groups_access", {"base.group_user": {"read": True, "write": True, "create": True, "unlink": True}})
            model_security = generate_access_rights(model_name, groups)
            security_content += model_security[model_security.find("\n")+1:]  # Skip header row

    # Update models/__init__.py with imports
    files[os.path.join(module_path, "models", "__init__.py")] = "\n".join(model_imports)

    # Add security file
    files[os.path.join(module_path, "security", "ir.model.access.csv")] = security_content

    return files


def generate_model_from_description(
    description: str,
    model_name: Optional[str] = None,
    use_fallback: bool = True
) -> Dict[str, Any]:
    """
    Generate a model definition from a natural language description.

    Args:
        description: Natural language description of the model
        model_name: Optional technical name for the model
        use_fallback: Whether to use fallback models if needed

    Returns:
        Model definition dictionary
    """
    from src.odoo_code_agent.utils.fallback_models import generate_with_fallback

    # Default model definition
    model_def = {
        "name": model_name or "custom.model",
        "description": "Custom Model",
        "fields": {
            "name": {
                "type": "Char",
                "string": "Name",
                "required": True
            },
            "description": {
                "type": "Text",
                "string": "Description"
            },
            "active": {
                "type": "Boolean",
                "string": "Active",
                "default": True
            }
        }
    }

    # Try to generate a better model definition using AI
    if use_fallback:
        prompt = f"""
Generate an Odoo model definition based on this description:
"{description}"

The response should be a valid Python dictionary with the following structure:
{{
    "name": "technical.model.name",  # Technical name of the model
    "description": "Human-readable description",
    "fields": {{
        "field_name": {{
            "type": "Field Type",  # One of: Char, Text, Integer, Float, Boolean, Date, Datetime, Binary, Selection, Many2one, One2many, Many2many
            "string": "Field Label",
            # Other attributes as needed: required, readonly, default, help, etc.
        }},
        # More fields...
    }}
}}

Only include common Odoo field types and attributes. Make sure the technical name follows Odoo conventions.
"""

        result = generate_with_fallback(prompt)

        if result:
            try:
                # Try to extract the dictionary from the response
                import re
                dict_match = re.search(r'({[\s\S]*})', result)
                if dict_match:
                    dict_str = dict_match.group(1)
                    # Safely evaluate the dictionary string
                    import ast
                    generated_def = ast.literal_eval(dict_str)

                    # Validate and merge with defaults
                    if isinstance(generated_def, dict):
                        if "name" in generated_def:
                            model_def["name"] = generated_def["name"]
                        if "description" in generated_def:
                            model_def["description"] = generated_def["description"]
                        if "fields" in generated_def and isinstance(generated_def["fields"], dict):
                            model_def["fields"] = generated_def["fields"]
            except Exception as e:
                logger.error(f"Error parsing generated model definition: {str(e)}")

    return model_def


def generate_method_from_description(
    description: str,
    method_name: Optional[str] = None,
    params: Optional[str] = None,
    use_fallback: bool = True
) -> Dict[str, Any]:
    """
    Generate a method definition from a natural language description.

    Args:
        description: Natural language description of the method
        method_name: Optional name for the method
        params: Optional parameters for the method
        use_fallback: Whether to use fallback models if needed

    Returns:
        Method definition dictionary
    """
    from src.odoo_code_agent.utils.fallback_models import generate_with_fallback

    # Default method definition
    method_def = {
        "name": method_name or "custom_method",
        "params": params or "self",
        "docstring": description,
        "body": "pass"
    }

    # Try to generate a better method definition using AI
    if use_fallback:
        prompt = f"""
Generate an Odoo model method based on this description:
"{description}"

Method name: {method_name or "custom_method"}
Parameters: {params or "self"}

The response should be the method body only, properly indented with 4 spaces per level.
Include appropriate docstring, error handling, and logging.
Only use standard Odoo ORM methods and APIs.
"""

        result = generate_with_fallback(prompt)

        if result:
            # Clean up the result to extract just the method body
            import re

            # Remove any markdown code block markers
            result = re.sub(r'```python|```', '', result)

            # Remove any method definition line
            result = re.sub(r'^def\s+\w+\s*\([^)]*\):\s*\n', '', result)

            # Ensure proper indentation
            lines = result.strip().split('\n')
            indented_lines = []
            for line in lines:
                # Remove any leading indentation
                stripped = line.lstrip()
                if stripped:
                    # Add back consistent indentation
                    indented_lines.append(stripped)

            if indented_lines:
                method_def["body"] = "\n".join(indented_lines)

    return method_def


def generate_views_from_model(
    model_def: Dict[str, Any],
    use_fallback: bool = True
) -> Dict[str, str]:
    """
    Generate views for a model definition following Odoo 18 guidelines.

    Args:
        model_def: Model definition dictionary
        use_fallback: Whether to use fallback models if needed

    Returns:
        Dictionary mapping view types to their XML content
    """
    model_name = model_def.get("name", "custom.model")
    fields = list(model_def.get("fields", {}).keys())

    # Check if model inherits from mail.thread
    mail_thread_model = model_def.get("inherit") == "mail.thread" or model_def.get("mail_thread", False)

    # Generate views using the utility functions
    views = {
        "form": generate_form_view(
            model_name,
            fields,
            include_chatter=True,
            mail_thread_model=mail_thread_model
        ),
        "list": generate_list_view(model_name, fields[:min(5, len(fields))]),
        "search": generate_search_view(model_name, fields[:min(3, len(fields))]),
        "action": generate_action_window(model_name, view_mode="list,form")
    }

    # Try to enhance views using AI if requested
    if use_fallback and fields:
        from src.odoo_code_agent.utils.fallback_models import generate_with_fallback

        # Create a prompt for better field grouping in form view
        field_info = "\n".join([f"- {field}: {model_def['fields'][field].get('type', 'Char')} - {model_def['fields'][field].get('string', field)}"
                               for field in fields])

        prompt = f"""
Given this Odoo model definition:
Model: {model_name}
Description: {model_def.get('description', 'Custom Model')}

Fields:
{field_info}

Suggest a logical grouping of fields for the form view. The response should be a valid Python list of dictionaries, where each dictionary has a group name as key and a list of field names as value.

Example format:
[
    {{"Basic Information": ["name", "description"]}},
    {{"Additional Details": ["field1", "field2"]}}
]

Only include fields that exist in the model definition.
"""

        result = generate_with_fallback(prompt)

        if result:
            try:
                # Try to extract the list from the response
                import re
                list_match = re.search(r'(\[[\s\S]*\])', result)
                if list_match:
                    list_str = list_match.group(1)
                    # Safely evaluate the list string
                    import ast
                    groups = ast.literal_eval(list_str)

                    # Validate and use the groups
                    if isinstance(groups, list) and all(isinstance(g, dict) for g in groups):
                        # Regenerate the form view with the suggested groups
                        views["form"] = generate_form_view(model_name, fields, groups=groups)
            except Exception as e:
                logger.error(f"Error parsing generated field groups: {str(e)}")

    return views


def generate_complete_module_from_description(
    description: str,
    module_name: Optional[str] = None,
    base_path: str = ".",
    use_fallback: bool = True
) -> Dict[str, str]:
    """
    Generate a complete Odoo module from a natural language description.

    Args:
        description: Natural language description of the module
        module_name: Optional name for the module
        base_path: Base path where the module should be created
        use_fallback: Whether to use fallback models if needed

    Returns:
        Dictionary mapping file paths to their content
    """
    from src.odoo_code_agent.utils.fallback_models import generate_with_fallback

    # Generate a default module name if not provided
    if not module_name:
        # Convert description to a module name
        import re
        words = re.findall(r'\w+', description.lower())
        if words:
            module_name = "_".join(words[:3])  # Use first 3 words
        else:
            module_name = "custom_module"

    # Try to extract model definitions from the description
    models = []

    if use_fallback:
        prompt = f"""
Analyze this description and identify Odoo models that should be created:
"{description}"

For each model, provide a definition in this format:
{{
    "name": "technical.model.name",
    "description": "Human-readable description",
    "fields": {{
        "field_name": {{
            "type": "Field Type",  # One of: Char, Text, Integer, Float, Boolean, Date, Datetime, Binary, Selection, Many2one, One2many, Many2many
            "string": "Field Label",
            # Other attributes as needed: required, readonly, default, help, etc.
        }},
        # More fields...
    }}
}}

Return a list of model definitions, with at least one model.
Only include common Odoo field types and attributes. Make sure the technical names follow Odoo conventions.
"""

        result = generate_with_fallback(prompt)

        if result:
            try:
                # Try to extract the list from the response
                import re
                list_match = re.search(r'(\[[\s\S]*\])', result)
                if list_match:
                    list_str = list_match.group(1)
                    # Safely evaluate the list string
                    import ast
                    models_list = ast.literal_eval(list_str)

                    # Validate and use the models
                    if isinstance(models_list, list) and all(isinstance(m, dict) for m in models_list):
                        models = models_list
            except Exception as e:
                logger.error(f"Error parsing generated models: {str(e)}")

    # If no models were extracted, create a default one
    if not models:
        models = [{
            "name": f"{module_name}.model",
            "description": f"{module_name.replace('_', ' ').title()} Model",
            "fields": {
                "name": {
                    "type": "Char",
                    "string": "Name",
                    "required": True
                },
                "description": {
                    "type": "Text",
                    "string": "Description"
                },
                "active": {
                    "type": "Boolean",
                    "string": "Active",
                    "default": True
                }
            }
        }]

    # Generate the module files
    return generate_module_files(module_name, models, base_path)


def generate_model_from_odoo(
    model_name: str,
    odoo_client = None,
    include_fields: bool = True,
    include_views: bool = True
) -> Dict[str, Any]:
    """
    Generate model definition from an existing Odoo model.

    Args:
        model_name: Technical name of the model (e.g., 'res.partner')
        odoo_client: Optional OdooClient instance
        include_fields: Whether to include field definitions
        include_views: Whether to include view definitions

    Returns:
        Dictionary with model definition and generated code
    """
    try:
        # Import here to avoid circular imports
        from src.odoo.dynamic.model_discovery import ModelDiscovery
        from src.odoo.dynamic.field_analyzer import FieldAnalyzer

        # Create model discovery instance if client is provided
        if odoo_client:
            model_discovery = ModelDiscovery(odoo_client)
            field_analyzer = FieldAnalyzer(model_discovery)
        else:
            # Try to create a client from environment variables
            from src.odoo.client import OdooClient
            from src.odoo.schemas import OdooConfig
            import os

            config = OdooConfig(
                url=os.environ.get("ODOO_URL", "http://localhost:8069"),
                db=os.environ.get("ODOO_DB", "llmdb18"),
                username=os.environ.get("ODOO_USERNAME", "admin"),
                password=os.environ.get("ODOO_PASSWORD", "admin")
            )

            odoo_client = OdooClient(config)
            model_discovery = ModelDiscovery(odoo_client)
            field_analyzer = FieldAnalyzer(model_discovery)

            # Add helper methods to ModelDiscovery if they don't exist
            if not hasattr(model_discovery, 'has_mail_thread'):
                def has_mail_thread(self, model_name: str) -> bool:
                    """Check if a model inherits from mail.thread."""
                    try:
                        # Check if the model has message_ids field (indicator of mail.thread)
                        fields = self.get_model_fields(model_name)
                        return 'message_ids' in fields
                    except Exception:
                        return False

                model_discovery.has_mail_thread = has_mail_thread.__get__(model_discovery)

            if not hasattr(model_discovery, 'has_mail_activity'):
                def has_mail_activity(self, model_name: str) -> bool:
                    """Check if a model inherits from mail.activity.mixin."""
                    try:
                        # Check if the model has activity_ids field (indicator of mail.activity.mixin)
                        fields = self.get_model_fields(model_name)
                        return 'activity_ids' in fields
                    except Exception:
                        return False

                model_discovery.has_mail_activity = has_mail_activity.__get__(model_discovery)

        # Get model information
        model_info = model_discovery.get_model_info(model_name)
        if not model_info:
            raise ValueError(f"Model {model_name} not found in Odoo")

        # Create model definition
        model_def = {
            "name": model_name,
            "description": model_info.get("name", model_name.replace(".", " ").title()),
            "fields": {},
            "views": {}
        }

        # Get field information if requested
        if include_fields:
            fields_info = model_discovery.get_model_fields(model_name)

            # Get important fields
            important_fields = field_analyzer.get_create_fields(model_name)

            # Add fields to model definition
            for field_name in important_fields:
                if field_name in fields_info:
                    field_info = fields_info[field_name]

                    # Convert Odoo field type to Python field type
                    field_type = field_info.get("type", "char")
                    python_type = {
                        "char": "Char",
                        "text": "Text",
                        "integer": "Integer",
                        "float": "Float",
                        "boolean": "Boolean",
                        "date": "Date",
                        "datetime": "Datetime",
                        "binary": "Binary",
                        "selection": "Selection",
                        "many2one": "Many2one",
                        "one2many": "One2many",
                        "many2many": "Many2many",
                        "html": "Html"
                    }.get(field_type, "Char")

                    # Create field definition
                    model_def["fields"][field_name] = {
                        "type": python_type,
                        "string": field_info.get("string", field_name.replace("_", " ").title()),
                        "required": field_info.get("required", False)
                    }

                    # Add relation for relational fields
                    if field_type in ["many2one", "one2many", "many2many"]:
                        model_def["fields"][field_name]["relation"] = field_info.get("relation", "")

                    # Add selection for selection fields
                    if field_type == "selection" and "selection" in field_info:
                        model_def["fields"][field_name]["selection"] = field_info["selection"]

        # Generate model code
        model_code = generate_model_class(
            model_name=model_name,
            fields=model_def["fields"],
            description=model_def["description"],
            mail_thread=model_discovery.has_mail_thread(model_name),
            mail_activity=model_discovery.has_mail_activity(model_name)
        )

        # Generate views if requested
        if include_views:
            model_def["views"] = generate_views_from_model(
                model_def,
                use_fallback=False
            )

        return {
            "model_def": model_def,
            "model_code": model_code,
            "views": model_def.get("views", {})
        }

    except Exception as e:
        logger.error(f"Error generating model from Odoo: {str(e)}")
        # Return a basic model definition as fallback
        return {
            "model_def": {
                "name": model_name,
                "description": model_name.replace(".", " ").title(),
                "fields": {
                    "name": {
                        "type": "Char",
                        "string": "Name",
                        "required": True
                    }
                }
            },
            "model_code": generate_model_class(
                model_name=model_name,
                fields={"name": {"type": "Char", "string": "Name", "required": True}},
                description=model_name.replace(".", " ").title()
            ),
            "views": {}
        }