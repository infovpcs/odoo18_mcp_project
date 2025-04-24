#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dynamic Model Handling Module

This module provides functionality for dynamically discovering and working with
Odoo models and their fields.
"""

from .model_discovery import ModelDiscovery
from .field_analyzer import FieldAnalyzer
from .crud_generator import CrudGenerator
from .nlp_analyzer import NlpAnalyzer