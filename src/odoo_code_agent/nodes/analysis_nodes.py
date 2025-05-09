#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analysis nodes for the Odoo Code Agent.

This module provides the analysis phase nodes for the Odoo Code Agent workflow.
"""

import logging
import json
from typing import Dict, List, Optional, Any

# Set up logging
logger = logging.getLogger(__name__)

from ..state import OdooCodeAgentState, AgentPhase
from ..utils.gemini_client import GeminiClient
from src.odoo_docs_rag.docs_retriever import OdooDocsRetriever

# Import for model discovery and field analysis
try:
    from src.odoo.dynamic.model_discovery import ModelDiscovery
    from src.odoo.dynamic.field_analyzer import FieldAnalyzer
    HAS_MODEL_DISCOVERY = True
    logger.info("Successfully imported ModelDiscovery and FieldAnalyzer")
except ImportError as e:
    logger.warning(f"Model discovery imports failed: {str(e)}")
    HAS_MODEL_DISCOVERY = False


def initialize_analysis(state: OdooCodeAgentState, query: Optional[str] = None) -> OdooCodeAgentState:
    """Initialize the analysis phase.

    Args:
        state: The current agent state
        query: Optional query from the user

    Returns:
        Updated agent state
    """
    if query:
        state.analysis_state.query = query

    state.phase = AgentPhase.ANALYSIS
    state.current_step = "gather_documentation"

    # Add the query to the history
    state.history.append(f"User query: {state.analysis_state.query}")

    logger.info(f"Analysis initialized with query: {state.analysis_state.query}")
    return state


def gather_documentation(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """Gather documentation related to the query.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    try:
        # Initialize the Odoo documentation retriever
        docs_dir = "/Users/vinusoft85/workspace/odoo18_mcp_project/odoo_docs"

        retriever = OdooDocsRetriever(
            docs_dir=docs_dir,
            force_rebuild=False
        )

        # Extract key concepts from the query for targeted documentation retrieval
        query = state.analysis_state.query

        # Create specialized queries based on the original query
        specialized_queries = [
            query,  # Original query
            f"Odoo 18 module structure and development {query}",  # Module structure
            f"Odoo 18 models and fields for {query}",  # Models and fields
            f"Odoo 18 views and UI for {query}"  # Views and UI
        ]

        # Extract potential module types from the query
        module_types = []
        query_lower = query.lower()

        if "crm" in query_lower:
            module_types.append("CRM")
            specialized_queries.append("Odoo 18 CRM module development")

        if "mail" in query_lower or "email" in query_lower or "mailing" in query_lower:
            module_types.append("Mail")
            specialized_queries.append("Odoo 18 mail integration and mass mailing")

        if "website" in query_lower or "portal" in query_lower:
            module_types.append("Website")
            specialized_queries.append("Odoo 18 website and portal development")

        if "report" in query_lower or "reporting" in query_lower:
            module_types.append("Reporting")
            specialized_queries.append("Odoo 18 reporting and QWeb reports")

        if "accounting" in query_lower or "invoice" in query_lower or "payment" in query_lower:
            module_types.append("Accounting")
            specialized_queries.append("Odoo 18 accounting module development")

        # Store identified module types
        state.analysis_state.context["module_types"] = module_types

        # Query the documentation with multiple specialized queries
        all_results = []

        for specialized_query in specialized_queries:
            try:
                logger.info(f"Querying documentation with: {specialized_query}")
                results = retriever.retrieve(specialized_query, max_results=3)

                # Add source query to each result for reference
                for result in results:
                    result["source_query"] = specialized_query

                all_results.extend(results)

                # Short pause to avoid overwhelming the retriever
                import time
                time.sleep(0.1)

            except Exception as e:
                logger.warning(f"Error retrieving documentation for query '{specialized_query}': {str(e)}")
                # Continue with other queries even if one fails

        # Deduplicate results based on content similarity
        unique_results = []
        seen_content = set()

        for result in all_results:
            # Create a content fingerprint (first 100 chars)
            content = result.get("text", "")
            fingerprint = content[:100] if content else ""

            if fingerprint and fingerprint not in seen_content:
                seen_content.add(fingerprint)
                unique_results.append(result)

        # Sort by score
        unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Limit to top results
        top_results = unique_results[:8]  # Increased from 5 to 8 for more context

        # Store the results in the state
        state.analysis_state.documentation_results = top_results

        # Format the documentation for context
        formatted_docs = []
        for result in top_results:
            formatted_docs.append({
                "source": result.get("metadata", {}).get("file_name", "Unknown"),
                "query": result.get("source_query", ""),
                "content": result.get("text", "")[:500] + "..." if len(result.get("text", "")) > 500 else result.get("text", ""),
                "score": result.get("score", 0)
            })

        # Add documentation to context
        state.analysis_state.context["documentation"] = formatted_docs

        # Add to history
        state.history.append(f"Retrieved {len(top_results)} documentation results from {len(specialized_queries)} specialized queries")

        # Proceed to gather model information
        state.current_step = "gather_model_information"
        logger.info(f"Documentation gathered: {len(top_results)} results")

    except Exception as e:
        logger.error(f"Error gathering documentation: {str(e)}")
        state.analysis_state.error = f"Error gathering documentation: {str(e)}"
        state.current_step = "error"

    return state


def gather_model_information(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """Gather information about relevant Odoo models based on the query.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    logger.info("Starting gather_model_information function")
    try:
        # Skip if model discovery is not available
        if not HAS_MODEL_DISCOVERY:
            logger.warning("Model discovery not available, skipping model information gathering")
            state.current_step = "analyze_requirements"
            return state

        logger.info("Model discovery is available, proceeding with model information gathering")

        # Extract potential model keywords from the query
        query = state.analysis_state.query
        query_lower = query.lower()

        # Initialize model discovery
        from src.odoo.client import OdooClient
        from src.odoo.schemas import OdooConfig
        from ..utils import odoo_connector

        # Use the Odoo client from the state if available, otherwise create a new one
        try:
            # Create OdooConfig with the correct parameters
            config = OdooConfig(
                url=odoo_connector.ODOO_URL,
                db=odoo_connector.ODOO_DB,
                username=odoo_connector.ODOO_USERNAME,
                password=odoo_connector.ODOO_PASSWORD
            )

            # Initialize OdooClient with the config
            odoo_client = OdooClient(config)
            logger.info(f"Successfully initialized Odoo client with URL: {odoo_connector.ODOO_URL}")
        except Exception as e:
            logger.error(f"Failed to initialize Odoo client: {str(e)}")
            # Continue to analyze requirements even if model information gathering fails
            state.current_step = "analyze_requirements"
            return state
        model_discovery = ModelDiscovery(odoo_client)
        field_analyzer = FieldAnalyzer(model_discovery)

        # We'll focus on using ModelDiscovery and FieldAnalyzer directly
        logger.info("Using ModelDiscovery and FieldAnalyzer for gathering model information")

        # Store model information in the state
        model_info = {}

        # Identify potential models based on the query
        potential_models = []

        # Common model keywords mapping
        model_keywords = {
            "customer": ["res.partner"],
            "partner": ["res.partner"],
            "contact": ["res.partner"],
            "product": ["product.product", "product.template"],
            "sale": ["sale.order", "sale.order.line"],
            "invoice": ["account.move"],
            "bill": ["account.move"],
            "project": ["project.project", "project.task"],
            "task": ["project.task"],
            "crm": ["crm.lead"],
            "lead": ["crm.lead"],
            "opportunity": ["crm.lead"],
            "mail": ["mail.message", "mail.mail", "mail.template"],
            "email": ["mail.mail", "mail.template"],
            "user": ["res.users"],
            "employee": ["hr.employee"],
            "inventory": ["stock.inventory", "stock.move", "stock.picking"],
            "stock": ["stock.move", "stock.picking"],
            "warehouse": ["stock.warehouse"],
            "purchase": ["purchase.order", "purchase.order.line"],
            "payment": ["account.payment"],
            "tax": ["account.tax"],
            "website": ["website.page", "website.menu"],
            "event": ["event.event", "event.registration"],
        }

        # Check for model keywords in the query
        for keyword, models in model_keywords.items():
            if keyword in query_lower:
                for model in models:
                    if model not in potential_models:
                        potential_models.append(model)

        # If no potential models found, add some common ones
        if not potential_models:
            potential_models = ["res.partner", "product.product", "sale.order"]

        logger.info(f"Identified potential models: {potential_models}")

        # Gather information about each potential model
        logger.info(f"Starting to gather information for {len(potential_models)} potential models")
        for model_name in potential_models:
            try:
                logger.info(f"Processing model: {model_name}")

                # Get model information
                logger.info(f"Getting model info for {model_name}")
                model_details = model_discovery.get_model_info(model_name)
                if not model_details:
                    logger.warning(f"No model details found for {model_name}, skipping")
                    continue

                # Get field information
                logger.info(f"Getting field information for {model_name}")
                fields_info = model_discovery.get_model_fields(model_name)
                logger.info(f"Retrieved {len(fields_info)} fields for {model_name}")

                # Get important fields
                logger.info(f"Analyzing field importance for {model_name}")
                try:
                    important_fields = field_analyzer.get_read_fields(model_name, min_importance=30)
                    logger.info(f"Identified {len(important_fields)} important fields for {model_name}")
                except Exception as field_err:
                    logger.error(f"Error analyzing field importance: {str(field_err)}")
                    # Use a fallback approach if field analysis fails
                    important_fields = list(fields_info.keys())[:10]  # Take first 10 fields as fallback
                    logger.info(f"Using fallback: {len(important_fields)} fields for {model_name}")

                # Store model information
                model_info[model_name] = {
                    "name": model_details.get("name", model_name),
                    "fields": {field: fields_info.get(field, {}) for field in important_fields if field in fields_info},
                    "important_fields": important_fields
                }

                logger.info(f"Successfully gathered information for model {model_name} with {len(important_fields)} important fields")

            except Exception as e:
                logger.error(f"Error gathering information for model {model_name}: {str(e)}")

        # Store model information in the state
        state.analysis_state.context["model_info"] = model_info

        # Get additional field details for the most relevant models
        logger.info("Getting additional field details for relevant models")
        try:
            # Select the most relevant models based on the query
            relevant_models = []

            # Check for specific module types in the query
            query_lower = query.lower()

            if "crm" in query_lower or "customer relationship" in query_lower:
                relevant_models.append("crm.lead")

            if "mail" in query_lower or "email" in query_lower or "mass mailing" in query_lower:
                relevant_models.extend(["mail.mail", "mail.template", "mailing.mailing"])

            if "contact" in query_lower or "partner" in query_lower:
                relevant_models.append("res.partner")

            if "sale" in query_lower or "order" in query_lower:
                relevant_models.append("sale.order")

            # If no specific models were identified, use the first few from potential_models
            if not relevant_models and potential_models:
                relevant_models = potential_models[:2]  # Take the first two models

            logger.info(f"Selected relevant models for detailed analysis: {relevant_models}")

            # Get detailed field information for each relevant model
            detailed_model_info = {}

            for model_name in relevant_models:
                try:
                    logger.info(f"Getting detailed field information for {model_name}")

                    # Get all fields including technical details
                    all_fields = model_discovery.get_model_fields(model_name)

                    # Get field groups for better organization
                    field_groups = field_analyzer.get_field_groups(model_name)

                    # Store detailed information
                    detailed_model_info[model_name] = {
                        "all_fields": all_fields,
                        "field_groups": field_groups
                    }

                    logger.info(f"Successfully retrieved detailed information for {model_name}")
                except Exception as detail_err:
                    logger.error(f"Error getting detailed information for {model_name}: {str(detail_err)}")

            # Store the detailed model information in the state
            state.analysis_state.context["detailed_model_info"] = detailed_model_info

            # Create empty sample data structure to maintain compatibility
            state.analysis_state.context["sample_data"] = {"model": "unknown", "records": []}

        except Exception as e:
            logger.error(f"Error getting detailed model information: {str(e)}")
            # Create empty structures to avoid errors later
            state.analysis_state.context["detailed_model_info"] = {}
            state.analysis_state.context["sample_data"] = {"model": "unknown", "records": []}
            # Continue with analysis even if detailed information gathering fails

        # Add to history
        state.history.append(f"Gathered information for {len(model_info)} models")

        # Proceed to analyze requirements
        state.current_step = "analyze_requirements"
        logger.info("Model information gathering completed, proceeding to analyze_requirements")

    except Exception as e:
        logger.error(f"Error gathering model information: {str(e)}")
        # Continue to analyze requirements even if model information gathering fails
        state.current_step = "analyze_requirements"
        logger.info("Error in model information gathering, proceeding to analyze_requirements anyway")

    logger.info("Returning from gather_model_information function")
    return state


def analyze_requirements(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """Analyze the requirements based on the query, documentation, and model information.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    logger.info("Starting analyze_requirements function")
    try:
        # Use Gemini to analyze the requirements if available
        if state.use_gemini:
            logger.info("Using Gemini to analyze requirements")
            try:
                gemini_client = GeminiClient()
                logger.info("GeminiClient initialized")
            except Exception as e:
                logger.error(f"Failed to initialize GeminiClient: {str(e)}")
                logger.info("Falling back to default analysis")
                state.use_gemini = False

            # Prepare context for the analysis
            query = state.analysis_state.query

            # Get documentation from the state
            documentation = state.analysis_state.context.get("documentation", [])
            formatted_docs = ""

            if documentation:
                formatted_docs = "RELEVANT DOCUMENTATION:\n\n"
                for i, doc in enumerate(documentation):
                    formatted_docs += f"Document {i+1}: {doc.get('source', 'Unknown')}\n"
                    formatted_docs += f"Query: {doc.get('query', 'Unknown')}\n"
                    formatted_docs += f"Content: {doc.get('content', '')}\n\n"

            # Get model information from the state
            model_info = state.analysis_state.context.get("model_info", {})
            detailed_model_info = state.analysis_state.context.get("detailed_model_info", {})
            formatted_models = ""

            if model_info or detailed_model_info:
                formatted_models = "RELEVANT ODOO MODELS:\n\n"

                # First add the basic model information
                for model_name, info in model_info.items():
                    formatted_models += f"Model: {model_name} ({info.get('name', '')})\n"
                    formatted_models += "Important fields:\n"

                    fields = info.get("fields", {})
                    for field_name, field_info in fields.items():
                        field_type = field_info.get("type", "char")
                        field_string = field_info.get("string", field_name)
                        relation = field_info.get("relation", "")
                        relation_info = f" -> {relation}" if relation else ""

                        formatted_models += f"  - {field_name} ({field_type}{relation_info}): {field_string}\n"

                    formatted_models += "\n"

                # Then add the detailed model information
                if detailed_model_info:
                    formatted_models += "DETAILED MODEL INFORMATION:\n\n"

                    for model_name, details in detailed_model_info.items():
                        formatted_models += f"Model: {model_name}\n"

                        # Add field groups if available
                        field_groups = details.get("field_groups", {})
                        if field_groups:
                            formatted_models += "Field groups:\n"
                            for group_name, fields in field_groups.items():
                                formatted_models += f"  Group: {group_name}\n"
                                for field in fields[:5]:  # Limit to 5 fields per group to avoid too much text
                                    formatted_models += f"    - {field}\n"
                            formatted_models += "\n"

                        # Add some key fields with detailed information
                        all_fields = details.get("all_fields", {})
                        if all_fields:
                            formatted_models += "Key fields with details:\n"
                            # Select important fields based on common patterns
                            key_field_patterns = ["name", "partner_id", "user_id", "state", "date", "email", "phone", "address"]
                            key_fields = []

                            # Find fields matching the patterns
                            for pattern in key_field_patterns:
                                for field_name in all_fields:
                                    if pattern in field_name and field_name not in key_fields:
                                        key_fields.append(field_name)
                                        if len(key_fields) >= 10:  # Limit to 10 key fields
                                            break
                                if len(key_fields) >= 10:
                                    break

                            # If we didn't find enough key fields, add some more
                            if len(key_fields) < 5 and len(all_fields) > 0:
                                additional_fields = list(all_fields.keys())[:10]  # Take first 10 fields
                                for field in additional_fields:
                                    if field not in key_fields:
                                        key_fields.append(field)
                                        if len(key_fields) >= 10:
                                            break

                            # Add the key fields to the formatted text
                            for field_name in key_fields:
                                field_info = all_fields.get(field_name, {})
                                field_type = field_info.get("type", "char")
                                field_string = field_info.get("string", field_name)
                                relation = field_info.get("relation", "")
                                required = "Required" if field_info.get("required", False) else "Optional"
                                readonly = "Readonly" if field_info.get("readonly", False) else "Editable"
                                relation_info = f" -> {relation}" if relation else ""

                                formatted_models += f"  - {field_name} ({field_type}{relation_info}): {field_string} [{required}, {readonly}]\n"

                            formatted_models += "\n"

            # Get module types from the state
            module_types = state.analysis_state.context.get("module_types", [])
            formatted_module_types = ""

            if module_types:
                formatted_module_types = "DETECTED MODULE TYPES:\n"
                formatted_module_types += ", ".join(module_types)
                formatted_module_types += "\n\n"

            # Get sample data from the state
            sample_data = state.analysis_state.context.get("sample_data", {})
            formatted_sample_data = ""

            if sample_data and "records" in sample_data:
                formatted_sample_data = "SAMPLE DATA:\n\n"
                formatted_sample_data += f"Model: {sample_data.get('model', 'Unknown')}\n"
                formatted_sample_data += f"Records: {len(sample_data.get('records', []))}\n\n"

                # Include a few sample records
                records = sample_data.get("records", [])
                for i, record in enumerate(records[:3]):  # Limit to 3 records
                    formatted_sample_data += f"Record {i+1}:\n"
                    for field, value in record.items():
                        if isinstance(value, (dict, list)):
                            value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                        formatted_sample_data += f"  {field}: {value}\n"
                    formatted_sample_data += "\n"

            # Combine all context information
            context = f"{formatted_module_types}{formatted_docs}{formatted_models}{formatted_sample_data}"

            # Get the analysis from Gemini with enhanced context
            logger.info("Attempting to analyze requirements with Gemini")
            analysis_result = gemini_client.analyze_requirements(query, context)

            if "error" in analysis_result:
                logger.warning(f"Gemini analysis error: {analysis_result['error']}")

                # Check if Ollama is available as a fallback
                if state.use_ollama:
                    logger.info("Falling back to Ollama for analysis")
                    try:
                        # Import the Ollama client
                        from ..utils.ollama_client import OllamaClient

                        # Initialize the Ollama client
                        ollama_client = OllamaClient()

                        # Try to get analysis from Ollama
                        logger.info("Attempting to analyze requirements with Ollama")
                        analysis_result = ollama_client.analyze_requirements(query, context)

                        if "error" not in analysis_result:
                            logger.info("Successfully analyzed requirements with Ollama")
                        else:
                            logger.error(f"Ollama analysis error: {analysis_result['error']}")
                            # Continue with fallback analysis
                            state.use_gemini = False
                            state.use_ollama = False
                    except Exception as ollama_err:
                        logger.error(f"Error using Ollama fallback: {str(ollama_err)}")
                        # Continue with fallback analysis
                        state.use_gemini = False
                        state.use_ollama = False
                else:
                    # Continue with fallback analysis
                    state.use_gemini = False

            # Store the analysis in the state
            state.analysis_state.context["analysis"] = analysis_result

            # Add to history
            state.history.append(f"Requirements analyzed: {analysis_result.get('module_name', 'Unknown module')}")

            # Mark analysis as complete
            state.analysis_state.analysis_complete = True
            state.current_step = "complete_analysis"

            logger.info(f"Requirements analyzed successfully: {json.dumps(analysis_result, indent=2)[:200]}...")
        else:
            # Fallback to a simpler analysis
            logger.info("Gemini not available, using fallback analysis")

            # Extract module name from query
            query = state.analysis_state.query.lower()

            # Try to find a meaningful module name based on the query
            if "customer feedback" in query:
                module_name = "customer_feedback"
            elif "project" in query and "management" in query:
                module_name = "project_management"
            elif "inventory" in query:
                module_name = "inventory_management"
            elif "sales" in query:
                module_name = "sales_management"
            elif "purchase" in query:
                module_name = "purchase_management"
            elif "hr" in query or "employee" in query:
                module_name = "hr_management"
            elif "point of sale" in query or "pos" in query:
                if "multi-currency" in query or "currency" in query:
                    module_name = "pos_multi_currency"
                else:
                    module_name = "pos_custom"
            elif "website" in query:
                module_name = "website_custom"
            elif "ecommerce" in query or "e-commerce" in query:
                module_name = "website_sale_custom"
            elif "crm" in query:
                module_name = "crm_custom"
            else:
                # Default fallback: extract key words from the query
                words = query.split()
                key_words = [w for w in words if len(w) > 3 and w not in ["odoo", "module", "create", "with", "that", "this", "for", "and", "the"]]
                module_name = "_".join(key_words[:2]) if key_words else "custom_module"

            # Add _vpcs_ext suffix to prevent conflicts with existing Odoo apps
            module_name = module_name.replace(" ", "_").replace("-", "_").lower()
            module_name = f"{module_name}_vpcs_ext"

            # Create a basic analysis with fields based on the module type
            models = []

            # Customer feedback module
            if "customer feedback" in query or "feedback" in query:
                models = [
                    {
                        "name": f"{module_name}.feedback",
                        "description": "Customer Feedback",
                        "fields": [
                            {
                                "name": "name",
                                "type": "char",
                                "description": "Feedback Title"
                            },
                            {
                                "name": "partner_id",
                                "type": "many2one",
                                "description": "Customer",
                                "relation": "res.partner"
                            },
                            {
                                "name": "rating",
                                "type": "selection",
                                "description": "Rating",
                                "selection": [
                                    ("1", "Poor"),
                                    ("2", "Fair"),
                                    ("3", "Average"),
                                    ("4", "Good"),
                                    ("5", "Excellent")
                                ]
                            },
                            {
                                "name": "feedback_date",
                                "type": "date",
                                "description": "Feedback Date"
                            },
                            {
                                "name": "comment",
                                "type": "text",
                                "description": "Comment"
                            },
                            {
                                "name": "state",
                                "type": "selection",
                                "description": "Status",
                                "selection": [
                                    ("draft", "Draft"),
                                    ("submitted", "Submitted"),
                                    ("reviewed", "Reviewed"),
                                    ("closed", "Closed")
                                ]
                            }
                        ]
                    }
                ]
            # Project management module
            elif "project" in query:
                models = [
                    {
                        "name": f"{module_name}.project",
                        "description": "Project",
                        "fields": [
                            {
                                "name": "name",
                                "type": "char",
                                "description": "Project Name"
                            },
                            {
                                "name": "description",
                                "type": "text",
                                "description": "Description"
                            },
                            {
                                "name": "start_date",
                                "type": "date",
                                "description": "Start Date"
                            },
                            {
                                "name": "end_date",
                                "type": "date",
                                "description": "End Date"
                            },
                            {
                                "name": "state",
                                "type": "selection",
                                "description": "Status",
                                "selection": [
                                    ("draft", "Draft"),
                                    ("in_progress", "In Progress"),
                                    ("completed", "Completed"),
                                    ("cancelled", "Cancelled")
                                ]
                            }
                        ]
                    }
                ]
            # Point of Sale module
            elif "point of sale" in query or "pos" in query:
                if "multi-currency" in query or "currency" in query:
                    models = [
                        {
                            "name": f"{module_name}.currency",
                            "description": "POS Multi-Currency Configuration",
                            "fields": [
                                {
                                    "name": "name",
                                    "type": "char",
                                    "description": "Name"
                                },
                                {
                                    "name": "currency_id",
                                    "type": "many2one",
                                    "relation": "res.currency",
                                    "description": "Currency"
                                },
                                {
                                    "name": "rate",
                                    "type": "float",
                                    "description": "Exchange Rate"
                                },
                                {
                                    "name": "pos_config_id",
                                    "type": "many2one",
                                    "relation": "pos.config",
                                    "description": "POS Configuration"
                                },
                                {
                                    "name": "active",
                                    "type": "boolean",
                                    "description": "Active"
                                }
                            ]
                        }
                    ]
                else:
                    models = [
                        {
                            "name": f"{module_name}.config",
                            "description": "POS Custom Configuration",
                            "fields": [
                                {
                                    "name": "name",
                                    "type": "char",
                                    "description": "Name"
                                },
                                {
                                    "name": "pos_config_id",
                                    "type": "many2one",
                                    "relation": "pos.config",
                                    "description": "POS Configuration"
                                },
                                {
                                    "name": "active",
                                    "type": "boolean",
                                    "description": "Active"
                                }
                            ]
                        }
                    ]
            # CRM module
            elif "crm" in query:
                models = [
                    {
                        "name": f"{module_name}.lead",
                        "description": "Custom CRM Lead",
                        "fields": [
                            {
                                "name": "name",
                                "type": "char",
                                "description": "Lead Name"
                            },
                            {
                                "name": "partner_id",
                                "type": "many2one",
                                "relation": "res.partner",
                                "description": "Customer"
                            },
                            {
                                "name": "email",
                                "type": "char",
                                "description": "Email"
                            },
                            {
                                "name": "phone",
                                "type": "char",
                                "description": "Phone"
                            },
                            {
                                "name": "description",
                                "type": "text",
                                "description": "Description"
                            },
                            {
                                "name": "state",
                                "type": "selection",
                                "description": "Status",
                                "selection": [
                                    ("new", "New"),
                                    ("qualified", "Qualified"),
                                    ("proposition", "Proposition"),
                                    ("won", "Won"),
                                    ("lost", "Lost")
                                ]
                            }
                        ]
                    }
                ]
            # Website module
            elif "website" in query or "ecommerce" in query or "e-commerce" in query:
                models = [
                    {
                        "name": f"{module_name}.page",
                        "description": "Custom Website Page",
                        "fields": [
                            {
                                "name": "name",
                                "type": "char",
                                "description": "Page Name"
                            },
                            {
                                "name": "url",
                                "type": "char",
                                "description": "URL"
                            },
                            {
                                "name": "content",
                                "type": "html",
                                "description": "Content"
                            },
                            {
                                "name": "is_published",
                                "type": "boolean",
                                "description": "Published"
                            },
                            {
                                "name": "website_id",
                                "type": "many2one",
                                "relation": "website",
                                "description": "Website"
                            }
                        ]
                    }
                ]
            # Default model for other types
            else:
                # Extract a meaningful model name from the query
                model_words = []
                for word in query.split():
                    if len(word) > 3 and word.lower() not in ["odoo", "module", "create", "with", "that", "this", "for", "and", "the"]:
                        model_words.append(word.lower())
                        if len(model_words) >= 1:
                            break

                model_suffix = model_words[0] if model_words else "main"

                models = [
                    {
                        "name": f"{module_name}.{model_suffix}",
                        "description": f"{model_suffix.capitalize()} model for the {module_name} module",
                        "fields": [
                            {
                                "name": "name",
                                "type": "char",
                                "description": "Name"
                            },
                            {
                                "name": "active",
                                "type": "boolean",
                                "description": "Active"
                            },
                            {
                                "name": "description",
                                "type": "text",
                                "description": "Description"
                            }
                        ]
                    }
                ]

            # Create the analysis result
            analysis_result = {
                "module_name": module_name,
                "module_title": state.analysis_state.query,
                "description": f"Module for {state.analysis_state.query}",
                "models": models,
                "views": ["list", "form", "kanban"],
                "security": ["base.group_user"],
                "dependencies": ["base", "mail"]
            }

            # Store the analysis in the state
            state.analysis_state.context["analysis"] = analysis_result

            # Add to history
            state.history.append(f"Requirements analyzed (fallback): {module_name}")

            # Mark analysis as complete
            state.analysis_state.analysis_complete = True
            state.current_step = "complete_analysis"

            logger.info(f"Requirements analyzed with fallback: {json.dumps(analysis_result, indent=2)}")

    except Exception as e:
        logger.error(f"Error analyzing requirements: {str(e)}")
        state.analysis_state.error = f"Error analyzing requirements: {str(e)}"
        state.current_step = "error"

    return state


def complete_analysis(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """Complete the analysis phase and transition to planning.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    # Transfer relevant information to the planning state
    # Make sure analysis results are available for planning phase
    if "analysis" in state.analysis_state.context:
        logger.info("Analysis results available for planning phase")
    else:
        logger.warning("No analysis results available for planning phase")

    # Add to history
    state.history.append("Analysis phase completed")

    # Transition to planning phase
    state.phase = AgentPhase.PLANNING
    state.current_step = "create_plan"

    logger.info("Analysis phase completed, transitioning to planning")
    return state
