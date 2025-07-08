# GitHub Setup and Project Deployment

This document provides instructions for setting up the project on GitHub and deploying it in different environments.

## GitHub Setup

1. Create a new private repository on GitHub:
   - Go to https://github.com/new
   - Name: `odoo18-mcp-project`
   - Description: `Odoo 18 MCP Integration - A robust integration server that connects MCP with Odoo 18.0 ERP system`
   - Set to Private
   - Do not initialize with README, .gitignore, or license

2. Push your local repository to GitHub:
   ```bash
   git remote add origin https://github.com/yourusername/odoo18-mcp-project.git
   
   # Push the master branch
   git checkout master
   git push -u origin master
   
   # Push the 18.0 branch
   git checkout 18.0
   git push -u origin 18.0
   ```

3. Verify that all files have been pushed correctly by checking the GitHub repository.

## Project Setup in Different Environments

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/odoo18-mcp-project.git
   cd odoo18-mcp-project
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

4. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file with your Odoo connection details.

6. Run the MCP server:
   ```bash
   python main.py
   ```

### Streamlit Client

The project includes a Streamlit application that provides a user-friendly interface for interacting with the MCP server and its tools. It includes the following pages:

- **Odoo Module Generator**: Generate Odoo 18 modules.
- **Odoo Documentation Search**: Search and retrieve Odoo documentation.
- **Data Export/Import**: Perform export and import operations.
- **CRUD Test Page**: Test Odoo CRUD and method execution tools.
- **Workflow Visualization**: Visualize workflows and diagrams.

To run the Streamlit client:

1. Ensure you have followed the steps under "Local Development" to set up the environment and install dependencies.
2. Run the Streamlit app from the project root directory:
   ```bash
   streamlit run app.py
   ```
3. The Streamlit app will open in your web browser.

### Cloud Desktop (VS Code Remote)

1. Connect to your cloud desktop using VS Code Remote.

2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/odoo18-mcp-project.git
   cd odoo18-mcp-project
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

4. Install the package in development mode:
   ```bash
   pip install -e .
   ```

5. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```

6. Edit the `.env` file with your Odoo connection details.

7. Open the project in VS Code:
   ```bash
   code .
   ```

8. Install the recommended VS Code extensions:
   - Python
   - Pylance
   - Python Docstring Generator
   - Python Test Explorer
   - GitLens

9. Run the MCP server:
   ```bash
   python main.py
   ```

### Production Deployment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/odoo18-mcp-project.git
   cd odoo18-mcp-project
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install the package:
   ```bash
   pip install .
   ```

4. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file with your production Odoo connection details.

6. Run the MCP server with a production WSGI server:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker "src.mcp.client:MCPClient().app"
   ```

7. For systemd service setup, create a file `/etc/systemd/system/odoo18-mcp.service`:
   ```
   [Unit]
   Description=Odoo 18 MCP Integration
   After=network.target

   [Service]
   User=your_user
   Group=your_group
   WorkingDirectory=/path/to/odoo18-mcp-project
   Environment="PATH=/path/to/odoo18-mcp-project/venv/bin"
   EnvironmentFile=/path/to/odoo18-mcp-project/.env
   ExecStart=/path/to/odoo18-mcp-project/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker "src.mcp.client:MCPClient().app" --bind 0.0.0.0:8000
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

8. Enable and start the service:
   ```bash
   sudo systemctl enable odoo18-mcp
   sudo systemctl start odoo18-mcp
   ```

## Docker Deployment

1. Create a `Dockerfile`:
   ```dockerfile
   FROM python:3.10-slim

   WORKDIR /app

   COPY . .
   RUN pip install --no-cache-dir .

   EXPOSE 8000

   CMD ["uvicorn", "src.mcp.client:MCPClient().app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. Create a `.dockerignore` file:
   ```
   .git
   .env
   venv
   __pycache__
   *.pyc
   *.pyo
   *.pyd
   .Python
   env
   pip-log.txt
   pip-delete-this-directory.txt
   .tox
   .coverage
   htmlcov
   .pytest_cache
   .mypy_cache
   ```

3. Build the Docker image:
   ```bash
   docker build -t odoo18-mcp-project .
   ```

4. Run the Docker container:
   ```bash
   docker run -d -p 8000:8000 --env-file .env --name odoo18-mcp odoo18-mcp-project
   ```

## Testing

1. Run the basic client test:
   ```bash
   python client_test.py
   ```

2. Run the advanced client test:
   ```bash
   python advanced_client_test.py
   ```

3. Run the dynamic model test:
   ```bash
   python dynamic_model_test.py
   ```

## Troubleshooting

### Connection Issues

If you encounter connection issues with Odoo:

1. Verify that the Odoo server is running and accessible.
2. Check that the URL, database name, username, and password in the `.env` file are correct.
3. Ensure that the Odoo server allows XML-RPC connections.
4. Check for any firewalls or network restrictions that might be blocking the connection.

### Authentication Issues

If you encounter authentication issues:

1. Verify that the username and password in the `.env` file are correct.
2. Check that the user has the necessary permissions in Odoo.
3. Try using the API key authentication method if available.

### Performance Issues

If you encounter performance issues:

1. Increase the number of workers in the gunicorn command.
2. Consider using a connection pool for Odoo connections.
3. Implement caching for frequently accessed data.
4. Monitor the server resources and scale as needed.