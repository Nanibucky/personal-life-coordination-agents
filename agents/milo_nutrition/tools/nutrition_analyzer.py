"""
Nutrition Analyzer Tool for Agent Milo
Comprehensive nutritional assessment and optimization
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import statistics

from shared.mcp_framework.base_server import BaseMCPTool, ExecutionContext, ExecutionResult

class NutritionAnalyzerTool(BaseMCPTool):
    """Comprehensive nutritional assessment and optimization"""
    
    def __init__(self):
        super().__init__("nutrition_analyzer", "Analyze nutritional content and provide optimization recommendations")
        self.nutrition_database = self._load_nutrition_database()
        self.daily_values = self._load_daily_values()
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["analyze_meal", "track_daily_intake", "assess_nutrition_gaps", "optimize_nutrition", "compare_foods"]
                },
                "food_items": {"type": "array"},
                "daily_log": {"type": "object"},
                "user_profile": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "integer"},
                        "gender": {"type": "string"},
                        "weight": {"type": "number"},
                        "height": {"type": "number"},
                        "activity_level": {"type": "string", "enum": ["sedentary", "light", "moderate", "active", "very_active"]},
                        "health_goals": {"type": "array"}
                    }
                },
                "target_nutrition": {"type": "object"},
                "time_period": {"type": "string", "enum": ["daily", "weekly", "monthly"]}
            },
            "required": ["action"]
        }
    
    def get_return_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "nutrition_analysis": {"type": "object"},
                "daily_summary": {"type": "object"},
                "nutrition_gaps": {"type": "array"},
                "optimization_suggestions": {"type": "array"},
                "food_comparisons": {"type": "array"}
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        action = parameters["action"]
        
        try:
            if action == "analyze_meal":
                result = await self._analyze_meal_nutrition(
                    parameters.get("food_items", []),
                    context
                )
            elif action == "track_daily_intake":
                result = await self._track_daily_nutrition(
                    parameters.get("daily_log", {}),
                    parameters.get("user_profile", {}),
                    context
                )
            elif action == "assess_nutrition_gaps":
                result = await self._assess_nutritional_gaps(
                    parameters.get("daily_log", {}),
                    parameters.get("target_nutrition", {}),
                    context
                )
            elif action == "optimize_nutrition":
                result = await self._optimize_nutritional_intake(
                    parameters.get("daily_log", {}),
                    parameters.get("user_profile", {}),
                    context
                )
            else:  # compare_foods
                result = await self._compare_food_nutrition(
                    parameters.get("food_items", []),
                    context
                )
            
            return ExecutionResult(success=True, result=result, execution_time=1.0)
            
        except Exception as e:
            self.logger.error(f"Nutrition analysis failed: {e}")
            return ExecutionResult(success=False, error=str(e), execution_time=0.0)
    
    def _load_nutrition_database(self) -> Dict[str, Any]:
        """Load nutrition database for common foods"""
        return {
            "chicken_breast": {
                "calories_per_100g": 165,
                "protein": 31,
                "carbs": 0,
                "fat": 3.6,
                "fiber": 0,
                "sugar": 0,
                "sodium": 74,
                "vitamins": {"B6": 0.9, "niacin": 14.8, "B12": 0.3},
                "minerals": {"phosphorus": 228, "selenium": 27.6}
            },
            "quinoa": {
                "calories_per_100g": 368,
                "protein": 14.1,
                "carbs": 64.2,
                "fat": 6.1,
                "fiber": 7,
                "sugar": 4.6,
                "sodium": 5,
                "vitamins": {"folate": 184, "thiamine": 0.4},
                "minerals": {"iron": 4.6, "magnesium": 197}
            },
            "spinach": {
                "calories_per_100g": 23,
                "protein": 2.9,
                "carbs": 3.6,
                "fat": 0.4,
                "fiber": 2.2,
                "sugar": 0.4,
                "sodium": 79,
                "vitamins": {"K": 483, "folate": 194, "A": 469},
                "minerals": {"iron": 2.7, "calcium": 99}
            },
            "sweet_potato": {
                "calories_per_100g": 86,
                "protein": 1.6,
                "carbs": 20.1,
                "fat": 0.1,
                "fiber": 3,
                "sugar": 4.2,
                "sodium": 7,
                "vitamins": {"A": 709, "C": 2.4, "B6": 0.2},
                "minerals": {"potassium": 337, "manganese": 0.3}
            }
        }
    
    def _load_daily_values(self) -> Dict[str, Any]:
        """Load recommended daily values for nutrients"""
        return {
            "calories": 2000,  # General reference
            "protein": 50,
            "carbs": 300,
            "fat": 65,
            "fiber": 25,
            "sodium": 2300,
            "vitamins": {
                "A": 900,  # mcg
                "C": 90,   # mg
                "K": 120,  # mcg
                "folate": 400,  # mcg
                "B12": 2.4,  # mcg
                "B6": 1.7   # mg
            },
            "minerals": {
                "iron": 18,      # mg
                "calcium": 1000, # mg
                "potassium": 4700, # mg
                "magnesium": 420   # mg
            }
        }
    
    async def _analyze_meal_nutrition(self, food_items: List[Dict], context: ExecutionContext) -> Dict[str, Any]:
        """Analyze nutritional content of a meal"""
        total_nutrition = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "fiber": 0,
            "sugar": 0,
            "sodium": 0,
            "vitamins": {},
            "minerals": {}
        }
        
        meal_details = []
        
        for item in food_items:
            food_name = item.get("name", "").lower().replace(" ", "_")
            amount = item.get("amount", 100)  # grams
            
            if food_name in self.nutrition_database:
                food_data = self.nutrition_database[food_name]
                serving_factor = amount / 100  # Convert to per serving
                
                # Calculate nutrition for this serving
                serving_nutrition = {
                    "food": item.get("name"),
                    "amount": f"{amount}g",
                    "calories": food_data["calories_per_100g"] * serving_factor,
                    "protein": food_data["protein"] * serving_factor,
                    "carbs": food_data["carbs"] * serving_factor,
                    "fat": food_data["fat"] * serving_factor,
                    "fiber": food_data["fiber"] * serving_factor
                }
                
                meal_details.append(serving_nutrition)
                
                # Add to totals
                total_nutrition["calories"] += serving_nutrition["calories"]
                total_nutrition["protein"] += serving_nutrition["protein"]
                total_nutrition["carbs"] += serving_nutrition["carbs"]
                total_nutrition["fat"] += serving_nutrition["fat"]
                total_nutrition["fiber"] += serving_nutrition["fiber"]
        
        # Calculate macro percentages
        total_cals = total_nutrition["calories"]
        if total_cals > 0:
            macro_percentages = {
                "protein": (total_nutrition["protein"] * 4 / total_cals) * 100,
                "carbs": (total_nutrition["carbs"] * 4 / total_cals) * 100,
                "fat": (total_nutrition["fat"] * 9 / total_cals) * 100
            }
        else:
            macro_percentages = {"protein": 0, "carbs": 0, "fat": 0}
        
        # Health assessment
        health_score = self._calculate_meal_health_score(total_nutrition, macro_percentages)
        
        analysis = {
            "meal_summary": total_nutrition,
            "macro_percentages": macro_percentages,
            "food_breakdown": meal_details,
            "health_score": health_score,
            "meal_quality": "excellent" if health_score >= 8 else "good" if health_score >= 6 else "fair",
            "recommendations": self._generate_meal_recommendations(total_nutrition, macro_percentages)
        }
        
        return {"nutrition_analysis": analysis}
    
    def _calculate_meal_health_score(self, nutrition: Dict, macros: Dict) -> float:
        """Calculate a health score for the meal (0-10)"""
        score = 7.0  # Start with base score
        
        # Protein adequacy (25-35% is ideal)
        if 25 <= macros["protein"] <= 35:
            score += 1
        elif macros["protein"] < 15 or macros["protein"] > 40:
            score -= 1
        
        # Fiber content (aim for 5g+ per meal)
        if nutrition["fiber"] >= 8:
            score += 1
        elif nutrition["fiber"] >= 5:
            score += 0.5
        elif nutrition["fiber"] < 3:
            score -= 1
        
        # Calorie density (not too high)
        if nutrition["calories"] <= 600:
            score += 0.5
        elif nutrition["calories"] > 800:
            score -= 0.5
        
        return max(0, min(10, score))
    
    def _generate_meal_recommendations(self, nutrition: Dict, macros: Dict) -> List[str]:
        """Generate recommendations based on meal analysis"""
        recommendations = []
        
        if macros["protein"] < 20:
            recommendations.append("Consider adding more protein sources like lean meat, legumes, or Greek yogurt")
        
        if nutrition["fiber"] < 5:
            recommendations.append("Add more vegetables or whole grains to increase fiber content")
        
        if macros["fat"] > 35:
            recommendations.append("Consider reducing high-fat ingredients to balance macronutrients")
        
        if nutrition["calories"] > 700:
            recommendations.append("This is a calorie-dense meal - consider smaller portions or lighter sides")
        
        if not recommendations:
            recommendations.append("Well-balanced meal with good nutritional content!")
        
        return recommendations
    
    async def _track_daily_nutrition(self, daily_log: Dict, user_profile: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Track and analyze daily nutritional intake"""
        daily_totals = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "fiber": 0,
            "meals_logged": 0
        }
        
        meal_breakdown = {}
        
        # Process each meal
        for meal_time, foods in daily_log.items():
            if isinstance(foods, list):
                meal_nutrition = await self._analyze_meal_nutrition(foods, context)
                meal_totals = meal_nutrition["nutrition_analysis"]["meal_summary"]
                
                meal_breakdown[meal_time] = meal_totals
                daily_totals["meals_logged"] += 1
                
                # Add to daily totals
                for nutrient in ["calories", "protein", "carbs", "fat", "fiber"]:
                    daily_totals[nutrient] += meal_totals.get(nutrient, 0)
        
        # Calculate targets based on user profile
        targets = self._calculate_personal_targets(user_profile)
        
        # Calculate achievement percentages
        achievements = {}
        for nutrient, target in targets.items():
            if target > 0:
                achievements[nutrient] = {
                    "current": daily_totals.get(nutrient, 0),
                    "target": target,
                    "percentage": (daily_totals.get(nutrient, 0) / target) * 100,
                    "status": "met" if daily_totals.get(nutrient, 0) >= target * 0.9 else "under"
                }
        
        summary = {
            "daily_totals": daily_totals,
            "targets": targets,
            "achievements": achievements,
            "meal_breakdown": meal_breakdown,
            "overall_score": self._calculate_daily_nutrition_score(achievements),
            "recommendations": self._generate_daily_recommendations(achievements)
        }
        
        return {"daily_summary": summary}
    
    def _calculate_personal_targets(self, user_profile: Dict) -> Dict[str, float]:
        """Calculate personalized nutrition targets"""
        # Basic calculations - would be more sophisticated in reality
        weight = user_profile.get("weight", 70)  # kg
        activity_level = user_profile.get("activity_level", "moderate")
        goals = user_profile.get("health_goals", [])
        
        # Base calorie calculation (simplified)
        base_calories = 1800 if user_profile.get("gender") == "female" else 2000
        
        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }
        
        calories = base_calories * activity_multipliers.get(activity_level, 1.55)
        
        # Adjust for goals
        if "weight_loss" in goals:
            calories *= 0.85
        elif "muscle_gain" in goals:
            calories *= 1.1
        
        return {
            "calories": calories,
            "protein": weight * 1.2,  # 1.2g per kg
            "carbs": calories * 0.45 / 4,  # 45% of calories
            "fat": calories * 0.25 / 9,   # 25% of calories
            "fiber": 25
        }
    
    def _calculate_daily_nutrition_score(self, achievements: Dict) -> float:
        """Calculate overall daily nutrition score"""
        scores = []
        for nutrient, data in achievements.items():
            percentage = data["percentage"]
            if 90 <= percentage <= 110:
                scores.append(10)
            elif 80 <= percentage <= 120:
                scores.append(8)
            elif 70 <= percentage <= 130:
                scores.append(6)
            else:
                scores.append(4)
        
        return statistics.mean(scores) if scores else 5.0
    
    def _generate_daily_recommendations(self, achievements: Dict) -> List[str]:
        """Generate daily nutrition recommendations"""
        recommendations = []
        
        for nutrient, data in achievements.items():
            percentage = data["percentage"]
            if percentage < 80:
                if nutrient == "protein":
                    recommendations.append("Increase protein intake with lean meats, eggs, or plant-based options")
                elif nutrient == "fiber":
                    recommendations.append("Add more fruits, vegetables, and whole grains for fiber")
                elif nutrient == "calories":
                    recommendations.append("Consider adding healthy snacks to meet your calorie goals")
            elif percentage > 120:
                if nutrient == "calories":
                    recommendations.append("Consider smaller portions or lighter meal options")
                elif nutrient == "fat":
                    recommendations.append("Reduce high-fat foods to balance your macronutrients")
        
        if not recommendations:
            recommendations.append("Great job maintaining balanced nutrition today!")
        
        return recommendations
    
    async def _assess_nutritional_gaps(self, daily_log: Dict, target_nutrition: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Assess nutritional gaps and deficiencies"""
        # Analyze current intake
        daily_summary = await self._track_daily_nutrition(daily_log, {}, context)
        current_intake = daily_summary["daily_summary"]["daily_totals"]
        
        gaps = []
        
        # Compare with targets
        for nutrient, target in target_nutrition.items():
            current = current_intake.get(nutrient, 0)
            if current < target * 0.8:  # Less than 80% of target
                gap_percentage = ((target - current) / target) * 100
                gaps.append({
                    "nutrient": nutrient,
                    "current_intake": current,
                    "target_intake": target,
                    "gap_percentage": gap_percentage,
                    "severity": "high" if gap_percentage > 40 else "moderate" if gap_percentage > 20 else "low",
                    "food_suggestions": self._get_food_suggestions_for_nutrient(nutrient),
                    "health_impact": self._get_health_impact(nutrient)
                })
        
        # Priority ranking
        gaps.sort(key=lambda x: x["gap_percentage"], reverse=True)
        
        return {
            "nutrition_gaps": gaps,
            "total_gaps_found": len(gaps),
            "priority_nutrients": [gap["nutrient"] for gap in gaps[:3]],
            "overall_adequacy": "good" if len(gaps) <= 2 else "needs_improvement"
        }
    
    def _get_food_suggestions_for_nutrient(self, nutrient: str) -> List[str]:
        """Get food suggestions to address nutrient gaps"""
        suggestions = {
            "protein": ["chicken breast", "eggs", "Greek yogurt", "lentils", "quinoa"],
            "fiber": ["oats", "berries", "broccoli", "beans", "apples"],
            "iron": ["spinach", "red meat", "chickpeas", "fortified cereals"],
            "calcium": ["dairy products", "leafy greens", "almonds", "fortified plant milk"],
            "vitamin_c": ["citrus fruits", "bell peppers", "strawberries", "broccoli"],
            "folate": ["leafy greens", "legumes", "fortified grains", "asparagus"]
        }
        return suggestions.get(nutrient, ["consult with a nutritionist"])
    
    def _get_health_impact(self, nutrient: str) -> str:
        """Get health impact description for nutrient deficiency"""
        impacts = {
            "protein": "May affect muscle maintenance and immune function",
            "fiber": "Could impact digestive health and blood sugar control",
            "iron": "May lead to fatigue and reduced oxygen transport",
            "calcium": "Important for bone health and muscle function",
            "vitamin_c": "Essential for immune system and collagen production",
            "folate": "Critical for DNA synthesis and red blood cell formation"
        }
        return impacts.get(nutrient, "Important for overall health and wellness")
    
    async def _optimize_nutritional_intake(self, daily_log: Dict, user_profile: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Provide optimization suggestions for nutritional intake"""
        # Get current nutrition status
        daily_summary = await self._track_daily_nutrition(daily_log, user_profile, context)
        achievements = daily_summary["daily_summary"]["achievements"]
        
        optimizations = []
        
        # Analyze each nutrient
        for nutrient, data in achievements.items():
            percentage = data["percentage"]
            
            if percentage < 90:
                optimizations.append({
                    "type": "increase",
                    "nutrient": nutrient,
                    "current": data["current"],
                    "target": data["target"],
                    "recommendation": f"Increase {nutrient} intake by {data['target'] - data['current']:.1f}g",
                    "food_swaps": self._suggest_food_swaps(nutrient, "increase"),
                    "priority": "high" if percentage < 70 else "medium"
                })
            elif percentage > 120:
                optimizations.append({
                    "type": "decrease",
                    "nutrient": nutrient,
                    "current": data["current"],
                    "target": data["target"],
                    "recommendation": f"Reduce {nutrient} intake by {data['current'] - data['target']:.1f}g",
                    "food_swaps": self._suggest_food_swaps(nutrient, "decrease"),
                    "priority": "medium"
                })
        
        # Meal timing suggestions
        timing_suggestions = [
            "Spread protein intake throughout the day for better absorption",
            "Include fiber-rich foods at each meal for sustained energy",
            "Consider post-workout protein within 30 minutes"
        ]
        
        return {
            "optimization_suggestions": optimizations,
            "meal_timing_advice": timing_suggestions,
            "hydration_reminder": "Aim for 8-10 glasses of water daily",
            "supplement_considerations": self._suggest_supplements(optimizations)
        }
    
    def _suggest_food_swaps(self, nutrient: str, direction: str) -> List[Dict[str, str]]:
        """Suggest food swaps to optimize nutrient intake"""
        swaps = {
            "protein": {
                "increase": [
                    {"from": "regular yogurt", "to": "Greek yogurt", "benefit": "+10g protein"},
                    {"from": "white rice", "to": "quinoa", "benefit": "+6g protein per cup"}
                ],
                "decrease": [
                    {"from": "protein shake", "to": "fruit smoothie", "benefit": "-20g protein"},
                    {"from": "steak", "to": "fish", "benefit": "lighter protein option"}
                ]
            },
            "carbs": {
                "increase": [
                    {"from": "salad only", "to": "salad with quinoa", "benefit": "+30g healthy carbs"}
                ],
                "decrease": [
                    {"from": "white bread", "to": "lettuce wrap", "benefit": "-20g carbs"},
                    {"from": "pasta", "to": "zucchini noodles", "benefit": "-35g carbs"}
                ]
            }
        }
        
        return swaps.get(nutrient, {}).get(direction, [])
    
    def _suggest_supplements(self, optimizations: List[Dict]) -> List[str]:
        """Suggest supplements based on optimization needs"""
        suggestions = []
        
        for opt in optimizations:
            if opt["type"] == "increase" and opt["priority"] == "high":
                nutrient = opt["nutrient"]
                if nutrient == "protein":
                    suggestions.append("Consider a protein powder for post-workout")
                elif nutrient == "fiber":
                    suggestions.append("Psyllium husk or fiber supplement may help")
                elif nutrient in ["vitamins", "minerals"]:
                    suggestions.append(f"Consult doctor about {nutrient} supplementation")
        
        if not suggestions:
            suggestions.append("Your nutrition looks well-balanced - focus on whole foods")
        
        return suggestions
    
    async def _compare_food_nutrition(self, food_items: List[str], context: ExecutionContext) -> Dict[str, Any]:
        """Compare nutritional profiles of different foods"""
        comparisons = []
        
        for food in food_items:
            food_key = food.lower().replace(" ", "_")
            if food_key in self.nutrition_database:
                nutrition = self.nutrition_database[food_key]
                comparisons.append({
                    "food": food,
                    "per_100g": nutrition,
                    "protein_density": nutrition["protein"] / nutrition["calories_per_100g"] * 100,
                    "fiber_content": nutrition["fiber"],
                    "calorie_density": nutrition["calories_per_100g"]
                })
        
        if len(comparisons) >= 2:
            # Find best options for different goals
            best_protein = max(comparisons, key=lambda x: x["protein_density"])
            best_fiber = max(comparisons, key=lambda x: x["fiber_content"])
            lowest_calorie = min(comparisons, key=lambda x: x["calorie_density"])
            
            recommendations = {
                "best_for_protein": best_protein["food"],
                "best_for_fiber": best_fiber["food"],
                "lowest_calorie": lowest_calorie["food"]
            }
        else:
            recommendations = {}
        
        return {
            "food_comparisons": comparisons,
            "recommendations": recommendations,
            "comparison_summary": f"Compared {len(comparisons)} foods across key nutrients"
        }