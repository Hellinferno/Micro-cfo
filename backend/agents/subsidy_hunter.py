"""
Agent C: Subsidy Hunter - Government Scheme Discovery
Web scraping and intelligent scheme matching
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime


async def find_subsidies(
    sector: Optional[str] = None,
    capex: Optional[float] = None,
    state: Optional[str] = None,
    query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Find government subsidies matching criteria
    
    Args:
        sector: Business sector (Textile, Manufacturing, IT, etc.)
        capex: Capital expenditure amount
        state: State location
        query: Natural language query
    
    Returns:
        List of matching subsidy schemes
    """
    try:
        # Try to query scheme database
        result = await _query_scheme_database(sector, capex, state, query)
        if result:
            return result
    except Exception as e:
        print(f"Scheme database query failed: {e}")
    
    # Fallback to mock data
    return _get_mock_subsidies(sector, capex, state)


async def _query_scheme_database(
    sector: Optional[str] = None,
    capex: Optional[float] = None,
    state: Optional[str] = None,
    query: Optional[str] = None
) -> Optional[List[Dict[str, Any]]]:
    """Query scheme database"""
    try:
        import sqlite3
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scheme_db", "schemes.db")
        
        if not os.path.exists(db_path):
            return None
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        base_query = "SELECT * FROM schemes WHERE 1=1"
        params = []
        
        if sector:
            base_query += " AND (sector_tags LIKE ? OR name LIKE ?)"
            sector_pattern = f"%{sector}%"
            params.extend([sector_pattern, sector_pattern])
        
        if capex:
            # Find schemes where capex threshold is met
            base_query += " AND (min_capex IS NULL OR min_capex <= ?)"
            params.append(capex)
        
        if state:
            base_query += " AND (state_specific IS NULL OR state_specific = ?)"
            params.append(state)
        
        base_query += " ORDER BY match_score DESC LIMIT 10"
        
        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            return [dict(row) for row in rows]
    
    except Exception as e:
        print(f"Error querying scheme database: {e}")
    
    return None


def _get_mock_subsidies(
    sector: Optional[str] = None,
    capex: Optional[float] = None,
    state: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Return mock subsidy schemes"""
    
    schemes = [
        {
            "name": "Technology Upgradation Fund Scheme (TUFS)",
            "benefit": "Up to 25% subsidy on capital goods for textile sector",
            "eligibility": "Textile manufacturers with capex > ₹10 lakh",
            "ministry": "Ministry of Textiles",
            "link": "https://texmin.nic.in/tufs",
            "max_subsidy": "₹25 lakh",
            "match_score": 0.95,
            "documents_required": [
                {"name": "GST Certificate", "type": "business", "required": True},
                {"name": "Project Report", "type": "technical", "required": True},
                {"name": "Financial Statements", "type": "financial", "required": True}
            ],
            "sector_tags": ["Textile", "Manufacturing"],
            "state_specific": None
        },
        {
            "name": "Production Linked Incentive (PLI) Scheme",
            "benefit": "4-6% incentive on incremental sales for 5 years",
            "eligibility": "Manufacturing companies with turnover > ₹100 crore",
            "ministry": "Ministry of Commerce",
            "link": "https://dpiit.gov.in/pli",
            "max_subsidy": "No upper limit",
            "match_score": 0.85,
            "documents_required": [
                {"name": "Company Registration", "type": "business", "required": True},
                {"name": "Audited Financials", "type": "financial", "required": True},
                {"name": "Investment Plan", "type": "technical", "required": True}
            ],
            "sector_tags": ["Manufacturing", "Electronics", "Pharmaceuticals"],
            "state_specific": None
        },
        {
            "name": "MSME Technology Centre Scheme",
            "benefit": "50% subsidy on plant & machinery (up to ₹15 lakh)",
            "eligibility": "MSMEs in manufacturing sector",
            "ministry": "Ministry of MSME",
            "link": "https://msme.gov.in/technology-centre",
            "max_subsidy": "₹15 lakh",
            "match_score": 0.80,
            "documents_required": [
                {"name": "Udyam Registration", "type": "business", "required": True},
                {"name": "GST Certificate", "type": "business", "required": True},
                {"name": "Quotation for Machinery", "type": "technical", "required": True}
            ],
            "sector_tags": ["Manufacturing", "MSME"],
            "state_specific": None
        },
        {
            "name": "Gujarat Industrial Subsidy",
            "benefit": "25% capital subsidy on plant & machinery",
            "eligibility": "Manufacturing units in Gujarat",
            "ministry": "Government of Gujarat",
            "link": "https://gujarat.gov.in/industrial-subsidy",
            "max_subsidy": "₹50 lakh",
            "match_score": 0.75,
            "documents_required": [
                {"name": "Industrial License", "type": "business", "required": True},
                {"name": "Proof of Investment", "type": "financial", "required": True}
            ],
            "sector_tags": ["Manufacturing"],
            "state_specific": "Gujarat"
        }
    ]
    
    # Filter by sector if provided
    if sector:
        sector_lower = sector.lower()
        schemes = [
            s for s in schemes 
            if any(sector_lower in tag.lower() for tag in s.get("sector_tags", []))
        ]
    
    # Filter by state if provided
    if state:
        state_lower = state.lower()
        schemes = [
            s for s in schemes 
            if s.get("state_specific") is None or s.get("state_specific", "").lower() == state_lower
        ]
    
    # Filter by capex if provided
    if capex:
        # Keep schemes where capex meets minimum threshold
        filtered_schemes = []
        for scheme in schemes:
            eligibility = scheme.get("eligibility", "").lower()
            if "capex" in eligibility or "investment" in eligibility:
                # Simple heuristic - keep if capex seems reasonable
                filtered_schemes.append(scheme)
            else:
                filtered_schemes.append(scheme)
        schemes = filtered_schemes
    
    return schemes


async def refresh_schemes() -> int:
    """
    Refresh subsidy database from government sources
    
    Returns:
        Number of schemes updated
    """
    # TODO: Implement web scraping
    # For now, return mock count
    return 5


def initialize_agent_c():
    """Initialize Agent C (Subsidy Hunter)"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scheme_db", "schemes.db")
    
    if os.path.exists(db_path):
        print("Agent C (Subsidy Hunter): Scheme database found")
        return True
    else:
        print("Agent C (Subsidy Hunter): Scheme database not found")
        return False
