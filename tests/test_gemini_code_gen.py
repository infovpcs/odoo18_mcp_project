#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini API Code Generation Test Script

This script tests whether Gemini can generate code properly by requesting
a simple Odoo model class.
"""

import os
import json
import asyncio
import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_gemini_code_generation():
    """Test Gemini's ability to generate Odoo model code."""
    logger.info("Testing Gemini code generation capabilities...")
    
    # Initialize the Gemini model
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.error("No GEMINI_API_KEY or GOOGLE_API_KEY found in environment variables")
        return
    
    try:
        # Create the model with verbose mode to see the full API interaction
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",  # or gemini-1.5-pro for more complex tasks
            google_api_key=api_key,
            temperature=0.2,  # Lower temperature for more deterministic code generation
            verbose=True
        )
        
        # Create a simple prompt to test code generation
        code_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Odoo developer specializing in Python.
Generate clean, readable, and efficient Odoo model code.
Include proper docstrings, type hints, and follow PEP8 standards.
Only respond with Python code. No explanations or additional text."""),
            ("user", """Create a simple Odoo 18 model class called 'ProductExtension' that 
extends the product.template model with the following fields:
1. A Many2one field linking to res.partner called 'supplier_id'
2. A Float field called 'minimum_margin' with default value 0.1
3. A Boolean field called 'is_premium' with default value False
4. A Selection field called 'quality_grade' with options: ('A', 'Grade A'), ('B', 'Grade B'), ('C', 'Grade C')
5. A Html field called 'extended_description'

Implement an onchange method for supplier_id that sets a default minimum_margin of 0.2 when a supplier is selected.
Also add a compute method for a field called 'margin_warning' that returns a warning message if the margin is too low.
""")
        ])
        
        # Create a chain that extracts just the generated code
        chain = code_prompt | llm | StrOutputParser()
        
        # Run the chain and get the result
        logger.info("Sending code generation request to Gemini...")
        result = await chain.ainvoke({})
        
        # Print the result
        logger.info("Gemini code generation result:")
        print("\n" + "="*80)
        print(result)
        print("="*80 + "\n")
        
        # Verify if the result looks like valid Python code
        python_indicators = [
            "class ProductExtension",
            "models.Model",
            "_inherit",
            "fields.",
            "def"
        ]
        
        all_indicators_present = all(indicator in result for indicator in python_indicators)
        if all_indicators_present:
            logger.info("SUCCESS: Generated content appears to be valid Python code!")
        else:
            logger.warning("WARNING: Generated content may not be valid Python code.")
            # List the missing indicators
            missing = [i for i in python_indicators if i not in result]
            logger.warning(f"Missing expected code elements: {missing}")
        
        return all_indicators_present, result
        
    except Exception as e:
        logger.error(f"Error testing Gemini code generation: {str(e)}")
        return False, str(e)

if __name__ == "__main__":
    asyncio.run(test_gemini_code_generation())
