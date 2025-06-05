#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Odoo Code Agent based on LangGraph.

This package provides a simplified workflow for generating Odoo 18 modules and components
using a LangGraph-based workflow inspired by the CodeAgent_LLamabot project.
"""

from .odoo_code_generator import generate_odoo_module, OdooCodeGenerator
from . import utils