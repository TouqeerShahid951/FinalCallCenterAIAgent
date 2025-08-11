import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np
import logging
from .llm import LLMWrapper

logger = logging.getLogger(__name__)

class PolicyRAG:
    """Retrieve policy docs and decide whether to respond."""

    def __init__(self, collection_name: str = "company_policies", threshold: float = 2.0):  # INCREASED from 1.2 to 2.0 for more lenient matching
        logger.info("🧠 Initializing RAG system...")
        try:
            # Use new Chroma client configuration
            self.chroma = chromadb.PersistentClient(path="./chroma")
            logger.info("ChromaDB: Using persistent client")
        except Exception as e:
            logger.warning(f"ChromaDB: Persistent client failed ({e}), using default client")
            # Fall back to ephemeral client if persistent fails
            self.chroma = chromadb.Client()
        
        self.collection = self.chroma.get_or_create_collection(collection_name)
        logger.info(f"ChromaDB: Collection '{collection_name}' ready")
        
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Embeddings: SentenceTransformer loaded")
        
        self.threshold = threshold
        logger.info(f"RAG: Similarity threshold = {threshold} (MORE LENIENT)")
        
        self.llm = LLMWrapper()
        logger.info("✅ RAG system initialized successfully")

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
                logger.info("RAG: No policy documents found in database")
                return "Hello! I'd be happy to help you with questions about our company policies, returns, shipping, warranties, and payments. What would you like to know?"
            
            # Check similarity threshold
            best_distance = results["distances"][0][0]
            logger.info(f"RAG: Best similarity distance = {best_distance:.3f} (threshold = {self.threshold})")
            
            if best_distance > self.threshold:
                logger.info("RAG: Query not similar enough to policies - redirecting to business focus")
                return "Hi there! I'm here to help with questions about our company policies, returns, shipping, warranties, and payments. Is there something specific you'd like to know about our services?"

            # Build context from retrieved docs
            context = "\n\n".join(results["documents"][0][:2])  # Use top 2 results
            logger.info(f"RAG: Found {len(results['documents'][0])} relevant policy documents")
            logger.debug(f"RAG: Context preview: {context[:100]}...")
            
            prompt = f"""You are a friendly business policy assistant. Answer the customer's question using the company policies provided below.

Company Policies:
{context}

Customer Question: {query}

INSTRUCTIONS:
- Answer the specific question directly and professionally
- Only use greetings if the customer greeted you first
- Be conversational but focus on providing the requested information
- Keep your response concise and helpful (2-3 sentences)
- Don't add unnecessary pleasantries to every response"""

            logger.info("RAG: Sending prompt to LLM...")
            response = self.llm.generate(prompt, max_tokens=200)  # Increased to allow more natural responses
            logger.info(f"RAG: LLM response received: '{response[:50]}...'")
            
            # Allow natural, friendly responses - no more filtering of greeting phrases
            # Just ensure response isn't excessively long
            if len(response) > 300:  # Reasonable limit for voice responses
                response = response[:300].rsplit('.', 1)[0] + '.'
                logger.info("RAG: Response truncated to reasonable length")
            
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

A GENERAL query is about:
- Weather, sports, entertainment, news
- Personal topics, health, recipes
- Time, dates, jokes, general conversation
- Technology tutorials, math, science
- Travel, restaurants (not business-related)

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
