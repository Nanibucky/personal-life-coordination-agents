"""
LangChain Luna Agent - Health & Fitness Tracking
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
_workout_data = {}
_health_data = {}

class FitnessTrackerTool(LangChainTool):
    """LangChain tool for fitness tracking"""
    
    def __init__(self):
        super().__init__(
            name="fitness_tracker",
            description="Track workouts, fitness goals, and health metrics"
        )
    
    async def _arun(self, action: str, **kwargs) -> str:
        """Async execution of fitness tracking actions"""
        try:
            if action == "log_workout":
                return await self._log_workout(**kwargs)
            elif action == "get_workouts":
                return await self._get_workouts(**kwargs)
            elif action == "get_fitness_stats":
                return await self._get_fitness_stats(**kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error in fitness tracking: {str(e)}"
    
    def _run(self, action: str, **kwargs) -> str:
        """Sync execution - not implemented"""
        raise NotImplementedError("Use async execution")
    
    async def _log_workout(self, workout_type: str, duration: int, calories_burned: int, **kwargs) -> str:
        """Log a workout session"""
        workout_id = f"workout_{datetime.now().timestamp()}"
        workout = {
            "id": workout_id,
            "type": workout_type,
            "duration": duration,
            "calories_burned": calories_burned,
            "date": datetime.now().isoformat(),
            "notes": kwargs.get("notes", "")
        }
        
        _workout_data[workout_id] = workout
        return f"Logged {workout_type} workout: {duration} minutes, {calories_burned} calories burned"
    
    async def _get_workouts(self, days: int = 7, **kwargs) -> str:
        """Get recent workouts"""
        if not _workout_data:
            return "No workouts logged yet"
        
        # Filter recent workouts
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_workouts = []
        
        for workout in _workout_data.values():
            workout_date = datetime.fromisoformat(workout["date"])
            if workout_date >= cutoff_date:
                recent_workouts.append(workout)
        
        if not recent_workouts:
            return f"No workouts in the last {days} days"
        
        result = f"Recent workouts (last {days} days):\n"
        for workout in recent_workouts:
            result += f"- {workout['type']}: {workout['duration']} min, {workout['calories_burned']} cal\n"
        
        return result
    
    async def _get_fitness_stats(self, **kwargs) -> str:
        """Get fitness statistics"""
        if not _workout_data:
            return "No fitness data available"
        
        total_workouts = len(_workout_data)
        total_calories = sum(w["calories_burned"] for w in _workout_data.values())
        total_duration = sum(w["duration"] for w in _workout_data.values())
        
        # Calculate weekly average
        week_ago = datetime.now() - timedelta(days=7)
        weekly_workouts = [w for w in _workout_data.values() 
                          if datetime.fromisoformat(w["date"]) >= week_ago]
        
        weekly_calories = sum(w["calories_burned"] for w in weekly_workouts)
        weekly_duration = sum(w["duration"] for w in weekly_workouts)
        
        stats = f"Fitness Statistics:\n"
        stats += f"Total workouts: {total_workouts}\n"
        stats += f"Total calories burned: {total_calories}\n"
        stats += f"Total duration: {total_duration} minutes\n"
        stats += f"Weekly average calories: {weekly_calories // 7}\n"
        stats += f"Weekly average duration: {weekly_duration // 7} minutes"
        
        return stats

class WorkoutPlannerTool(LangChainTool):
    """LangChain tool for workout planning"""
    
    def __init__(self):
        super().__init__(
            name="workout_planner",
            description="Create personalized workout plans and exercise recommendations"
        )
    
    async def _arun(self, action: str, **kwargs) -> str:
        """Async execution of workout planning actions"""
        try:
            if action == "create_workout_plan":
                return await self._create_workout_plan(**kwargs)
            elif action == "get_exercise_recommendations":
                return await self._get_exercise_recommendations(**kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error in workout planning: {str(e)}"
    
    def _run(self, action: str, **kwargs) -> str:
        """Sync execution - not implemented"""
        raise NotImplementedError("Use async execution")
    
    async def _create_workout_plan(self, fitness_level: str, goals: List[str], days_per_week: int = 3, **kwargs) -> str:
        """Create a personalized workout plan"""
        exercises = {
            "beginner": {
                "cardio": ["Walking", "Light jogging", "Cycling"],
                "strength": ["Bodyweight squats", "Push-ups", "Planks"],
                "flexibility": ["Stretching", "Yoga basics"]
            },
            "intermediate": {
                "cardio": ["Running", "Swimming", "HIIT"],
                "strength": ["Weight training", "Resistance bands", "Dumbbells"],
                "flexibility": ["Dynamic stretching", "Pilates"]
            },
            "advanced": {
                "cardio": ["Sprint intervals", "CrossFit", "Advanced HIIT"],
                "strength": ["Compound lifts", "Olympic lifts", "Advanced calisthenics"],
                "flexibility": ["Advanced yoga", "Mobility work"]
            }
        }
        
        level_exercises = exercises.get(fitness_level, exercises["beginner"])
        
        plan = f"Workout Plan for {fitness_level} level ({days_per_week} days/week):\n\n"
        
        for i in range(1, days_per_week + 1):
            plan += f"Day {i}:\n"
            if "weight_loss" in goals:
                plan += f"  - Cardio: {level_exercises['cardio'][i % len(level_exercises['cardio'])]} (30 min)\n"
            if "strength" in goals:
                plan += f"  - Strength: {level_exercises['strength'][i % len(level_exercises['strength'])]} (20 min)\n"
            plan += f"  - Flexibility: {level_exercises['flexibility'][i % len(level_exercises['flexibility'])]} (10 min)\n\n"
        
        return plan
    
    async def _get_exercise_recommendations(self, muscle_group: str, equipment: str = "bodyweight", **kwargs) -> str:
        """Get exercise recommendations for specific muscle groups"""
        exercises = {
            "chest": {
                "bodyweight": ["Push-ups", "Diamond push-ups", "Decline push-ups"],
                "equipment": ["Bench press", "Dumbbell flyes", "Cable crossovers"]
            },
            "back": {
                "bodyweight": ["Pull-ups", "Rows", "Superman holds"],
                "equipment": ["Deadlifts", "Lat pulldowns", "T-bar rows"]
            },
            "legs": {
                "bodyweight": ["Squats", "Lunges", "Calf raises"],
                "equipment": ["Leg press", "Romanian deadlifts", "Leg extensions"]
            },
            "shoulders": {
                "bodyweight": ["Pike push-ups", "Handstand holds"],
                "equipment": ["Overhead press", "Lateral raises", "Face pulls"]
            }
        }
        
        if muscle_group not in exercises:
            return f"No exercises found for {muscle_group}"
        
        muscle_exercises = exercises[muscle_group]
        if equipment not in muscle_exercises:
            equipment = "bodyweight"  # Default to bodyweight
        
        exercise_list = muscle_exercises[equipment]
        
        return f"Exercises for {muscle_group} ({equipment}):\n" + "\n".join([f"- {exercise}" for exercise in exercise_list])

class HealthAnalyzerTool(LangChainTool):
    """LangChain tool for health analysis"""
    
    def __init__(self):
        super().__init__(
            name="health_analyzer",
            description="Analyze health metrics and provide wellness recommendations"
        )
    
    async def _arun(self, action: str, **kwargs) -> str:
        """Async execution of health analysis actions"""
        try:
            if action == "analyze_health":
                return await self._analyze_health(**kwargs)
            elif action == "get_wellness_recommendations":
                return await self._get_wellness_recommendations(**kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error in health analysis: {str(e)}"
    
    def _run(self, action: str, **kwargs) -> str:
        """Sync execution - not implemented"""
        raise NotImplementedError("Use async execution")
    
    async def _analyze_health(self, metrics: Dict[str, Any], **kwargs) -> str:
        """Analyze health metrics"""
        analysis = "Health Analysis:\n\n"
        
        # Analyze BMI
        if "weight" in metrics and "height" in metrics:
            weight = metrics["weight"]
            height = metrics["height"] / 100  # Convert cm to meters
            bmi = weight / (height * height)
            
            analysis += f"BMI: {bmi:.1f} - "
            if bmi < 18.5:
                analysis += "Underweight\n"
            elif bmi < 25:
                analysis += "Normal weight\n"
            elif bmi < 30:
                analysis += "Overweight\n"
            else:
                analysis += "Obese\n"
        
        # Analyze heart rate
        if "heart_rate" in metrics:
            hr = metrics["heart_rate"]
            analysis += f"Heart Rate: {hr} bpm - "
            if hr < 60:
                analysis += "Bradycardia (slow)\n"
            elif hr > 100:
                analysis += "Tachycardia (fast)\n"
            else:
                analysis += "Normal\n"
        
        # Analyze blood pressure
        if "systolic" in metrics and "diastolic" in metrics:
            systolic = metrics["systolic"]
            diastolic = metrics["diastolic"]
            analysis += f"Blood Pressure: {systolic}/{diastolic} mmHg - "
            if systolic < 120 and diastolic < 80:
                analysis += "Normal\n"
            elif systolic < 130 and diastolic < 80:
                analysis += "Elevated\n"
            else:
                analysis += "High\n"
        
        return analysis
    
    async def _get_wellness_recommendations(self, age: int, activity_level: str, health_concerns: List[str], **kwargs) -> str:
        """Get personalized wellness recommendations"""
        recommendations = []
        
        # Age-based recommendations
        if age < 30:
            recommendations.append("Focus on building healthy habits early")
            recommendations.append("Aim for 150 minutes of moderate exercise per week")
        elif 30 <= age <= 50:
            recommendations.append("Maintain muscle mass with strength training")
            recommendations.append("Prioritize stress management and sleep")
        else:
            recommendations.append("Focus on balance and flexibility exercises")
            recommendations.append("Regular health check-ups are important")
        
        # Activity level recommendations
        if activity_level == "sedentary":
            recommendations.append("Start with 10-minute walks daily")
            recommendations.append("Gradually increase activity level")
        elif activity_level == "moderate":
            recommendations.append("Maintain current activity level")
            recommendations.append("Add variety to your routine")
        elif activity_level == "active":
            recommendations.append("Consider recovery and rest days")
            recommendations.append("Monitor for overtraining signs")
        
        # Health concern recommendations
        for concern in health_concerns:
            if concern == "stress":
                recommendations.append("Practice mindfulness and meditation")
            elif concern == "sleep":
                recommendations.append("Maintain consistent sleep schedule")
            elif concern == "nutrition":
                recommendations.append("Focus on whole foods and balanced meals")
        
        return "Wellness Recommendations:\n" + "\n".join([f"- {rec}" for rec in recommendations])

class LangChainLunaAgent(LangChainBaseAgent):
    """LangChain-based Luna Health Agent"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            config = config_manager.load_config("luna")
        
        super().__init__("luna", config)
        
        # Register with A2A coordinator
        a2a_coordinator.register_agent(self)
    
    def _register_tools(self):
        """Register Luna's tools"""
        self.add_tool(FitnessTrackerTool())
        self.add_tool(WorkoutPlannerTool())
        self.add_tool(HealthAnalyzerTool())
    
    def _register_a2a_handlers(self):
        """Register A2A message handlers"""
        self.register_a2a_handler("fitness_data_request", self._handle_fitness_data)
        self.register_a2a_handler("workout_planning", self._handle_workout_planning)
        self.register_a2a_handler("health_analysis", self._handle_health_analysis)
        self.register_a2a_handler("nutrition_fitness_coordination", self._handle_nutrition_coordination)
    
    def _get_system_prompt(self) -> str:
        return """You are Luna, a health and fitness tracking assistant. 
        You help users track their workouts, analyze health metrics, and create personalized fitness plans.
        
        Your capabilities include:
        - Tracking workouts and fitness progress
        - Creating personalized workout plans
        - Analyzing health metrics and providing recommendations
        - Coordinating with nutrition and scheduling agents
        
        Always use your tools to provide accurate and helpful information. Consider user fitness levels and health goals."""
    
    async def _handle_fitness_data(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fitness data requests"""
        try:
            days = payload.get("days", 7)
            
            workouts_result = await self.tools[0]._arun("get_workouts", days=days)
            stats_result = await self.tools[0]._arun("get_fitness_stats")
            
            return {
                "workouts": workouts_result,
                "fitness_stats": stats_result,
                "days_analyzed": days
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_workout_planning(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workout planning requests"""
        try:
            fitness_level = payload.get("fitness_level", "beginner")
            goals = payload.get("goals", ["general_fitness"])
            days_per_week = payload.get("days_per_week", 3)
            
            workout_plan = await self.tools[1]._arun("create_workout_plan", 
                fitness_level=fitness_level, 
                goals=goals, 
                days_per_week=days_per_week
            )
            
            return {
                "workout_plan": workout_plan,
                "fitness_level": fitness_level,
                "goals": goals
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_health_analysis(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health analysis requests"""
        try:
            metrics = payload.get("metrics", {})
            
            health_analysis = await self.tools[2]._arun("analyze_health", metrics=metrics)
            
            return {
                "health_analysis": health_analysis,
                "metrics_analyzed": list(metrics.keys())
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_nutrition_coordination(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle nutrition-fitness coordination"""
        try:
            meal_plan = payload.get("meal_plan", {})
            workout_schedule = payload.get("workout_schedule", {})
            
            # Provide recommendations for timing meals around workouts
            recommendations = [
                "Eat a light meal 2-3 hours before intense workouts",
                "Have a protein-rich snack within 30 minutes after strength training",
                "Stay hydrated throughout the day, especially on workout days",
                "Consider meal timing to optimize energy levels"
            ]
            
            return {
                "nutrition_fitness_recommendations": recommendations,
                "coordination_notes": "Meal timing optimized for workout schedule"
            }
        except Exception as e:
            return {"error": str(e)} 