"""
Module Generator Utilities

This module provides functions for generating Odoo module structures based on query analysis.
"""

import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def analyze_query_for_module_type(query):
    """
    Analyze the query to determine the module type and required dependencies.
    
    Args:
        query (str): User query describing the module to be created
        
    Returns:
        dict: Module information including type, name, category, dependencies, etc.
    """
    query_lower = query.lower()
    
    # Default module info
    module_info = {
        "type": "generic",
        "name": "Custom Module",
        "category": "Extra Tools",
        "summary": "Custom Odoo Module",
        "description": "This module extends Odoo functionality.",
        "depends": ["base"],
        "has_website": False,
        "has_api": False,
        "has_reports": False,
        "has_wizards": False,
        "has_security": True,
    }
    
    # Check for Point of Sale
    if any(term in query_lower for term in ["point of sale", "pos", "point-of-sale"]):
        module_info["type"] = "pos"
        module_info["name"] = "POS Extension"
        module_info["category"] = "Point of Sale"
        module_info["summary"] = "Point of Sale Extension"
        module_info["description"] = "This module extends the Point of Sale functionality."
        module_info["depends"] = ["point_of_sale", "base"]
    
    # Check for Website/eCommerce
    elif any(term in query_lower for term in ["website", "e-commerce", "ecommerce", "shop", "online store"]):
        module_info["type"] = "website"
        module_info["name"] = "Website Extension"
        module_info["category"] = "Website"
        module_info["summary"] = "Website/eCommerce Extension"
        module_info["description"] = "This module extends the Website/eCommerce functionality."
        module_info["depends"] = ["website", "website_sale", "base"]
        module_info["has_website"] = True
    
    # Check for Accounting/Finance
    elif any(term in query_lower for term in ["accounting", "finance", "invoice", "payment", "account"]):
        module_info["type"] = "accounting"
        module_info["name"] = "Accounting Extension"
        module_info["category"] = "Accounting"
        module_info["summary"] = "Accounting Extension"
        module_info["description"] = "This module extends the Accounting functionality."
        module_info["depends"] = ["account", "base"]
        module_info["has_reports"] = True
    
    # Check for HR/Employees
    elif any(term in query_lower for term in ["hr", "human resources", "employee", "payroll", "attendance"]):
        module_info["type"] = "hr"
        module_info["name"] = "HR Extension"
        module_info["category"] = "Human Resources"
        module_info["summary"] = "HR Extension"
        module_info["description"] = "This module extends the HR functionality."
        module_info["depends"] = ["hr", "base"]
    
    # Check for CRM
    elif any(term in query_lower for term in ["crm", "customer", "lead", "opportunity", "pipeline"]):
        module_info["type"] = "crm"
        module_info["name"] = "CRM Extension"
        module_info["category"] = "CRM"
        module_info["summary"] = "CRM Extension"
        module_info["description"] = "This module extends the CRM functionality."
        module_info["depends"] = ["crm", "base"]
    
    # Check for Inventory/Stock
    elif any(term in query_lower for term in ["inventory", "stock", "warehouse", "logistics"]):
        module_info["type"] = "inventory"
        module_info["name"] = "Inventory Extension"
        module_info["category"] = "Inventory"
        module_info["summary"] = "Inventory Extension"
        module_info["description"] = "This module extends the Inventory functionality."
        module_info["depends"] = ["stock", "base"]
    
    # Check for Manufacturing
    elif any(term in query_lower for term in ["manufacturing", "mrp", "production", "bom"]):
        module_info["type"] = "manufacturing"
        module_info["name"] = "Manufacturing Extension"
        module_info["category"] = "Manufacturing"
        module_info["summary"] = "Manufacturing Extension"
        module_info["description"] = "This module extends the Manufacturing functionality."
        module_info["depends"] = ["mrp", "base"]
    
    # Check for Purchase
    elif any(term in query_lower for term in ["purchase", "procurement", "vendor", "supplier"]):
        module_info["type"] = "purchase"
        module_info["name"] = "Purchase Extension"
        module_info["category"] = "Purchase"
        module_info["summary"] = "Purchase Extension"
        module_info["description"] = "This module extends the Purchase functionality."
        module_info["depends"] = ["purchase", "base"]
    
    # Check for Sales
    elif any(term in query_lower for term in ["sales", "sale", "order", "quotation"]):
        module_info["type"] = "sales"
        module_info["name"] = "Sales Extension"
        module_info["category"] = "Sales"
        module_info["summary"] = "Sales Extension"
        module_info["description"] = "This module extends the Sales functionality."
        module_info["depends"] = ["sale", "base"]
    
    # Check for Project
    elif any(term in query_lower for term in ["project", "task", "timesheet"]):
        module_info["type"] = "project"
        module_info["name"] = "Project Extension"
        module_info["category"] = "Project"
        module_info["summary"] = "Project Extension"
        module_info["description"] = "This module extends the Project functionality."
        module_info["depends"] = ["project", "base"]
    
    # Check for API/Integration
    elif any(term in query_lower for term in ["api", "integration", "connector", "rest", "webhook"]):
        module_info["type"] = "api"
        module_info["name"] = "API Integration"
        module_info["category"] = "Extra Tools"
        module_info["summary"] = "API Integration"
        module_info["description"] = "This module provides API integration."
        module_info["depends"] = ["base", "web"]
        module_info["has_api"] = True
    
    # Check for Report/Analysis
    elif any(term in query_lower for term in ["report", "analysis", "dashboard", "bi", "analytics"]):
        module_info["type"] = "report"
        module_info["name"] = "Reports & Analytics"
        module_info["category"] = "Reporting"
        module_info["summary"] = "Custom Reports & Analytics"
        module_info["description"] = "This module provides custom reports and analytics."
        module_info["depends"] = ["base", "web"]
        module_info["has_reports"] = True
    
    # Look for specific features mentioned
    if "wizard" in query_lower or "dialog" in query_lower:
        module_info["has_wizards"] = True
    
    if "report" in query_lower or "pdf" in query_lower or "print" in query_lower:
        module_info["has_reports"] = True
    
    if "security" in query_lower or "access right" in query_lower or "permission" in query_lower:
        module_info["has_security"] = True
    
    if "api" in query_lower or "rest" in query_lower or "json" in query_lower:
        module_info["has_api"] = True
    
    return module_info

def generate_fallback_module_structure(module_name, module_info):
    """
    Generate a fallback module structure based on the module type and requirements.
    
    Args:
        module_name (str): The name of the module to generate
        module_info (dict): Module information including type, features, etc.
        
    Returns:
        list: List of dictionaries containing generated files with paths and content
    """
    files = [
        # Basic module files
        {
            "path": f"{module_name}/__init__.py",
            "content": """from . import models
"""
        },
        {
            "path": f"{module_name}/models/__init__.py",
            "content": """from . import models
"""
        },
        {
            "path": f"{module_name}/models/models.py",
            "content": """from odoo import models, fields, api

# Define your models here
"""
        },
        {
            "path": f"{module_name}/security/ir.model.access.csv",
            "content": """id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
"""
        },
        {
            "path": f"{module_name}/views/views.xml",
            "content": """<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Define your views here -->
</odoo>
"""
        }
    ]
    
    # Build the manifest content
    depends = [d for d in module_info["depends"]]
    data = [
        'security/ir.model.access.csv',
        'views/views.xml',
    ]
    assets = {}
    
    # Add module-type specific files
    if module_info["type"] == "pos":
        files.append({
            "path": f"{module_name}/static/src/js/pos_extension.js",
            "content": f"""odoo.define('{module_name}.pos_extension', function(require) {{
    'use strict';

    // Basic structure for your POS extension
    const {{ PosGlobalState }} = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

    // Extend the POS models as needed
    // Complete implementation required
}});
"""
        })
        files.append({
            "path": f"{module_name}/static/src/xml/pos_extension.xml",
            "content": """<?xml version="1.0" encoding="UTF-8"?>
<templates id="template" xml:space="preserve">
    <!-- Define your POS templates here -->
</templates>
"""
        })
        assets = {
            'point_of_sale.assets': [
                f'{module_name}/static/src/js/**/*',
                f'{module_name}/static/src/xml/**/*',
            ]
        }
    
    elif module_info["type"] == "website":
        files.append({
            "path": f"{module_name}/controllers/__init__.py",
            "content": """from . import main
"""
        })
        files.append({
            "path": f"{module_name}/controllers/main.py",
            "content": """from odoo import http
from odoo.http import request

class WebsiteController(http.Controller):
    @http.route('/my/custom/page', type='http', auth='public', website=True)
    def custom_page(self, **kw):
        return request.render('{0}.custom_page_template', {{}})
""".format(module_name)
        })
        files.append({
            "path": f"{module_name}/views/templates.xml",
            "content": """<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <template id="custom_page_template" name="Custom Page">
        <t t-call="website.layout">
            <div class="container">
                <h1>Custom Page</h1>
                <p>This is a custom page template.</p>
            </div>
        </t>
    </template>
</odoo>
"""
        })
        depends.append("website")
        data.append('views/templates.xml')
    
    elif module_info["has_api"]:
        files.append({
            "path": f"{module_name}/controllers/__init__.py",
            "content": """from . import api
"""
        })
        files.append({
            "path": f"{module_name}/controllers/api.py",
            "content": """from odoo import http
from odoo.http import request
import json

class APIController(http.Controller):
    @http.route('/api/v1/resource', type='json', auth='user')
    def get_resource(self, **kw):
        return {{'success': True, 'data': []}}
"""
        })
        files.append({
            "path": f"{module_name}/__init__.py",
            "content": """from . import models
from . import controllers
"""
        })
    
    if module_info["has_reports"]:
        files.append({
            "path": f"{module_name}/report/__init__.py",
            "content": """from . import report
"""
        })
        files.append({
            "path": f"{module_name}/report/report.py",
            "content": """from odoo import api, models

class CustomReport(models.AbstractModel):
    _name = 'report.{0}.report_name'
    _description = 'Custom Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # logic to prepare report data
        return {{
            'doc_ids': docids,
            'doc_model': 'model.name',
            'docs': self.env['model.name'].browse(docids),
            'data': data,
        }}
""".format(module_name)
        })
        files.append({
            "path": f"{module_name}/report/report_templates.xml",
            "content": """<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <template id="report_template">
        <t t-call="web.html_container">
            <t t-call="web.external_layout">
                <div class="page">
                    <h1>Report Title</h1>
                    <!-- Report content -->
                </div>
            </t>
        </t>
    </template>
</odoo>
"""
        })
        files.append({
            "path": f"{module_name}/__init__.py",
            "content": """from . import models
from . import report
"""
        })
        data.append('report/report_templates.xml')
    
    if module_info["has_wizards"]:
        files.append({
            "path": f"{module_name}/wizard/__init__.py",
            "content": """from . import wizard
"""
        })
        files.append({
            "path": f"{module_name}/wizard/wizard.py",
            "content": """from odoo import api, fields, models

class CustomWizard(models.TransientModel):
    _name = '{0}.wizard'
    _description = 'Custom Wizard'

    name = fields.Char('Name')
    
    def action_confirm(self):
        # Action to execute when wizard is confirmed
        return {{'type': 'ir.actions.act_window_close'}}
""".format(module_name)
        })
        files.append({
            "path": f"{module_name}/wizard/wizard_views.xml",
            "content": """<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_custom_wizard_form" model="ir.ui.view">
        <field name="name">{0}.view_custom_wizard_form</field>
        <field name="model">{0}.wizard</field>
        <field name="arch" type="xml">
            <form string="Custom Wizard">
                <group>
                    <field name="name"/>
                </group>
                <footer>
                    <button string="Confirm" name="action_confirm" type="object" class="btn-primary"/>
                    <button string="Cancel" class="btn-secondary" special="cancel"/>
                </footer>
            </form>
        </field>
    </record>
</odoo>
""".format(module_name)
        })
        files.append({
            "path": f"{module_name}/__init__.py",
            "content": """from . import models
from . import wizard
"""
        })
        data.append('wizard/wizard_views.xml')
    
    # Create the proper combined __init__.py
    init_imports = ["models"]
    if module_info["has_api"] or module_info["type"] == "website":
        init_imports.append("controllers")
    if module_info["has_reports"]:
        init_imports.append("report")
    if module_info["has_wizards"]:
        init_imports.append("wizard")
    
    init_content = "from . import " + "\nfrom . import ".join(init_imports) + "\n"
    
    # Update the __init__.py file with combined imports
    for i, file in enumerate(files):
        if file["path"] == f"{module_name}/__init__.py":
            files[i]["content"] = init_content
            break
    else:
        files.append({
            "path": f"{module_name}/__init__.py",
            "content": init_content
        })
    
    # Generate the manifest file
    manifest_content = f"""{{    
    'name': '{module_info['name']}',
    'version': '1.0',
    'category': '{module_info['category']}',
    'summary': '{module_info['summary']}',
    'description': '''
{module_info['description']}
''',
    'author': 'Odoo Module Generator',
    'website': 'https://www.example.com',
    'depends': {str(depends)},
    'data': {str(data)},
    'assets': {str(assets) if assets else '{{}}'},
    'installable': True,
    'application': False,
    'auto_install': False,
}}"""
    
    files.append({
        "path": f"{module_name}/__manifest__.py",
        "content": manifest_content
    })
    
    return files
