"""
Bucky Shopping Agent - MCP-ONLY IMPLEMENTATION
ALL tool access goes through MCP server - NO DIRECT TOOL ACCESS
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from shared.mcp_framework.mcp_agent_base import MCPOnlyAgent, AgentError


class BuckyShoppingAgent(MCPOnlyAgent):
    """
    Bucky Shopping & Inventory Agent
    ALL ACTIONS PERFORMED THROUGH MCP - NO DIRECT TOOL ACCESS
    """
    
    def __init__(self):
        super().__init__(
            agent_name="bucky",
            mcp_server_url="http://localhost:8004"
        )
        
        # Agent-specific state
        self.shopping_lists: Dict[str, Dict[str, Any]] = {}
        self.price_alerts: List[Dict[str, Any]] = []
        self.inventory_cache: Optional[Dict[str, Any]] = None
        self.last_inventory_check: Optional[datetime] = None
    
    async def agent_initialize(self):
        """Initialize Bucky-specific functionality"""
        # Validate that all required shopping tools are available
        required_tools = ["pantry_tracker", "deal_finder", "price_comparator", "shopping_optimizer"]
        
        for tool in required_tools:
            if not self.mcp_client.is_tool_available(tool):
                raise AgentError(f"Required tool '{tool}' not available in MCP server")
        
        self.logger.info("Bucky agent initialized with all required shopping tools")
    
    async def agent_shutdown(self):
        """Cleanup Bucky-specific resources"""
        self.shopping_lists.clear()
        self.price_alerts.clear()
        self.inventory_cache = None
        self.logger.info("Bucky agent shutdown completed")
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process shopping-related requests through MCP tools"""
        action = request.get("action")
        
        if not action:
            return {"success": False, "error": "No action specified"}
        
        try:
            if action == "manage_inventory":
                return await self._handle_inventory_management(request)
            elif action == "find_deals":
                return await self._handle_deal_finding(request)
            elif action == "compare_prices":
                return await self._handle_price_comparison(request)
            elif action == "optimize_shopping":
                return await self._handle_shopping_optimization(request)
            elif action == "create_shopping_list":
                return await self._handle_shopping_list_creation(request)
            elif action == "get_inventory_status":
                return await self._handle_inventory_status(request)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            self.logger.error(f"Error processing request: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # ==================== SHOPPING ACTION HANDLERS ====================
    
    async def _handle_inventory_management(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle inventory management through MCP pantry_tracker tool"""
        inventory_action = request.get("inventory_action", "get_inventory")
        
        # Prepare arguments for MCP tool
        tool_args = {
            "action": inventory_action
        }
        
        # Add item details if provided
        if "item" in request:
            item = request["item"]
            tool_args.update({
                "item_name": item.get("name"),
                "quantity": item.get("quantity"),
                "unit": item.get("unit"),
                "expiration_date": item.get("expiration_date"),
                "location": item.get("location"),
                "category": item.get("category"),
                "brand": item.get("brand"),
                "cost": item.get("cost")
            })
        
        # Add other parameters
        if "days_ahead" in request:
            tool_args["days_ahead"] = request["days_ahead"]
        if "reorder_point" in request:
            tool_args["reorder_point"] = request["reorder_point"]
        
        # Call MCP tool
        result = await self.use_tool("pantry_tracker", tool_args)
        
        # Update local cache if getting inventory
        if inventory_action == "get_inventory":
            self.inventory_cache = result
            self.last_inventory_check = datetime.now()
        
        return {
            "success": True,
            "action": "manage_inventory",
            "inventory_action": inventory_action,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_deal_finding(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deal finding through MCP deal_finder tool"""
        deal_action = request.get("deal_action", "find_deals")
        
        # Prepare arguments for MCP tool
        tool_args = {
            "action": deal_action,
            "items": request.get("items", []),
            "stores": request.get("stores", []),
            "budget_limit": request.get("budget_limit"),
            "deal_types": request.get("deal_types", []),
            "savings_threshold": request.get("savings_threshold", 10),
            "time_sensitivity": request.get("time_sensitivity", "flexible")
        }
        
        # Call MCP tool
        result = await self.use_tool("deal_finder", tool_args)
        
        return {
            "success": True,
            "action": "find_deals",
            "deal_action": deal_action,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_price_comparison(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle price comparison through MCP price_comparator tool"""
        price_action = request.get("price_action", "compare_prices")
        
        # Prepare arguments for MCP tool
        tool_args = {
            "action": price_action,
            "items": request.get("items", []),
            "stores": request.get("stores", []),
            "brand_preference": request.get("brand_preference"),
            "price_threshold": request.get("price_threshold"),
            "time_period": request.get("time_period", "1m"),
            "include_shipping": request.get("include_shipping", True),
            "quality_preference": request.get("quality_preference", "standard")
        }
        
        # Call MCP tool
        result = await self.use_tool("price_comparator", tool_args)
        
        # Handle price alerts
        if price_action == "set_price_alert" and result.get("success"):
            self.price_alerts.append({
                "item": request.get("items", [{}])[0] if request.get("items") else {},
                "threshold": request.get("price_threshold"),
                "created_at": datetime.now().isoformat()
            })
        
        return {
            "success": True,
            "action": "compare_prices",
            "price_action": price_action,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_shopping_optimization(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shopping optimization through MCP shopping_optimizer tool"""
        optimization_action = request.get("optimization_action", "optimize_route")
        
        # Prepare arguments for MCP tool
        tool_args = {
            "action": optimization_action,
            "shopping_list": request.get("shopping_list", []),
            "budget": request.get("budget"),
            "preferred_stores": request.get("preferred_stores", []),
            "time_constraints": request.get("time_constraints"),
            "transportation": request.get("transportation", "car"),
            "location": request.get("location"),
            "optimization_criteria": request.get("optimization_criteria", ["price", "distance"])
        }
        
        # Call MCP tool
        result = await self.use_tool("shopping_optimizer", tool_args)
        
        return {
            "success": True,
            "action": "optimize_shopping",
            "optimization_action": optimization_action,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_shopping_list_creation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create and manage shopping lists"""
        list_name = request.get("list_name", f"shopping_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        items = request.get("items", [])
        
        # Create the shopping list
        shopping_list = {
            "name": list_name,
            "items": items,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "total_estimated_cost": 0
        }
        
        # Use shopping optimizer to enhance the list
        optimization_result = await self.use_tool("shopping_optimizer", {
            "action": "create_list",
            "shopping_list": items,
            "budget": request.get("budget"),
            "preferred_stores": request.get("preferred_stores", [])
        })
        
        if optimization_result.get("success"):
            shopping_list["optimization"] = optimization_result.get("result")
        
        # Store the shopping list
        self.shopping_lists[list_name] = shopping_list
        
        return {
            "success": True,
            "action": "create_shopping_list",
            "list_name": list_name,
            "shopping_list": shopping_list,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_inventory_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive inventory status"""
        # Get current inventory through MCP
        inventory_result = await self.use_tool("pantry_tracker", {"action": "get_inventory"})
        
        # Check expiring items
        expiry_result = await self.use_tool("pantry_tracker", {
            "action": "check_expiry",
            "days_ahead": request.get("days_ahead", 7)
        })
        
        # Get low stock alerts
        low_stock_result = await self.use_tool("pantry_tracker", {"action": "predict_needs"})
        
        return {
            "success": True,
            "action": "get_inventory_status",
            "inventory": inventory_result,
            "expiring_items": expiry_result,
            "low_stock_items": low_stock_result,
            "timestamp": datetime.now().isoformat()
        }
    
    # ==================== CONVENIENCE METHODS ====================
    
    async def add_inventory_item(self, name: str, quantity: float, unit: str, **kwargs) -> Dict[str, Any]:
        """Convenience method to add an inventory item"""
        return await self.process_request({
            "action": "manage_inventory",
            "inventory_action": "add_item",
            "item": {
                "name": name,
                "quantity": quantity,
                "unit": unit,
                **kwargs
            }
        })
    
    async def find_deals_for_items(self, items: List[str], stores: Optional[List[str]] = None) -> Dict[str, Any]:
        """Convenience method to find deals for specific items"""
        return await self.process_request({
            "action": "find_deals",
            "deal_action": "find_deals",
            "items": items,
            "stores": stores or []
        })
    
    async def compare_item_prices(self, items: List[str], stores: Optional[List[str]] = None) -> Dict[str, Any]:
        """Convenience method to compare prices for items"""
        return await self.process_request({
            "action": "compare_prices",
            "price_action": "compare_prices",
            "items": items,
            "stores": stores or []
        })
    
    async def optimize_shopping_trip(self, shopping_list: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Convenience method to optimize a shopping trip"""
        return await self.process_request({
            "action": "optimize_shopping",
            "optimization_action": "optimize_route",
            "shopping_list": shopping_list,
            **kwargs
        })
    
    async def get_shopping_recommendations(self) -> Dict[str, Any]:
        """Get comprehensive shopping recommendations"""
        # Get inventory status
        inventory_status = await self._handle_inventory_status({})
        
        if not inventory_status.get("success"):
            return inventory_status
        
        # Extract items that need replenishing
        low_stock_items = []
        expiring_items = []
        
        if inventory_status.get("low_stock_items", {}).get("success"):
            low_stock_items = inventory_status["low_stock_items"].get("result", [])
        
        if inventory_status.get("expiring_items", {}).get("success"):
            expiring_items = inventory_status["expiring_items"].get("result", [])
        
        # Create shopping list from low stock items
        shopping_items = []
        for item in low_stock_items:
            shopping_items.append({
                "item": item.get("name", ""),
                "quantity": item.get("reorder_quantity", 1),
                "priority": "high" if item in expiring_items else "medium"
            })
        
        if not shopping_items:
            return {
                "success": True,
                "message": "No items need replenishing",
                "recommendations": {
                    "shopping_needed": False,
                    "inventory_status": inventory_status
                }
            }
        
        # Optimize the shopping trip
        optimization_result = await self.optimize_shopping_trip(shopping_items)
        
        # Find deals for the items
        item_names = [item["item"] for item in shopping_items]
        deals_result = await self.find_deals_for_items(item_names)
        
        return {
            "success": True,
            "recommendations": {
                "shopping_needed": True,
                "items_to_buy": shopping_items,
                "optimization": optimization_result.get("result"),
                "available_deals": deals_result.get("result"),
                "inventory_status": inventory_status
            },
            "timestamp": datetime.now().isoformat()
        }


async def main():
    """Demo of Bucky agent using only MCP"""
    logging.basicConfig(level=logging.INFO)
    
    async with BuckyShoppingAgent() as bucky:
        # Test inventory management
        result = await bucky.add_inventory_item(
            name="Milk",
            quantity=2,
            unit="liters",
            expiration_date="2025-08-20",
            location="fridge"
        )
        print("Inventory add result:", json.dumps(result, indent=2))
        
        # Test deal finding
        deals = await bucky.find_deals_for_items(["Milk", "Bread"])
        print("Deals result:", json.dumps(deals, indent=2))
        
        # Test shopping recommendations
        recommendations = await bucky.get_shopping_recommendations()
        print("Shopping recommendations:", json.dumps(recommendations, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
