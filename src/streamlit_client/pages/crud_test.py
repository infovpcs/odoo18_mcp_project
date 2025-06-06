import streamlit as st
import json
import logging
from src.streamlit_client.utils.mcp_connector import MCPConnector # Import MCPConnector

logger = logging.getLogger(__name__)

def render_crud_test_page(mcp_connector: MCPConnector):
    # Remove this line as set_page_config should only be called once per app/page script
    # st.set_page_config(page_title="Odoo Tool Tester", layout="wide")

    st.title("Odoo Tool Tester")
    st.write("Use this page to test Odoo CRUD and method execution tools.")

    model_name = st.text_input("Odoo Model Name (e.g., res.partner)")

    st.header("CRUD Operations")

    # Create Record Section
    st.subheader("Create Record")
    create_values_str = st.text_area("Values (JSON) for Create", height=150)
    if st.button("Create Record"):
        if not model_name:
            st.error("Please enter an Odoo Model Name.")
        elif not create_values_str:
            st.error("Please enter values in JSON format for creating the record.")
        else:
            try:
                create_values = json.loads(create_values_str)
                st.info(f"Creating record in {model_name} with values: {create_values}...")
                # Call the tool to create the record using the passed mcp_connector
                result = mcp_connector.create_record(model_name=model_name, values=create_values)
                st.success("Create operation successful!")
                st.write("Result:")
                # Check if result is a string that looks like JSON or just a string
                try:
                    # Attempt to load as JSON
                    st.json(json.loads(result))
                except json.JSONDecodeError:
                    # If not JSON, display as text
                     st.text(result) # Use st.text for multi-line strings

            except json.JSONDecodeError:
                st.error("Invalid JSON format for values.")
            except Exception as e:
                st.error(f"An error occurred during Create: {e}")

    st.markdown("---")

    # Update Record Section
    st.subheader("Update Record")
    update_record_id = st.number_input("Record ID to Update", min_value=1)
    update_values_str = st.text_area("Values (JSON) for Update", height=150)
    if st.button("Update Record"):
        if not model_name:
            st.error("Please enter an Odoo Model Name.")
        elif not update_record_id:
            st.error("Please enter the ID of the record to update.")
        elif not update_values_str:
            st.error("Please enter values in JSON format for updating the record.")
        else:
            try:
                update_values = json.loads(update_values_str)
                st.info(f"Updating record {update_record_id} in {model_name} with values: {update_values}...")
                # Call the tool to update the record using the passed mcp_connector
                result = mcp_connector.update_record(model_name=model_name, record_id=update_record_id, values=update_values)
                st.success("Update operation successful!")
                st.write("Result:")
                # Check if result is a string that looks like JSON or just a string
                try:
                    # Attempt to load as JSON
                    st.json(json.loads(result))
                except json.JSONDecodeError:
                    # If not JSON, display as text
                     st.text(result) # Use st.text for multi-line strings
            except json.JSONDecodeError:
                st.error("Invalid JSON format for values.")
            except Exception as e:
                st.error(f"An error occurred during Update: {e}")

    st.markdown("--- Cas")

    # Delete Record Section
    st.subheader("Delete Record")
    delete_record_id = st.number_input("Record ID to Delete", min_value=1, key='delete_id')
    if st.button("Delete Record"):
        if not model_name:
            st.error("Please enter an Odoo Model Name.")
        elif not delete_record_id:
            st.error("Please enter the ID of the record to delete.")
        else:
            st.info(f"Deleting record {delete_record_id} from {model_name}...")
            try:
                # Call the tool to delete the record using the passed mcp_connector
                result = mcp_connector.delete_record(model_name=model_name, record_id=delete_record_id)
                st.success("Delete operation successful!")
                st.write("Result:")
                # Check if result is a string that looks like JSON or just a string
                try:
                    # Attempt to load as JSON
                    st.json(json.loads(result))
                except json.JSONDecodeError:
                    # If not JSON, display as text
                     st.text(result) # Use st.text for multi-line strings
            except Exception as e:
                st.error(f"An error occurred during Delete: {e}")

    st.markdown("--- ")

    # Execute Method Section
    st.header("Execute Method")
    method_name = st.text_input("Method Name (e.g., name_search)")
    method_args_str = st.text_area("Args (JSON list or dict) for Method", height=150)
    execute_record_id = st.number_input("Record ID (Optional, for method on specific record)", min_value=0, value=0, key='execute_id')

    if st.button("Execute Method"):
        if not model_name:
            st.error("Please enter an Odoo Model Name.")
        elif not method_name:
            st.error("Please enter the Method Name.")
        else:
            args_data = [] # Default to empty list if no args provided
            if method_args_str:
                try:
                    args_data = json.loads(method_args_str)
                except json.JSONDecodeError:
                     st.error("Invalid JSON format for method arguments.")
                     args_data = None # Set to None to indicate parsing failed

            if args_data is not None:
                st.info(f"Executing method '{method_name}' on {model_name}...")
                try:
                    # Prepare arguments based on record_id and args_data
                    tool_args = []

                    if execute_record_id > 0:
                        # If a record ID is specified, the first argument is the record ID or a list of IDs
                        tool_args = [execute_record_id] # Assuming single record for now
                        # The rest of the arguments follow the record ID
                        if isinstance(args_data, list):
                             tool_args.extend(args_data)
                        elif isinstance(args_data, dict):
                             # If it's a dictionary, pass the record ID in a list, and the dict as the next argument
                             # This matches the execute_kw signature when kwargs are used.
                             tool_args = [[execute_record_id], args_data]
                        elif method_args_str:
                             # If it was a non-list/dict but not empty string, add it after the ID
                            tool_args.append(args_data)

                    elif method_args_str:
                        # If no record ID and args are provided, pass them directly
                        if isinstance(args_data, list):
                            tool_args = args_data
                        elif isinstance(args_data, dict):
                             # If it's a dictionary and no record ID, pass as a single dictionary argument
                            tool_args = [args_data]
                        else:
                             # If it was a non-list/dict but not empty string, wrap in a list
                            tool_args = [args_data]

                    logger.info(f"Calling execute_method tool with model_name={model_name}, method={method_name}, args={tool_args}")

                    # Call the tool using the passed mcp_connector
                    result = mcp_connector.execute_method(model_name=model_name, method=method_name, args=tool_args)
                    st.success("Method execution successful!")
                    st.write("Result:")
                    # Check if result is a string that looks like JSON or just a string
                    try:
                        # Attempt to load as JSON
                        st.json(json.loads(result))
                    except json.JSONDecodeError:
                        # If not JSON, display as text
                         st.text(result) # Use st.text for multi-line strings

                except Exception as e:
                    st.error(f"An error occurred during Method Execution: {e}") 