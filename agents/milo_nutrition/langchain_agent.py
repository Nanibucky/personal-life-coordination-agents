"""
LangChain Milo Agent - Meal Planning & Nutrition
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
_recipe_data = {}
_nutrition_data = {}

class RecipeEngineTool(LangChainTool):
    """LangChain tool for recipe generation"""
    
    def __init__(self):
        super().__init__(
            name="recipe_engine",
            description="Generate recipes based on available ingredients and dietary preferences"
        )
    
    async def _arun(self, action: str, **kwargs) -> str:
        """Async execution of recipe engine actions"""
        try:
            if action == "generate_recipe":
                return await self._generate_recipe(**kwargs)
            elif action == "find_recipes":
                return await self._find_recipes(**kwargs)
            elif action == "get_recipe":
                return await self._get_recipe(**kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error in recipe engine: {str(e)}"
    
    def _run(self, action: str, **kwargs) -> str:
        """Sync execution - not implemented"""
        raise NotImplementedError("Use async execution")
    
    async def _generate_recipe(self, ingredients: List[str], dietary_preferences: List[str] = [], **kwargs) -> str:
        """Generate a recipe based on available ingredients"""
        recipe_id = f"recipe_{datetime.now().timestamp()}"
        recipe = {
            "id": recipe_id,
            "name": f"Recipe with {', '.join(ingredients[:3])}",
            "ingredients": ingredients,
            "instructions": [
                "1. Prepare all ingredients",
                "2. Cook according to standard methods",
                "3. Season to taste",
                "4. Serve hot"
            ],
            "cooking_time": "30 minutes",
            "servings": 4,
            "calories_per_serving": 350,
            "dietary_tags": dietary_preferences
        }
        
        _recipe_data[recipe_id] = recipe
        return f"Generated recipe: {recipe['name']} - {recipe['cooking_time']}, {recipe['calories_per_serving']} cal/serving"
    
    async def _find_recipes(self, ingredients: List[str], **kwargs) -> str:
        """Find recipes that can be made with given ingredients"""
        # Mock recipe search
        available_recipes = [
            "Pasta with Tomato Sauce",
            "Chicken Stir Fry",
            "Vegetable Soup",
            "Rice and Beans"
        ]
        
        return f"Recipes you can make with {', '.join(ingredients)}:\n" + "\n".join([f"- {recipe}" for recipe in available_recipes])
    
    async def _get_recipe(self, recipe_name: str, **kwargs) -> str:
        """Get detailed recipe information"""
        # Mock recipe details
        recipe_details = {
            "name": recipe_name,
            "ingredients": ["ingredient 1", "ingredient 2", "ingredient 3"],
            "instructions": ["Step 1", "Step 2", "Step 3"],
            "nutrition": {
                "calories": 400,
                "protein": "20g",
                "carbs": "45g",
                "fat": "15g"
            }
        }
        
        return f"Recipe: {recipe_name}\nIngredients: {', '.join(recipe_details['ingredients'])}\nCalories: {recipe_details['nutrition']['calories']}"

class NutritionAnalyzerTool(LangChainTool):
    """LangChain tool for nutrition analysis"""
    
    def __init__(self):
        super().__init__(
            name="nutrition_analyzer",
            description="Analyze nutritional content of meals and provide dietary recommendations"
        )
    
    async def _arun(self, action: str, **kwargs) -> str:
        """Async execution of nutrition analysis actions"""
        try:
            if action == "analyze_meal":
                return await self._analyze_meal(**kwargs)
            elif action == "get_recommendations":
                return await self._get_nutrition_recommendations(**kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error in nutrition analysis: {str(e)}"
    
    def _run(self, action: str, **kwargs) -> str:
        """Sync execution - not implemented"""
        raise NotImplementedError("Use async execution")
    
    async def _analyze_meal(self, foods: List[str], **kwargs) -> str:
        """Analyze the nutritional content of a meal"""
        # Mock nutrition analysis
        total_calories = len(foods) * 150  # Rough estimate
        protein = len(foods) * 8
        carbs = len(foods) * 20
        fat = len(foods) * 5
        
        analysis = f"Nutritional Analysis:\n"
        analysis += f"Total Calories: {total_calories}\n"
        analysis += f"Protein: {protein}g\n"
        analysis += f"Carbohydrates: {carbs}g\n"
        analysis += f"Fat: {fat}g\n"
        
        if total_calories > 800:
            analysis += "\nNote: This is a high-calorie meal"
        elif total_calories < 300:
            analysis += "\nNote: This is a light meal"
        
        return analysis
    
    async def _get_nutrition_recommendations(self, age: int, activity_level: str, goals: List[str], **kwargs) -> str:
        """Get personalized nutrition recommendations"""
        recommendations = []
        
        # Age-based recommendations
        if age < 30:
            recommendations.append("Focus on protein for muscle building")
        elif 30 <= age <= 50:
            recommendations.append("Balance protein, carbs, and healthy fats")
        else:
            recommendations.append("Prioritize protein and calcium for bone health")
        
        # Activity level recommendations
        if activity_level == "sedentary":
            recommendations.append("Limit calorie intake to maintain weight")
        elif activity_level == "moderate":
            recommendations.append("Moderate calorie intake with balanced macros")
        elif activity_level == "active":
            recommendations.append("Higher calorie intake to support activity")
        
        # Goal-based recommendations
        for goal in goals:
            if goal == "weight_loss":
                recommendations.append("Create a calorie deficit of 500 calories/day")
            elif goal == "muscle_gain":
                recommendations.append("Increase protein intake to 1.6-2.2g per kg body weight")
            elif goal == "maintenance":
                recommendations.append("Maintain current calorie intake with balanced nutrition")
        
        return "Nutrition Recommendations:\n" + "\n".join([f"- {rec}" for rec in recommendations])

class MealPlannerTool(LangChainTool):
    """LangChain tool for meal planning"""
    
    def __init__(self):
        super().__init__(
            name="meal_planner",
            description="Create meal plans and shopping lists based on dietary preferences"
        )
    
    async def _arun(self, action: str, **kwargs) -> str:
        """Async execution of meal planning actions"""
        try:
            if action == "create_meal_plan":
                return await self._create_meal_plan(**kwargs)
            elif action == "generate_shopping_list":
                return await self._generate_shopping_list(**kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error in meal planning: {str(e)}"
    
    def _run(self, action: str, **kwargs) -> str:
        """Sync execution - not implemented"""
        raise NotImplementedError("Use async execution")
    
    async def _create_meal_plan(self, days: int = 7, dietary_preferences: List[str] = [], **kwargs) -> str:
        """Create a meal plan for specified number of days"""
        meal_plan = {
            "breakfast": ["Oatmeal with berries", "Greek yogurt with granola", "Eggs and toast"],
            "lunch": ["Grilled chicken salad", "Vegetable soup", "Quinoa bowl"],
            "dinner": ["Salmon with vegetables", "Pasta with tomato sauce", "Stir-fried tofu"]
        }
        
        plan = f"Meal Plan for {days} days:\n\n"
        for day in range(1, min(days + 1, 8)):
            plan += f"Day {day}:\n"
            plan += f"  Breakfast: {meal_plan['breakfast'][day % 3]}\n"
            plan += f"  Lunch: {meal_plan['lunch'][day % 3]}\n"
            plan += f"  Dinner: {meal_plan['dinner'][day % 3]}\n\n"
        
        if dietary_preferences:
            plan += f"Dietary preferences considered: {', '.join(dietary_preferences)}"
        
        return plan
    
    async def _generate_shopping_list(self, meal_plan: Dict[str, Any], **kwargs) -> str:
        """Generate shopping list from meal plan"""
        # Mock shopping list generation
        ingredients = [
            "Chicken breast", "Salmon fillets", "Eggs", "Milk", "Bread",
            "Oatmeal", "Berries", "Greek yogurt", "Granola", "Quinoa",
            "Mixed vegetables", "Tomatoes", "Onions", "Garlic", "Olive oil"
        ]
        
        # Organize by category
        categories = {
            "Proteins": ["Chicken breast", "Salmon fillets", "Eggs"],
            "Dairy": ["Milk", "Greek yogurt"],
            "Grains": ["Bread", "Oatmeal", "Granola", "Quinoa"],
            "Produce": ["Berries", "Mixed vegetables", "Tomatoes", "Onions", "Garlic"],
            "Pantry": ["Olive oil"]
        }
        
        shopping_list = "Shopping List:\n\n"
        for category, items in categories.items():
            shopping_list += f"{category}:\n"
            for item in items:
                shopping_list += f"  - {item}\n"
            shopping_list += "\n"
        
        return shopping_list

class LangChainMiloAgent(LangChainBaseAgent):
    """LangChain-based Milo Nutrition Agent"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            config = config_manager.load_config("milo")
        
        super().__init__("milo", config)
        
        # Register with A2A coordinator
        a2a_coordinator.register_agent(self)
    
    def _register_tools(self):
        """Register Milo's tools"""
        self.add_tool(RecipeEngineTool())
        self.add_tool(NutritionAnalyzerTool())
        self.add_tool(MealPlannerTool())
    
    def _register_a2a_handlers(self):
        """Register A2A message handlers"""
        self.register_a2a_handler("meal_planning_request", self._handle_meal_planning)
        self.register_a2a_handler("nutrition_analysis", self._handle_nutrition_analysis)
        self.register_a2a_handler("recipe_generation", self._handle_recipe_generation)
        self.register_a2a_handler("shopping_list_generation", self._handle_shopping_list)
    
    def _get_system_prompt(self) -> str:
        return """You are Milo, a meal planning and nutrition assistant. 
        You help users create meal plans, analyze nutrition, and generate recipes based on their dietary preferences.
        
        Your capabilities include:
        - Generating recipes based on available ingredients
        - Analyzing nutritional content of meals
        - Creating personalized meal plans
        - Generating shopping lists
        - Providing nutrition recommendations
        
        Always use your tools to provide accurate and helpful information. Consider dietary restrictions and health goals."""
    
    async def _handle_meal_planning(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle meal planning requests"""
        try:
            days = payload.get("days", 7)
            dietary_preferences = payload.get("dietary_preferences", [])
            
            meal_plan = await self.tools[2]._arun("create_meal_plan", days=days, dietary_preferences=dietary_preferences)
            
            return {
                "meal_plan": meal_plan,
                "days_planned": days,
                "dietary_considerations": dietary_preferences
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_nutrition_analysis(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle nutrition analysis requests"""
        try:
            foods = payload.get("foods", [])
            
            analysis = await self.tools[1]._arun("analyze_meal", foods=foods)
            
            return {
                "nutrition_analysis": analysis,
                "foods_analyzed": foods
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_recipe_generation(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle recipe generation requests"""
        try:
            ingredients = payload.get("ingredients", [])
            dietary_preferences = payload.get("dietary_preferences", [])
            
            recipe = await self.tools[0]._arun("generate_recipe", ingredients=ingredients, dietary_preferences=dietary_preferences)
            
            return {
                "recipe": recipe,
                "ingredients_used": ingredients
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_shopping_list(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shopping list generation requests"""
        try:
            meal_plan = payload.get("meal_plan", {})
            
            shopping_list = await self.tools[2]._arun("generate_shopping_list", meal_plan=meal_plan)
            
            return {
                "shopping_list": shopping_list,
                "estimated_cost": "$75.00"
            }
        except Exception as e:
            return {"error": str(e)} 