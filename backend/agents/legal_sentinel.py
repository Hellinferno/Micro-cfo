"""
Agent B: Legal Sentinel - Structure-Aware RAG for Legal Compliance
Uses ChromaDB vector database with CA-logic based chunking
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """Compliance risk levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


async def check_compliance_law(
    query: str,
    user_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Check legal compliance using structure-aware RAG
    
    Args:
        query: Natural language compliance question
        user_context: User profile (turnover, sector, state, etc.)
    
    Returns:
        Compliance assessment with risk level, sections, and recommendations
    """
    try:
        # Try to use vector database
        result = await _query_legal_database(query, user_context)
        if result:
            return result
    except Exception as e:
        print(f"Vector database query failed: {e}")
    
    # Fallback to mock response
    return _get_mock_compliance_response(query, user_context)


async def _query_legal_database(
    query: str,
    user_context: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Query legal vector database"""
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Initialize ChromaDB
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "legal_db")
        client = chromadb.PersistentClient(path=db_path)
        
        # Get or create collection
        collection = client.get_or_create_collection(
            name="legal_documents",
            metadata={"description": "Indian legal documents"}
        )
        
        # Generate query embedding (using simple approach)
        # In production, use sentence-transformers
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        query_embedding = model.encode(query).tolist()
        
        # Query with filters
        where_filter = {}
        if user_context:
            if user_context.get("turnover_tier"):
                where_filter["turnover_threshold"] = user_context["turnover_tier"]
            if user_context.get("sector"):
                where_filter["sector_tag"] = user_context["sector"]
        
        # Perform similarity search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"]
        )
        
        # Process results
        if results and results["documents"] and results["documents"][0]:
            return _process_legal_results(query, results, user_context)
    
    except ImportError as e:
        print(f"Required packages not installed: {e}")
        return None
    except Exception as e:
        print(f"Error querying legal database: {e}")
        return None
    
    return None


def _process_legal_results(
    query: str,
    results: Dict,
    user_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process legal search results into compliance response"""
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    
    # Build context from top results
    context_chunks = []
    relevant_sections = []
    
    for doc, meta, distance in zip(documents, metadatas, distances):
        relevance_score = 1.0 - distance
        if relevance_score > 0.3:  # Threshold for relevance
            context_chunks.append(doc)
            if meta and "section_number" in meta:
                relevant_sections.append({
                    "section_name": meta.get("section_name", ""),
                    "section_number": meta.get("section_number", ""),
                    "act_name": meta.get("act_name", ""),
                    "description": doc[:200] + "..." if len(doc) > 200 else doc,
                    "relevance_score": round(relevance_score, 2)
                })
    
    # Generate response using LLM
    context = "\n\n".join(context_chunks)
    response = _generate_compliance_response(query, context, user_context)
    
    return response


def _generate_compliance_response(
    query: str,
    context: str,
    user_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate compliance response using LLM"""
    try:
        import google.generativeai as genai
        
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
You are a CA (Chartered Accountant) providing conservative compliance advice.

Context from legal database:
{context}

User Query: {query}
User Context: {json.dumps(user_context) if user_context else "Not provided"}

Provide response in JSON format:
{{
    "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "relevant_sections": [
        {{
            "section_name": "Section name",
            "section_number": "Section number",
            "act_name": "Act name",
            "description": "Brief description",
            "relevance_score": 0.0-1.0
        }}
    ],
    "explanation": "Clear 2-3 sentence explanation",
    "compliant_action": "Specific action to take",
    "warnings": ["list of warnings if any"]
}}

Be conservative - when in doubt, recommend verification with a practicing CA.
Return ONLY valid JSON.
"""
            
            response = model.generate_content(prompt)
            response_text = response.text
            
            # Parse JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                response_text = json_match.group()
            
            data = json.loads(response_text)
            return data
    
    except Exception as e:
        print(f"Error generating compliance response: {e}")
    
    return _get_mock_compliance_response(query, user_context)


def _get_mock_compliance_response(
    query: str,
    user_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Return mock compliance response for testing"""
    
    # Determine risk level based on query keywords
    query_lower = query.lower()
    risk_keywords = ["penalty", "fraud", "evasion", "illegal", "prohibited"]
    medium_keywords = ["itc", "credit", "exempt", "taxable", "gst"]
    
    if any(keyword in query_lower for keyword in risk_keywords):
        risk_level = "HIGH"
    elif any(keyword in query_lower for keyword in medium_keywords):
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    return {
        "risk_level": risk_level,
        "relevant_sections": [
            {
                "section_name": "Input Tax Credit",
                "section_number": "Section 16",
                "act_name": "CGST Act, 2017",
                "description": "Eligibility and conditions for taking input tax credit",
                "relevance_score": 0.85
            },
            {
                "section_name": "Blocked Credits",
                "section_number": "Section 17(5)",
                "act_name": "CGST Act, 2017",
                "description": "Apportionment of credit and blocked credits",
                "relevance_score": 0.75
            }
        ],
        "explanation": f"Based on your query about '{query}', the relevant provisions are under GST law. "
                      f"Input Tax Credit (ITC) eligibility depends on the nature of goods/services and their use in business. "
                      f"Some categories like food, beverages, and personal use items have blocked credits.",
        "compliant_action": "Review the expense category against Section 17(5) blocked credits list. "
                           "Maintain proper documentation including tax invoices and payment proofs.",
        "warnings": [
            "This is AI-generated guidance. Consult a practicing CA for critical decisions.",
            "GST laws are subject to frequent amendments. Verify with latest notifications."
        ]
    }


async def search_legal_sections(
    query: str,
    act: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Search legal sections by keyword"""
    # TODO: Implement actual search
    return [
        {
            "section_number": "Section 16",
            "section_name": "Eligibility and conditions for taking input tax credit",
            "act_name": "CGST Act, 2017",
            "summary": "Defines conditions for ITC eligibility"
        },
        {
            "section_number": "Section 17(5)",
            "section_name": "Apportionment of credit and blocked credits",
            "act_name": "CGST Act, 2017",
            "summary": "Lists blocked credits including food, beverages, personal use"
        }
    ]


def initialize_agent_b():
    """Initialize Agent B (Legal Sentinel)"""
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "legal_db")
        
        if os.path.exists(db_path):
            print("Agent B (Legal Sentinel): Vector database found")
            return True
        else:
            print("Agent B (Legal Sentinel): Vector database not found. Run legal ingestion first.")
            return False
    
    except ImportError:
        print("Agent B (Legal Sentinel): Required packages not installed")
        return False
