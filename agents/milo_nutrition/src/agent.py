"""
Agent Milo - Core Agent Implementation
Meal Planning & Nutrition Agent
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

from shared.mcp_framework.base_server import BaseMCPServer, ExecutionContext
from shared.a2a_protocol.message_router import A2AMessage

# Import Milo's tools
from agents.milo_nutrition.tools.recipe_engine import RecipeEngineTool
from agents.milo_nutrition.tools.nutrition_analyzer import NutritionAnalyzerTool
from agents.milo_nutrition.tools.meal_planner import MealPlannerTool

class MiloAgent(BaseMCPServer):
    """Agent Milo - Meal Planning & Nutrition"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("milo", 8003, config)
        
        # Register all Milo's tools
        self.register_tool(RecipeEngineTool())
        self.register_tool(NutritionAnalyzerTool())
        self.register_tool(MealPlannerTool())
        
        self.logger.info("Agent Milo initialized with 3 tools")
    
    async def process_a2a_message(self, message_data: dict) -> Dict[str, Any]:
        """Process incoming A2A messages from other agents"""
        try:
            message = A2AMessage(**message_data)
            self.logger.info(f"Milo received: {message.intent} from {message.from_agent}")
            
            if message.intent == "create_meal_plan":
                return await self._create_meal_plan(message)
            elif message.intent == "analyze_nutrition_goals":
                return await self._analyze_nutrition_for_goals(message)
            elif message.intent == "find_recipes_with_ingredients":
                return await self._find_recipes_for_ingredients(message)
            elif message.intent == "optimize_meal_prep":
                return await self._optimize_meal_prep_schedule(message)
            elif message.intent == "evaluate_dietary_compliance":
                return await self._evaluate_dietary_compliance(message)
            else:
                return {
                    "success": False, 
                    "error": f"Unknown intent: {message.intent}",
                    "agent": "milo"
                }
                
        except Exception as e:
            self.logger.error(f"A2A message processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": "milo"
            }
    
    async def _create_meal_plan(self, message: A2AMessage) -> Dict[str, Any]:
        """Create a comprehensive meal plan based on requirements"""
        payload = message.payload
        
        meal_planner_tool = self.tools["meal_planner"]
        context = ExecutionContext(
            user_id=payload.get("user_id", "default"),
            session_id=message.session_id,
            permissions=["read", "write"]
        )
        
        # Create meal plan with provided parameters
        meal_plan_result = await meal_planner_tool.execute({
            "action": "create_weekly_plan",
            "dietary_goals": payload.get("dietary_goals", {}),
            "available_ingredients": payload.get("available_ingredients", []),
            "budget_constraint": payload.get("budget_constraint", 100),
            "time_constraints": payload.get("time_constraints", {}),
            "family_preferences": payload.get("family_preferences", {})
        }, context)
        
        if meal_plan_result.success:
            return {
                "success": True,
                "meal_plan": meal_plan_result.result["meal_plan"],
                "nutrition_summary": meal_plan_result.result.get("nutrition_summary", {}),
                "shopping_list": meal_plan_result.result.get("shopping_list", []),
                "prep_schedule": meal_plan_result.result.get("prep_schedule", {}),
                "agent": "milo"
            }
        else:
            return {"success": False, "error": meal_plan_result.error, "agent": "milo"}
    
    async def _analyze_nutrition_for_goals(self, message: A2AMessage) -> Dict[str, Any]:
        """Analyze nutrition requirements for specific fitness/health goals"""
        payload = message.payload
        fitness_goals = payload.get("fitness_goals", [])
        current_metrics = payload.get("current_metrics", {})
        
        nutrition_analyzer = self.tools["nutrition_analyzer"]
        context = ExecutionContext(
            user_id=payload.get("user_id", "default"),
            session_id=message.session_id,
            permissions=["read"]
        )
        
        # Analyze nutrition needs based on goals
        analysis_result = await nutrition_analyzer.execute({
            "action": "calculate_requirements",
            "fitness_goals": fitness_goals,
            "current_metrics": current_metrics,
            "activity_level": payload.get("activity_level", "moderate"),
            "dietary_restrictions": payload.get("dietary_restrictions", [])
        }, context)
        
        if analysis_result.success:
            return {
                "success": True,
                "nutrition_requirements": analysis_result.result,
                "goal_alignment": self._assess_goal_alignment(fitness_goals, analysis_result.result),
                "meal_timing_recommendations": self._get_meal_timing_for_goals(fitness_goals),
                "agent": "milo"
            }
        else:
            return {"success": False, "error": analysis_result.error, "agent": "milo"}
    
    async def _find_recipes_for_ingredients(self, message: A2AMessage) -> Dict[str, Any]:
        """Find recipes based on available ingredients"""
        payload = message.payload
        available_ingredients = payload.get("available_ingredients", [])
        expiring_items = payload.get("expiring_items", [])
        
        recipe_engine = self.tools["recipe_engine"]
        context = ExecutionContext(
            user_id=payload.get("user_id", "default"),
            session_id=message.session_id,
            permissions=["read"]
        )
        
        # Prioritize recipes using expiring ingredients
        search_ingredients = expiring_items + available_ingredients
        
        recipe_result = await recipe_engine.execute({
            "action": "find_recipes",
            "available_ingredients": search_ingredients,
            "dietary_restrictions": payload.get("dietary_restrictions", []),
            "cuisine_preferences": payload.get("cuisine_preferences", []),
            "cooking_time": payload.get("max_cooking_time", 60),
            "difficulty_level": payload.get("difficulty_level", "easy")
        }, context)
        
        if recipe_result.success:
            recipes = recipe_result.result["recipes"]
            # Prioritize recipes that use expiring ingredients
            prioritized_recipes = self._prioritize_recipes_by_expiry(recipes, expiring_items)
            
            return {
                "success": True,
                "recipes": prioritized_recipes,
                "expiring_ingredient_usage": self._calculate_expiry_usage(recipes, expiring_items),
                "meal_suggestions": self._suggest_meals_from_recipes(prioritized_recipes),
                "agent": "milo"
            }
        else:
            return {"success": False, "error": recipe_result.error, "agent": "milo"}
    
    async def _optimize_meal_prep_schedule(self, message: A2AMessage) -> Dict[str, Any]:
        """Optimize meal prep schedule with Nani's calendar coordination"""
        payload = message.payload
        meal_plan = payload.get("meal_plan", {})
        available_time_slots = payload.get("available_time_slots", [])
        
        # Calculate prep time requirements
        prep_schedule = {}
        total_prep_time = 0
        
        for day, meals in meal_plan.items():
            if isinstance(meals, dict):
                day_prep_time = 0
                for meal_type, meal_info in meals.items():
                    prep_time = meal_info.get("prep_time", 15) if isinstance(meal_info, dict) else 15
                    day_prep_time += prep_time
                
                prep_schedule[day] = {
                    "total_prep_time": day_prep_time,
                    "recommended_prep_time": self._suggest_prep_time(day, day_prep_time),
                    "batch_opportunities": self._identify_batch_cooking(meals)
                }
                total_prep_time += day_prep_time
        
        # Optimize for batch cooking
        batch_schedule = self._create_batch_cooking_schedule(prep_schedule)
        
        return {
            "success": True,
            "prep_schedule": prep_schedule,
            "batch_cooking_plan": batch_schedule,
            "total_weekly_prep_time": total_prep_time,
            "time_saving_opportunities": self._identify_time_savings(prep_schedule),
            "kitchen_equipment_needs": self._assess_equipment_needs(meal_plan),
            "agent": "milo"
        }
    
    async def _evaluate_dietary_compliance(self, message: A2AMessage) -> Dict[str, Any]:
        """Evaluate how well current meal plan meets dietary goals"""
        payload = message.payload
        meal_plan = payload.get("meal_plan", {})
        dietary_goals = payload.get("dietary_goals", {})
        health_targets = payload.get("health_targets", {})
        
        nutrition_analyzer = self.tools["nutrition_analyzer"]
        context = ExecutionContext(
            user_id=payload.get("user_id", "default"),
            session_id=message.session_id,
            permissions=["read"]
        )
        
        # Analyze current meal plan compliance
        compliance_result = await nutrition_analyzer.execute({
            "action": "evaluate_compliance",
            "meal_plan": meal_plan,
            "dietary_goals": dietary_goals,
            "health_targets": health_targets
        }, context)
        
        if compliance_result.success:
            compliance_data = compliance_result.result
            
            return {
                "success": True,
                "compliance_score": compliance_data.get("overall_score", 0),
                "goal_adherence": compliance_data.get("goal_adherence", {}),
                "nutritional_gaps": compliance_data.get("gaps", []),
                "recommendations": compliance_data.get("recommendations", []),
                "meal_adjustments": self._suggest_meal_adjustments(compliance_data),
                "agent": "milo"
            }
        else:
            return {"success": False, "error": compliance_result.error, "agent": "milo"}
    
    def _assess_goal_alignment(self, fitness_goals: List[str], nutrition_data: Dict) -> Dict[str, Any]:
        """Assess how well nutrition plan aligns with fitness goals"""
        alignment_score = 0.8  # Mock calculation
        
        alignment_details = {}
        for goal in fitness_goals:
            if goal == "muscle_gain":
                protein_adequate = nutrition_data.get("protein_grams", 0) > 100
                alignment_details[goal] = {
                    "score": 0.9 if protein_adequate else 0.6,
                    "key_factors": ["protein_intake", "calorie_surplus", "meal_timing"]
                }
            elif goal == "weight_loss":
                calorie_deficit = nutrition_data.get("daily_calories", 2000) < 1800
                alignment_details[goal] = {
                    "score": 0.85 if calorie_deficit else 0.5,
                    "key_factors": ["calorie_deficit", "protein_preservation", "nutrient_density"]
                }
        
        return {
            "overall_alignment": alignment_score,
            "goal_specific": alignment_details,
            "optimization_opportunities": ["Increase protein timing around workouts", "Add more vegetables"]
        }
    
    def _get_meal_timing_for_goals(self, fitness_goals: List[str]) -> Dict[str, Any]:
        """Get meal timing recommendations based on fitness goals"""
        timing_recommendations = {
            "general": {
                "breakfast": "7:00-9:00",
                "lunch": "12:00-14:00",
                "dinner": "18:00-20:00",
                "snacks": ["10:00", "15:00"]
            }
        }
        
        if "muscle_gain" in fitness_goals:
            timing_recommendations["muscle_gain"] = {
                "pre_workout": "30-60 minutes before training",
                "post_workout": "within 30 minutes after training",
                "protein_frequency": "every 3-4 hours",
                "evening_protein": "casein protein before bed"
            }
        
        if "endurance" in fitness_goals:
            timing_recommendations["endurance"] = {
                "pre_workout": "2-3 hours before long sessions",
                "during_workout": "carbs every 45-60 minutes",
                "post_workout": "carbs and protein within 2 hours",
                "hydration": "continuous throughout day"
            }
        
        return timing_recommendations
    
    def _prioritize_recipes_by_expiry(self, recipes: List[Dict], expiring_items: List[str]) -> List[Dict]:
        """Prioritize recipes that use expiring ingredients"""
        prioritized = []
        
        for recipe in recipes:
            expiry_score = 0
            recipe_ingredients = recipe.get("ingredients", [])
            
            for ingredient in recipe_ingredients:
                if any(expiring in ingredient.lower() for expiring in expiring_items):
                    expiry_score += 1
            
            recipe["expiry_priority_score"] = expiry_score
            prioritized.append(recipe)
        
        return sorted(prioritized, key=lambda x: x["expiry_priority_score"], reverse=True)
    
    def _calculate_expiry_usage(self, recipes: List[Dict], expiring_items: List[str]) -> Dict[str, Any]:
        """Calculate how well recipes use expiring ingredients"""
        usage_stats = {}
        
        for item in expiring_items:
            usage_count = 0
            for recipe in recipes:
                recipe_ingredients = recipe.get("ingredients", [])
                if any(item.lower() in ingredient.lower() for ingredient in recipe_ingredients):
                    usage_count += 1
            
            usage_stats[item] = {
                "recipes_using": usage_count,
                "utilization_rate": min(usage_count / len(recipes), 1.0) if recipes else 0
            }
        
        return usage_stats
    
    def _suggest_meals_from_recipes(self, recipes: List[Dict]) -> Dict[str, List[str]]:
        """Suggest meal assignments for recipes"""
        meal_suggestions = {
            "breakfast": [],
            "lunch": [],
            "dinner": [],
            "snacks": []
        }
        
        for recipe in recipes[:6]:  # Top 6 recipes
            cooking_time = recipe.get("cooking_time", 30)
            recipe_type = recipe.get("type", "main")
            
            if cooking_time <= 15 and "breakfast" in recipe.get("name", "").lower():
                meal_suggestions["breakfast"].append(recipe["name"])
            elif "salad" in recipe.get("name", "").lower() or cooking_time <= 20:
                meal_suggestions["lunch"].append(recipe["name"])
            elif cooking_time > 20:
                meal_suggestions["dinner"].append(recipe["name"])
            else:
                meal_suggestions["snacks"].append(recipe["name"])
        
        return meal_suggestions
    
    def _suggest_prep_time(self, day: str, prep_time: int) -> str:
        """Suggest optimal prep time for a day"""
        if day in ["sunday", "saturday"]:
            return "14:00"  # Weekend afternoon prep
        elif prep_time > 30:
            return "19:00"  # Evening for longer prep
        else:
            return "18:30"  # Standard dinner prep
    
    def _identify_batch_cooking(self, meals: Dict) -> List[str]:
        """Identify batch cooking opportunities"""
        opportunities = []
        
        # Look for similar cooking methods or base ingredients
        if any("rice" in str(meal).lower() for meal in meals.values()):
            opportunities.append("Cook rice in large batch")
        
        if any("chicken" in str(meal).lower() for meal in meals.values()):
            opportunities.append("Prep chicken proteins together")
        
        return opportunities
    
    def _create_batch_cooking_schedule(self, prep_schedule: Dict) -> Dict[str, Any]:
        """Create optimized batch cooking schedule"""
        return {
            "sunday_batch_prep": {
                "time": "14:00-16:00",
                "tasks": ["Cook grains", "Prep proteins", "Wash and chop vegetables"],
                "estimated_time": 120
            },
            "mid_week_prep": {
                "time": "wednesday 18:00",
                "tasks": ["Refresh vegetables", "Quick protein prep"],
                "estimated_time": 30
            }
        }
    
    def _identify_time_savings(self, prep_schedule: Dict) -> List[str]:
        """Identify time-saving opportunities"""
        return [
            "Batch cook grains and proteins on Sunday",
            "Pre-chop vegetables for the week",
            "Use slow cooker for hands-off cooking",
            "Prepare overnight oats for quick breakfasts"
        ]
    
    def _assess_equipment_needs(self, meal_plan: Dict) -> List[str]:
        """Assess kitchen equipment needs for meal plan"""
        equipment = set()
        
        # Mock assessment based on meal types
        equipment.update(["cutting_board", "chef_knife", "measuring_cups"])
        
        # Add equipment based on cooking methods
        if any("bake" in str(meal).lower() for day_meals in meal_plan.values() for meal in day_meals.values()):
            equipment.add("baking_sheets")
        
        if any("stir" in str(meal).lower() for day_meals in meal_plan.values() for meal in day_meals.values()):
            equipment.add("wok_or_large_pan")
        
        return list(equipment)
    
    def _suggest_meal_adjustments(self, compliance_data: Dict) -> List[Dict[str, Any]]:
        """Suggest specific meal adjustments based on compliance analysis"""
        adjustments = []
        
        gaps = compliance_data.get("gaps", [])
        for gap in gaps:
            if gap == "insufficient_protein":
                adjustments.append({
                    "issue": "Low protein intake",
                    "suggestion": "Add Greek yogurt to breakfast and legumes to lunch",
                    "impact": "Increase daily protein by 20g"
                })
            elif gap == "low_fiber":
                adjustments.append({
                    "issue": "Insufficient fiber",
                    "suggestion": "Include more vegetables and whole grains",
                    "impact": "Improve digestive health and satiety"
                })
        
        return adjustments