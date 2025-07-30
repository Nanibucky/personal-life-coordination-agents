"""
Workout Planner Tool for Agent Luna
Personalized exercise program creation and management
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

from shared.mcp_framework.base_server import BaseMCPTool, ExecutionContext, ExecutionResult

class WorkoutPlannerTool(BaseMCPTool):
    """Personalized exercise program creation and management"""
    
    def __init__(self):
        super().__init__("workout_planner", "Create personalized workout programs")
        self.exercise_database = self._load_exercise_database()
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create_program", "generate_workout", "adapt_program", "track_progress"]
                },
                "fitness_goals": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["weight_loss", "muscle_gain", "endurance", "strength", "flexibility", "sports_performance"]
                    }
                },
                "constraints": {
                    "type": "object",
                    "properties": {
                        "time_available": {"type": "integer"},
                        "equipment": {"type": "array"},
                        "experience_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                        "injuries": {"type": "array"}
                    }
                },
                "current_fitness": {"type": "object"},
                "preferences": {"type": "object"}
            },
            "required": ["action", "fitness_goals"]
        }
    
    def get_return_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "workout_program": {"type": "object"},
                "daily_workout": {"type": "object"},
                "progress_tracking": {"type": "object"},
                "adaptations": {"type": "array"}
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        action = parameters["action"]
        fitness_goals = parameters["fitness_goals"]
        
        try:
            if action == "create_program":
                result = await self._create_workout_program(
                    fitness_goals,
                    parameters.get("constraints", {}),
                    parameters.get("current_fitness", {}),
                    context
                )
            elif action == "generate_workout":
                result = await self._generate_daily_workout(
                    fitness_goals,
                    parameters.get("constraints", {}),
                    context
                )
            elif action == "adapt_program":
                result = await self._adapt_workout_program(
                    parameters.get("current_fitness", {}),
                    context
                )
            else:
                result = await self._track_workout_progress(
                    parameters.get("workout_data", {}),
                    context
                )
            
            return ExecutionResult(success=True, result=result, execution_time=2.0)
            
        except Exception as e:
            self.logger.error(f"Workout planning failed: {e}")
            return ExecutionResult(success=False, error=str(e), execution_time=0.0)
    
    def _load_exercise_database(self) -> Dict[str, Any]:
        """Load exercise database"""
        return {
            "strength": [
                {"name": "Push-ups", "muscle_groups": ["chest", "triceps", "shoulders"], "equipment": "bodyweight"},
                {"name": "Squats", "muscle_groups": ["quadriceps", "glutes", "hamstrings"], "equipment": "bodyweight"},
                {"name": "Deadlifts", "muscle_groups": ["hamstrings", "glutes", "back"], "equipment": "barbell"},
                {"name": "Pull-ups", "muscle_groups": ["back", "biceps"], "equipment": "pull-up bar"},
                {"name": "Lunges", "muscle_groups": ["quadriceps", "glutes"], "equipment": "bodyweight"},
                {"name": "Plank", "muscle_groups": ["core", "shoulders"], "equipment": "bodyweight"}
            ],
            "cardio": [
                {"name": "Running", "intensity": "variable", "equipment": "none"},
                {"name": "Cycling", "intensity": "variable", "equipment": "bike"},
                {"name": "Jump Rope", "intensity": "high", "equipment": "jump rope"},
                {"name": "Burpees", "intensity": "very_high", "equipment": "bodyweight"},
                {"name": "Mountain Climbers", "intensity": "high", "equipment": "bodyweight"},
                {"name": "High Knees", "intensity": "moderate", "equipment": "bodyweight"}
            ],
            "flexibility": [
                {"name": "Yoga Flow", "duration": 30, "equipment": "yoga mat"},
                {"name": "Dynamic Stretching", "duration": 15, "equipment": "none"},
                {"name": "Foam Rolling", "duration": 20, "equipment": "foam roller"},
                {"name": "Static Stretching", "duration": 10, "equipment": "none"}
            ]
        }
    
    async def _create_workout_program(self, fitness_goals: List[str], constraints: Dict, 
                                    current_fitness: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Create a comprehensive workout program"""
        
        # Analyze goals and create program structure
        program_structure = self._analyze_goals_and_create_structure(fitness_goals, constraints)
        
        # Generate weekly schedule
        weekly_schedule = {}
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            if day in program_structure['training_days']:
                workout = self._generate_workout_for_day(
                    program_structure['daily_focus'][day],
                    constraints,
                    fitness_goals
                )
                weekly_schedule[day] = workout
            else:
                weekly_schedule[day] = {"type": "rest", "activities": ["light_stretching", "walk"]}
        
        program = {
            "program_id": f"program_{datetime.utcnow().timestamp()}",
            "name": f"Personalized {'+'.join(fitness_goals).title()} Program",
            "duration_weeks": 12,
            "weekly_schedule": weekly_schedule,
            "progression_plan": self._create_progression_plan(fitness_goals),
            "program_goals": fitness_goals,
            "constraints": constraints,
            "expected_outcomes": self._predict_outcomes(fitness_goals, constraints),
            "created_date": datetime.utcnow().isoformat()
        }
        
        return {"workout_program": program}
    
    def _analyze_goals_and_create_structure(self, goals: List[str], constraints: Dict) -> Dict[str, Any]:
        """Analyze fitness goals and create program structure"""
        time_available = constraints.get("time_available", 60)  # minutes per session
        experience_level = constraints.get("experience_level", "intermediate")
        
        # Determine training frequency based on goals and time
        if "strength" in goals or "muscle_gain" in goals:
            training_days = ['monday', 'wednesday', 'friday', 'saturday']
            daily_focus = {
                'monday': 'upper_body_strength',
                'wednesday': 'lower_body_strength',
                'friday': 'full_body_strength',
                'saturday': 'cardio_conditioning'
            }
        elif "endurance" in goals:
            training_days = ['tuesday', 'thursday', 'saturday', 'sunday']
            daily_focus = {
                'tuesday': 'interval_training',
                'thursday': 'steady_state_cardio',
                'saturday': 'long_duration_cardio',
                'sunday': 'recovery_cardio'
            }
        else:  # General fitness
            training_days = ['monday', 'wednesday', 'friday']
            daily_focus = {
                'monday': 'full_body_strength',
                'wednesday': 'cardio_strength_circuit',
                'friday': 'flexibility_recovery'
            }
        
        return {
            "training_days": training_days,
            "daily_focus": daily_focus,
            "sessions_per_week": len(training_days),
            "session_duration": time_available
        }
    
    def _generate_workout_for_day(self, focus: str, constraints: Dict, goals: List[str]) -> Dict[str, Any]:
        """Generate specific workout for a given day"""
        exercises = []
        
        if focus == "upper_body_strength":
            exercises = [
                {"name": "Push-ups", "sets": 3, "reps": "8-12", "rest": 60},
                {"name": "Pull-ups", "sets": 3, "reps": "5-8", "rest": 90},
                {"name": "Dips", "sets": 3, "reps": "8-10", "rest": 60},
                {"name": "Pike Push-ups", "sets": 2, "reps": "6-8", "rest": 60}
            ]
        elif focus == "lower_body_strength":
            exercises = [
                {"name": "Squats", "sets": 4, "reps": "10-15", "rest": 90},
                {"name": "Single-leg RDL", "sets": 3, "reps": "8-10 each", "rest": 60},
                {"name": "Lunges", "sets": 3, "reps": "10-12 each", "rest": 60},
                {"name": "Calf Raises", "sets": 3, "reps": "15-20", "rest": 45}
            ]
        elif focus == "cardio_conditioning":
            exercises = [
                {"name": "Burpees", "sets": 4, "duration": "30 seconds", "rest": 30},
                {"name": "Mountain Climbers", "sets": 4, "duration": "30 seconds", "rest": 30},
                {"name": "Jump Squats", "sets": 4, "duration": "30 seconds", "rest": 30},
                {"name": "High Knees", "sets": 4, "duration": "30 seconds", "rest": 30}
            ]
        elif focus == "full_body_strength":
            exercises = [
                {"name": "Squats", "sets": 3, "reps": "12-15", "rest": 60},
                {"name": "Push-ups", "sets": 3, "reps": "8-12", "rest": 60},
                {"name": "Plank", "sets": 3, "duration": "45 seconds", "rest": 45},
                {"name": "Lunges", "sets": 2, "reps": "10 each leg", "rest": 60}
            ]
        else:  # flexibility_recovery
            exercises = [
                {"name": "Dynamic Stretching", "duration": "10 minutes"},
                {"name": "Yoga Flow", "duration": "20 minutes"},
                {"name": "Foam Rolling", "duration": "10 minutes"}
            ]
        
        return {
            "focus": focus,
            "exercises": exercises,
            "warm_up": ["5 min dynamic stretching", "Joint mobility"],
            "cool_down": ["5 min static stretching", "Deep breathing"],
            "estimated_duration": constraints.get("time_available", 45),
            "intensity": "moderate_high",
            "equipment_needed": self._get_required_equipment(exercises)
        }
    
    def _create_progression_plan(self, goals: List[str]) -> Dict[str, Any]:
        """Create progression plan for the program"""
        return {
            "week_1_4": {
                "focus": "foundation_building",
                "progression": "Learn proper form, build base fitness",
                "load_increase": "0%"
            },
            "week_5_8": {
                "focus": "strength_development",
                "progression": "Increase intensity and volume",
                "load_increase": "10-15%"
            },
            "week_9_12": {
                "focus": "peak_performance",
                "progression": "Maximize goal-specific adaptations",
                "load_increase": "20-25%"
            }
        }
    
    def _predict_outcomes(self, goals: List[str], constraints: Dict) -> Dict[str, Any]:
        """Predict expected outcomes based on goals and constraints"""
        experience = constraints.get("experience_level", "intermediate")
        time_per_week = constraints.get("sessions_per_week", 3) * constraints.get("time_available", 45)
        
        outcomes = {}
        
        if "weight_loss" in goals:
            outcomes["weight_loss"] = {
                "expected_loss_lbs": min(1.5 * 12, time_per_week / 60),
                "timeline_weeks": 12,
                "confidence": 0.78
            }
        
        if "strength" in goals or "muscle_gain" in goals:
            strength_gain = 25 if experience == "beginner" else 15 if experience == "intermediate" else 8
            outcomes["strength_gain"] = {
                "expected_increase_percent": strength_gain,
                "timeline_weeks": 8,
                "confidence": 0.85
            }
        
        if "endurance" in goals:
            outcomes["endurance"] = {
                "expected_improvement": "20-30% increase in cardiovascular capacity",
                "timeline_weeks": 6,
                "confidence": 0.82
            }
        
        return outcomes
    
    def _get_required_equipment(self, exercises: List[Dict]) -> List[str]:
        """Determine equipment needed for exercises"""
        equipment = set()
        for exercise in exercises:
            if "Pull-ups" in exercise["name"]:
                equipment.add("pull-up bar")
            elif "Dips" in exercise["name"]:
                equipment.add("dip bars or chairs")
            elif "Foam Rolling" in exercise["name"]:
                equipment.add("foam roller")
            elif "Yoga" in exercise["name"]:
                equipment.add("yoga mat")
        
        return list(equipment) if equipment else ["bodyweight only"]
    
    async def _generate_daily_workout(self, fitness_goals: List[str], constraints: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Generate a single day's workout"""
        # Determine focus based on goals
        if "strength" in fitness_goals:
            focus = "full_body_strength"
        elif "endurance" in fitness_goals:
            focus = "cardio_conditioning"
        else:
            focus = "full_body_strength"
        
        workout = self._generate_workout_for_day(focus, constraints, fitness_goals)
        workout["workout_id"] = f"daily_{datetime.utcnow().timestamp()}"
        workout["date"] = datetime.utcnow().isoformat()
        
        return {"daily_workout": workout}
    
    async def _adapt_workout_program(self, current_fitness: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Adapt existing program based on progress"""
        adaptations = []
        
        # Mock adaptation logic
        if current_fitness.get("strength_improvement", 0) > 15:
            adaptations.append({
                "type": "increase_intensity",
                "description": "Increase weights or reps by 10%",
                "reason": "Strength gains detected"
            })
        
        if current_fitness.get("endurance_improvement", 0) > 20:
            adaptations.append({
                "type": "add_complexity",
                "description": "Add plyometric exercises",
                "reason": "Cardiovascular fitness improved"
            })
        
        return {
            "adaptations": adaptations,
            "adapted_date": datetime.utcnow().isoformat(),
            "next_review": (datetime.utcnow() + timedelta(weeks=2)).isoformat()
        }
    
    async def _track_workout_progress(self, workout_data: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Track progress from completed workouts"""
        progress = {
            "workout_completed": True,
            "completion_rate": workout_data.get("completion_percentage", 100),
            "difficulty_rating": workout_data.get("difficulty", 7),
            "energy_level": workout_data.get("energy_after", 6),
            "form_quality": workout_data.get("form_rating", 8),
            "improvements_noted": [
                "Increased reps on push-ups",
                "Better balance during lunges"
            ],
            "next_workout_adjustments": [
                "Increase squat reps to 15",
                "Add 30 seconds to plank hold"
            ]
        }
        
        return {"progress_tracking": progress}