"""
Milo Nutrition Agent - MCP Server
Meal planning and nutrition analysis using MCP protocol
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from shared.mcp_framework.mcp_server_base import BaseMCPServer
from agents.milo_nutrition.tools.meal_planner import MealPlannerTool
from agents.milo_nutrition.tools.nutrition_analyzer import NutritionAnalyzerTool
from agents.milo_nutrition.tools.recipe_engine import RecipeEngineTool


class MiloMCPServer(BaseMCPServer):
    """
    Milo Nutrition Agent MCP Server
    Provides meal planning, nutrition analysis, and recipe generation tools
    """
    
    def __init__(self):
        super().__init__(
            server_name="milo",
            port=8002,
            description="Meal Planning & Nutrition Agent with AI-powered meal planning, nutritional analysis, and recipe generation"
        )
        
        # Initialize tools
        self.meal_planner = MealPlannerTool()
        self.nutrition_analyzer = NutritionAnalyzerTool()
        self.recipe_engine = RecipeEngineTool()
    
    async def initialize_agent(self):
        """Initialize Milo's tools and resources"""
        
        # Register meal planning tool
        self.register_tool(
            name="meal_planner",
            description="AI-powered meal planning with dietary restrictions and preferences",
            input_schema={
                "type": "object",
                "properties": {
                    "dietary_restrictions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of dietary restrictions (vegetarian, vegan, gluten-free, etc.)"
                    },
                    "calories_target": {
                        "type": "integer",
                        "description": "Target daily calories"
                    },
                    "meals_per_day": {
                        "type": "integer",
                        "default": 3,
                        "description": "Number of meals per day"
                    },
                    "days": {
                        "type": "integer",
                        "default": 7,
                        "description": "Number of days to plan for"
                    },
                    "cuisine_preferences": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Preferred cuisines"
                    },
                    "exclude_ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Ingredients to exclude"
                    }
                },
                "required": ["calories_target"]
            },
            function=self._plan_meals
        )
        
        # Register nutrition analysis tool
        self.register_tool(
            name="nutrition_analyzer",
            description="Analyze nutritional content of meals and ingredients",
            input_schema={
                "type": "object",
                "properties": {
                    "food_items": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of food items to analyze"
                    },
                    "recipe": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "ingredients": {"type": "array", "items": {"type": "string"}},
                            "servings": {"type": "integer"}
                        },
                        "description": "Recipe to analyze"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["basic", "detailed", "macro_breakdown"],
                        "default": "basic",
                        "description": "Type of nutritional analysis"
                    }
                }
            },
            function=self._analyze_nutrition
        )
        
        # Register recipe generation tool
        self.register_tool(
            name="recipe_generator",
            description="Generate and modify recipes based on ingredients and preferences",
            input_schema={
                "type": "object",
                "properties": {
                    "ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Available ingredients"
                    },
                    "recipe_type": {
                        "type": "string",
                        "enum": ["breakfast", "lunch", "dinner", "snack", "dessert"],
                        "description": "Type of recipe to generate"
                    },
                    "cooking_time": {
                        "type": "integer",
                        "description": "Maximum cooking time in minutes"
                    },
                    "difficulty": {
                        "type": "string",
                        "enum": ["easy", "medium", "hard"],
                        "default": "medium",
                        "description": "Recipe difficulty level"
                    },
                    "dietary_requirements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Dietary requirements to follow"
                    },
                    "cuisine_style": {
                        "type": "string",
                        "description": "Preferred cuisine style"
                    }
                },
                "required": ["ingredients", "recipe_type"]
            },
            function=self._generate_recipe
        )
        
        # Register meal optimization tool
        self.register_tool(
            name="meal_optimizer",
            description="Optimize meal plans for nutrition, cost, and time efficiency",
            input_schema={
                "type": "object",
                "properties": {
                    "current_meal_plan": {
                        "type": "object",
                        "description": "Current meal plan to optimize"
                    },
                    "optimization_goals": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["nutrition", "cost", "time", "variety"]},
                        "description": "Optimization priorities"
                    },
                    "budget_constraint": {
                        "type": "number",
                        "description": "Budget constraint for the meal plan"
                    },
                    "prep_time_limit": {
                        "type": "integer",
                        "description": "Maximum preparation time per meal in minutes"
                    }
                },
                "required": ["current_meal_plan", "optimization_goals"]
            },
            function=self._optimize_meals
        )
        
        # Register resources
        self.register_resource(
            uri="milo://nutrition-database",
            name="Nutrition Database",
            description="Comprehensive nutrition information for foods and ingredients",
            mime_type="application/json"
        )
        
        self.register_resource(
            uri="milo://recipe-database", 
            name="Recipe Database",
            description="Collection of recipes with nutritional information",
            mime_type="application/json"
        )
        
        self.register_resource(
            uri="milo://dietary-guidelines",
            name="Dietary Guidelines",
            description="Nutritional guidelines and recommendations",
            mime_type="text/markdown"
        )
        
        self.logger.info("Milo MCP Server initialized with 4 tools and 3 resources")
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute tool using legacy tool classes if function not provided"""
        if tool_name == "meal_planner":
            return await self._plan_meals(arguments)
        elif tool_name == "nutrition_analyzer":
            return await self._analyze_nutrition(arguments)
        elif tool_name == "recipe_generator":
            return await self._generate_recipe(arguments)
        elif tool_name == "meal_optimizer":
            return await self._optimize_meals(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _plan_meals(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Plan meals based on dietary requirements"""
        try:
            # Extract parameters
            calories_target = arguments.get("calories_target")
            dietary_restrictions = arguments.get("dietary_restrictions", [])
            meals_per_day = arguments.get("meals_per_day", 3)
            days = arguments.get("days", 7)
            cuisine_preferences = arguments.get("cuisine_preferences", [])
            exclude_ingredients = arguments.get("exclude_ingredients", [])
            
            # Generate meal plan (mock implementation)
            meal_plan = {
                "plan_id": f"plan_{int(datetime.now().timestamp())}",
                "target_calories": calories_target,
                "dietary_restrictions": dietary_restrictions,
                "duration_days": days,
                "meals_per_day": meals_per_day,
                "daily_plans": []
            }
            
            # Generate daily meal plans
            for day in range(days):
                daily_plan = {
                    "day": day + 1,
                    "date": (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d")),
                    "meals": [],
                    "total_calories": 0,
                    "macros": {"protein": 0, "carbs": 0, "fat": 0}
                }
                
                # Distribute calories across meals
                calories_per_meal = calories_target // meals_per_day
                
                meal_types = ["breakfast", "lunch", "dinner", "snack"][:meals_per_day]
                
                for i, meal_type in enumerate(meal_types):
                    meal = {
                        "meal_type": meal_type,
                        "time": ["08:00", "12:00", "18:00", "15:00"][i],
                        "recipes": [
                            {
                                "name": f"Healthy {meal_type.title()}",
                                "ingredients": ["ingredient1", "ingredient2", "ingredient3"],
                                "calories": calories_per_meal,
                                "prep_time": 20,
                                "difficulty": "medium",
                                "macros": {
                                    "protein": calories_per_meal * 0.2 // 4,
                                    "carbs": calories_per_meal * 0.5 // 4,
                                    "fat": calories_per_meal * 0.3 // 9
                                }
                            }
                        ],
                        "total_calories": calories_per_meal
                    }
                    daily_plan["meals"].append(meal)
                    daily_plan["total_calories"] += calories_per_meal
                
                meal_plan["daily_plans"].append(daily_plan)
            
            # Add shopping list
            meal_plan["shopping_list"] = {
                "categories": {
                    "proteins": ["chicken breast", "salmon", "tofu"],
                    "vegetables": ["broccoli", "spinach", "bell peppers"],
                    "grains": ["quinoa", "brown rice", "oats"],
                    "dairy": ["greek yogurt", "cheese", "milk"]
                },
                "estimated_cost": calories_target * days * 0.002  # Mock cost calculation
            }
            
            return {
                "success": True,
                "meal_plan": meal_plan,
                "summary": f"Generated {days}-day meal plan with {calories_target} calories/day"
            }
            
        except Exception as e:
            self.logger.error(f"Meal planning error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate meal plan"
            }
    
    async def _analyze_nutrition(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze nutritional content"""
        try:
            food_items = arguments.get("food_items", [])
            recipe = arguments.get("recipe")
            analysis_type = arguments.get("analysis_type", "basic")
            
            if recipe:
                # Analyze recipe
                nutrition_analysis = {
                    "item_type": "recipe",
                    "name": recipe.get("name", "Unknown Recipe"),
                    "servings": recipe.get("servings", 1),
                    "per_serving": {
                        "calories": 350,
                        "protein": 25,
                        "carbohydrates": 30,
                        "fat": 15,
                        "fiber": 8,
                        "sugar": 5,
                        "sodium": 400
                    },
                    "total": {
                        "calories": 350 * recipe.get("servings", 1),
                        "protein": 25 * recipe.get("servings", 1),
                        "carbohydrates": 30 * recipe.get("servings", 1),
                        "fat": 15 * recipe.get("servings", 1)
                    }
                }
                
                if analysis_type == "detailed":
                    nutrition_analysis["vitamins"] = {
                        "vitamin_a": "15% DV",
                        "vitamin_c": "25% DV",
                        "calcium": "12% DV",
                        "iron": "18% DV"
                    }
                    nutrition_analysis["health_score"] = 8.5
                    nutrition_analysis["allergens"] = ["gluten", "dairy"]
            
            else:
                # Analyze food items
                nutrition_analysis = {
                    "item_type": "food_items",
                    "items": [],
                    "total_nutrition": {
                        "calories": 0,
                        "protein": 0,
                        "carbohydrates": 0,
                        "fat": 0
                    }
                }
                
                for item in food_items:
                    item_nutrition = {
                        "name": item,
                        "calories": 100,  # Mock values
                        "protein": 5,
                        "carbohydrates": 15,
                        "fat": 3,
                        "serving_size": "100g"
                    }
                    nutrition_analysis["items"].append(item_nutrition)
                    
                    # Add to totals
                    for nutrient in ["calories", "protein", "carbohydrates", "fat"]:
                        nutrition_analysis["total_nutrition"][nutrient] += item_nutrition[nutrient]
            
            return {
                "success": True,
                "analysis": nutrition_analysis,
                "analysis_type": analysis_type,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Nutrition analysis error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to analyze nutrition"
            }
    
    async def _generate_recipe(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recipe from ingredients"""
        try:
            ingredients = arguments.get("ingredients", [])
            recipe_type = arguments.get("recipe_type")
            cooking_time = arguments.get("cooking_time", 30)
            difficulty = arguments.get("difficulty", "medium")
            dietary_requirements = arguments.get("dietary_requirements", [])
            cuisine_style = arguments.get("cuisine_style", "international")
            
            # Generate recipe (mock implementation)
            recipe = {
                "id": f"recipe_{int(datetime.now().timestamp())}",
                "name": f"Delicious {recipe_type.title()}",
                "description": f"A {difficulty} {cuisine_style} {recipe_type} made with available ingredients",
                "cuisine": cuisine_style,
                "recipe_type": recipe_type,
                "difficulty": difficulty,
                "prep_time": max(10, cooking_time // 3),
                "cook_time": cooking_time,
                "total_time": max(10, cooking_time // 3) + cooking_time,
                "servings": 4,
                "dietary_info": {
                    "requirements_met": dietary_requirements,
                    "calories_per_serving": 280,
                    "allergens": []
                },
                "ingredients_used": ingredients[:6],  # Use up to 6 ingredients
                "additional_ingredients": ["salt", "pepper", "olive oil"],
                "instructions": [
                    "Prepare all ingredients by washing and chopping as needed",
                    "Heat cooking surface to medium temperature",
                    "Combine main ingredients according to recipe requirements",
                    "Cook according to timing specifications",
                    "Season to taste and serve immediately"
                ],
                "nutrition": {
                    "calories": 280,
                    "protein": 18,
                    "carbohydrates": 25,
                    "fat": 12,
                    "fiber": 6
                },
                "tips": [
                    f"This recipe works best with fresh {ingredients[0] if ingredients else 'ingredients'}",
                    "Can be prepared ahead of time and reheated",
                    "Adjust seasoning to personal preference"
                ]
            }
            
            return {
                "success": True,
                "recipe": recipe,
                "ingredients_used": len(ingredients),
                "estimated_cost": len(ingredients) * 2.5,
                "message": f"Generated {recipe_type} recipe using {len(ingredients)} available ingredients"
            }
            
        except Exception as e:
            self.logger.error(f"Recipe generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate recipe"
            }
    
    async def _optimize_meals(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize meal plans"""
        try:
            current_meal_plan = arguments.get("current_meal_plan", {})
            optimization_goals = arguments.get("optimization_goals", [])
            budget_constraint = arguments.get("budget_constraint")
            prep_time_limit = arguments.get("prep_time_limit")
            
            optimizations_applied = []
            optimized_plan = current_meal_plan.copy()
            
            # Apply optimizations based on goals
            if "cost" in optimization_goals and budget_constraint:
                optimizations_applied.append("Reduced ingredient costs by substituting premium items")
                optimized_plan["estimated_cost"] = min(
                    current_meal_plan.get("estimated_cost", 100),
                    budget_constraint
                )
            
            if "time" in optimization_goals and prep_time_limit:
                optimizations_applied.append("Simplified recipes to meet time constraints")
                optimized_plan["avg_prep_time"] = min(30, prep_time_limit)
            
            if "nutrition" in optimization_goals:
                optimizations_applied.append("Balanced macronutrients and increased vegetable content")
                optimized_plan["nutrition_score"] = 9.2
            
            if "variety" in optimization_goals:
                optimizations_applied.append("Increased cuisine diversity and ingredient rotation")
                optimized_plan["cuisine_diversity"] = 85
            
            optimization_summary = {
                "original_plan_id": current_meal_plan.get("plan_id", "unknown"),
                "optimized_plan_id": f"opt_{int(datetime.now().timestamp())}",
                "optimization_goals": optimization_goals,
                "optimizations_applied": optimizations_applied,
                "improvements": {
                    "cost_savings": "15%" if "cost" in optimization_goals else "0%",
                    "time_savings": "25%" if "time" in optimization_goals else "0%",
                    "nutrition_improvement": "12%" if "nutrition" in optimization_goals else "0%",
                    "variety_increase": "30%" if "variety" in optimization_goals else "0%"
                }
            }
            
            return {
                "success": True,
                "optimized_plan": optimized_plan,
                "optimization_summary": optimization_summary,
                "message": f"Applied {len(optimizations_applied)} optimizations to meal plan"
            }
            
        except Exception as e:
            self.logger.error(f"Meal optimization error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to optimize meal plan"
            }
    
    async def _read_resource(self, uri: str) -> str:
        """Read resource content"""
        if uri == "milo://nutrition-database":
            return json.dumps({
                "database": "USDA Food Database",
                "foods_count": 15000,
                "last_updated": "2025-08-10",
                "sample_foods": [
                    {"name": "Apple", "calories_per_100g": 52, "nutrients": {"vitamin_c": 4.6}},
                    {"name": "Chicken Breast", "calories_per_100g": 165, "nutrients": {"protein": 31}}
                ]
            }, indent=2)
        
        elif uri == "milo://recipe-database":
            return json.dumps({
                "recipes_count": 5000,
                "categories": ["breakfast", "lunch", "dinner", "snacks", "desserts"],
                "sample_recipes": [
                    {"name": "Quinoa Buddha Bowl", "calories": 380, "prep_time": 25},
                    {"name": "Grilled Salmon", "calories": 290, "prep_time": 15}
                ]
            }, indent=2)
        
        elif uri == "milo://dietary-guidelines":
            return """# Dietary Guidelines

## Daily Caloric Needs
- Adult Women: 1800-2400 calories
- Adult Men: 2200-3000 calories

## Macronutrient Distribution
- Carbohydrates: 45-65% of total calories
- Protein: 10-35% of total calories  
- Fat: 20-35% of total calories

## Key Recommendations
- Include variety of vegetables and fruits
- Choose whole grains over refined grains
- Include lean proteins and healthy fats
- Limit added sugars and sodium
"""
        
        else:
            raise ValueError(f"Unknown resource: {uri}")


async def main():
    """Run Milo MCP Server"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = MiloMCPServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())