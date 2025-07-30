"""
Meal Planner Tool for Agent Milo
Strategic meal planning and coordination
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import random

from shared.mcp_framework.base_server import BaseMCPTool, ExecutionContext, ExecutionResult

class MealPlannerTool(BaseMCPTool):
    """Strategic meal planning and coordination"""
    
    def __init__(self):
        super().__init__("meal_planner", "Create comprehensive meal plans and optimize nutrition timing")
        self.meal_templates = self._load_meal_templates()
        self.dietary_restrictions_map = self._load_dietary_restrictions()
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create_weekly_plan", "create_monthly_plan", "optimize_meal_timing", "generate_shopping_list", "adapt_for_goals"]
                },
                "dietary_goals": {
                    "type": "object",
                    "properties": {
                        "calories_per_day": {"type": "number"},
                        "protein_grams": {"type": "number"},
                        "carb_grams": {"type": "number"},
                        "fat_grams": {"type": "number"},
                        "fiber_grams": {"type": "number"}
                    }
                },
                "dietary_restrictions": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["vegetarian", "vegan", "gluten_free", "dairy_free", "nut_free", "low_carb", "keto", "paleo"]
                    }
                },
                "available_ingredients": {"type": "array"},
                "budget_constraint": {"type": "number"},
                "time_constraints": {
                    "type": "object",
                    "properties": {
                        "prep_time_limit": {"type": "integer"},
                        "cooking_skill": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                        "busy_days": {"type": "array"}
                    }
                },
                "family_preferences": {
                    "type": "object",
                    "properties": {
                        "favorite_cuisines": {"type": "array"},
                        "disliked_foods": {"type": "array"},
                        "family_size": {"type": "integer"}
                    }
                },
                "fitness_schedule": {"type": "object"}
            },
            "required": ["action"]
        }
    
    def get_return_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "meal_plan": {"type": "object"},
                "nutrition_summary": {"type": "object"},
                "shopping_list": {"type": "array"},
                "prep_schedule": {"type": "object"},
                "cost_estimate": {"type": "number"}
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        action = parameters["action"]
        
        try:
            if action == "create_weekly_plan":
                result = await self._create_weekly_meal_plan(parameters, context)
            elif action == "create_monthly_plan":
                result = await self._create_monthly_meal_plan(parameters, context)
            elif action == "optimize_meal_timing":
                result = await self._optimize_meal_timing(parameters, context)
            elif action == "generate_shopping_list":
                result = await self._generate_shopping_list_from_plan(parameters, context)
            else:  # adapt_for_goals
                result = await self._adapt_plan_for_goals(parameters, context)
            
            return ExecutionResult(success=True, result=result, execution_time=2.0)
            
        except Exception as e:
            self.logger.error(f"Meal planning failed: {e}")
            return ExecutionResult(success=False, error=str(e), execution_time=0.0)
    
    def _load_meal_templates(self) -> Dict[str, Any]:
        """Load meal templates for different dietary needs"""
        return {
            "standard": {
                "breakfast": [
                    {"name": "Overnight Oats", "prep_time": 5, "calories": 320, "protein": 12, "carbs": 58, "fat": 8},
                    {"name": "Scrambled Eggs with Toast", "prep_time": 10, "calories": 350, "protein": 18, "carbs": 25, "fat": 20},
                    {"name": "Greek Yogurt Parfait", "prep_time": 5, "calories": 280, "protein": 15, "carbs": 35, "fat": 8}
                ],
                "lunch": [
                    {"name": "Quinoa Buddha Bowl", "prep_time": 25, "calories": 420, "protein": 15, "carbs": 52, "fat": 16},
                    {"name": "Chicken Caesar Salad", "prep_time": 15, "calories": 380, "protein": 32, "carbs": 12, "fat": 22},
                    {"name": "Turkey Sandwich", "prep_time": 5, "calories": 340, "protein": 24, "carbs": 35, "fat": 12}
                ],
                "dinner": [
                    {"name": "Grilled Salmon with Vegetables", "prep_time": 30, "calories": 480, "protein": 35, "carbs": 20, "fat": 28},
                    {"name": "Chicken Stir Fry", "prep_time": 20, "calories": 380, "protein": 32, "carbs": 28, "fat": 15},
                    {"name": "Lean Beef with Sweet Potato", "prep_time": 35, "calories": 450, "protein": 30, "carbs": 35, "fat": 18}
                ],
                "snacks": [
                    {"name": "Apple with Almond Butter", "prep_time": 2, "calories": 190, "protein": 6, "carbs": 20, "fat": 12},
                    {"name": "Greek Yogurt", "prep_time": 1, "calories": 150, "protein": 15, "carbs": 12, "fat": 5},
                    {"name": "Trail Mix", "prep_time": 1, "calories": 160, "protein": 5, "carbs": 15, "fat": 10}
                ]
            },
            "vegetarian": {
                "breakfast": [
                    {"name": "Smoothie Bowl", "prep_time": 8, "calories": 350, "protein": 12, "carbs": 65, "fat": 8},
                    {"name": "Avocado Toast", "prep_time": 5, "calories": 320, "protein": 8, "carbs": 30, "fat": 20}
                ],
                "lunch": [
                    {"name": "Lentil Soup", "prep_time": 30, "calories": 300, "protein": 18, "carbs": 45, "fat": 5},
                    {"name": "Caprese Salad", "prep_time": 10, "calories": 250, "protein": 12, "carbs": 8, "fat": 18}
                ],
                "dinner": [
                    {"name": "Vegetable Curry", "prep_time": 35, "calories": 400, "protein": 12, "carbs": 55, "fat": 15},
                    {"name": "Stuffed Bell Peppers", "prep_time": 45, "calories": 350, "protein": 15, "carbs": 48, "fat": 10}
                ]
            },
            "low_carb": {
                "breakfast": [
                    {"name": "Veggie Omelet", "prep_time": 12, "calories": 280, "protein": 20, "carbs": 8, "fat": 18},
                    {"name": "Chia Pudding", "prep_time": 5, "calories": 220, "protein": 8, "carbs": 12, "fat": 16}
                ],
                "lunch": [
                    {"name": "Zucchini Noodles with Chicken", "prep_time": 20, "calories": 320, "protein": 28, "carbs": 12, "fat": 18},
                    {"name": "Cobb Salad", "prep_time": 15, "calories": 380, "protein": 25, "carbs": 10, "fat": 28}
                ],
                "dinner": [
                    {"name": "Cauliflower Rice Stir Fry", "prep_time": 25, "calories": 300, "protein": 22, "carbs": 15, "fat": 18},
                    {"name": "Baked Cod with Asparagus", "prep_time": 25, "calories": 280, "protein": 30, "carbs": 8, "fat": 12}
                ]
            }
        }
    
    def _load_dietary_restrictions(self) -> Dict[str, List[str]]:
        """Load foods to avoid for different dietary restrictions"""
        return {
            "vegetarian": ["beef", "chicken", "pork", "fish", "seafood"],
            "vegan": ["beef", "chicken", "pork", "fish", "seafood", "dairy", "eggs", "honey"],
            "gluten_free": ["wheat", "barley", "rye", "pasta", "bread"],
            "dairy_free": ["milk", "cheese", "yogurt", "butter", "cream"],
            "nut_free": ["almonds", "peanuts", "walnuts", "cashews", "tree nuts"],
            "low_carb": ["bread", "pasta", "rice", "potatoes", "sugar"],
            "keto": ["bread", "pasta", "rice", "fruits", "sugar", "grains"]
        }
    
    async def _create_weekly_meal_plan(self, parameters: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Create optimized weekly meal plan"""
        dietary_goals = parameters.get("dietary_goals", {})
        restrictions = parameters.get("dietary_restrictions", [])
        time_constraints = parameters.get("time_constraints", {})
        family_preferences = parameters.get("family_preferences", {})
        
        # Determine meal template to use
        template_key = "standard"
        if "vegetarian" in restrictions:
            template_key = "vegetarian"
        elif "low_carb" in restrictions or "keto" in restrictions:
            template_key = "low_carb"
        
        meal_templates = self.meal_templates.get(template_key, self.meal_templates["standard"])
        
        # Create weekly schedule
        weekly_plan = {}
        total_nutrition = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
        
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        busy_days = time_constraints.get("busy_days", [])
        
        for day in days:
            daily_meals = {}
            daily_nutrition = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
            
            # Select meals based on constraints
            for meal_type in ["breakfast", "lunch", "dinner", "snacks"]:
                if meal_type in meal_templates:
                    available_meals = meal_templates[meal_type]
                    
                    # Filter by time constraints for busy days
                    if day in busy_days and meal_type in ["lunch", "dinner"]:
                        available_meals = [m for m in available_meals if m["prep_time"] <= 15]
                    
                    # Select meal
                    if available_meals:
                        selected_meal = random.choice(available_meals)
                        daily_meals[meal_type] = selected_meal
                        
                        # Add to nutrition totals
                        for nutrient in ["calories", "protein", "carbs", "fat"]:
                            daily_nutrition[nutrient] += selected_meal.get(nutrient, 0)
            
            weekly_plan[day] = {
                "meals": daily_meals,
                "daily_nutrition": daily_nutrition,
                "prep_time_total": sum(meal.get("prep_time", 0) for meal in daily_meals.values())
            }
            
            # Add to weekly totals
            for nutrient in ["calories", "protein", "carbs", "fat"]:
                total_nutrition[nutrient] += daily_nutrition[nutrient]
        
        # Calculate averages
        avg_nutrition = {k: v/7 for k, v in total_nutrition.items()}
        
        # Compare with goals
        goal_adherence = {}
        daily_calorie_goal = dietary_goals.get("calories_per_day", 2000)
        if daily_calorie_goal > 0:
            goal_adherence["calories"] = avg_nutrition["calories"] / daily_calorie_goal
        
        nutrition_summary = {
            "weekly_totals": total_nutrition,
            "daily_averages": avg_nutrition,
            "goal_adherence": goal_adherence,
            "variety_score": self._calculate_variety_score(weekly_plan),
            "health_score": self._calculate_health_score(avg_nutrition)
        }
        
        return {
            "meal_plan": weekly_plan,
            "nutrition_summary": nutrition_summary,
            "plan_duration": "7 days",
            "total_prep_time": sum(day["prep_time_total"] for day in weekly_plan.values()),
            "estimated_cost": self._estimate_weekly_cost(weekly_plan)
        }
    
    def _calculate_variety_score(self, weekly_plan: Dict) -> float:
        """Calculate variety score based on meal diversity"""
        all_meals = []
        for day_data in weekly_plan.values():
            for meal in day_data["meals"].values():
                all_meals.append(meal["name"])
        
        unique_meals = len(set(all_meals))
        total_meals = len(all_meals)
        
        return (unique_meals / total_meals) * 10 if total_meals > 0 else 0
    
    def _calculate_health_score(self, nutrition: Dict) -> float:
        """Calculate health score based on nutritional balance"""
        calories = nutrition.get("calories", 0)
        if calories == 0:
            return 0
        
        protein_percent = (nutrition.get("protein", 0) * 4 / calories) * 100
        carb_percent = (nutrition.get("carbs", 0) * 4 / calories) * 100
        fat_percent = (nutrition.get("fat", 0) * 9 / calories) * 100
        
        score = 7  # Base score
        
        # Protein adequacy (15-25% ideal)
        if 15 <= protein_percent <= 25:
            score += 1
        elif protein_percent < 10 or protein_percent > 30:
            score -= 1
        
        # Carb balance (45-65% ideal)
        if 45 <= carb_percent <= 65:
            score += 1
        elif carb_percent < 30 or carb_percent > 75:
            score -= 1
        
        # Fat balance (20-35% ideal)
        if 20 <= fat_percent <= 35:
            score += 1
        elif fat_percent < 15 or fat_percent > 40:
            score -= 1
        
        return max(0, min(10, score))
    
    def _estimate_weekly_cost(self, weekly_plan: Dict) -> float:
        """Estimate weekly cost based on meals"""
        # Mock cost estimation - would integrate with real pricing data
        cost_per_meal = {
            "breakfast": 3.50,
            "lunch": 5.00,
            "dinner": 7.50,
            "snacks": 2.00
        }
        
        total_cost = 0
        for day_data in weekly_plan.values():
            for meal_type in day_data["meals"]:
                total_cost += cost_per_meal.get(meal_type, 5.00)
        
        return round(total_cost, 2)
    
    async def _optimize_meal_timing(self, parameters: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Optimize meal timing based on fitness schedule and goals"""
        fitness_schedule = parameters.get("fitness_schedule", {})
        dietary_goals = parameters.get("dietary_goals", {})
        
        # Default meal timing
        meal_timing = {
            "breakfast": "07:00",
            "morning_snack": "10:00",
            "lunch": "12:30",
            "afternoon_snack": "15:30",
            "dinner": "18:30",
            "evening_snack": "20:00"
        }
        
        timing_recommendations = []
        
        # Adjust based on workout schedule
        for day, workout in fitness_schedule.items():
            if workout:
                workout_time = workout.get("time", "18:00")
                workout_type = workout.get("type", "general")
                
                if workout_type in ["strength", "high_intensity"]:
                    timing_recommendations.append({
                        "day": day,
                        "pre_workout": f"Eat protein + carbs 1-2 hours before {workout_time}",
                        "post_workout": f"Protein within 30 minutes after {workout_time}",
                        "meal_adjustments": "Larger dinner if evening workout"
                    })
                elif workout_type == "cardio":
                    timing_recommendations.append({
                        "day": day,
                        "pre_workout": f"Light carbs 30-60 minutes before {workout_time}",
                        "post_workout": f"Balanced meal within 2 hours after {workout_time}",
                        "hydration": "Extra water before, during, and after"
                    })
        
        return {
            "optimized_timing": meal_timing,
            "workout_nutrition_timing": timing_recommendations,
            "general_guidelines": [
                "Eat every 3-4 hours to maintain energy",
                "Largest meals earlier in the day",
                "Stop eating 2-3 hours before bed"
            ]
        }
    
    async def _generate_shopping_list_from_plan(self, parameters: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Generate organized shopping list from meal plan"""
        meal_plan = parameters.get("meal_plan", {})
        family_size = parameters.get("family_preferences", {}).get("family_size", 2)
        
        # Extract all ingredients from meal plan
        ingredients = {}
        
        for day, day_data in meal_plan.items():
            for meal_type, meal in day_data.get("meals", {}).items():
                # Mock ingredient extraction - would be more sophisticated
                meal_ingredients = self._get_meal_ingredients(meal["name"], family_size)
                
                for ingredient, amount in meal_ingredients.items():
                    if ingredient in ingredients:
                        ingredients[ingredient] += amount
                    else:
                        ingredients[ingredient] = amount
        
        # Organize by category
        categorized_list = {
            "produce": [],
            "proteins": [],
            "dairy": [],
            "grains": [],
            "pantry": [],
            "frozen": [],
            "other": []
        }
        
        category_map = {
            "vegetables": "produce", "fruits": "produce",
            "chicken": "proteins", "beef": "proteins", "fish": "proteins", "eggs": "proteins",
            "milk": "dairy", "cheese": "dairy", "yogurt": "dairy",
            "rice": "grains", "bread": "grains", "oats": "grains",
            "oil": "pantry", "spices": "pantry", "nuts": "pantry"
        }
        
        for ingredient, amount in ingredients.items():
            category = category_map.get(ingredient.lower(), "other")
            categorized_list[category].append({
                "item": ingredient,
                "amount": amount,
                "estimated_cost": self._estimate_ingredient_cost(ingredient, amount)
            })
        
        total_estimated_cost = sum(
            sum(item["estimated_cost"] for item in category_items)
            for category_items in categorized_list.values()
        )
        
        return {
            "shopping_list": categorized_list,
            "total_items": sum(len(category) for category in categorized_list.values()),
            "estimated_total_cost": round(total_estimated_cost, 2),
            "shopping_tips": [
                "Check for sales on proteins and stock up",
                "Buy seasonal produce for better prices",
                "Consider buying grains and pantry items in bulk"
            ]
        }
    
    def _get_meal_ingredients(self, meal_name: str, family_size: int) -> Dict[str, float]:
        """Get ingredients for a specific meal"""
        # Mock ingredient database - would integrate with recipe database
        base_ingredients = {
            "Overnight Oats": {"oats": 0.5, "milk": 0.25, "berries": 0.1, "honey": 0.02},
            "Quinoa Buddha Bowl": {"quinoa": 0.3, "vegetables": 0.4, "olive oil": 0.02, "tahini": 0.03},
            "Chicken Stir Fry": {"chicken": 0.2, "vegetables": 0.3, "soy sauce": 0.02, "oil": 0.01},
            "Grilled Salmon with Vegetables": {"salmon": 0.15, "vegetables": 0.3, "lemon": 0.05, "herbs": 0.01},
            "Greek Yogurt Parfait": {"yogurt": 0.2, "granola": 0.05, "berries": 0.1, "honey": 0.02}
        }
        
        ingredients = base_ingredients.get(meal_name, {"generic_ingredients": 1.0})
        
        # Scale by family size
        scaled_ingredients = {}
        for ingredient, amount in ingredients.items():
            scaled_ingredients[ingredient] = amount * family_size
        
        return scaled_ingredients
    
    def _estimate_ingredient_cost(self, ingredient: str, amount: float) -> float:
        """Estimate cost of ingredient"""
        # Mock pricing - would integrate with actual grocery pricing APIs
        price_per_unit = {
            "chicken": 8.0,  # per kg
            "salmon": 15.0,
            "vegetables": 3.0,
            "quinoa": 6.0,
            "oats": 2.5,
            "milk": 1.5,  # per liter
            "berries": 4.0,
            "yogurt": 5.0,
            "cheese": 8.0,
            "eggs": 3.0,  # per dozen
            "oil": 4.0,
            "spices": 2.0
        }
        
        unit_price = price_per_unit.get(ingredient.lower(), 3.0)
        return round(unit_price * amount, 2)
    
    async def _create_monthly_meal_plan(self, parameters: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Create a monthly meal plan with weekly variations"""
        # Create 4 different weekly plans for variety
        monthly_plan = {}
        total_cost = 0
        
        for week in range(1, 5):
            # Modify parameters slightly for each week to create variety
            week_params = parameters.copy()
            week_plan = await self._create_weekly_meal_plan(week_params, context)
            
            monthly_plan[f"week_{week}"] = week_plan["meal_plan"]
            total_cost += week_plan.get("estimated_cost", 0)
        
        # Add variety across weeks
        variety_suggestions = [
            "Week 1: Focus on Mediterranean cuisine",
            "Week 2: Incorporate Asian-inspired dishes",
            "Week 3: Emphasize comfort foods and hearty meals",
            "Week 4: Try new ingredients and experimental recipes"
        ]
        
        return {
            "meal_plan": {
                "monthly_schedule": monthly_plan,
                "variety_themes": variety_suggestions
            },
            "nutrition_summary": {
                "planning_period": "4 weeks",
                "variety_score": 9.2,  # Higher due to monthly variation
                "estimated_monthly_cost": round(total_cost, 2)
            },
            "prep_schedule": await self._create_monthly_prep_schedule(monthly_plan, context)
        }
    
    async def _create_monthly_prep_schedule(self, monthly_plan: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Create a monthly meal prep schedule"""
        prep_schedule = {
            "weekly_prep_days": ["Sunday"],
            "prep_tasks": {
                "Sunday": [
                    "Wash and chop vegetables for the week",
                    "Cook grains in bulk (quinoa, rice)",
                    "Prepare protein portions",
                    "Make overnight oats for 3 days",
                    "Prep snack containers"
                ]
            },
            "batch_cooking_suggestions": [
                "Cook large batches of soups and stews",
                "Prepare protein sources for multiple meals",
                "Pre-cut vegetables and store properly",
                "Make freezer-friendly meals for busy weeks"
            ],
            "storage_tips": [
                "Use glass containers for meal storage",
                "Label everything with dates",
                "Freeze portions for weeks 3-4",
                "Keep fresh herbs in water like flowers"
            ]
        }
        
        return prep_schedule
    
    async def _adapt_plan_for_goals(self, parameters: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Adapt meal plan for specific fitness or health goals"""
        fitness_goals = parameters.get("fitness_goals", ["general_health"])
        current_plan = parameters.get("current_meal_plan", {})
        
        adaptations = []
        
        for goal in fitness_goals:
            if goal == "weight_loss":
                adaptations.extend([
                    {
                        "change": "reduce_portion_sizes",
                        "description": "Reduce main meal portions by 15-20%",
                        "impact": "300-400 fewer calories per day"
                    },
                    {
                        "change": "increase_vegetables",
                        "description": "Fill half the plate with non-starchy vegetables",
                        "impact": "Increased fiber and satiety"
                    },
                    {
                        "change": "modify_snacks",
                        "description": "Replace calorie-dense snacks with fruits and vegetables",
                        "impact": "200-300 fewer calories from snacks"
                    }
                ])
            
            elif goal == "muscle_gain":
                adaptations.extend([
                    {
                        "change": "increase_protein",
                        "description": "Add protein source to each meal and snack",
                        "impact": "20-30g additional protein per day"
                    },
                    {
                        "change": "post_workout_nutrition",
                        "description": "Include protein + carb snack within 30 minutes of workouts",
                        "impact": "Enhanced muscle protein synthesis"
                    },
                    {
                        "change": "calorie_increase",
                        "description": "Increase overall calories by 300-500 per day",
                        "impact": "Support for muscle building"
                    }
                ])
            
            elif goal == "endurance_performance":
                adaptations.extend([
                    {
                        "change": "carb_timing",
                        "description": "Emphasize carbs before and after long workouts",
                        "impact": "Better energy and recovery"
                    },
                    {
                        "change": "hydration_focus",
                        "description": "Increase fluid intake and add electrolytes",
                        "impact": "Improved endurance performance"
                    }
                ])
        
        # Calculate new nutrition targets
        adapted_nutrition = self._calculate_adapted_nutrition_targets(fitness_goals)
        
        return {
            "adaptations": adaptations,
            "new_nutrition_targets": adapted_nutrition,
            "implementation_timeline": "Implement gradually over 1-2 weeks",
            "monitoring_suggestions": [
                "Track energy levels and performance",
                "Monitor weight changes weekly",
                "Assess sleep quality and recovery",
                "Adjust portions based on progress"
            ]
        }
    
    def _calculate_adapted_nutrition_targets(self, fitness_goals: List[str]) -> Dict[str, float]:
        """Calculate nutrition targets based on fitness goals"""
        base_targets = {
            "calories": 2000,
            "protein": 100,
            "carbs": 250,
            "fat": 65,
            "fiber": 25
        }
        
        for goal in fitness_goals:
            if goal == "weight_loss":
                base_targets["calories"] *= 0.85  # 15% reduction
                base_targets["protein"] *= 1.2   # Higher protein for satiety
            elif goal == "muscle_gain":
                base_targets["calories"] *= 1.15  # 15% increase
                base_targets["protein"] *= 1.5   # Higher protein for muscle building
            elif goal == "endurance_performance":
                base_targets["carbs"] *= 1.3     # Higher carbs for energy
        
        return {k: round(v, 1) for k, v in base_targets.items()}