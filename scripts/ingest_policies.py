#!/usr/bin/env python3
"""
Script to ingest policy documents into Chroma vector database.
Run this after adding new policy files to the policies/ directory.
"""

import os
import glob
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end - overlap
    return [c for c in chunks if c]  # Remove empty chunks

def ingest_policies(policies_dir: str = "./policies", collection_name: str = "company_policies"):
    """Load policy documents and embed them into Chroma."""
    
    # Initialize Chroma client (new configuration)
    client = chromadb.PersistentClient(path="./chroma")
    
    # Get or create collection
    collection = client.get_or_create_collection(collection_name)
    
    # Initialize embedding model
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Find all policy files
    policy_files = glob.glob(os.path.join(policies_dir, "*.md")) + \
                  glob.glob(os.path.join(policies_dir, "*.txt"))
    
    if not policy_files:
        print(f"No policy files found in {policies_dir}")
        return
    
    all_chunks = []
    all_ids = []
    all_metadata = []
    
    for file_path in policy_files:
        print(f"Processing {file_path}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into chunks
        chunks = chunk_text(content)
        filename = Path(file_path).stem
        
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{filename}_chunk_{i}")
            all_metadata.append({
                "source": filename,
                "chunk_index": i,
                "file_path": file_path
            })
    
    if all_chunks:
        # Generate embeddings
        print(f"Generating embeddings for {len(all_chunks)} chunks...")
        embeddings = embed_model.encode(all_chunks).tolist()
        
        # Add to collection
        collection.add(
            documents=all_chunks,
            embeddings=embeddings,
            ids=all_ids,
            metadatas=all_metadata
        )
        
        print(f"Successfully ingested {len(all_chunks)} chunks from {len(policy_files)} files")
    else:
        print("No content found to ingest")

if __name__ == "__main__":
    ingest_policies()
