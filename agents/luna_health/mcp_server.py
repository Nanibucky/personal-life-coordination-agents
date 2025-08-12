"""
Luna Health & Fitness Agent - MCP Server
Health tracking, fitness planning, and wellness management using MCP protocol
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from shared.mcp_framework.mcp_server_base import BaseMCPServer
from agents.luna_health.tools.fitness_tracker import FitnessTrackerTool
from agents.luna_health.tools.health_analyzer import HealthAnalyzerTool
from agents.luna_health.tools.recovery_monitor import RecoveryMonitorTool
from agents.luna_health.tools.workout_planner import WorkoutPlannerTool


class LunaMCPServer(BaseMCPServer):
    """
    Luna Health & Fitness Agent MCP Server
    Provides fitness tracking, health monitoring, workout planning, and wellness tools
    """
    
    def __init__(self):
        super().__init__(
            server_name="luna",
            port=8003,
            description="Health & Fitness Agent with comprehensive health tracking, workout planning, and wellness management"
        )
        
        # Initialize tools
        self.fitness_tracker = FitnessTrackerTool()
        self.health_analyzer = HealthAnalyzerTool()
        self.recovery_monitor = RecoveryMonitorTool()
        self.workout_planner = WorkoutPlannerTool()
    
    async def initialize_agent(self):
        """Initialize Luna's tools and resources"""
        
        # Register fitness tracking tool
        self.register_tool(
            name="fitness_tracker",
            description="Track fitness activities, workouts, and progress metrics",
            input_schema={
                "type": "object",
                "properties": {
                    "activity_type": {
                        "type": "string",
                        "enum": ["running", "cycling", "swimming", "weightlifting", "yoga", "walking", "cardio", "strength"],
                        "description": "Type of fitness activity"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Duration of activity in minutes"
                    },
                    "intensity": {
                        "type": "string",
                        "enum": ["low", "moderate", "high", "very_high"],
                        "description": "Exercise intensity level"
                    },
                    "calories_burned": {
                        "type": "integer",
                        "description": "Estimated calories burned (optional)"
                    },
                    "heart_rate_avg": {
                        "type": "integer",
                        "description": "Average heart rate during activity (optional)"
                    },
                    "distance_km": {
                        "type": "number",
                        "description": "Distance covered in kilometers (for cardio activities)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes about the workout"
                    },
                    "date": {
                        "type": "string",
                        "format": "date",
                        "description": "Date of activity (YYYY-MM-DD), defaults to today"
                    }
                },
                "required": ["activity_type", "duration_minutes", "intensity"]
            },
            function=self._track_fitness_activity
        )
        
        # Register health monitoring tool
        self.register_tool(
            name="health_analyzer",
            description="Analyze health metrics and provide wellness insights",
            input_schema={
                "type": "object",
                "properties": {
                    "metrics": {
                        "type": "object",
                        "properties": {
                            "weight_kg": {"type": "number", "description": "Current weight in kg"},
                            "body_fat_percentage": {"type": "number", "description": "Body fat percentage"},
                            "muscle_mass_kg": {"type": "number", "description": "Muscle mass in kg"},
                            "resting_heart_rate": {"type": "integer", "description": "Resting heart rate BPM"},
                            "blood_pressure_systolic": {"type": "integer", "description": "Systolic blood pressure"},
                            "blood_pressure_diastolic": {"type": "integer", "description": "Diastolic blood pressure"},
                            "sleep_hours": {"type": "number", "description": "Hours of sleep last night"},
                            "stress_level": {"type": "integer", "minimum": 1, "maximum": 10, "description": "Stress level 1-10"},
                            "energy_level": {"type": "integer", "minimum": 1, "maximum": 10, "description": "Energy level 1-10"}
                        },
                        "description": "Health metrics to analyze"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["comprehensive", "fitness", "wellness", "risk_assessment"],
                        "default": "comprehensive",
                        "description": "Type of health analysis to perform"
                    },
                    "time_period": {
                        "type": "string",
                        "enum": ["daily", "weekly", "monthly", "quarterly"],
                        "default": "weekly",
                        "description": "Time period for trend analysis"
                    }
                },
                "required": ["metrics"]
            },
            function=self._analyze_health
        )
        
        # Register workout planner tool
        self.register_tool(
            name="workout_planner",
            description="Create personalized workout plans and exercise routines",
            input_schema={
                "type": "object",
                "properties": {
                    "fitness_goals": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["weight_loss", "muscle_gain", "endurance", "strength", "flexibility", "general_fitness"]
                        },
                        "description": "Primary fitness goals"
                    },
                    "fitness_level": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "advanced"],
                        "description": "Current fitness level"
                    },
                    "available_equipment": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Available exercise equipment"
                    },
                    "workout_duration": {
                        "type": "integer",
                        "description": "Preferred workout duration in minutes"
                    },
                    "frequency_per_week": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 7,
                        "description": "Number of workout sessions per week"
                    },
                    "preferred_activities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Preferred types of activities"
                    },
                    "limitations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Physical limitations or injuries to consider"
                    },
                    "plan_duration_weeks": {
                        "type": "integer",
                        "default": 4,
                        "description": "Duration of workout plan in weeks"
                    }
                },
                "required": ["fitness_goals", "fitness_level", "workout_duration", "frequency_per_week"]
            },
            function=self._create_workout_plan
        )
        
        # Register recovery monitor tool
        self.register_tool(
            name="recovery_monitor",
            description="Monitor recovery status and provide rest recommendations",
            input_schema={
                "type": "object",
                "properties": {
                    "recent_workouts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string", "format": "date"},
                                "activity": {"type": "string"},
                                "intensity": {"type": "string", "enum": ["low", "moderate", "high", "very_high"]},
                                "duration": {"type": "integer"},
                                "muscle_groups": {"type": "array", "items": {"type": "string"}}
                            }
                        },
                        "description": "Recent workout history"
                    },
                    "recovery_metrics": {
                        "type": "object",
                        "properties": {
                            "sleep_quality": {"type": "integer", "minimum": 1, "maximum": 10},
                            "muscle_soreness": {"type": "integer", "minimum": 1, "maximum": 10},
                            "energy_level": {"type": "integer", "minimum": 1, "maximum": 10},
                            "motivation": {"type": "integer", "minimum": 1, "maximum": 10},
                            "resting_heart_rate": {"type": "integer"},
                            "heart_rate_variability": {"type": "number"}
                        },
                        "description": "Current recovery indicators"
                    },
                    "assessment_type": {
                        "type": "string",
                        "enum": ["quick", "detailed", "prediction"],
                        "default": "quick",
                        "description": "Type of recovery assessment"
                    }
                },
                "required": ["recovery_metrics"]
            },
            function=self._assess_recovery
        )
        
        # Register resources
        self.register_resource(
            uri="luna://exercise-database",
            name="Exercise Database",
            description="Comprehensive database of exercises with instructions and muscle group targeting",
            mime_type="application/json"
        )
        
        self.register_resource(
            uri="luna://health-guidelines", 
            name="Health Guidelines",
            description="Evidence-based health and fitness guidelines and recommendations",
            mime_type="text/markdown"
        )
        
        self.register_resource(
            uri="luna://recovery-protocols",
            name="Recovery Protocols",
            description="Recovery strategies and protocols for optimal performance",
            mime_type="application/json"
        )
        
        self.register_resource(
            uri="luna://nutrition-fitness",
            name="Fitness Nutrition Guide",
            description="Nutrition guidelines for fitness and performance optimization",
            mime_type="text/markdown"
        )
        
        self.logger.info("Luna MCP Server initialized with 4 tools and 4 resources")
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute tool using legacy tool classes if function not provided"""
        if tool_name == "fitness_tracker":
            return await self._track_fitness_activity(arguments)
        elif tool_name == "health_analyzer":
            return await self._analyze_health(arguments)
        elif tool_name == "workout_planner":
            return await self._create_workout_plan(arguments)
        elif tool_name == "recovery_monitor":
            return await self._assess_recovery(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _track_fitness_activity(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Track a fitness activity"""
        try:
            # Extract parameters
            activity_type = arguments.get("activity_type")
            duration_minutes = arguments.get("duration_minutes")
            intensity = arguments.get("intensity")
            calories_burned = arguments.get("calories_burned")
            heart_rate_avg = arguments.get("heart_rate_avg")
            distance_km = arguments.get("distance_km")
            notes = arguments.get("notes", "")
            date = arguments.get("date", datetime.now().strftime("%Y-%m-%d"))
            
            # Calculate estimated calories if not provided
            if not calories_burned:
                # Simple calorie estimation based on activity and intensity
                base_calories = {
                    "running": 10,
                    "cycling": 8,
                    "swimming": 11,
                    "weightlifting": 6,
                    "yoga": 3,
                    "walking": 4,
                    "cardio": 9,
                    "strength": 6
                }
                
                intensity_multiplier = {
                    "low": 0.7,
                    "moderate": 1.0,
                    "high": 1.3,
                    "very_high": 1.6
                }
                
                calories_burned = int(
                    base_calories.get(activity_type, 7) * 
                    duration_minutes * 
                    intensity_multiplier.get(intensity, 1.0)
                )
            
            # Create activity record
            activity_record = {
                "activity_id": f"activity_{int(datetime.now().timestamp())}",
                "date": date,
                "activity_type": activity_type,
                "duration_minutes": duration_minutes,
                "intensity": intensity,
                "calories_burned": calories_burned,
                "heart_rate_avg": heart_rate_avg,
                "distance_km": distance_km,
                "notes": notes,
                "timestamp": datetime.now().isoformat(),
                "performance_metrics": {
                    "calories_per_minute": round(calories_burned / duration_minutes, 2),
                    "intensity_score": {"low": 2, "moderate": 5, "high": 7, "very_high": 9}.get(intensity, 5)
                }
            }
            
            # Add distance-based metrics for cardio activities
            if distance_km and activity_type in ["running", "cycling", "swimming", "walking"]:
                activity_record["performance_metrics"]["pace_min_per_km"] = round(duration_minutes / distance_km, 2)
                activity_record["performance_metrics"]["speed_kmh"] = round(distance_km / (duration_minutes / 60), 2)
            
            # Generate progress insights
            progress_insights = {
                "achievement_level": "good" if calories_burned > duration_minutes * 5 else "moderate",
                "intensity_rating": intensity,
                "recommendations": [],
                "next_goals": []
            }
            
            # Add recommendations based on activity
            if intensity == "low":
                progress_insights["recommendations"].append("Consider increasing intensity gradually for better results")
            elif intensity == "very_high":
                progress_insights["recommendations"].append("Great intensity! Make sure to allow adequate recovery time")
                
            if duration_minutes < 30:
                progress_insights["next_goals"].append("Try to extend duration to 30+ minutes for optimal cardiovascular benefits")
            
            return {
                "success": True,
                "activity_record": activity_record,
                "progress_insights": progress_insights,
                "summary": f"Tracked {activity_type} session: {duration_minutes}min, {calories_burned} calories burned"
            }
            
        except Exception as e:
            self.logger.error(f"Fitness tracking error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to track fitness activity"
            }
    
    async def _analyze_health(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze health metrics"""
        try:
            metrics = arguments.get("metrics", {})
            analysis_type = arguments.get("analysis_type", "comprehensive")
            time_period = arguments.get("time_period", "weekly")
            
            # Perform health analysis
            health_analysis = {
                "analysis_id": f"health_{int(datetime.now().timestamp())}",
                "timestamp": datetime.now().isoformat(),
                "analysis_type": analysis_type,
                "time_period": time_period,
                "metrics_analyzed": list(metrics.keys()),
                "overall_health_score": 0,
                "category_scores": {},
                "insights": [],
                "recommendations": [],
                "alerts": []
            }
            
            # Analyze different health categories
            total_score = 0
            category_count = 0
            
            # Physical metrics analysis
            if any(key in metrics for key in ["weight_kg", "body_fat_percentage", "muscle_mass_kg"]):
                physical_score = 75  # Mock score
                bmi = None
                
                if "weight_kg" in metrics:
                    # Assuming average height for BMI calculation (placeholder)
                    height_m = 1.7  # This should come from user profile
                    bmi = metrics["weight_kg"] / (height_m ** 2)
                    
                    if 18.5 <= bmi <= 24.9:
                        physical_score += 10
                    elif 25 <= bmi <= 29.9:
                        physical_score += 5
                        health_analysis["insights"].append("BMI indicates overweight range")
                    elif bmi >= 30:
                        health_analysis["alerts"].append("BMI indicates obesity - consult healthcare provider")
                
                if "body_fat_percentage" in metrics:
                    bf_percent = metrics["body_fat_percentage"]
                    if 10 <= bf_percent <= 20:  # Healthy range varies by gender
                        physical_score += 10
                        health_analysis["insights"].append("Body fat percentage in healthy range")
                    elif bf_percent > 25:
                        health_analysis["recommendations"].append("Consider incorporating more cardiovascular exercise")
                
                health_analysis["category_scores"]["physical_health"] = min(100, physical_score)
                total_score += physical_score
                category_count += 1
            
            # Cardiovascular analysis
            if any(key in metrics for key in ["resting_heart_rate", "blood_pressure_systolic", "blood_pressure_diastolic"]):
                cardio_score = 70
                
                if "resting_heart_rate" in metrics:
                    rhr = metrics["resting_heart_rate"]
                    if 60 <= rhr <= 80:
                        cardio_score += 15
                        health_analysis["insights"].append("Resting heart rate in excellent range")
                    elif rhr > 100:
                        health_analysis["alerts"].append("High resting heart rate - consider medical consultation")
                        cardio_score -= 10
                
                if "blood_pressure_systolic" in metrics and "blood_pressure_diastolic" in metrics:
                    sys_bp = metrics["blood_pressure_systolic"]
                    dia_bp = metrics["blood_pressure_diastolic"]
                    
                    if sys_bp < 120 and dia_bp < 80:
                        cardio_score += 15
                        health_analysis["insights"].append("Blood pressure in optimal range")
                    elif sys_bp >= 140 or dia_bp >= 90:
                        health_analysis["alerts"].append("High blood pressure detected - seek medical advice")
                        cardio_score -= 15
                
                health_analysis["category_scores"]["cardiovascular_health"] = max(0, min(100, cardio_score))
                total_score += cardio_score
                category_count += 1
            
            # Wellness analysis
            if any(key in metrics for key in ["sleep_hours", "stress_level", "energy_level"]):
                wellness_score = 60
                
                if "sleep_hours" in metrics:
                    sleep = metrics["sleep_hours"]
                    if 7 <= sleep <= 9:
                        wellness_score += 20
                        health_analysis["insights"].append("Sleep duration in optimal range")
                    elif sleep < 6:
                        health_analysis["recommendations"].append("Aim for 7-9 hours of sleep for better recovery")
                        wellness_score -= 10
                
                if "stress_level" in metrics:
                    stress = metrics["stress_level"]
                    if stress <= 3:
                        wellness_score += 15
                    elif stress >= 7:
                        health_analysis["recommendations"].append("Consider stress management techniques like meditation or yoga")
                        wellness_score -= 10
                
                if "energy_level" in metrics:
                    energy = metrics["energy_level"]
                    if energy >= 7:
                        wellness_score += 10
                        health_analysis["insights"].append("Good energy levels indicate overall wellness")
                    elif energy <= 4:
                        health_analysis["recommendations"].append("Low energy may indicate need for better nutrition or sleep")
                
                health_analysis["category_scores"]["wellness"] = max(0, min(100, wellness_score))
                total_score += wellness_score
                category_count += 1
            
            # Calculate overall score
            if category_count > 0:
                health_analysis["overall_health_score"] = round(total_score / category_count, 1)
            
            # Add general recommendations
            if health_analysis["overall_health_score"] < 70:
                health_analysis["recommendations"].extend([
                    "Focus on consistent exercise routine",
                    "Prioritize quality sleep",
                    "Consider consulting with healthcare professionals"
                ])
            elif health_analysis["overall_health_score"] >= 85:
                health_analysis["insights"].append("Excellent overall health metrics - maintain current lifestyle!")
            
            return {
                "success": True,
                "health_analysis": health_analysis,
                "summary": f"Health analysis complete - Overall score: {health_analysis['overall_health_score']}/100",
                "action_items": len(health_analysis["recommendations"]) + len(health_analysis["alerts"])
            }
            
        except Exception as e:
            self.logger.error(f"Health analysis error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to analyze health metrics"
            }
    
    async def _create_workout_plan(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a personalized workout plan"""
        try:
            fitness_goals = arguments.get("fitness_goals", [])
            fitness_level = arguments.get("fitness_level")
            available_equipment = arguments.get("available_equipment", [])
            workout_duration = arguments.get("workout_duration")
            frequency_per_week = arguments.get("frequency_per_week")
            preferred_activities = arguments.get("preferred_activities", [])
            limitations = arguments.get("limitations", [])
            plan_duration_weeks = arguments.get("plan_duration_weeks", 4)
            
            # Create workout plan structure
            workout_plan = {
                "plan_id": f"workout_plan_{int(datetime.now().timestamp())}",
                "created_date": datetime.now().isoformat(),
                "plan_details": {
                    "duration_weeks": plan_duration_weeks,
                    "frequency_per_week": frequency_per_week,
                    "workout_duration": workout_duration,
                    "fitness_level": fitness_level,
                    "primary_goals": fitness_goals
                },
                "weekly_schedule": [],
                "exercise_library": [],
                "progression_plan": {},
                "safety_guidelines": []
            }
            
            # Generate weekly schedules
            for week in range(plan_duration_weeks):
                weekly_plan = {
                    "week": week + 1,
                    "focus": self._get_weekly_focus(fitness_goals, week),
                    "workouts": []
                }
                
                # Generate workouts for this week
                workout_types = self._determine_workout_types(fitness_goals, frequency_per_week)
                
                for day in range(frequency_per_week):
                    workout_type = workout_types[day % len(workout_types)]
                    
                    workout = {
                        "day": day + 1,
                        "type": workout_type,
                        "duration_minutes": workout_duration,
                        "exercises": self._generate_exercises(
                            workout_type, 
                            fitness_level, 
                            available_equipment, 
                            limitations,
                            workout_duration
                        ),
                        "intensity": self._get_workout_intensity(fitness_level, week)
                    }
                    
                    weekly_plan["workouts"].append(workout)
                
                workout_plan["weekly_schedule"].append(weekly_plan)
            
            # Add progression plan
            workout_plan["progression_plan"] = {
                "week_1_2": "Foundation building - focus on form and adaptation",
                "week_3_4": "Intensity increase - progressive overload begins",
                "beyond_week_4": "Advanced progression - increase weights/reps by 5-10%"
            }
            
            # Add safety guidelines
            workout_plan["safety_guidelines"] = [
                "Always warm up for 5-10 minutes before exercising",
                "Cool down and stretch after each workout",
                "Listen to your body - rest if experiencing pain",
                "Stay hydrated throughout your workout",
                "Maintain proper form over heavy weights"
            ]
            
            if limitations:
                workout_plan["safety_guidelines"].append(f"Special considerations for: {', '.join(limitations)}")
            
            # Generate exercise library
            workout_plan["exercise_library"] = self._build_exercise_library(
                fitness_goals, 
                available_equipment, 
                fitness_level
            )
            
            # Calculate plan metrics
            total_workouts = frequency_per_week * plan_duration_weeks
            estimated_calories_per_workout = workout_duration * 8  # Rough estimate
            total_estimated_calories = total_workouts * estimated_calories_per_workout
            
            return {
                "success": True,
                "workout_plan": workout_plan,
                "plan_metrics": {
                    "total_workouts": total_workouts,
                    "total_training_hours": round((total_workouts * workout_duration) / 60, 1),
                    "estimated_total_calories": total_estimated_calories,
                    "equipment_required": len(available_equipment) > 0,
                    "difficulty_progression": fitness_level
                },
                "summary": f"Created {plan_duration_weeks}-week workout plan with {frequency_per_week} sessions/week focusing on {', '.join(fitness_goals)}"
            }
            
        except Exception as e:
            self.logger.error(f"Workout planning error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create workout plan"
            }
    
    async def _assess_recovery(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Assess recovery status and provide recommendations"""
        try:
            recent_workouts = arguments.get("recent_workouts", [])
            recovery_metrics = arguments.get("recovery_metrics", {})
            assessment_type = arguments.get("assessment_type", "quick")
            
            # Perform recovery assessment
            recovery_assessment = {
                "assessment_id": f"recovery_{int(datetime.now().timestamp())}",
                "timestamp": datetime.now().isoformat(),
                "assessment_type": assessment_type,
                "overall_recovery_score": 0,
                "recovery_categories": {},
                "recommendations": [],
                "next_workout_suggestion": {},
                "warning_flags": []
            }
            
            # Analyze recovery metrics
            recovery_score = 50  # Base score
            
            # Sleep quality impact
            if "sleep_quality" in recovery_metrics:
                sleep_quality = recovery_metrics["sleep_quality"]
                sleep_impact = (sleep_quality - 5) * 10  # Scale around 5
                recovery_score += sleep_impact
                recovery_assessment["recovery_categories"]["sleep"] = {
                    "score": sleep_quality * 10,
                    "status": "excellent" if sleep_quality >= 8 else "good" if sleep_quality >= 6 else "poor"
                }
                
                if sleep_quality <= 4:
                    recovery_assessment["warning_flags"].append("Poor sleep quality affecting recovery")
            
            # Muscle soreness impact
            if "muscle_soreness" in recovery_metrics:
                soreness = recovery_metrics["muscle_soreness"]
                soreness_impact = (10 - soreness) * 5  # Inverted scale
                recovery_score += soreness_impact
                recovery_assessment["recovery_categories"]["muscle_recovery"] = {
                    "score": (10 - soreness) * 10,
                    "status": "ready" if soreness <= 3 else "moderate" if soreness <= 6 else "high_soreness"
                }
                
                if soreness >= 8:
                    recovery_assessment["warning_flags"].append("High muscle soreness - consider rest day")
            
            # Energy level impact
            if "energy_level" in recovery_metrics:
                energy = recovery_metrics["energy_level"]
                energy_impact = (energy - 5) * 8
                recovery_score += energy_impact
                recovery_assessment["recovery_categories"]["energy"] = {
                    "score": energy * 10,
                    "status": "high" if energy >= 8 else "moderate" if energy >= 5 else "low"
                }
            
            # Heart rate metrics
            if "resting_heart_rate" in recovery_metrics:
                rhr = recovery_metrics["resting_heart_rate"]
                # Assume elevated RHR indicates poor recovery
                if 50 <= rhr <= 70:
                    recovery_score += 10
                elif rhr > 80:
                    recovery_score -= 15
                    recovery_assessment["warning_flags"].append("Elevated resting heart rate may indicate incomplete recovery")
            
            # Analyze workout load from recent workouts
            if recent_workouts:
                workout_load = 0
                for workout in recent_workouts[-7:]:  # Last 7 days
                    intensity_weight = {"low": 1, "moderate": 2, "high": 3, "very_high": 4}
                    workout_load += workout.get("duration", 0) * intensity_weight.get(workout.get("intensity", "moderate"), 2)
                
                if workout_load > 800:  # High weekly load
                    recovery_score -= 10
                    recovery_assessment["warning_flags"].append("High training load - prioritize recovery")
                
                recovery_assessment["recovery_categories"]["training_load"] = {
                    "score": max(0, 100 - (workout_load / 10)),
                    "weekly_load": workout_load,
                    "status": "high" if workout_load > 800 else "moderate" if workout_load > 400 else "manageable"
                }
            
            # Finalize overall score
            recovery_assessment["overall_recovery_score"] = max(0, min(100, recovery_score))
            
            # Generate recommendations based on score
            if recovery_assessment["overall_recovery_score"] >= 80:
                recovery_assessment["recommendations"] = [
                    "Great recovery status! Ready for high-intensity training",
                    "Consider progressive overload in next workout"
                ]
                recovery_assessment["next_workout_suggestion"] = {
                    "intensity": "high",
                    "type": "strength or high-intensity cardio",
                    "duration": "normal to extended"
                }
            elif recovery_assessment["overall_recovery_score"] >= 60:
                recovery_assessment["recommendations"] = [
                    "Moderate recovery status - proceed with planned workout",
                    "Focus on proper warm-up and listen to your body"
                ]
                recovery_assessment["next_workout_suggestion"] = {
                    "intensity": "moderate",
                    "type": "planned workout with attention to form",
                    "duration": "normal"
                }
            else:
                recovery_assessment["recommendations"] = [
                    "Poor recovery status - consider rest day or active recovery",
                    "Focus on sleep, hydration, and stress management",
                    "Light activity like walking or gentle stretching recommended"
                ]
                recovery_assessment["next_workout_suggestion"] = {
                    "intensity": "low or rest",
                    "type": "active recovery or complete rest",
                    "duration": "short if any"
                }
                recovery_assessment["warning_flags"].append("Overall poor recovery - prioritize rest")
            
            return {
                "success": True,
                "recovery_assessment": recovery_assessment,
                "summary": f"Recovery score: {recovery_assessment['overall_recovery_score']}/100 - {recovery_assessment['next_workout_suggestion']['intensity']} intensity recommended",
                "warning_count": len(recovery_assessment["warning_flags"])
            }
            
        except Exception as e:
            self.logger.error(f"Recovery assessment error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to assess recovery status"
            }
    
    def _get_weekly_focus(self, goals: List[str], week: int) -> str:
        """Get focus theme for a specific week"""
        if "strength" in goals:
            focuses = ["Foundation Building", "Progressive Loading", "Intensity Focus", "Peak Performance"]
        elif "endurance" in goals:
            focuses = ["Base Building", "Aerobic Development", "Tempo Training", "Performance Testing"]
        else:
            focuses = ["Adaptation", "Development", "Intensification", "Optimization"]
        return focuses[week % len(focuses)]
    
    def _determine_workout_types(self, goals: List[str], frequency: int) -> List[str]:
        """Determine workout types based on goals and frequency"""
        if "strength" in goals:
            types = ["strength", "strength", "cardio", "strength", "flexibility"]
        elif "weight_loss" in goals:
            types = ["cardio", "strength", "cardio", "strength", "cardio"]
        elif "endurance" in goals:
            types = ["cardio", "strength", "cardio", "cardio", "flexibility"]
        else:
            types = ["strength", "cardio", "flexibility", "strength", "cardio"]
        
        return types[:frequency]
    
    def _generate_exercises(self, workout_type: str, fitness_level: str, equipment: List[str], limitations: List[str], duration: int) -> List[Dict]:
        """Generate exercises for a specific workout"""
        exercises = []
        
        if workout_type == "strength":
            base_exercises = [
                {"name": "Push-ups", "sets": 3, "reps": "10-15", "muscle_groups": ["chest", "shoulders", "triceps"]},
                {"name": "Squats", "sets": 3, "reps": "12-20", "muscle_groups": ["quads", "glutes", "core"]},
                {"name": "Lunges", "sets": 3, "reps": "10 each leg", "muscle_groups": ["legs", "glutes"]},
                {"name": "Plank", "sets": 3, "duration": "30-60 seconds", "muscle_groups": ["core"]},
            ]
        elif workout_type == "cardio":
            base_exercises = [
                {"name": "Jumping Jacks", "duration": "2 minutes", "intensity": "moderate"},
                {"name": "High Knees", "duration": "1 minute", "intensity": "high"},
                {"name": "Burpees", "sets": 3, "reps": "5-10", "intensity": "high"},
                {"name": "Mountain Climbers", "duration": "1 minute", "intensity": "high"},
            ]
        else:  # flexibility
            base_exercises = [
                {"name": "Forward Fold", "duration": "30 seconds", "type": "stretch"},
                {"name": "Cat-Cow Stretch", "duration": "1 minute", "type": "dynamic"},
                {"name": "Child's Pose", "duration": "30 seconds", "type": "rest"},
                {"name": "Downward Dog", "duration": "30 seconds", "type": "stretch"},
            ]
        
        # Adjust for fitness level
        if fitness_level == "beginner":
            for exercise in base_exercises:
                if "sets" in exercise:
                    exercise["sets"] = max(1, exercise["sets"] - 1)
                if "reps" in exercise and "-" in exercise["reps"]:
                    exercise["reps"] = exercise["reps"].split("-")[0]
        elif fitness_level == "advanced":
            for exercise in base_exercises:
                if "sets" in exercise:
                    exercise["sets"] += 1
                if "duration" in exercise and "second" in exercise["duration"]:
                    # Increase duration for advanced
                    pass
        
        return base_exercises[:6]  # Limit exercises based on duration
    
    def _get_workout_intensity(self, fitness_level: str, week: int) -> str:
        """Determine workout intensity based on level and progression"""
        base_intensities = {
            "beginner": ["low", "low", "moderate", "moderate"],
            "intermediate": ["moderate", "moderate", "high", "high"], 
            "advanced": ["moderate", "high", "high", "very_high"]
        }
        
        intensities = base_intensities.get(fitness_level, base_intensities["intermediate"])
        return intensities[week % len(intensities)]
    
    def _build_exercise_library(self, goals: List[str], equipment: List[str], fitness_level: str) -> List[Dict]:
        """Build a comprehensive exercise library"""
        library = [
            {
                "name": "Push-up",
                "category": "strength",
                "muscle_groups": ["chest", "shoulders", "triceps", "core"],
                "equipment": "bodyweight",
                "difficulty": "beginner",
                "instructions": ["Start in plank position", "Lower body to ground", "Push back up to start"],
                "variations": ["knee push-ups", "diamond push-ups", "decline push-ups"]
            },
            {
                "name": "Squat",
                "category": "strength", 
                "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
                "equipment": "bodyweight",
                "difficulty": "beginner",
                "instructions": ["Feet shoulder-width apart", "Lower as if sitting back", "Return to standing"],
                "variations": ["jump squats", "goblet squats", "single-leg squats"]
            },
            {
                "name": "Burpee",
                "category": "cardio",
                "muscle_groups": ["full body"],
                "equipment": "bodyweight",
                "difficulty": "intermediate",
                "instructions": ["Start standing", "Drop to squat", "Jump back to plank", "Do push-up", "Jump feet forward", "Jump up"],
                "variations": ["half burpees", "burpee with tuck jump"]
            }
        ]
        
        return library
    
    async def _read_resource(self, uri: str) -> str:
        """Read resource content"""
        if uri == "luna://exercise-database":
            return json.dumps({
                "database": "Luna Exercise Database",
                "total_exercises": 500,
                "categories": ["strength", "cardio", "flexibility", "sports", "rehabilitation"],
                "last_updated": "2025-08-10",
                "sample_exercises": [
                    {
                        "name": "Deadlift",
                        "category": "strength",
                        "muscle_groups": ["hamstrings", "glutes", "lower_back"],
                        "equipment": "barbell",
                        "difficulty": "intermediate"
                    },
                    {
                        "name": "Interval Running",
                        "category": "cardio",
                        "equipment": "none",
                        "difficulty": "intermediate",
                        "duration": "20-30 minutes"
                    }
                ]
            }, indent=2)
        
        elif uri == "luna://health-guidelines":
            return """# Health & Fitness Guidelines

## Exercise Recommendations
- **Adults**: 150 minutes moderate aerobic activity OR 75 minutes vigorous activity per week
- **Strength Training**: 2+ days per week targeting all major muscle groups
- **Flexibility**: Daily stretching, especially after workouts

## Recovery Guidelines
- **Sleep**: 7-9 hours per night for optimal recovery
- **Rest Days**: At least 1-2 complete rest days per week
- **Hydration**: 8+ glasses of water daily, more during exercise

## Health Monitoring
- **Resting Heart Rate**: 60-100 BPM (lower is generally better for fitness)
- **Blood Pressure**: <120/80 mmHg optimal
- **Body Composition**: Focus on muscle mass and strength over weight alone

## Safety Priorities
1. Proper warm-up (5-10 minutes)
2. Correct form over heavy weights
3. Progressive overload (gradual increases)
4. Listen to your body - pain vs. discomfort
5. Cool-down and stretching (5-10 minutes)
"""
        
        elif uri == "luna://recovery-protocols":
            return json.dumps({
                "recovery_strategies": {
                    "sleep_optimization": {
                        "recommendations": ["7-9 hours nightly", "consistent bedtime", "dark, cool environment"],
                        "impact": "primary recovery driver"
                    },
                    "active_recovery": {
                        "activities": ["light walking", "gentle yoga", "swimming"],
                        "duration": "20-30 minutes",
                        "intensity": "very light"
                    },
                    "nutrition_timing": {
                        "post_workout": "protein within 30 minutes",
                        "carb_replenishment": "within 2 hours",
                        "hydration": "continuous throughout day"
                    },
                    "stress_management": {
                        "techniques": ["meditation", "deep breathing", "progressive relaxation"],
                        "frequency": "daily, 10-20 minutes"
                    }
                },
                "recovery_indicators": {
                    "positive": ["good sleep quality", "low muscle soreness", "high energy", "stable mood"],
                    "negative": ["fatigue", "elevated RHR", "decreased performance", "irritability"]
                }
            }, indent=2)
        
        elif uri == "luna://nutrition-fitness":
            return """# Fitness Nutrition Guide

## Pre-Workout Nutrition
- **Timing**: 1-3 hours before exercise
- **Carbohydrates**: For energy (banana, oatmeal, whole grain toast)
- **Protein**: Moderate amount (Greek yogurt, nuts)
- **Hydration**: 16-20 oz water 2-3 hours before

## During Workout
- **Hydration**: 6-12 oz every 15-20 minutes
- **Electrolytes**: For sessions >60 minutes
- **Quick Carbs**: For endurance activities >90 minutes

## Post-Workout Recovery
- **Protein**: 20-40g within 30 minutes (whey, chicken, eggs)
- **Carbohydrates**: 1.5x protein amount for glycogen replenishment
- **Fluids**: 150% of fluid lost through sweat

## Daily Nutrition for Fitness
- **Protein**: 0.8-2.2g per kg body weight (higher for strength training)
- **Carbohydrates**: 45-65% of total calories
- **Fats**: 20-35% of total calories
- **Fiber**: 25-35g daily
- **Water**: Half body weight in ounces minimum

## Supplements to Consider
- **Creatine**: 3-5g daily for strength/power
- **Protein Powder**: If dietary intake insufficient
- **Vitamin D**: If deficient (common)
- **Omega-3**: For inflammation reduction
"""
        
        else:
            raise ValueError(f"Unknown resource: {uri}")


async def main():
    """Run Luna MCP Server"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = LunaMCPServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())