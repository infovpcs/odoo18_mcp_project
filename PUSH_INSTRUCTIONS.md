# Push Instructions for Odoo 18 MCP Project

Follow these steps to push your Odoo 18 MCP project to GitHub under the infovpcs account.

## 1. Create a New Private Repository

1. Go to https://github.com/new
2. Enter the following details:
   - Repository name: `odoo18_mcp_project`
   - Description: `Odoo 18 MCP Integration - A robust integration server that connects MCP with Odoo 18.0 ERP system`
   - Visibility: Private
   - Do not initialize with README, .gitignore, or license

## 2. Push Your Local Repository

Run the following commands in your terminal:

```bash
# Add the GitHub repository as a remote
git remote add origin https://github.com/infovpcs/odoo18_mcp_project.git

# Push the master branch
git checkout master
git push -u origin master

# Push the 18.0 branch
git checkout 18.0
git push -u origin 18.0
```

## 3. Set the Default Branch

1. Go to https://github.com/infovpcs/odoo18_mcp_project/settings/branches
2. Under "Default branch", select "18.0" from the dropdown
3. Click "Update"
4. Confirm the change

## 4. Protect the Branches (Optional)

1. Go to https://github.com/infovpcs/odoo18_mcp_project/settings/branches
2. Under "Branch protection rules", click "Add rule"
3. Enter "18.0" as the branch name pattern
4. Select the following options:
   - Require pull request reviews before merging
   - Require status checks to pass before merging
   - Require branches to be up to date before merging
   - Include administrators
5. Click "Create"
6. Repeat for the "master" branch if desired

## 5. Verify the Repository

1. Go to https://github.com/infovpcs/odoo18_mcp_project
2. Ensure that all files have been pushed correctly
3. Check that the 18.0 branch is set as the default branch

## 6. Clone the Repository for Development

To clone the repository for development:

```bash
git clone https://github.com/infovpcs/odoo18_mcp_project.git
cd odoo18_mcp_project
git checkout 18.0
```

## 7. Set Up Development Environment

Follow the instructions in the README.md file to set up your development environment:

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your Odoo connection details

# Run the server
python main.py
```

## 8. Run Tests

```bash
# Run the basic client test
python client_test.py

# Run the advanced client test
python advanced_client_test.py

# Run the dynamic model test
python dynamic_model_test.py
```

For more detailed instructions on setting up the project in different environments, including Cloud Desktop and production deployment, please refer to the `GITHUB_SETUP.md` file.