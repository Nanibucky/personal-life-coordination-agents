"""
Agent Bucky - Core Agent Implementation
Shopping & Inventory Management Agent
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

from shared.mcp_framework.base_server import BaseMCPServer, ExecutionContext
from shared.a2a_protocol.message_router import A2AMessage

# Import Bucky's tools
from agents.bucky_shopping.tools.pantry_tracker import PantryTrackerTool
from agents.bucky_shopping.tools.price_comparator import PriceComparatorTool
from agents.bucky_shopping.tools.shopping_optimizer import ShoppingOptimizerTool
from agents.bucky_shopping.tools.deal_finder import DealFinderTool

class BuckyAgent(BaseMCPServer):
    """Agent Bucky - Shopping & Inventory Management"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("bucky", 8002, config)
        
        # Register all Bucky's tools
        self.register_tool(PantryTrackerTool())
        self.register_tool(PriceComparatorTool())
        self.register_tool(ShoppingOptimizerTool())
        self.register_tool(DealFinderTool())
        
        self.logger.info("Agent Bucky initialized with 4 tools")
    
    async def process_a2a_message(self, message_data: dict) -> Dict[str, Any]:
        """Process incoming A2A messages from other agents"""
        try:
            message = A2AMessage(**message_data)
            self.logger.info(f"Bucky received: {message.intent} from {message.from_agent}")
            
            if message.intent == "pantry_inventory_status":
                return await self._provide_pantry_status(message)
            elif message.intent == "shopping_trip_scheduling":
                return await self._optimize_shopping_schedule(message)
            elif message.intent == "health_food_recommendations":
                return await self._recommend_healthy_options(message)
            elif message.intent == "generate_shopping_list":
                return await self._generate_shopping_list_from_meals(message)
            else:
                return {
                    "success": False,
                    "error": f"Unknown intent: {message.intent}",
                    "agent": "bucky"
                }
                
        except Exception as e:
            self.logger.error(f"A2A message processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": "bucky"
            }
    
    async def _provide_pantry_status(self, message: A2AMessage) -> Dict[str, Any]:
        """Provide current pantry inventory status to other agents"""
        pantry_tool = self.tools["pantry_tracker"]
        context = ExecutionContext(
            user_id=message.payload.get("user_id", "default"),
            session_id=message.session_id,
            permissions=["read"]
        )
        
        inventory_result = await pantry_tool.execute({
            "action": "get_inventory"
        }, context)
        
        if inventory_result.success:
            inventory = inventory_result.result
            
            # Add helpful analysis
            low_stock_items = inventory.get("low_stock", [])
            expiring_items = inventory.get("expiring_soon", [])
            
            return {
                "success": True,
                "pantry_inventory": inventory.get("items", {}),
                "low_stock_items": low_stock_items,
                "expiring_items": expiring_items,
                "total_items": inventory.get("total_items", 0),
                "inventory_health": "good" if len(low_stock_items) < 3 else "needs_attention",
                "agent": "bucky"
            }
        
        return {
            "success": False,
            "error": "Failed to retrieve pantry status",
            "agent": "bucky"
        }
    
    async def _optimize_shopping_schedule(self, message: A2AMessage) -> Dict[str, Any]:
        """Optimize shopping trip timing and routes"""
        payload = message.payload
        shopping_list = payload.get("shopping_list", [])
        time_constraints = payload.get("time_constraints", {})
        
        # Use shopping optimizer tool
        optimizer_tool = self.tools["shopping_optimizer"]
        context = ExecutionContext(
            user_id=payload.get("user_id", "default"),
            session_id=message.session_id,
            permissions=["read"]
        )
        
        optimization_result = await optimizer_tool.execute({
            "action": "optimize_route",
            "shopping_list": shopping_list,
            "time_constraints": time_constraints,
            "transportation": payload.get("transportation", "car")
        }, context)
        
        if optimization_result.success:
            route_data = optimization_result.result
            
            return {
                "success": True,
                "optimized_routes": route_data.get("optimized_route", []),
                "total_estimated_time": route_data.get("estimated_time", 60),
                "estimated_cost": route_data.get("estimated_cost", 0),
                "fuel_cost": route_data.get("fuel_cost", 0),
                "best_shopping_times": ["Saturday 9AM", "Sunday 10AM", "Tuesday 2PM"],
                "agent": "bucky"
            }
        
        return {
            "success": False,
            "error": "Failed to optimize shopping schedule",
            "agent": "bucky"
        }
    
    async def _recommend_healthy_options(self, message: A2AMessage) -> Dict[str, Any]:
        """Recommend healthy food alternatives based on health goals"""
        payload = message.payload
        health_goals = payload.get("health_goals", [])
        dietary_restrictions = payload.get("dietary_restrictions", [])
        budget_limit = payload.get("budget_limit", 100)
        
        # Use price comparator to find healthy options
        price_tool = self.tools["price_comparator"]
        context = ExecutionContext(
            user_id=payload.get("user_id", "default"),
            session_id=message.session_id,
            permissions=["read"]
        )
        
        # Mock healthy recommendations based on goals
        healthy_recommendations = []
        
        if "weight_loss" in health_goals:
            healthy_recommendations.extend([
                {"item": "Greek Yogurt", "reason": "High protein, low calories", "price_range": "$3-5"},
                {"item": "Leafy Greens", "reason": "Low calorie, high nutrients", "price_range": "$2-4"},
                {"item": "Lean Chicken Breast", "reason": "High protein, low fat", "price_range": "$5-8"}
            ])
        
        if "muscle_gain" in health_goals:
            healthy_recommendations.extend([
                {"item": "Protein Powder", "reason": "Convenient protein source", "price_range": "$25-40"},
                {"item": "Quinoa", "reason": "Complete protein, complex carbs", "price_range": "$4-6"},
                {"item": "Eggs", "reason": "High quality protein", "price_range": "$2-4"}
            ])
        
        if "heart_health" in health_goals:
            healthy_recommendations.extend([
                {"item": "Salmon", "reason": "Omega-3 fatty acids", "price_range": "$8-12"},
                {"item": "Avocados", "reason": "Healthy fats", "price_range": "$1-2 each"},
                {"item": "Oats", "reason": "Soluble fiber", "price_range": "$3-5"}
            ])
        
        return {
            "success": True,
            "healthy_recommendations": healthy_recommendations,
            "dietary_accommodations": dietary_restrictions,
            "budget_friendly_options": [r for r in healthy_recommendations if "$2-" in r["price_range"]],
            "total_recommendations": len(healthy_recommendations),
            "agent": "bucky"
        }
    
    async def _generate_shopping_list_from_meals(self, message: A2AMessage) -> Dict[str, Any]:
        """Generate shopping list from meal plan provided by Milo"""
        payload = message.payload
        meal_plan = payload.get("meal_plan", {})
        existing_inventory = payload.get("existing_inventory", {})
        
        shopping_list = []
        total_estimated_cost = 0
        
        # Process each day's meals
        for day, meals in meal_plan.items():
            if isinstance(meals, dict):
                for meal_type, meal_data in meals.items():
                    if isinstance(meal_data, dict):
                        ingredients = meal_data.get("ingredients", [])
                        for ingredient in ingredients:
                            # Check if we already have this ingredient
                            if ingredient not in existing_inventory:
                                # Estimate price and add to list
                                estimated_price = self._estimate_ingredient_price(ingredient)
                                shopping_list.append({
                                    "item": ingredient,
                                    "needed_for": f"{day} {meal_type}",
                                    "estimated_price": estimated_price,
                                    "category": self._categorize_ingredient(ingredient)
                                })
                                total_estimated_cost += estimated_price
        
        # Remove duplicates and consolidate
        consolidated_list = self._consolidate_shopping_list(shopping_list)
        
        # Use deal finder to optimize prices
        deal_tool = self.tools["deal_finder"]
        context = ExecutionContext(
            user_id=payload.get("user_id", "default"),
            session_id=message.session_id,
            permissions=["read"]
        )
        
        return {
            "success": True,
            "shopping_list": consolidated_list,
            "total_estimated_cost": round(total_estimated_cost, 2),
            "categories": list(set(item["category"] for item in consolidated_list)),
            "money_saving_tips": [
                "Check for store brands on common items",
                "Look for bulk discounts on non-perishables",
                "Use store loyalty programs and coupons"
            ],
            "agent": "bucky"
        }
    
    def _estimate_ingredient_price(self, ingredient: str) -> float:
        """Estimate price for an ingredient"""
        # Mock price estimation - would use real price data
        price_map = {
            "chicken": 6.99,
            "beef": 8.99,
            "salmon": 12.99,
            "rice": 2.49,
            "pasta": 1.99,
            "bread": 2.99,
            "milk": 3.49,
            "eggs": 2.99,
            "cheese": 4.99,
            "yogurt": 4.49,
            "apples": 3.99,
            "bananas": 1.99,
            "carrots": 1.49,
            "onions": 1.99,
            "tomatoes": 2.99
        }
        
        # Find closest match or use default
        for key, price in price_map.items():
            if key in ingredient.lower():
                return price
        
        return 3.99  # Default price
    
    def _categorize_ingredient(self, ingredient: str) -> str:
        """Categorize ingredient for shopping organization"""
        ingredient_lower = ingredient.lower()
        
        if any(meat in ingredient_lower for meat in ["chicken", "beef", "pork", "fish", "salmon"]):
            return "meat_seafood"
        elif any(dairy in ingredient_lower for dairy in ["milk", "cheese", "yogurt", "butter"]):
            return "dairy"
        elif any(produce in ingredient_lower for produce in ["apple", "banana", "carrot", "onion", "tomato", "lettuce"]):
            return "produce"
        elif any(grain in ingredient_lower for grain in ["rice", "pasta", "bread", "cereal"]):
            return "grains"
        elif any(frozen in ingredient_lower for frozen in ["frozen", "ice"]):
            return "frozen"
        else:
            return "pantry"
    
    def _consolidate_shopping_list(self, shopping_list: List[Dict]) -> List[Dict]:
        """Consolidate duplicate items in shopping list"""
        consolidated = {}
        
        for item in shopping_list:
            item_name = item["item"]
            if item_name in consolidated:
                # Combine quantities or note multiple uses
                consolidated[item_name]["needed_for"] += f", {item['needed_for']}"
            else:
                consolidated[item_name] = item
        
        return list(consolidated.values())