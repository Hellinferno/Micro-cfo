#!/usr/bin/env python3
"""
MCP Bridge Component for MicroCFO Integration Server
Translates between HTTP requests and MCP tool calls
"""

import json
import logging
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import the existing MCP server and its models
from src.server import (
    mcp,
    Invoice,
    LegalRisk,
    NegotiationDraft,
    UserProfile
)

# Import connection pool for resource management
from src.connection_pool import connection_pool, resource_queue

logger = logging.getLogger(__name__)


class MCPBridgeError(Exception):
    """Custom exception for MCP Bridge errors"""
    pass


class MCPBridge:
    """
    Bridge component that translates between HTTP requests and MCP tool calls
    
    This class provides a clean interface for the FastAPI integration server
    to call MCP tools without directly importing the MCP server implementation.
    """
    
    def __init__(self):
        """Initialize the MCP Bridge"""
        self.executor = ThreadPoolExecutor(max_workers=4)
        logger.info("MCPBridge initialized")
    
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Call an MCP tool and return JSON-serializable result
        
        Args:
            tool_name: Name of the MCP tool to call
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Dict containing the tool result in JSON-serializable format
            
        Raises:
            MCPBridgeError: If tool call fails or tool doesn't exist
        """
        try:
            logger.info(f"Calling MCP tool: {tool_name} with args: {kwargs}")
            
            # Import the tool functions directly from server
            from src.server import (
                scan_invoice_document,
                check_compliance_law,
                find_applicable_subsidies,
                generate_negotiation_draft
            )
            
            # Map tool names to functions
            tool_map = {
                "scan_invoice_document": scan_invoice_document,
                "check_compliance_law": check_compliance_law,
                "find_applicable_subsidies": find_applicable_subsidies,
                "generate_negotiation_draft": generate_negotiation_draft
            }
            
            if tool_name not in tool_map:
                raise MCPBridgeError(f"Unknown tool: {tool_name}")
            
            # Get the tool function
            tool_fn = tool_map[tool_name]
            
            # Execute the tool function in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                lambda: tool_fn(**kwargs)
            )
            
            # Serialize the result to JSON-compatible format
            serialized_result = self.serialize_pydantic(result)
            
            logger.info(f"Tool {tool_name} completed successfully")
            return {
                "success": True,
                "result": serialized_result,
                "tool_name": tool_name
            }
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {str(e)}", exc_info=True)
            raise MCPBridgeError(f"Tool execution failed: {str(e)}") from e
    
    async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """
        Get an MCP resource and return JSON result
        
        Args:
            resource_uri: URI of the resource to retrieve
            
        Returns:
            Dict containing the resource data
            
        Raises:
            MCPBridgeError: If resource retrieval fails
        """
        try:
            logger.info(f"Getting MCP resource: {resource_uri}")
            
            # Import the resource functions directly from server
            from src.server import get_user_profile
            
            # Map resource URIs to functions
            resource_map = {
                "microcfo://data/profile": get_user_profile
            }
            
            if resource_uri not in resource_map:
                raise MCPBridgeError(f"Unknown resource: {resource_uri}")
            
            # Get the resource function
            resource_fn = resource_map[resource_uri]
            
            # Execute the resource function
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                resource_fn
            )
            
            # Parse JSON string result if needed
            if isinstance(result, str):
                try:
                    parsed_result = json.loads(result)
                except json.JSONDecodeError:
                    parsed_result = {"data": result}
            else:
                parsed_result = self.serialize_pydantic(result)
            
            logger.info(f"Resource {resource_uri} retrieved successfully")
            return {
                "success": True,
                "result": parsed_result,
                "resource_uri": resource_uri
            }
            
        except Exception as e:
            logger.error(f"Error getting resource {resource_uri}: {str(e)}", exc_info=True)
            raise MCPBridgeError(f"Resource retrieval failed: {str(e)}") from e
    
    def serialize_pydantic(self, model: Union[BaseModel, Any]) -> Dict[str, Any]:
        """
        Convert Pydantic models to JSON-safe dictionaries
        
        Args:
            model: Pydantic model instance or other object
            
        Returns:
            JSON-serializable dictionary
        """
        try:
            if isinstance(model, BaseModel):
                # Use Pydantic's built-in serialization
                return model.model_dump()
            elif hasattr(model, '__dict__'):
                # Handle objects with __dict__
                return {
                    key: self.serialize_pydantic(value) 
                    for key, value in model.__dict__.items()
                    if not key.startswith('_')
                }
            elif isinstance(model, (list, tuple)):
                # Handle lists and tuples
                return [self.serialize_pydantic(item) for item in model]
            elif isinstance(model, dict):
                # Handle dictionaries
                return {
                    key: self.serialize_pydantic(value)
                    for key, value in model.items()
                }
            else:
                # Handle primitive types and other objects
                return model
                
        except Exception as e:
            logger.warning(f"Serialization warning for {type(model)}: {str(e)}")
            # Fallback to string representation
            return {"serialized_string": str(model)}
    
    async def call_agent_a(self, image_url: str, use_mock: bool = False) -> Dict[str, Any]:
        """
        Convenience method for calling Agent A (Visual Auditor)
        
        Args:
            image_url: URL or base64 encoded image of the invoice
            use_mock: Whether to use mock data for testing
            
        Returns:
            Invoice data in JSON format
        """
        return await self.call_tool(
            "scan_invoice_document",
            image_url=image_url,
            use_mock=use_mock
        )
    
    async def call_agent_b(self, query: str, user_context: str = "") -> Dict[str, Any]:
        """
        Convenience method for calling Agent B (Legal Sentinel)
        
        Uses resource queue for vector database operations to prevent overload.
        
        Args:
            query: Legal compliance query
            user_context: Additional user context
            
        Returns:
            Legal risk assessment in JSON format
        """
        # Use resource queue for vector database operations
        async def _execute_legal_query():
            return await self.call_tool(
                "check_compliance_law",
                query=query,
                user_context=user_context
            )
        
        return await resource_queue.execute_resource_intensive(_execute_legal_query)
    
    async def call_agent_c(self, sector: str, capex_amount: float, fetch_live: bool = True) -> Dict[str, Any]:
        """
        Convenience method for calling Agent C (Subsidy Hunter)
        
        Uses resource queue for vector database operations to prevent overload.
        Includes web scraping for real-time subsidy information when fetch_live=True.
        
        Args:
            sector: Business sector
            capex_amount: Capital expenditure amount
            fetch_live: Whether to attempt live web scraping (default True)
            
        Returns:
            Subsidy information in JSON format
        """
        # Use resource queue for vector database operations
        async def _execute_subsidy_search():
            return await self.call_tool(
                "find_applicable_subsidies",
                sector=sector,
                capex_amount=capex_amount
            )
        
        return await resource_queue.execute_resource_intensive(_execute_subsidy_search)
    
    async def call_agent_d(
        self,
        counterparty_name: str,
        amount: float,
        transaction_type: str,
        due_date: str,
        current_cash_position: float,
        upcoming_outflows: float = 0,
        invoice_id: Optional[str] = None,
        vendor_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convenience method for calling Agent D (Negotiator)
        
        Args:
            counterparty_name: Name of vendor/customer
            amount: Transaction amount
            transaction_type: "payable" or "receivable"
            due_date: Due date in YYYY-MM-DD format
            current_cash_position: Current cash balance
            upcoming_outflows: Predicted outflows
            invoice_id: Optional invoice ID
            vendor_context: Optional vendor profile context for personalization
            
        Returns:
            Negotiation draft in JSON format
        """
        return await self.call_tool(
            "generate_negotiation_draft",
            counterparty_name=counterparty_name,
            amount=amount,
            transaction_type=transaction_type,
            due_date=due_date,
            current_cash_position=current_cash_position,
            upcoming_outflows=upcoming_outflows,
            invoice_id=invoice_id
        )
    
    async def get_user_profile(self) -> Dict[str, Any]:
        """
        Convenience method for getting user profile
        
        Returns:
            User profile data in JSON format
        """
        return await self.get_resource("microcfo://data/profile")
    
    def __del__(self):
        """Cleanup thread pool on destruction"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)