"""
Recipe Engine Tool for Agent Milo
Intelligent recipe discovery and management
"""

from datetime import datetime
from typing import Dict, List, Any
import json

from shared.mcp_framework.base_server import BaseMCPTool, ExecutionContext, ExecutionResult

class RecipeEngineTool(BaseMCPTool):
    """Intelligent recipe discovery and management"""
    
    def __init__(self):
        super().__init__("recipe_engine", "Discover and manage recipes based on available ingredients")
        self.recipe_cache = {}
        self.user_preferences = {}
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["find_recipes", "analyze_recipe", "scale_recipe", "substitute_ingredients", "save_recipe"]
                },
                "available_ingredients": {"type": "array"},
                "dietary_restrictions": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["vegetarian", "vegan", "gluten_free", "dairy_free", "nut_free", "low_carb", "keto"]
                    }
                },
                "cuisine_preferences": {"type": "array"},
                "cooking_time": {"type": "integer"},
                "difficulty_level": {"type": "string", "enum": ["easy", "medium", "hard"]},
                "recipe_id": {"type": "string"},
                "servings": {"type": "integer"},
                "nutritional_goals": {"type": "object"}
            },
            "required": ["action"]
        }
    
    def get_return_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "recipes": {"type": "array"},
                "recipe_analysis": {"type": "object"},
                "scaled_recipe": {"type": "object"},
                "substitutions": {"type": "array"},
                "saved_recipes": {"type": "array"}
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        action = parameters["action"]
        
        try:
            if action == "find_recipes":
                result = await self._find_recipes_by_ingredients(
                    parameters.get("available_ingredients", []),
                    parameters.get("dietary_restrictions", []),
                    parameters.get("cooking_time", 60),
                    parameters.get("cuisine_preferences", []),
                    context
                )
            elif action == "analyze_recipe":
                result = await self._analyze_recipe_nutrition(
                    parameters.get("recipe_id"), 
                    context
                )
            elif action == "scale_recipe":
                result = await self._scale_recipe_portions(
                    parameters.get("recipe_id"),
                    parameters.get("servings", 4),
                    context
                )
            elif action == "substitute_ingredients":
                result = await self._suggest_ingredient_substitutions(
                    parameters.get("recipe_id"),
                    parameters.get("available_ingredients", []),
                    context
                )
            else:  # save_recipe
                result = await self._save_user_recipe(
                    parameters.get("recipe_data", {}),
                    context
                )
            
            return ExecutionResult(success=True, result=result, execution_time=1.2)
            
        except Exception as e:
            self.logger.error(f"Recipe engine failed: {e}")
            return ExecutionResult(success=False, error=str(e), execution_time=0.0)
    
    async def _find_recipes_by_ingredients(self, ingredients: List[str], restrictions: List[str], 
                                         max_time: int, cuisines: List[str], context: ExecutionContext) -> Dict[str, Any]:
        """Find recipes based on available ingredients"""
        # Mock recipe database - would integrate with Spoonacular API
        all_recipes = [
            {
                "id": "recipe_001",
                "title": "Mediterranean Quinoa Bowl",
                "ingredients": ["quinoa", "tomatoes", "cucumber", "feta", "olive oil", "lemon"],
                "missing_ingredients": [],
                "cooking_time": 25,
                "difficulty": "easy",
                "cuisine": "mediterranean",
                "nutrition": {
                    "calories": 420,
                    "protein": 15,
                    "carbs": 52,
                    "fat": 16,
                    "fiber": 8,
                    "sugar": 8
                },
                "dietary_tags": ["vegetarian", "gluten_free"],
                "ingredient_match_score": 0.95,
                "estimated_cost": 8.50,
                "prep_time": 15,
                "cook_time": 10,
                "servings": 2
            },
            {
                "id": "recipe_002",
                "title": "Chicken Stir Fry",
                "ingredients": ["chicken breast", "broccoli", "bell peppers", "soy sauce", "ginger", "garlic"],
                "missing_ingredients": ["sesame oil"],
                "cooking_time": 20,
                "difficulty": "easy",
                "cuisine": "asian",
                "nutrition": {
                    "calories": 380,
                    "protein": 35,
                    "carbs": 28,
                    "fat": 12,
                    "fiber": 6,
                    "sugar": 12
                },
                "dietary_tags": ["high_protein", "low_carb"],
                "ingredient_match_score": 0.88,
                "estimated_cost": 12.00,
                "prep_time": 15,
                "cook_time": 5,
                "servings": 3
            },
            {
                "id": "recipe_003",
                "title": "Vegan Buddha Bowl",
                "ingredients": ["chickpeas", "sweet potato", "spinach", "tahini", "lemon", "quinoa"],
                "missing_ingredients": [],
                "cooking_time": 35,
                "difficulty": "medium",
                "cuisine": "healthy",
                "nutrition": {
                    "calories": 450,
                    "protein": 18,
                    "carbs": 65,
                    "fat": 14,
                    "fiber": 12,
                    "sugar": 10
                },
                "dietary_tags": ["vegan", "vegetarian", "gluten_free", "high_fiber"],
                "ingredient_match_score": 0.92,
                "estimated_cost": 9.00,
                "prep_time": 20,
                "cook_time": 15,
                "servings": 2
            }
        ]
        
        # Filter by dietary restrictions
        filtered_recipes = []
        for recipe in all_recipes:
            # Check dietary restrictions
            if restrictions:
                if not any(tag in recipe["dietary_tags"] for tag in restrictions):
                    continue
            
            # Check cooking time
            if recipe["cooking_time"] > max_time:
                continue
            
            # Check cuisine preferences
            if cuisines and recipe["cuisine"] not in cuisines:
                continue
            
            # Calculate ingredient match
            available_set = set(ingredients)
            required_set = set(recipe["ingredients"])
            missing = required_set - available_set
            recipe["missing_ingredients"] = list(missing)
            recipe["ingredient_match_score"] = len(required_set - missing) / len(required_set)
            
            if recipe["ingredient_match_score"] >= 0.7:  # At least 70% match
                filtered_recipes.append(recipe)
        
        # Sort by match score and other factors
        filtered_recipes.sort(key=lambda x: (x["ingredient_match_score"], -x["cooking_time"]), reverse=True)
        
        return {
            "recipes": filtered_recipes[:10],  # Return top 10
            "total_found": len(filtered_recipes),
            "search_criteria": {
                "ingredients": ingredients,
                "restrictions": restrictions,
                "max_cooking_time": max_time,
                "cuisines": cuisines
            }
        }
    
    async def _analyze_recipe_nutrition(self, recipe_id: str, context: ExecutionContext) -> Dict[str, Any]:
        """Analyze nutritional content of a recipe"""
        # Mock nutrition analysis
        nutrition_analysis = {
            "recipe_id": recipe_id,
            "nutritional_breakdown": {
                "macros": {
                    "protein": {"grams": 25, "calories": 100, "percentage": 24},
                    "carbs": {"grams": 45, "calories": 180, "percentage": 43},
                    "fat": {"grams": 15, "calories": 135, "percentage": 33}
                },
                "micros": {
                    "vitamin_c": {"amount": "75mg", "daily_value": 83},
                    "iron": {"amount": "8mg", "daily_value": 44},
                    "calcium": {"amount": "200mg", "daily_value": 20},
                    "fiber": {"amount": "12g", "daily_value": 48}
                },
                "calories_per_serving": 420,
                "glycemic_index": "medium",
                "sodium": {"amount": "650mg", "daily_value": 28}
            },
            "health_score": 8.5,
            "diet_compatibility": {
                "weight_loss": "excellent",
                "muscle_gain": "good",
                "heart_healthy": "excellent",
                "diabetic_friendly": "good"
            },
            "recommendations": [
                "Great source of complete protein",
                "High fiber content supports digestive health",
                "Consider reducing sodium for heart health"
            ]
        }
        
        return {"recipe_analysis": nutrition_analysis}
    
    async def _scale_recipe_portions(self, recipe_id: str, new_servings: int, context: ExecutionContext) -> Dict[str, Any]:
        """Scale recipe ingredients for different serving sizes"""
        # Mock recipe scaling
        original_servings = 2
        scale_factor = new_servings / original_servings
        
        scaled_recipe = {
            "recipe_id": recipe_id,
            "original_servings": original_servings,
            "new_servings": new_servings,
            "scale_factor": scale_factor,
            "scaled_ingredients": [
                {"ingredient": "quinoa", "original": "1 cup", "scaled": f"{1 * scale_factor} cups"},
                {"ingredient": "tomatoes", "original": "2 medium", "scaled": f"{int(2 * scale_factor)} medium"},
                {"ingredient": "cucumber", "original": "1 large", "scaled": f"{int(1 * scale_factor)} large"},
                {"ingredient": "feta cheese", "original": "100g", "scaled": f"{int(100 * scale_factor)}g"},
                {"ingredient": "olive oil", "original": "2 tbsp", "scaled": f"{2 * scale_factor} tbsp"}
            ],
            "cooking_adjustments": {
                "prep_time": f"{int(15 * (1 + (scale_factor - 1) * 0.3))} minutes",
                "cook_time": "10 minutes (unchanged)",
                "pan_size": "large" if scale_factor > 2 else "medium"
            },
            "nutrition_per_serving": {
                "calories": 420,  # Per serving stays the same
                "protein": 15,
                "carbs": 52,
                "fat": 16
            }
        }
        
        return {"scaled_recipe": scaled_recipe}
    
    async def _suggest_ingredient_substitutions(self, recipe_id: str, available_ingredients: List[str], context: ExecutionContext) -> Dict[str, Any]:
        """Suggest ingredient substitutions based on what's available"""
        # Mock substitution suggestions
        substitutions = [
            {
                "original_ingredient": "quinoa",
                "substitutes": [
                    {"ingredient": "brown rice", "ratio": "1:1", "impact": "slightly more carbs"},
                    {"ingredient": "bulgur wheat", "ratio": "1:1", "impact": "similar nutrition"},
                    {"ingredient": "couscous", "ratio": "1:1", "impact": "less protein"}
                ],
                "available": "brown rice" in available_ingredients
            },
            {
                "original_ingredient": "feta cheese",
                "substitutes": [
                    {"ingredient": "goat cheese", "ratio": "1:1", "impact": "creamier texture"},
                    {"ingredient": "cottage cheese", "ratio": "1:1", "impact": "higher protein"},
                    {"ingredient": "nutritional yeast", "ratio": "2 tbsp", "impact": "vegan option"}
                ],
                "available": any(sub in available_ingredients for sub in ["goat cheese", "cottage cheese"])
            },
            {
                "original_ingredient": "olive oil",
                "substitutes": [
                    {"ingredient": "avocado oil", "ratio": "1:1", "impact": "higher smoke point"},
                    {"ingredient": "coconut oil", "ratio": "1:1", "impact": "different flavor"},
                    {"ingredient": "butter", "ratio": "1:1", "impact": "richer taste"}
                ],
                "available": "avocado oil" in available_ingredients
            }
        ]
        
        return {
            "substitutions": substitutions,
            "recipe_id": recipe_id,
            "substitution_impact": "minimal changes to nutrition and taste",
            "difficulty_change": "none"
        }
    
    async def _save_user_recipe(self, recipe_data: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Save a user's custom recipe"""
        saved_recipe = {
            "id": f"user_recipe_{datetime.utcnow().timestamp()}",
            "title": recipe_data.get("title", "My Custom Recipe"),
            "ingredients": recipe_data.get("ingredients", []),
            "instructions": recipe_data.get("instructions", []),
            "prep_time": recipe_data.get("prep_time", 0),
            "cook_time": recipe_data.get("cook_time", 0),
            "servings": recipe_data.get("servings", 1),
            "tags": recipe_data.get("tags", []),
            "notes": recipe_data.get("notes", ""),
            "created_by": context.user_id,
            "created_at": datetime.utcnow().isoformat(),
            "rating": None,
            "times_made": 0
        }
        
        return {
            "saved_recipe": saved_recipe,
            "message": "Recipe saved successfully",
            "recipe_id": saved_recipe["id"]
        }