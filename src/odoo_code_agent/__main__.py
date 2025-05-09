#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line interface for the Odoo Code Agent.
"""

import argparse
import json
import logging
import sys
from typing import Dict, Any

from .main import run_odoo_code_agent

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Odoo Code Agent - Generate Odoo modules from natural language")
    
    # Required arguments
    parser.add_argument("--query", type=str, required=True, help="The natural language query describing the module to create")
    
    # Optional arguments
    parser.add_argument("--odoo-url", type=str, default="http://localhost:8069", help="Odoo server URL")
    parser.add_argument("--odoo-db", type=str, default="llmdb18", help="Odoo database name")
    parser.add_argument("--odoo-username", type=str, default="admin", help="Odoo username")
    parser.add_argument("--odoo-password", type=str, default="admin", help="Odoo password")
    
    # Model options
    parser.add_argument("--use-gemini", action="store_true", help="Use Google Gemini for analysis and planning")
    parser.add_argument("--use-ollama", action="store_true", help="Use Ollama as a fallback")
    parser.add_argument("--no-llm", action="store_true", help="Don't use any LLM, use fallback analysis only")
    
    # Feedback options
    parser.add_argument("--feedback", type=str, help="Feedback to incorporate into the code generation")
    
    # Output options
    parser.add_argument("--save-to-files", action="store_true", help="Save the generated files to disk")
    parser.add_argument("--output-dir", type=str, help="Directory to save the generated files to")
    
    # Workflow options
    parser.add_argument("--wait-for-validation", action="store_true", help="Wait for human validation at validation points")
    parser.add_argument("--current-phase", type=str, help="The current phase to resume from")
    parser.add_argument("--state-file", type=str, help="Path to a state file to resume from")
    parser.add_argument("--max-steps", type=int, default=20, help="Maximum number of steps to run")
    
    # Debug options
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    return parser.parse_args()


def main():
    """Main entry point for the Odoo Code Agent."""
    args = parse_args()
    
    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load state from file if provided
    state_dict = None
    if args.state_file:
        try:
            with open(args.state_file, "r") as f:
                state_dict = json.load(f)
            logger.info(f"Loaded state from {args.state_file}")
        except Exception as e:
            logger.error(f"Error loading state from {args.state_file}: {str(e)}")
            sys.exit(1)
    
    # Handle the no-llm option
    if args.no_llm:
        args.use_gemini = False
        args.use_ollama = False
    
    # Run the Odoo Code Agent
    try:
        result = run_odoo_code_agent(
            query=args.query,
            odoo_url=args.odoo_url,
            odoo_db=args.odoo_db,
            odoo_username=args.odoo_username,
            odoo_password=args.odoo_password,
            use_gemini=args.use_gemini,
            use_ollama=args.use_ollama,
            feedback=args.feedback,
            max_steps=args.max_steps,
            save_to_files=args.save_to_files,
            output_dir=args.output_dir,
            wait_for_validation=args.wait_for_validation,
            current_phase=args.current_phase,
            state_dict=state_dict
        )
        
        # Print the result
        print(json.dumps(result, indent=2))
        
        # Save the state to a file if requested
        if args.wait_for_validation and result.get("requires_validation"):
            state_file = f"odoo_code_agent_state_{result.get('current_phase')}.json"
            with open(state_file, "w") as f:
                json.dump(result.get("state_dict"), f, indent=2)
            logger.info(f"Saved state to {state_file}")
            print(f"\nState saved to {state_file}. To resume, use --state-file={state_file}")
        
        # Exit with success
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running Odoo Code Agent: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
