#!/usr/bin/env python3
"""
Script to load company policies into ChromaDB for the RAG system.
This will allow the agent to actually answer questions about company policies.
"""

import os
import sys
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.rag import PolicyRAG

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_policies():
    """Load company policies from markdown file into ChromaDB."""
    logger.info("🚀 Starting policy loading process...")
    
    # Path to the policies file
    policies_file = Path(__file__).parent.parent / "policies" / "company_policies.md"
    
    if not policies_file.exists():
        logger.error(f"❌ Policies file not found: {policies_file}")
        return False
    
    logger.info(f"📄 Found policies file: {policies_file}")
    
    try:
        # Read the policies file
        with open(policies_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"📖 Read {len(content)} characters from policies file")
        
        # Parse the markdown into sections
        sections = parse_markdown_sections(content)
        logger.info(f"🔍 Parsed {len(sections)} policy sections")
        
        # Initialize RAG system
        logger.info("🧠 Initializing RAG system...")
        rag = PolicyRAG()
        
        # Clear existing collection
        logger.info("🧹 Clearing existing collection...")
        rag.chroma.delete_collection("company_policies")
        rag.collection = rag.chroma.create_collection("company_policies")
        
        # Add each section to the database
        logger.info("📝 Adding policy sections to ChromaDB...")
        for i, (title, content) in enumerate(sections):
            logger.info(f"  Adding section {i+1}: {title}")
            
            # Create a document with title and content
            document = f"Title: {title}\n\n{content}"
            
            # Add to collection
            rag.collection.add(
                documents=[document],
                metadatas=[{"title": title, "section": i+1}],
                ids=[f"policy_{i+1}"]
            )
        
        # Verify the documents were added
        count = rag.collection.count()
        logger.info(f"✅ Successfully loaded {count} policy documents into ChromaDB")
        
        # Test a simple query
        logger.info("🧪 Testing RAG system with a sample query...")
        test_query = "What is the return policy?"
        response = rag.respond(test_query)
        logger.info(f"Test query: '{test_query}'")
        logger.info(f"Response: '{response}'")
        
        if "return" in response.lower() and "30 days" in response.lower():
            logger.info("✅ RAG system is working correctly!")
        else:
            logger.warning("⚠️ RAG response doesn't seem to contain expected policy information")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading policies: {e}", exc_info=True)
        return False

def parse_markdown_sections(content):
    """Parse markdown content into sections."""
    sections = []
    lines = content.split('\n')
    current_title = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        
        # Check for headers (## or #)
        if line.startswith('## '):
            # Save previous section if exists
            if current_title and current_content:
                sections.append((current_title, '\n'.join(current_content).strip()))
            
            # Start new section
            current_title = line[3:]  # Remove '## '
            current_content = []
            
        elif line.startswith('# '):
            # Main title, skip
            continue
            
        elif line and current_title:
            # Add content to current section
            current_content.append(line)
    
    # Add the last section
    if current_title and current_content:
        sections.append((current_title, '\n'.join(current_content).strip()))
    
    return sections

if __name__ == "__main__":
    success = load_policies()
    if success:
        print("\n🎉 Policy loading completed successfully!")
        print("The RAG system should now be able to answer questions about company policies.")
    else:
        print("\n❌ Policy loading failed. Check the logs above for details.")
        sys.exit(1)
