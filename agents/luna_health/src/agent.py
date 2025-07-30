"""
Agent Luna - Core Agent Implementation
Fitness & Health Optimization Agent
"""

from datetime import datetime
from typing import Dict, List, Any

from shared.mcp_framework.base_server import BaseMCPServer, ExecutionContext
from shared.a2a_protocol.message_router import A2AMessage

# Import Luna's tools
from agents.luna_health.tools.fitness_tracker import FitnessTrackerTool
from agents.luna_health.tools.health_analyzer import HealthAnalyzerTool
from agents.luna_health.tools.workout_planner import WorkoutPlannerTool
from agents.luna_health.tools.recovery_monitor import RecoveryMonitorTool

class LunaAgent(BaseMCPServer):
    """Agent Luna - Fitness & Health Optimization"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("luna", 8004, config)
        
        # Register all Luna's tools
        self.register_tool(FitnessTrackerTool())
        self.register_tool(HealthAnalyzerTool())
        self.register_tool(WorkoutPlannerTool())
        self.register_tool(RecoveryMonitorTool())
        
        self.logger.info("Agent Luna initialized with 4 tools")
    
    async def process_a2a_message(self, message_data: dict) -> Dict[str, Any]:
        """Process incoming A2A messages from other agents"""
        try:
            message = A2AMessage(**message_data)
            self.logger.info(f"Luna received: {message.intent} from {message.from_agent}")
            
            if message.intent == "workout_time_recommendations":
                return await self._provide_workout_timing(message)
            elif message.intent == "nutrition_requirements":
                return await self._provide_nutrition_needs(message)
            elif message.intent == "analyze_schedule_health_impact":
                return await self._analyze_schedule_impact(message)
            elif message.intent == "evaluate_meal_plan_fitness":
                return await self._evaluate_meal_plan(message)
            else:
                return {
                    "success": False, 
                    "error": f"Unknown intent: {message.intent}",
                    "agent": "luna"
                }
                
        except Exception as e:
            self.logger.error(f"A2A message processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": "luna"
            }
    
    async def _provide_workout_timing(self, message: A2AMessage) -> Dict[str, Any]:
        """Provide optimal workout timing recommendations to Nani"""
        payload = message.payload
        
        # Get current recovery status
        recovery_tool = self.tools["recovery_monitor"]
        context = ExecutionContext(
            user_id=payload.get("user_id", "default"),
            session_id=message.session_id,
            permissions=["read"]
        )
        
        recovery_result = await recovery_tool.execute({
            "action": "predict_readiness",
            "recovery_data": payload.get("current_recovery", {}),
            "recent_workouts": payload.get("recent_workouts", [])
        }, context)
        
        if recovery_result.success:
            predictions = recovery_result.result["predictions"]
            
            optimal_times = []
            for pred in predictions:
                if pred["predicted_score"] >= 70:
                    optimal_times.append({
                        "day": pred["day"],
                        "recommended_times": ["06:00", "18:00"],  # Morning or evening
                        "intensity_level": "high" if pred["predicted_score"] >= 85 else "moderate",
                        "workout_type": "strength" if pred["predicted_score"] >= 80 else "cardio",
                        "duration_minutes": 60 if pred["predicted_score"] >= 85 else 45,
                        "confidence": pred["confidence"]
                    })
            
            return {
                "success": True,
                "optimal_workout_times": optimal_times,
                "recovery_insights": recovery_result.result["current_readiness"],
                "scheduling_priority": "high",
                "agent": "luna"
            }
        
        return {"success": False, "error": "Failed to analyze workout timing", "agent": "luna"}
    
    async def _provide_nutrition_needs(self, message: A2AMessage) -> Dict[str, Any]:
        """Provide nutrition requirements to Milo based on fitness goals"""
        payload = message.payload
        fitness_goals = payload.get("fitness_goals", ["general_fitness"])
        current_metrics = payload.get("current_metrics", {})
        
        # Calculate nutrition requirements based on goals
        if "muscle_gain" in fitness_goals:
            protein_multiplier = 1.6  # g per kg body weight
            calorie_surplus = 300
        elif "weight_loss" in fitness_goals:
            protein_multiplier = 1.2
            calorie_surplus = -500
        elif "endurance" in fitness_goals:
            protein_multiplier = 1.2
            calorie_surplus = 0
        else:
            protein_multiplier = 1.0
            calorie_surplus = 0
        
        body_weight = current_metrics.get("weight_kg", 70)
        base_calories = current_metrics.get("bmr", 1800)
        
        nutrition_requirements = {
            "daily_calories": base_calories + calorie_surplus,
            "protein_grams": body_weight * protein_multiplier,
            "carbs_grams": body_weight * 4,  # 4g per kg for active individuals
            "fat_grams": (base_calories + calorie_surplus) * 0.25 / 9,  # 25% of calories from fat
            "water_liters": body_weight * 0.035,
            "meal_timing": {
                "pre_workout": "30-60 minutes before: light carbs + protein",
                "post_workout": "within 30 minutes: protein + carbs",
                "daily_distribution": "5-6 smaller meals throughout day"
            },
            "supplements": self._recommend_supplements(fitness_goals),
            "special_considerations": self._get_dietary_considerations(fitness_goals)
        }
        
        return {
            "success": True,
            "nutrition_requirements": nutrition_requirements,
            "fitness_goals": fitness_goals,
            "adjustment_rationale": f"Optimized for {', '.join(fitness_goals)}",
            "agent": "luna"
        }
    
    async def _analyze_schedule_impact(self, message: A2AMessage) -> Dict[str, Any]:
        """Analyze health impact of scheduling patterns"""
        payload = message.payload
        schedule_data = payload.get("schedule_data", {})
        
        # Mock analysis of schedule health impact
        health_impact = {
            "stress_level": "moderate",
            "recovery_time_needed": "6-8 hours between intense activities",
            "energy_depletion_risk": "low",
            "recommendations": [
                "Schedule recovery time after intense meetings",
                "Block lunch time for nutrition",
                "Avoid back-to-back high-stress activities"
            ]
        }
        
        return {
            "success": True,
            "health_impact_analysis": health_impact,
            "agent": "luna"
        }
    
    async def _evaluate_meal_plan(self, message: A2AMessage) -> Dict[str, Any]:
        """Evaluate meal plan against fitness goals"""
        payload = message.payload
        meal_plan = payload.get("meal_plan", {})
        fitness_goals = payload.get("fitness_goals", ["general_fitness"])
        
        # Mock meal plan evaluation
        evaluation = {
            "nutrition_score": 85,
            "goal_alignment": "good",
            "protein_adequacy": "excellent",
            "calorie_balance": "appropriate",
            "suggestions": [
                "Add more vegetables for micronutrients",
                "Consider post-workout protein timing"
            ]
        }
        
        return {
            "success": True,
            "meal_plan_evaluation": evaluation,
            "fitness_alignment": fitness_goals,
            "agent": "luna"
        }
    
    def _recommend_supplements(self, fitness_goals: List[str]) -> List[Dict[str, Any]]:
        """Recommend supplements based on fitness goals"""
        supplements = []
        
        if "muscle_gain" in fitness_goals:
            supplements.extend([
                {"name": "Whey Protein", "dosage": "25-30g", "timing": "post-workout"},
                {"name": "Creatine", "dosage": "5g", "timing": "daily"},
                {"name": "Vitamin D", "dosage": "2000 IU", "timing": "with meal"}
            ])
        
        if "endurance" in fitness_goals:
            supplements.extend([
                {"name": "Electrolytes", "dosage": "as needed", "timing": "during long workouts"},
                {"name": "Beta-Alanine", "dosage": "3-5g", "timing": "daily"},
                {"name": "Iron", "dosage": "18mg", "timing": "with vitamin C"}
            ])
        
        # Always recommend basics
        supplements.extend([
            {"name": "Multivitamin", "dosage": "1 daily", "timing": "with breakfast"},
            {"name": "Omega-3", "dosage": "1-2g", "timing": "with meal"}
        ])
        
        return supplements
    
    def _get_dietary_considerations(self, fitness_goals: List[str]) -> List[str]:
        """Get special dietary considerations"""
        considerations = []
        
        if "weight_loss" in fitness_goals:
            considerations.extend([
                "Focus on high-volume, low-calorie foods",
                "Increase fiber intake for satiety"
            ])
        
        if "muscle_gain" in fitness_goals:
            considerations.extend([
                "Eat in slight caloric surplus",
                "Prioritize protein at each meal"
            ])
        
        if "endurance" in fitness_goals:
            considerations.extend([
                "Emphasize complex carbohydrates",
                "Maintain consistent fueling during long sessions"
            ])
        
        return considerations