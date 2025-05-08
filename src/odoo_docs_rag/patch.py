
# Patch for OdooDocsRetriever to use existing embeddings
import logging
logger = logging.getLogger("odoo_docs_rag")

# Save the original initialize_index method
from src.odoo_docs_rag.docs_retriever import OdooDocsRetriever
original_initialize_index = OdooDocsRetriever.initialize_index

# Override the initialize_index method
def patched_initialize_index(self):
    # Skip index initialization if embeddings already exist
    if hasattr(self, 'skip_embedding_if_exists') and self.skip_embedding_if_exists:
        logger.info("Using existing embeddings, skipping index initialization")
        self.initialized = True
        return True
    
    # Check if the index files exist
    if self.index_path and self.index_path.exists() and self.documents_path and self.documents_path.exists():
        logger.info("Using existing index files, skipping index initialization")
        self.initialized = True
        return True
    
    # Check if the database has embeddings
    if self.db and hasattr(self.db, 'has_embeddings') and self.db.has_embeddings(self.model_name):
        logger.info("Using existing embeddings from database, skipping index initialization")
        self.initialized = True
        return True
    
    # Fall back to the original method
    return original_initialize_index(self)

# Apply the patch
OdooDocsRetriever.initialize_index = patched_initialize_index
logger.info("OdooDocsRetriever patched to use existing embeddings")
