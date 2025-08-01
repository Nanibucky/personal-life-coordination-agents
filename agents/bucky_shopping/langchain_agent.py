"""
LangChain Bucky Agent - Shopping & Inventory Management
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import logging

from langchain.tools import BaseTool
from langchain.schema import HumanMessage, AIMessage

from shared.langchain_framework.base_agent import LangChainBaseAgent, LangChainTool
from shared.langchain_framework.a2a_coordinator import a2a_coordinator, A2AMessage
from shared.utils.config import config_manager

# Global storage for tool data (in a real app, this would be a database)
_inventory_data = {}
_price_data = {}

class PantryTrackerTool(LangChainTool):
    """LangChain tool for pantry tracking"""
    
    def __init__(self):
        super().__init__(
            name="pantry_tracker",
            description="Track pantry inventory, check expiration dates, and manage household items"
        )
    
    async def _arun(self, action: str, **kwargs) -> str:
        """Async execution of pantry tracking actions"""
        try:
            if action == "add_item":
                return await self._add_item(**kwargs)
            elif action == "remove_item":
                return await self._remove_item(**kwargs)
            elif action == "get_inventory":
                return await self._get_inventory(**kwargs)
            elif action == "check_expiry":
                return await self._check_expiry(**kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error in pantry tracking: {str(e)}"
    
    def _run(self, action: str, **kwargs) -> str:
        """Sync execution - not implemented"""
        raise NotImplementedError("Use async execution")
    
    async def _add_item(self, item_name: str, quantity: float, unit: str, 
                       expiration_date: Optional[str] = None, **kwargs) -> str:
        """Add item to inventory"""
        if item_name not in _inventory_data:
            _inventory_data[item_name] = {
                "quantity": 0,
                "unit": unit,
                "expiration_date": expiration_date,
                "last_updated": datetime.now().isoformat()
            }
        
        _inventory_data[item_name]["quantity"] += quantity
        _inventory_data[item_name]["last_updated"] = datetime.now().isoformat()
        
        return f"Added {quantity} {unit} of {item_name} to inventory. Total: {_inventory_data[item_name]['quantity']} {unit}"
    
    async def _remove_item(self, item_name: str, quantity: float, **kwargs) -> str:
        """Remove item from inventory"""
        if item_name not in _inventory_data:
            return f"Item {item_name} not found in inventory"
        
        current_quantity = _inventory_data[item_name]["quantity"]
        if current_quantity < quantity:
            return f"Insufficient quantity. Available: {current_quantity}, requested: {quantity}"
        
        _inventory_data[item_name]["quantity"] -= quantity
        _inventory_data[item_name]["last_updated"] = datetime.now().isoformat()
        
        return f"Removed {quantity} of {item_name}. Remaining: {_inventory_data[item_name]['quantity']}"
    
    async def _get_inventory(self, **kwargs) -> str:
        """Get current inventory"""
        if not _inventory_data:
            return "Inventory is empty"
        
        inventory_list = []
        for item, data in _inventory_data.items():
            inventory_list.append(f"- {item}: {data['quantity']} {data['unit']}")
        
        return "Current Inventory:\n" + "\n".join(inventory_list)
    
    async def _check_expiry(self, **kwargs) -> str:
        """Check for expiring items"""
        expiring_items = []
        today = datetime.now()
        
        for item, data in _inventory_data.items():
            if data.get("expiration_date"):
                try:
                    expiry_date = datetime.fromisoformat(data["expiration_date"])
                    days_until_expiry = (expiry_date - today).days
                    if days_until_expiry <= 7:
                        expiring_items.append(f"- {item}: expires in {days_until_expiry} days")
                except:
                    pass
        
        if expiring_items:
            return "Expiring Items:\n" + "\n".join(expiring_items)
        else:
            return "No items expiring soon"

class PriceComparatorTool(LangChainTool):
    """LangChain tool for price comparison"""
    
    def __init__(self):
        super().__init__(
            name="price_comparator",
            description="Compare prices across different stores and find the best deals"
        )
    
    async def _arun(self, action: str, **kwargs) -> str:
        """Async execution of price comparison actions"""
        try:
            if action == "compare_prices":
                return await self._compare_prices(**kwargs)
            elif action == "find_deals":
                return await self._find_deals(**kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error in price comparison: {str(e)}"
    
    def _run(self, action: str, **kwargs) -> str:
        """Sync execution - not implemented"""
        raise NotImplementedError("Use async execution")
    
    async def _compare_prices(self, item_name: str, **kwargs) -> str:
        """Compare prices for an item across stores"""
        # Mock price data - in real implementation, this would fetch from APIs
        mock_prices = {
            "milk": {"Walmart": 3.99, "Target": 4.29, "Kroger": 3.79},
            "bread": {"Walmart": 2.49, "Target": 2.79, "Kroger": 2.39},
            "eggs": {"Walmart": 4.99, "Target": 5.29, "Kroger": 4.79}
        }
        
        if item_name.lower() in mock_prices:
            prices = mock_prices[item_name.lower()]
            best_store = min(prices, key=prices.get)
            best_price = prices[best_store]
            
            price_list = [f"- {store}: ${price:.2f}" for store, price in prices.items()]
            return f"Price comparison for {item_name}:\n" + "\n".join(price_list) + f"\n\nBest deal: {best_store} at ${best_price:.2f}"
        else:
            return f"No price data available for {item_name}"
    
    async def _find_deals(self, category: Optional[str] = None, **kwargs) -> str:
        """Find current deals and discounts"""
        # Mock deals data
        deals = [
            "Milk: 20% off at Walmart",
            "Bread: Buy 1 Get 1 Free at Target",
            "Eggs: $1 off at Kroger",
            "Chicken: 30% off at Walmart"
        ]
        
        if category:
            deals = [deal for deal in deals if category.lower() in deal.lower()]
        
        if deals:
            return "Current Deals:\n" + "\n".join([f"- {deal}" for deal in deals])
        else:
            return "No deals found"

class ShoppingOptimizerTool(LangChainTool):
    """LangChain tool for shopping optimization"""
    
    def __init__(self):
        super().__init__(
            name="shopping_optimizer",
            description="Optimize shopping routes, timing, and create efficient shopping lists"
        )
    
    async def _arun(self, action: str, **kwargs) -> str:
        """Async execution of shopping optimization actions"""
        try:
            if action == "optimize_route":
                return await self._optimize_route(**kwargs)
            elif action == "create_list":
                return await self._create_shopping_list(**kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error in shopping optimization: {str(e)}"
    
    def _run(self, action: str, **kwargs) -> str:
        """Sync execution - not implemented"""
        raise NotImplementedError("Use async execution")
    
    async def _optimize_route(self, stores: List[str], items: List[str], **kwargs) -> str:
        """Optimize shopping route"""
        if not stores or not items:
            return "Please provide stores and items to optimize route"
        
        # Simple route optimization (in real implementation, would use mapping APIs)
        optimized_route = " → ".join(stores)
        
        return f"Optimized shopping route:\n{optimized_route}\n\nItems to buy: {', '.join(items)}"
    
    async def _create_shopping_list(self, items: List[str], budget: Optional[float] = None, **kwargs) -> str:
        """Create an organized shopping list"""
        if not items:
            return "Please provide items for the shopping list"
        
        # Organize items by category
        categories = {
            "Dairy": ["milk", "cheese", "yogurt", "butter"],
            "Produce": ["apples", "bananas", "lettuce", "tomatoes"],
            "Meat": ["chicken", "beef", "pork", "fish"],
            "Pantry": ["rice", "pasta", "canned goods", "spices"]
        }
        
        organized_list = {}
        for item in items:
            categorized = False
            for category, category_items in categories.items():
                if any(cat_item in item.lower() for cat_item in category_items):
                    if category not in organized_list:
                        organized_list[category] = []
                    organized_list[category].append(item)
                    categorized = True
                    break
            
            if not categorized:
                if "Other" not in organized_list:
                    organized_list["Other"] = []
                organized_list["Other"].append(item)
        
        result = "Shopping List:\n"
        for category, category_items in organized_list.items():
            result += f"\n{category}:\n"
            for item in category_items:
                result += f"  - {item}\n"
        
        if budget:
            result += f"\nBudget: ${budget:.2f}"
        
        return result

class LangChainBuckyAgent(LangChainBaseAgent):
    """LangChain-based Bucky Shopping Agent"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            config = config_manager.load_config("bucky")
        
        super().__init__("bucky", config)
        
        # Register with A2A coordinator
        a2a_coordinator.register_agent(self)
    
    def _register_tools(self):
        """Register Bucky's tools"""
        self.add_tool(PantryTrackerTool())
        self.add_tool(PriceComparatorTool())
        self.add_tool(ShoppingOptimizerTool())
    
    def _register_a2a_handlers(self):
        """Register A2A message handlers"""
        self.register_a2a_handler("pantry_inventory_status", self._handle_pantry_status)
        self.register_a2a_handler("shopping_trip_scheduling", self._handle_shopping_scheduling)
        self.register_a2a_handler("health_food_recommendations", self._handle_health_recommendations)
        self.register_a2a_handler("generate_shopping_list", self._handle_generate_shopping_list)
    
    def _get_system_prompt(self) -> str:
        return """You are Bucky, a shopping and inventory management assistant. 
        You help users manage their household inventory, compare prices, optimize shopping trips, and find the best deals.
        
        Your capabilities include:
        - Tracking pantry inventory and expiration dates
        - Comparing prices across different stores
        - Optimizing shopping routes and timing
        - Creating organized shopping lists
        - Finding deals and discounts
        
        Always use your tools to provide accurate and helpful information. Be proactive in suggesting ways to save money and optimize shopping trips."""
    
    async def _handle_pantry_status(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pantry inventory status requests"""
        try:
            # Use the pantry tracker tool
            inventory_result = await self.tools[0]._arun("get_inventory")
            expiry_result = await self.tools[0]._arun("check_expiry")
            
            return {
                "inventory_summary": inventory_result,
                "expiry_warnings": expiry_result,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_shopping_scheduling(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shopping trip scheduling requests"""
        try:
            stores = payload.get("stores", ["Walmart", "Target"])
            items = payload.get("items", [])
            
            route_result = await self.tools[2]._arun("optimize_route", stores=stores, items=items)
            
            return {
                "optimized_route": route_result,
                "estimated_time": "45 minutes",
                "recommended_timing": "Weekday mornings for less crowds"
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_health_recommendations(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health food recommendations"""
        try:
            dietary_preferences = payload.get("dietary_preferences", [])
            health_goals = payload.get("health_goals", [])
            
            recommendations = [
                "Organic fruits and vegetables",
                "Lean proteins like chicken and fish",
                "Whole grains and complex carbohydrates",
                "Low-fat dairy products"
            ]
            
            if "vegetarian" in dietary_preferences:
                recommendations.append("Plant-based protein sources like beans and lentils")
            
            if "weight_loss" in health_goals:
                recommendations.append("High-fiber foods to promote satiety")
            
            return {
                "recommendations": recommendations,
                "reasoning": "Based on your dietary preferences and health goals"
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_generate_shopping_list(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shopping list generation from meal plans"""
        try:
            ingredients = payload.get("ingredients", [])
            budget = payload.get("budget")
            
            list_result = await self.tools[2]._arun("create_list", items=ingredients, budget=budget)
            
            return {
                "shopping_list": list_result,
                "estimated_cost": "$45.00",
                "suggested_stores": ["Walmart", "Target"]
            }
        except Exception as e:
            return {"error": str(e)} 