import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np
import logging
from .llm import LLMWrapper

logger = logging.getLogger(__name__)

class PolicyRAG:
    """Retrieve policy docs and decide whether to respond."""

    def __init__(self, collection_name: str = "company_policies_v3", threshold: float = 1.2):  # Updated to v3 with corruption prevention
        logger.info("🧠 Initializing RAG system with robust database...")
        try:
            # Use absolute path to backend/chroma (works regardless of working directory)
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))  # Get directory of rag.py
            project_root = os.path.dirname(os.path.dirname(script_dir))  # Go up to project root
            chroma_path = os.path.join(project_root, "backend", "chroma")
            
            self.chroma = chromadb.PersistentClient(path=chroma_path)
            logger.info(f"ChromaDB: Using persistent client with absolute path: {chroma_path}")
        except Exception as e:
            logger.error(f"ChromaDB: Failed to connect to backend/chroma: {e}")
            raise RuntimeError("ChromaDB connection failed. Please run fix_chromadb_permanent.py first.")
        
        self.collection = self.chroma.get_or_create_collection(collection_name)
        logger.info(f"ChromaDB: Collection '{collection_name}' ready")
        
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Embeddings: SentenceTransformer loaded")
        
        self.threshold = threshold
        logger.info(f"RAG: Similarity threshold = {threshold}")
        
        self.llm = LLMWrapper()
        
        # Perform database health check on startup
        self._verify_database_health()
        
        logger.info("✅ RAG system initialized successfully with health verification")

    def respond(self, query: str) -> str:
        logger.info(f"🔍 RAG processing query: '{query}'")
        
        if not query.strip():
            logger.warning("RAG: Empty query received")
            return "Hi! I'm here to help with questions about our company policies, returns, shipping, warranties, or payments. What would you like to know?"
        
        # Check if the query is business-related using LLM classification
        if not self._is_business_related_query(query):
            logger.info("RAG: Non-business query detected - redirecting to business topics")
            return "I'm a business assistant focused on helping with company policies, returns, shipping, warranties, and payment questions. Is there something about our business services I can help you with?"
        
        try:
            # Now search for business content
            logger.debug("RAG: Encoding query with SentenceTransformer...")
            vector = self.embed_model.encode(query).tolist()
            logger.debug(f"RAG: Query encoded to {len(vector)}-dimensional vector")
            
            # Search in vector database
            logger.debug("RAG: Searching ChromaDB for similar policies...")
            results = self.collection.query(query_embeddings=[vector], n_results=3)
            
            # Check if we found relevant policy content
            if not results["documents"] or not results["documents"][0] or len(results["distances"][0]) == 0:
                logger.warning("RAG: No policy documents found in database - ChromaDB may be empty!")
                logger.warning("RAG: Run 'python fix_chromadb_permanent.py' to populate the database")
                return "Hello! I'd be happy to help you with questions about our company policies, returns, shipping, warranties, and payments. What would you like to know?"
            
            # Check similarity threshold
            best_distance = results["distances"][0][0]
            logger.info(f"RAG: Best similarity distance = {best_distance:.3f} (threshold = {self.threshold})")
            
            if best_distance > self.threshold:
                logger.info("RAG: Query not similar enough to policies - polite business redirect")
                return "Thank you for your question! While I don't have specific information about that, I'd be happy to help you with our company policies, returns, shipping, warranties, and payments. Is there anything about our services I can assist you with?"

            # Build context from retrieved docs
            context = "\n\n".join(results["documents"][0][:2])  # Use top 2 results
            logger.info(f"RAG: Found {len(results['documents'][0])} relevant policy documents")
            logger.debug(f"RAG: Context preview: {context[:100]}...")
            
            prompt = f"""You are a friendly business policy assistant. Answer the customer's question using the company policies provided below.

Company Policies:
{context}

Customer Question: {query}

INSTRUCTIONS:
- If the customer greets you (hello, hi, good morning, etc.), greet them back warmly
- If they say thank you, acknowledge it graciously
- Answer the specific question directly and professionally
- Be polite, conversational, and helpful
- IMPORTANT: Keep your response SHORT - maximum 2-3 sentences only
- Get straight to the point while being friendly
- Always maintain a friendly, customer service tone"""

            logger.info("RAG: Sending prompt to LLM...")
            response = self.llm.generate(prompt, max_tokens=60)  # Very limited for short responses (1-2 sentences)
            logger.info(f"RAG: LLM response received: '{response[:50]}...'")
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"RAG: Error processing query: {e}", exc_info=True)
            return "I apologize, I'm having a technical issue right now. Please feel free to ask me about our company policies, returns, or shipping, and I'll do my best to help!"


    def _is_business_related_query(self, query: str) -> bool:
        """Use LLM to intelligently classify if a query is business-related."""
        try:
            # Quick classification prompt
            classification_prompt = f"""Classify this user query as either "BUSINESS" or "GENERAL".

A BUSINESS query is about:
- Company policies, returns, refunds, exchanges
- Shipping, delivery, warranties  
- Payments, pricing, orders, purchases
- Products, services, customer support
- Account, billing, cancellations
- Greetings with business context (hello + business question)
- Polite interactions in customer service context

A GENERAL query is about:
- Weather, sports, entertainment, news
- Personal topics, health, recipes
- Time, dates, jokes, general conversation
- Technology tutorials, math, science
- Travel, restaurants (not business-related)
- Pure casual conversation without business intent

User Query: "{query}"

Classification (respond with only "BUSINESS" or "GENERAL"):"""

            # Get classification from LLM (quick, low-token response)
            classification = self.llm.generate(classification_prompt, max_tokens=10).strip().upper()
            logger.debug(f"RAG: Query classification: {classification}")
            
            # Return True if it's business-related
            return "BUSINESS" in classification
            
        except Exception as e:
            logger.warning(f"RAG: Classification error: {e}")
            # Default to allowing the query through if classification fails
            return True

    def _verify_database_health(self):
        """Verify database health and integrity on startup."""
        try:
            # Check if collection exists and has documents
            count = self.collection.count()
            logger.info(f"RAG: Database health check - {count} documents in collection")
            
            if count == 0:
                logger.warning("RAG: Database is empty! Run 'python fix_chromadb_permanent.py' to populate")
                return False
            
            # Test a simple query to verify functionality
            test_query = "shipping"
            test_vector = self.embed_model.encode(test_query).tolist()
            results = self.collection.query(query_embeddings=[test_vector], n_results=1)
            
            if results["documents"] and results["documents"][0]:
                logger.info("RAG: Database health check passed - query functionality verified")
                return True
            else:
                logger.warning("RAG: Database health check failed - query returned no results")
                return False
                
        except Exception as e:
            logger.error(f"RAG: Database health check failed: {e}")
            return False
