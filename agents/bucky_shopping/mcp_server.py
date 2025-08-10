"""
Bucky Shopping & Inventory Agent - MCP Server
Shopping management, inventory tracking, and procurement optimization using MCP protocol
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from shared.mcp_framework.mcp_server_base import BaseMCPServer
from agents.bucky_shopping.tools.inventory_manager import InventoryManagerTool
from agents.bucky_shopping.tools.shopping_list_manager import ShoppingListManagerTool
from agents.bucky_shopping.tools.price_tracker import PriceTrackerTool


class BuckyMCPServer(BaseMCPServer):
    """
    Bucky Shopping & Inventory Agent MCP Server
    Provides inventory management, shopping list optimization, price tracking, and procurement tools
    """
    
    def __init__(self):
        super().__init__(
            server_name="bucky",
            port=8004,
            description="Shopping & Inventory Agent with intelligent shopping lists, inventory tracking, and price optimization"
        )
        
        # Initialize tools
        self.inventory_manager = InventoryManagerTool()
        self.shopping_list_manager = ShoppingListManagerTool()
        self.price_tracker = PriceTrackerTool()
    
    async def initialize_agent(self):
        """Initialize Bucky's tools and resources"""
        
        # Register inventory management tool
        self.register_tool(
            name="inventory_manager",
            description="Track and manage household inventory with smart replenishment alerts",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add_item", "update_quantity", "remove_item", "check_inventory", "low_stock_alert", "expire_soon"],
                        "description": "Action to perform on inventory"
                    },
                    "item": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Item name"},
                            "category": {
                                "type": "string", 
                                "enum": ["food", "beverages", "household", "personal_care", "cleaning", "medicine", "other"],
                                "description": "Item category"
                            },
                            "quantity": {"type": "number", "description": "Current quantity"},
                            "unit": {"type": "string", "description": "Unit of measurement (kg, liters, pieces, etc.)"},
                            "min_threshold": {"type": "number", "description": "Minimum quantity before reordering"},
                            "expiry_date": {"type": "string", "format": "date", "description": "Expiration date (YYYY-MM-DD)"},
                            "purchase_date": {"type": "string", "format": "date", "description": "Date of purchase"},
                            "price": {"type": "number", "description": "Purchase price"},
                            "location": {"type": "string", "description": "Storage location (pantry, fridge, freezer, etc.)"}
                        },
                        "required": ["name", "category"],
                        "description": "Item details"
                    },
                    "category_filter": {
                        "type": "string",
                        "description": "Filter inventory by category"
                    },
                    "days_until_expiry": {
                        "type": "integer",
                        "default": 7,
                        "description": "Days threshold for expiry alerts"
                    }
                },
                "required": ["action"]
            },
            function=self._manage_inventory
        )
        
        # Register shopping list manager tool
        self.register_tool(
            name="shopping_optimizer",
            description="Create and optimize shopping lists with price tracking and store recommendations",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create_list", "add_item", "remove_item", "optimize_list", "find_deals", "compare_stores"],
                        "description": "Shopping list action"
                    },
                    "list_name": {
                        "type": "string",
                        "description": "Name of the shopping list"
                    },
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Item name"},
                                "quantity": {"type": "number", "description": "Quantity needed"},
                                "unit": {"type": "string", "description": "Unit of measurement"},
                                "priority": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high", "urgent"],
                                    "default": "medium",
                                    "description": "Purchase priority"
                                },
                                "preferred_brand": {"type": "string", "description": "Preferred brand"},
                                "max_price": {"type": "number", "description": "Maximum acceptable price"},
                                "category": {"type": "string", "description": "Item category"}
                            },
                            "required": ["name", "quantity"]
                        },
                        "description": "Items to add to shopping list"
                    },
                    "budget": {
                        "type": "number",
                        "description": "Total budget for shopping trip"
                    },
                    "preferred_stores": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Preferred stores to shop at"
                    },
                    "optimization_criteria": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["price", "quality", "distance", "availability", "eco_friendly"]
                        },
                        "description": "Criteria for optimization"
                    }
                },
                "required": ["action"]
            },
            function=self._optimize_shopping
        )
        
        # Register price tracking tool
        self.register_tool(
            name="price_tracker",
            description="Track prices across stores and alert for deals and price changes",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["track_item", "check_prices", "price_history", "deal_alerts", "price_comparison"],
                        "description": "Price tracking action"
                    },
                    "item_name": {
                        "type": "string",
                        "description": "Name of item to track"
                    },
                    "stores": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Stores to check prices from"
                    },
                    "target_price": {
                        "type": "number",
                        "description": "Desired price for deal alerts"
                    },
                    "time_range": {
                        "type": "string",
                        "enum": ["week", "month", "quarter", "year"],
                        "default": "month",
                        "description": "Time range for price history"
                    },
                    "deal_threshold": {
                        "type": "number",
                        "default": 0.2,
                        "description": "Percentage discount threshold for deal alerts (0.2 = 20%)"
                    }
                },
                "required": ["action"]
            },
            function=self._track_prices
        )
        
        # Register smart procurement tool
        self.register_tool(
            name="procurement_advisor",
            description="Provide intelligent procurement advice based on usage patterns and market conditions",
            input_schema={
                "type": "object",
                "properties": {
                    "analysis_type": {
                        "type": "string",
                        "enum": ["usage_patterns", "bulk_opportunities", "seasonal_planning", "cost_optimization"],
                        "description": "Type of procurement analysis"
                    },
                    "category": {
                        "type": "string",
                        "description": "Product category to analyze"
                    },
                    "time_horizon": {
                        "type": "string",
                        "enum": ["weekly", "monthly", "quarterly", "yearly"],
                        "default": "monthly",
                        "description": "Planning time horizon"
                    },
                    "household_size": {
                        "type": "integer",
                        "description": "Number of people in household"
                    },
                    "dietary_preferences": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Dietary preferences affecting purchases"
                    },
                    "storage_capacity": {
                        "type": "object",
                        "properties": {
                            "pantry_space": {"type": "string", "enum": ["small", "medium", "large"]},
                            "fridge_space": {"type": "string", "enum": ["small", "medium", "large"]},
                            "freezer_space": {"type": "string", "enum": ["small", "medium", "large"]}
                        },
                        "description": "Available storage capacity"
                    }
                },
                "required": ["analysis_type"]
            },
            function=self._advise_procurement
        )
        
        # Register resources
        self.register_resource(
            uri="bucky://product-database",
            name="Product Database",
            description="Comprehensive product database with prices, availability, and specifications",
            mime_type="application/json"
        )
        
        self.register_resource(
            uri="bucky://store-directory", 
            name="Store Directory",
            description="Directory of stores with locations, hours, and specialties",
            mime_type="application/json"
        )
        
        self.register_resource(
            uri="bucky://deals-coupons",
            name="Deals & Coupons",
            description="Current deals, coupons, and promotional offers",
            mime_type="application/json"
        )
        
        self.register_resource(
            uri="bucky://shopping-analytics",
            name="Shopping Analytics",
            description="Shopping patterns, trends, and optimization insights",
            mime_type="application/json"
        )
        
        self.logger.info("Bucky MCP Server initialized with 4 tools and 4 resources")
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute tool using legacy tool classes if function not provided"""
        if tool_name == "inventory_manager":
            return await self._manage_inventory(arguments)
        elif tool_name == "shopping_optimizer":
            return await self._optimize_shopping(arguments)
        elif tool_name == "price_tracker":
            return await self._track_prices(arguments)
        elif tool_name == "procurement_advisor":
            return await self._advise_procurement(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _manage_inventory(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Manage household inventory"""
        try:
            action = arguments.get("action")
            item = arguments.get("item", {})
            category_filter = arguments.get("category_filter")
            days_until_expiry = arguments.get("days_until_expiry", 7)
            
            result = {
                "action_performed": action,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            if action == "add_item":
                # Add new item to inventory
                item_id = f"item_{int(datetime.now().timestamp())}"
                inventory_item = {
                    "item_id": item_id,
                    "name": item.get("name"),
                    "category": item.get("category", "other"),
                    "quantity": item.get("quantity", 1),
                    "unit": item.get("unit", "pieces"),
                    "min_threshold": item.get("min_threshold", 1),
                    "expiry_date": item.get("expiry_date"),
                    "purchase_date": item.get("purchase_date", datetime.now().strftime("%Y-%m-%d")),
                    "price": item.get("price"),
                    "location": item.get("location", "pantry"),
                    "status": "in_stock",
                    "last_updated": datetime.now().isoformat()
                }
                
                # Check if item is low stock immediately
                if inventory_item["quantity"] <= inventory_item["min_threshold"]:
                    inventory_item["status"] = "low_stock"
                
                result.update({
                    "item_added": inventory_item,
                    "message": f"Added {item.get('name')} to inventory",
                    "low_stock_warning": inventory_item["status"] == "low_stock"
                })
            
            elif action == "update_quantity":
                # Update existing item quantity
                current_quantity = item.get("quantity", 0)
                min_threshold = item.get("min_threshold", 1)
                
                updated_item = {
                    "name": item.get("name"),
                    "previous_quantity": current_quantity + 5,  # Mock previous
                    "new_quantity": current_quantity,
                    "min_threshold": min_threshold,
                    "status": "low_stock" if current_quantity <= min_threshold else "in_stock",
                    "last_updated": datetime.now().isoformat()
                }
                
                result.update({
                    "item_updated": updated_item,
                    "message": f"Updated quantity for {item.get('name')}",
                    "reorder_needed": current_quantity <= min_threshold
                })
            
            elif action == "check_inventory":
                # Get current inventory status
                mock_inventory = [
                    {"name": "Rice", "category": "food", "quantity": 2.5, "unit": "kg", "status": "in_stock", "location": "pantry"},
                    {"name": "Milk", "category": "beverages", "quantity": 1, "unit": "liters", "status": "low_stock", "location": "fridge"},
                    {"name": "Bread", "category": "food", "quantity": 1, "unit": "loaves", "status": "expires_soon", "location": "pantry", "expiry_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")},
                    {"name": "Detergent", "category": "cleaning", "quantity": 0.5, "unit": "bottles", "status": "low_stock", "location": "utility"},
                ]
                
                if category_filter:
                    mock_inventory = [item for item in mock_inventory if item["category"] == category_filter]
                
                result.update({
                    "inventory_items": mock_inventory,
                    "total_items": len(mock_inventory),
                    "low_stock_items": [item for item in mock_inventory if item["status"] == "low_stock"],
                    "expires_soon_items": [item for item in mock_inventory if item["status"] == "expires_soon"]
                })
            
            elif action == "low_stock_alert":
                # Get items that need reordering
                low_stock_items = [
                    {"name": "Milk", "current_quantity": 1, "min_threshold": 2, "suggested_purchase": 3},
                    {"name": "Detergent", "current_quantity": 0.5, "min_threshold": 1, "suggested_purchase": 2},
                    {"name": "Toilet Paper", "current_quantity": 2, "min_threshold": 4, "suggested_purchase": 8}
                ]
                
                result.update({
                    "low_stock_items": low_stock_items,
                    "total_low_stock": len(low_stock_items),
                    "estimated_cost": sum(item.get("suggested_purchase", 1) * 5 for item in low_stock_items),  # Mock pricing
                    "priority_items": [item for item in low_stock_items if item["current_quantity"] == 0]
                })
            
            elif action == "expire_soon":
                # Get items expiring within specified days
                expire_soon_items = [
                    {"name": "Bread", "expiry_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"), "days_left": 2},
                    {"name": "Yogurt", "expiry_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"), "days_left": 5},
                    {"name": "Lettuce", "expiry_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"), "days_left": 3}
                ]
                
                expire_soon_items = [item for item in expire_soon_items if item["days_left"] <= days_until_expiry]
                
                result.update({
                    "expiring_items": expire_soon_items,
                    "total_expiring": len(expire_soon_items),
                    "urgent_items": [item for item in expire_soon_items if item["days_left"] <= 2],
                    "usage_suggestions": [
                        f"Use {item['name']} in next {item['days_left']} days" for item in expire_soon_items
                    ]
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Inventory management error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to manage inventory"
            }
    
    async def _optimize_shopping(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize shopping lists and recommendations"""
        try:
            action = arguments.get("action")
            list_name = arguments.get("list_name", "Default List")
            items = arguments.get("items", [])
            budget = arguments.get("budget")
            preferred_stores = arguments.get("preferred_stores", [])
            optimization_criteria = arguments.get("optimization_criteria", ["price", "quality"])
            
            result = {
                "action_performed": action,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            if action == "create_list":
                # Create new shopping list
                shopping_list = {
                    "list_id": f"list_{int(datetime.now().timestamp())}",
                    "name": list_name,
                    "created_date": datetime.now().isoformat(),
                    "items": [],
                    "estimated_total": 0,
                    "budget": budget,
                    "optimization_criteria": optimization_criteria,
                    "status": "draft"
                }
                
                # Add items to list
                total_cost = 0
                for item in items:
                    # Mock pricing
                    estimated_price = self._estimate_item_price(item["name"])
                    list_item = {
                        "name": item["name"],
                        "quantity": item.get("quantity", 1),
                        "unit": item.get("unit", "pieces"),
                        "priority": item.get("priority", "medium"),
                        "estimated_price": estimated_price,
                        "total_cost": estimated_price * item.get("quantity", 1),
                        "preferred_brand": item.get("preferred_brand"),
                        "max_price": item.get("max_price"),
                        "category": item.get("category", "general")
                    }
                    shopping_list["items"].append(list_item)
                    total_cost += list_item["total_cost"]
                
                shopping_list["estimated_total"] = round(total_cost, 2)
                shopping_list["within_budget"] = budget is None or total_cost <= budget
                
                result.update({
                    "shopping_list": shopping_list,
                    "message": f"Created shopping list '{list_name}' with {len(items)} items",
                    "budget_status": "within budget" if shopping_list["within_budget"] else "over budget"
                })
            
            elif action == "optimize_list":
                # Optimize existing shopping list
                optimization_results = {
                    "original_total": 85.50,
                    "optimized_total": 72.25,
                    "savings": 13.25,
                    "savings_percentage": 15.5,
                    "optimizations_applied": [],
                    "store_recommendations": []
                }
                
                # Apply optimization criteria
                if "price" in optimization_criteria:
                    optimization_results["optimizations_applied"].append("Switched to store brands for 30% savings")
                    optimization_results["store_recommendations"].append("Shop at Walmart for basics")
                
                if "quality" in optimization_criteria:
                    optimization_results["optimizations_applied"].append("Selected premium brands for produce")
                    optimization_results["store_recommendations"].append("Get fresh produce from Whole Foods")
                
                if "distance" in optimization_criteria:
                    optimization_results["optimizations_applied"].append("Grouped items by store proximity")
                    optimization_results["store_recommendations"].append("Visit Target for one-stop shopping")
                
                # Generate optimized route
                optimization_results["suggested_route"] = [
                    {"store": "Target", "items": 8, "estimated_time": "45 min", "distance": "2.3 miles"},
                    {"store": "Whole Foods", "items": 3, "estimated_time": "20 min", "distance": "1.8 miles"}
                ]
                
                result.update({
                    "optimization_results": optimization_results,
                    "message": f"Optimized shopping list - ${optimization_results['savings']:.2f} savings found"
                })
            
            elif action == "find_deals":
                # Find current deals and promotions
                current_deals = [
                    {"item": "Bananas", "original_price": 3.99, "deal_price": 2.49, "discount": "37%", "store": "Kroger", "valid_until": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")},
                    {"item": "Ground Beef", "original_price": 8.99, "deal_price": 6.99, "discount": "22%", "store": "Safeway", "valid_until": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")},
                    {"item": "Greek Yogurt", "original_price": 5.49, "deal_price": 3.99, "discount": "27%", "store": "Target", "valid_until": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")}
                ]
                
                # Filter deals based on shopping list items if provided
                relevant_deals = current_deals
                if items:
                    item_names = [item.get("name", "").lower() for item in items]
                    relevant_deals = [deal for deal in current_deals if any(name in deal["item"].lower() for name in item_names)]
                
                result.update({
                    "current_deals": relevant_deals,
                    "total_deals_found": len(relevant_deals),
                    "potential_savings": sum(deal["original_price"] - deal["deal_price"] for deal in relevant_deals),
                    "message": f"Found {len(relevant_deals)} deals matching your list"
                })
            
            elif action == "compare_stores":
                # Compare prices across different stores
                store_comparison = {
                    "comparison_date": datetime.now().isoformat(),
                    "items_compared": len(items) if items else 10,
                    "stores_analyzed": ["Walmart", "Target", "Kroger", "Whole Foods"],
                    "price_comparison": [
                        {"store": "Walmart", "total": 68.45, "avg_savings": "15%", "specialty": "Everyday low prices"},
                        {"store": "Target", "total": 74.20, "avg_savings": "8%", "specialty": "Quality brands"},
                        {"store": "Kroger", "total": 71.30, "avg_savings": "12%", "specialty": "Fresh produce"},
                        {"store": "Whole Foods", "total": 89.95, "avg_savings": "-12%", "specialty": "Organic options"}
                    ],
                    "best_for_budget": "Walmart",
                    "best_for_quality": "Whole Foods",
                    "best_overall_value": "Kroger"
                }
                
                result.update({
                    "store_comparison": store_comparison,
                    "message": f"Compared prices across {len(store_comparison['stores_analyzed'])} stores"
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Shopping optimization error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to optimize shopping"
            }
    
    async def _track_prices(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Track prices and monitor deals"""
        try:
            action = arguments.get("action")
            item_name = arguments.get("item_name")
            stores = arguments.get("stores", ["Walmart", "Target", "Kroger"])
            target_price = arguments.get("target_price")
            time_range = arguments.get("time_range", "month")
            deal_threshold = arguments.get("deal_threshold", 0.2)
            
            result = {
                "action_performed": action,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            if action == "track_item":
                # Start tracking an item
                tracking_info = {
                    "item_name": item_name,
                    "tracking_id": f"track_{int(datetime.now().timestamp())}",
                    "stores_monitored": stores,
                    "target_price": target_price,
                    "current_prices": {},
                    "tracking_started": datetime.now().isoformat(),
                    "alert_threshold": deal_threshold
                }
                
                # Get current prices from stores
                for store in stores:
                    tracking_info["current_prices"][store] = {
                        "price": round(self._estimate_item_price(item_name) * (0.8 + hash(store) % 40 / 100), 2),
                        "in_stock": True,
                        "last_updated": datetime.now().isoformat()
                    }
                
                # Find best current price
                best_price = min(tracking_info["current_prices"].values(), key=lambda x: x["price"])
                best_store = [store for store, info in tracking_info["current_prices"].items() if info["price"] == best_price["price"]][0]
                
                result.update({
                    "tracking_info": tracking_info,
                    "best_current_price": {"store": best_store, **best_price},
                    "target_met": target_price and best_price["price"] <= target_price,
                    "message": f"Now tracking {item_name} across {len(stores)} stores"
                })
            
            elif action == "check_prices":
                # Check current prices for item
                current_prices = {}
                for store in stores:
                    price = round(self._estimate_item_price(item_name) * (0.8 + hash(store) % 40 / 100), 2)
                    current_prices[store] = {
                        "price": price,
                        "in_stock": True,
                        "promotion": price < self._estimate_item_price(item_name) * 0.9,
                        "last_checked": datetime.now().isoformat()
                    }
                
                # Calculate price statistics
                prices = [info["price"] for info in current_prices.values()]
                price_stats = {
                    "lowest_price": min(prices),
                    "highest_price": max(prices),
                    "average_price": round(sum(prices) / len(prices), 2),
                    "price_range": round(max(prices) - min(prices), 2),
                    "variation_percentage": round((max(prices) - min(prices)) / min(prices) * 100, 1)
                }
                
                result.update({
                    "item_name": item_name,
                    "current_prices": current_prices,
                    "price_statistics": price_stats,
                    "best_deal": min(current_prices.items(), key=lambda x: x[1]["price"]),
                    "message": f"Price check complete for {item_name}"
                })
            
            elif action == "price_history":
                # Get price history for item
                days_back = {"week": 7, "month": 30, "quarter": 90, "year": 365}[time_range]
                
                # Generate mock historical data
                history = []
                base_price = self._estimate_item_price(item_name)
                
                for i in range(0, days_back, 7):  # Weekly data points
                    date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                    price_variation = 0.8 + (hash(date) % 40) / 100  # Random but consistent variation
                    history.append({
                        "date": date,
                        "price": round(base_price * price_variation, 2),
                        "store": "Average across stores"
                    })
                
                history.sort(key=lambda x: x["date"])
                
                # Calculate trend
                recent_avg = sum(h["price"] for h in history[-4:]) / 4  # Last 4 weeks
                older_avg = sum(h["price"] for h in history[:4]) / 4  # First 4 weeks
                
                trend_analysis = {
                    "trend": "increasing" if recent_avg > older_avg else "decreasing",
                    "price_change": round(recent_avg - older_avg, 2),
                    "percentage_change": round((recent_avg - older_avg) / older_avg * 100, 1),
                    "recommendation": "Wait for better prices" if recent_avg > older_avg else "Good time to buy"
                }
                
                result.update({
                    "item_name": item_name,
                    "time_range": time_range,
                    "price_history": history,
                    "trend_analysis": trend_analysis,
                    "message": f"Price history retrieved for {time_range} period"
                })
            
            elif action == "deal_alerts":
                # Get current deal alerts
                deal_alerts = [
                    {"item": "Ground Coffee", "current_price": 8.99, "target_price": 7.00, "discount": "21%", "store": "Target", "expires": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")},
                    {"item": "Laundry Detergent", "current_price": 12.49, "target_price": 10.00, "discount": "25%", "store": "Walmart", "expires": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")},
                    {"item": "Olive Oil", "current_price": 6.99, "target_price": 8.00, "discount": "15%", "store": "Kroger", "expires": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")}
                ]
                
                # Filter by item name if specified
                if item_name:
                    deal_alerts = [alert for alert in deal_alerts if item_name.lower() in alert["item"].lower()]
                
                result.update({
                    "deal_alerts": deal_alerts,
                    "total_alerts": len(deal_alerts),
                    "potential_savings": sum(float(alert["discount"].strip("%")) for alert in deal_alerts),
                    "urgent_deals": [alert for alert in deal_alerts if (datetime.strptime(alert["expires"], "%Y-%m-%d") - datetime.now()).days <= 2],
                    "message": f"Found {len(deal_alerts)} active deal alerts"
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Price tracking error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to track prices"
            }
    
    async def _advise_procurement(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Provide procurement advice and analysis"""
        try:
            analysis_type = arguments.get("analysis_type")
            category = arguments.get("category")
            time_horizon = arguments.get("time_horizon", "monthly")
            household_size = arguments.get("household_size", 2)
            dietary_preferences = arguments.get("dietary_preferences", [])
            storage_capacity = arguments.get("storage_capacity", {})
            
            result = {
                "analysis_type": analysis_type,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            if analysis_type == "usage_patterns":
                # Analyze consumption patterns
                usage_analysis = {
                    "analysis_period": time_horizon,
                    "household_size": household_size,
                    "category": category or "all_categories",
                    "consumption_patterns": {
                        "food": {"weekly_spend": 150, "trend": "stable", "peak_days": ["Saturday", "Sunday"]},
                        "household": {"weekly_spend": 45, "trend": "increasing", "bulk_opportunities": True},
                        "personal_care": {"weekly_spend": 25, "trend": "stable", "subscription_worthy": True}
                    },
                    "seasonal_variations": {
                        "summer": "15% increase in beverages",
                        "winter": "20% increase in comfort foods",
                        "holidays": "40% increase in entertaining supplies"
                    },
                    "recommendations": [
                        f"Based on {household_size}-person household, budget ${150 * household_size / 2:.0f}/week for groceries",
                        "Consider bulk buying for cleaning supplies - 25% savings potential",
                        "Meal planning could reduce food waste by 20%"
                    ]
                }
                
                result.update({
                    "usage_analysis": usage_analysis,
                    "message": "Usage pattern analysis complete"
                })
            
            elif analysis_type == "bulk_opportunities":
                # Identify bulk buying opportunities
                bulk_opportunities = [
                    {
                        "item": "Rice",
                        "regular_price": 3.99,
                        "bulk_price": 12.99,
                        "bulk_quantity": "10 lbs",
                        "unit_savings": 0.70,
                        "total_savings": 28.60,
                        "storage_required": "pantry_medium",
                        "shelf_life": "2 years"
                    },
                    {
                        "item": "Laundry Detergent",
                        "regular_price": 8.99,
                        "bulk_price": 24.99,
                        "bulk_quantity": "4 bottles",
                        "unit_savings": 2.00,
                        "total_savings": 8.00,
                        "storage_required": "utility_space",
                        "shelf_life": "3 years"
                    },
                    {
                        "item": "Toilet Paper",
                        "regular_price": 12.99,
                        "bulk_price": 45.99,
                        "bulk_quantity": "48 rolls",
                        "unit_savings": 0.25,
                        "total_savings": 12.00,
                        "storage_required": "large_space",
                        "shelf_life": "indefinite"
                    }
                ]
                
                # Filter by storage capacity
                if storage_capacity:
                    pantry_size = storage_capacity.get("pantry_space", "medium")
                    if pantry_size == "small":
                        bulk_opportunities = [opp for opp in bulk_opportunities if "large" not in opp["storage_required"]]
                
                total_savings = sum(opp["total_savings"] for opp in bulk_opportunities)
                
                result.update({
                    "bulk_opportunities": bulk_opportunities,
                    "total_opportunities": len(bulk_opportunities),
                    "potential_annual_savings": round(total_savings * 2, 2),  # Assume twice per year
                    "storage_requirements": list(set(opp["storage_required"] for opp in bulk_opportunities)),
                    "message": f"Found {len(bulk_opportunities)} bulk buying opportunities"
                })
            
            elif analysis_type == "seasonal_planning":
                # Seasonal procurement planning
                current_season = self._get_current_season()
                seasonal_plan = {
                    "current_season": current_season,
                    "seasonal_items": {
                        "spring": ["Fresh herbs", "Spring vegetables", "Easter items"],
                        "summer": ["BBQ supplies", "Cold beverages", "Sunscreen"],
                        "fall": ["Back-to-school supplies", "Halloween items", "Warm spices"],
                        "winter": ["Holiday baking items", "Comfort foods", "Cold medicine"]
                    },
                    "upcoming_deals": [
                        {"item": "BBQ Sauce", "expected_discount": "30%", "timing": "Memorial Day weekend"},
                        {"item": "Sunscreen", "expected_discount": "40%", "timing": "End of summer"},
                        {"item": "Winter Coats", "expected_discount": "50%", "timing": "February clearance"}
                    ],
                    "stock_up_recommendations": [
                        "Buy holiday items 75% off after season",
                        "Stock up on canned goods during fall sales",
                        "Purchase gardening supplies in winter for spring savings"
                    ]
                }
                
                result.update({
                    "seasonal_plan": seasonal_plan,
                    "next_season_prep": f"Prepare for {self._get_next_season()} shopping",
                    "message": "Seasonal procurement plan generated"
                })
            
            elif analysis_type == "cost_optimization":
                # Cost optimization analysis
                optimization_analysis = {
                    "current_spending": {
                        "monthly_total": 600,
                        "categories": {
                            "food": 400,
                            "household": 120,
                            "personal_care": 80
                        }
                    },
                    "optimization_opportunities": [
                        {"strategy": "Store brand substitutions", "potential_savings": 60, "effort": "low"},
                        {"strategy": "Bulk buying program", "potential_savings": 45, "effort": "medium"},
                        {"strategy": "Coupon/deal hunting", "potential_savings": 35, "effort": "high"},
                        {"strategy": "Meal planning", "potential_savings": 80, "effort": "medium"},
                        {"strategy": "Generic medications", "potential_savings": 25, "effort": "low"}
                    ],
                    "recommended_budget": {
                        "food": 320,
                        "household": 90,
                        "personal_care": 65,
                        "total": 475,
                        "monthly_savings": 125
                    }
                }
                
                # Adjust for household size
                if household_size != 2:
                    multiplier = household_size / 2
                    optimization_analysis["current_spending"]["monthly_total"] *= multiplier
                    optimization_analysis["recommended_budget"]["total"] *= multiplier
                    optimization_analysis["recommended_budget"]["monthly_savings"] *= multiplier
                
                result.update({
                    "optimization_analysis": optimization_analysis,
                    "annual_savings_potential": optimization_analysis["recommended_budget"]["monthly_savings"] * 12,
                    "top_recommendation": max(optimization_analysis["optimization_opportunities"], key=lambda x: x["potential_savings"]),
                    "message": "Cost optimization analysis complete"
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Procurement advice error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to provide procurement advice"
            }
    
    def _estimate_item_price(self, item_name: str) -> float:
        """Estimate item price based on name"""
        price_map = {
            "milk": 3.99, "bread": 2.49, "eggs": 3.49, "chicken": 5.99,
            "rice": 3.99, "pasta": 1.99, "bananas": 1.29, "apples": 2.99,
            "ground beef": 8.99, "detergent": 8.99, "toilet paper": 12.99,
            "shampoo": 6.99, "coffee": 9.99, "yogurt": 5.49
        }
        
        item_lower = item_name.lower()
        for key, price in price_map.items():
            if key in item_lower:
                return price
        
        # Default price based on item name length (mock)
        return round(2.00 + len(item_name) * 0.25, 2)
    
    def _get_current_season(self) -> str:
        """Get current season"""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"
    
    def _get_next_season(self) -> str:
        """Get next season"""
        seasons = ["winter", "spring", "summer", "fall"]
        current = self._get_current_season()
        current_idx = seasons.index(current)
        return seasons[(current_idx + 1) % 4]
    
    async def _read_resource(self, uri: str) -> str:
        """Read resource content"""
        if uri == "bucky://product-database":
            return json.dumps({
                "database": "Bucky Product Database",
                "total_products": 50000,
                "categories": ["food", "beverages", "household", "personal_care", "cleaning", "medicine"],
                "last_updated": "2025-08-10",
                "sample_products": [
                    {
                        "name": "Organic Bananas",
                        "category": "food",
                        "average_price": 2.49,
                        "unit": "bunch",
                        "stores": ["Whole Foods", "Target", "Kroger"],
                        "nutritional_info": {"calories": 105, "potassium": "422mg"}
                    },
                    {
                        "name": "All-Purpose Cleaner",
                        "category": "cleaning",
                        "average_price": 4.99,
                        "unit": "bottle",
                        "stores": ["Walmart", "Target", "Home Depot"],
                        "eco_friendly": True
                    }
                ],
                "price_tracking_enabled": True
            }, indent=2)
        
        elif uri == "bucky://store-directory":
            return json.dumps({
                "stores": [
                    {
                        "name": "Walmart",
                        "type": "supermarket",
                        "specialties": ["low_prices", "grocery", "household"],
                        "locations": 15,
                        "average_prices": "low",
                        "online_shopping": True,
                        "delivery_available": True
                    },
                    {
                        "name": "Target",
                        "type": "department_store",
                        "specialties": ["quality_brands", "household", "electronics"],
                        "locations": 8,
                        "average_prices": "medium",
                        "online_shopping": True,
                        "delivery_available": True
                    },
                    {
                        "name": "Whole Foods",
                        "type": "organic_grocery",
                        "specialties": ["organic", "fresh_produce", "premium_brands"],
                        "locations": 3,
                        "average_prices": "high",
                        "online_shopping": True,
                        "delivery_available": True
                    },
                    {
                        "name": "Costco",
                        "type": "warehouse_club",
                        "specialties": ["bulk_buying", "membership_required", "wholesale_prices"],
                        "locations": 2,
                        "average_prices": "low_bulk",
                        "online_shopping": True,
                        "delivery_available": False
                    }
                ]
            }, indent=2)
        
        elif uri == "bucky://deals-coupons":
            return json.dumps({
                "deals_updated": datetime.now().isoformat(),
                "active_deals": [
                    {
                        "store": "Target",
                        "item": "Tide Laundry Detergent",
                        "original_price": 12.99,
                        "deal_price": 8.99,
                        "discount_percentage": 31,
                        "valid_until": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                        "deal_type": "weekly_ad"
                    },
                    {
                        "store": "Kroger",
                        "item": "Ground Turkey",
                        "original_price": 5.99,
                        "deal_price": 3.99,
                        "discount_percentage": 33,
                        "valid_until": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                        "deal_type": "clearance"
                    }
                ],
                "coupons_available": [
                    {
                        "brand": "Crest",
                        "product": "Toothpaste",
                        "discount": "$2.00 off",
                        "minimum_purchase": 2,
                        "expires": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                    }
                ],
                "total_active_deals": 47,
                "total_coupons": 23
            }, indent=2)
        
        elif uri == "bucky://shopping-analytics":
            return json.dumps({
                "analytics_period": "last_30_days",
                "shopping_patterns": {
                    "most_frequent_stores": ["Target", "Kroger", "Walmart"],
                    "peak_shopping_days": ["Saturday", "Sunday"],
                    "average_cart_size": "$78.45",
                    "category_spending": {
                        "food": 65,
                        "household": 20,
                        "personal_care": 15
                    }
                },
                "savings_opportunities": {
                    "store_brand_potential": "$23.50/month",
                    "bulk_buying_potential": "$18.75/month",
                    "coupon_usage_potential": "$12.25/month"
                },
                "price_trends": {
                    "food_inflation": "3.2%",
                    "household_items": "1.8%",
                    "seasonal_variation": "12%"
                },
                "recommendations": [
                    "Shop Tuesday-Thursday for better deals",
                    "Compare unit prices, not just item prices",
                    "Use store apps for exclusive digital coupons"
                ]
            }, indent=2)
        
        else:
            raise ValueError(f"Unknown resource: {uri}")


async def main():
    """Run Bucky MCP Server"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = BuckyMCPServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())