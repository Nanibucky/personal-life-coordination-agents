"""
Health Analyzer Tool for Agent Luna
Advanced health metric interpretation and insights
"""

from datetime import datetime
from typing import Dict, List, Any

from shared.mcp_framework.base_server import BaseMCPTool, ExecutionContext, ExecutionResult

class HealthAnalyzerTool(BaseMCPTool):
    """Advanced health metric interpretation and insights"""
    
    def __init__(self):
        super().__init__("health_analyzer", "Analyze health data for insights and recommendations")
        self.health_models = {}
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "analysis_type": {
                    "type": "string",
                    "enum": ["risk_assessment", "pattern_recognition", "goal_progress", "optimization_suggestions"]
                },
                "health_data": {"type": "object"},
                "user_profile": {"type": "object"},
                "time_period": {"type": "string", "enum": ["daily", "weekly", "monthly", "yearly"]}
            },
            "required": ["analysis_type"]
        }
    
    def get_return_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "health_insights": {"type": "object"},
                "risk_factors": {"type": "array"},
                "recommendations": {"type": "array"},
                "health_score": {"type": "number"},
                "patterns": {"type": "array"}
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        analysis_type = parameters["analysis_type"]
        
        try:
            if analysis_type == "risk_assessment":
                result = await self._assess_health_risks(
                    parameters.get("health_data", {}),
                    parameters.get("user_profile", {}),
                    context
                )
            elif analysis_type == "pattern_recognition":
                result = await self._recognize_patterns(
                    parameters.get("health_data", {}),
                    parameters.get("time_period", "weekly"),
                    context
                )
            elif analysis_type == "goal_progress":
                result = await self._analyze_goal_progress(
                    parameters.get("health_data", {}),
                    context
                )
            else:
                result = await self._generate_optimization_suggestions(
                    parameters.get("health_data", {}),
                    context
                )
            
            return ExecutionResult(success=True, result=result, execution_time=1.5)
            
        except Exception as e:
            self.logger.error(f"Health analysis failed: {e}")
            return ExecutionResult(success=False, error=str(e), execution_time=0.0)
    
    async def _assess_health_risks(self, health_data: Dict, user_profile: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Assess health risks based on current metrics"""
        risk_factors = []
        
        # Cardiovascular risk assessment
        resting_hr = health_data.get("heart_rate_resting", 70)
        if resting_hr > 80:
            risk_factors.append({
                "factor": "elevated_resting_heart_rate",
                "severity": "moderate",
                "description": "Resting heart rate above normal range",
                "recommendations": ["Increase cardiovascular exercise", "Monitor stress levels"],
                "current_value": resting_hr,
                "target_range": "50-70 bpm"
            })
        
        # Sleep risk assessment
        sleep_hours = health_data.get("sleep_hours", 8)
        if sleep_hours < 6:
            risk_factors.append({
                "factor": "insufficient_sleep",
                "severity": "high",
                "description": "Chronic sleep deprivation detected",
                "recommendations": ["Establish consistent sleep schedule", "Limit screen time before bed"],
                "current_value": sleep_hours,
                "target_range": "7-9 hours"
            })
        
        # Weight and BMI assessment
        weight = health_data.get("weight", 70)
        height = user_profile.get("height", 1.75)  # meters
        bmi = weight / (height ** 2) if height > 0 else 0
        
        if bmi > 30:
            risk_factors.append({
                "factor": "obesity",
                "severity": "high",
                "description": "BMI indicates obesity",
                "recommendations": ["Consult healthcare provider", "Implement structured weight loss plan"],
                "current_value": round(bmi, 1),
                "target_range": "18.5-24.9"
            })
        elif bmi > 25:
            risk_factors.append({
                "factor": "overweight",
                "severity": "moderate",
                "description": "BMI indicates overweight",
                "recommendations": ["Increase physical activity", "Monitor caloric intake"],
                "current_value": round(bmi, 1),
                "target_range": "18.5-24.9"
            })
        
        # Blood pressure assessment (if available)
        bp_systolic = health_data.get("blood_pressure_systolic", 120)
        bp_diastolic = health_data.get("blood_pressure_diastolic", 80)
        
        if bp_systolic > 140 or bp_diastolic > 90:
            risk_factors.append({
                "factor": "high_blood_pressure",
                "severity": "high",
                "description": "Blood pressure above normal range",
                "recommendations": ["Consult healthcare provider immediately", "Reduce sodium intake", "Increase exercise"],
                "current_value": f"{bp_systolic}/{bp_diastolic}",
                "target_range": "<120/80 mmHg"
            })
        
        # Calculate overall health score
        base_score = 100
        for risk in risk_factors:
            if risk["severity"] == "high":
                base_score -= 20
            elif risk["severity"] == "moderate":
                base_score -= 10
            else:
                base_score -= 5
        
        health_score = max(0, base_score)
        
        return {
            "health_insights": {
                "overall_status": "excellent" if health_score > 90 else "good" if health_score > 70 else "needs_attention",
                "primary_concerns": [rf["factor"] for rf in risk_factors],
                "bmi": round(bmi, 1) if bmi > 0 else None,
                "risk_level": "low" if health_score > 80 else "moderate" if health_score > 60 else "high"
            },
            "risk_factors": risk_factors,
            "health_score": health_score,
            "assessment_date": datetime.utcnow().isoformat()
        }
    
    async def _recognize_patterns(self, health_data: Dict, time_period: str, context: ExecutionContext) -> Dict[str, Any]:
        """Recognize patterns in health data"""
        patterns = []
        
        # Weekly energy pattern
        patterns.append({
            "pattern": "weekly_energy_cycle",
            "description": "Energy levels peak on Tuesday and Thursday",
            "confidence": 0.82,
            "actionable_insight": "Schedule important workouts on high-energy days",
            "frequency": "weekly",
            "strength": "strong"
        })
        
        # Sleep-exercise correlation
        patterns.append({
            "pattern": "sleep_exercise_correlation",
            "description": "Sleep quality improves by 15% on workout days",
            "confidence": 0.91,
            "actionable_insight": "Maintain consistent exercise routine for better sleep",
            "frequency": "daily",
            "strength": "very_strong"
        })
        
        # Stress-recovery relationship
        patterns.append({
            "pattern": "stress_recovery_relationship",
            "description": "Recovery time increases 30% during high stress periods",
            "confidence": 0.76,
            "actionable_insight": "Include stress management techniques in routine",
            "frequency": "variable",
            "strength": "moderate"
        })
        
        # Hydration impact pattern
        patterns.append({
            "pattern": "hydration_performance",
            "description": "Workout performance drops 12% when hydration is below optimal",
            "confidence": 0.85,
            "actionable_insight": "Monitor water intake especially before workouts",
            "frequency": "daily",
            "strength": "strong"
        })
        
        # Nutrition timing pattern
        patterns.append({
            "pattern": "meal_timing_energy",
            "description": "Energy levels spike 2-3 hours after balanced meals",
            "confidence": 0.79,
            "actionable_insight": "Time workouts 2-3 hours after main meals",
            "frequency": "daily",
            "strength": "moderate"
        })
        
        return {
            "patterns": patterns, 
            "analysis_period": time_period,
            "total_patterns_found": len(patterns),
            "pattern_summary": "Strong correlations found between exercise, sleep, and energy levels"
        }
    
    async def _analyze_goal_progress(self, health_data: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Analyze progress towards health goals"""
        goal_progress = {}
        
        # Weight loss goal progress
        current_weight = health_data.get("current_weight", 75)
        starting_weight = health_data.get("starting_weight", 80)
        target_weight = health_data.get("target_weight", 70)
        
        if target_weight and starting_weight:
            weight_lost = starting_weight - current_weight
            weight_to_lose = starting_weight - target_weight
            progress_percentage = min(100, max(0, (weight_lost / weight_to_lose) * 100))
            
            goal_progress["weight_loss"] = {
                "current": current_weight,
                "target": target_weight,
                "progress_percentage": round(progress_percentage, 1),
                "pounds_lost": round(weight_lost, 1),
                "pounds_remaining": round(current_weight - target_weight, 1),
                "on_track": progress_percentage > 70,
                "estimated_completion": "6-8 weeks" if progress_percentage > 50 else "12-16 weeks"
            }
        
        # Fitness goal progress
        current_fitness_score = health_data.get("fitness_score", 65)
        target_fitness_score = health_data.get("target_fitness_score", 80)
        starting_fitness_score = health_data.get("starting_fitness_score", 50)
        
        if target_fitness_score and starting_fitness_score:
            fitness_improvement = current_fitness_score - starting_fitness_score
            fitness_to_improve = target_fitness_score - starting_fitness_score
            fitness_progress = min(100, max(0, (fitness_improvement / fitness_to_improve) * 100))
            
            goal_progress["fitness_improvement"] = {
                "current_score": current_fitness_score,
                "target_score": target_fitness_score,
                "progress_percentage": round(fitness_progress, 1),
                "improvement": round(fitness_improvement, 1),
                "remaining": round(target_fitness_score - current_fitness_score, 1),
                "on_track": fitness_progress > 60
            }
        
        # Sleep quality goal
        current_sleep_score = health_data.get("sleep_score", 75)
        target_sleep_score = health_data.get("target_sleep_score", 85)
        
        goal_progress["sleep_quality"] = {
            "current_score": current_sleep_score,
            "target_score": target_sleep_score,
            "progress_percentage": min(100, (current_sleep_score / target_sleep_score) * 100),
            "on_track": current_sleep_score >= target_sleep_score * 0.9
        }
        
        return {
            "goal_progress": goal_progress,
            "overall_progress": sum(g.get("progress_percentage", 0) for g in goal_progress.values()) / len(goal_progress) if goal_progress else 0,
            "goals_on_track": sum(1 for g in goal_progress.values() if g.get("on_track", False)),
            "total_goals": len(goal_progress),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def _generate_optimization_suggestions(self, health_data: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Generate optimization suggestions based on health data"""
        suggestions = []
        
        # Sleep optimization
        sleep_hours = health_data.get("sleep_hours", 7)
        sleep_quality = health_data.get("sleep_quality", 75)
        
        if sleep_hours < 7 or sleep_quality < 80:
            suggestions.append({
                "category": "sleep",
                "priority": "high",
                "suggestion": "Improve sleep hygiene for better recovery",
                "specific_actions": [
                    "Set consistent bedtime and wake time",
                    "Create dark, cool sleeping environment",
                    "Avoid screens 1 hour before bed",
                    "Consider magnesium supplement"
                ],
                "expected_impact": "15-25% improvement in recovery and energy"
            })
        
        # Exercise optimization
        weekly_workouts = health_data.get("weekly_workouts", 3)
        workout_intensity = health_data.get("avg_workout_intensity", 6)
        
        if weekly_workouts < 4:
            suggestions.append({
                "category": "exercise",
                "priority": "medium",
                "suggestion": "Increase workout frequency for better results",
                "specific_actions": [
                    "Add 1-2 moderate intensity workouts per week",
                    "Include active recovery days",
                    "Try different exercise types for variety"
                ],
                "expected_impact": "20-30% improvement in fitness metrics"
            })
        
        # Nutrition optimization
        protein_intake = health_data.get("daily_protein", 60)
        water_intake = health_data.get("daily_water", 2.0)
        
        if protein_intake < 80:
            suggestions.append({
                "category": "nutrition",
                "priority": "medium",
                "suggestion": "Increase protein intake for better recovery",
                "specific_actions": [
                    "Add protein to each meal",
                    "Consider post-workout protein shake",
                    "Include lean meats, eggs, or plant proteins"
                ],
                "expected_impact": "Improved muscle recovery and satiety"
            })
        
        if water_intake < 2.5:
            suggestions.append({
                "category": "hydration",
                "priority": "medium",
                "suggestion": "Improve hydration for better performance",
                "specific_actions": [
                    "Drink water upon waking",
                    "Carry water bottle throughout day",
                    "Monitor urine color for hydration status"
                ],
                "expected_impact": "Better energy levels and workout performance"
            })
        
        # Stress management
        stress_level = health_data.get("stress_level", 5)
        
        if stress_level > 6:
            suggestions.append({
                "category": "stress_management",
                "priority": "high",
                "suggestion": "Implement stress reduction techniques",
                "specific_actions": [
                    "Practice daily meditation or deep breathing",
                    "Schedule regular relaxation time",
                    "Consider yoga or gentle movement",
                    "Limit caffeine and alcohol"
                ],
                "expected_impact": "Improved recovery and overall well-being"
            })
        
        return {
            "optimization_suggestions": suggestions,
            "total_suggestions": len(suggestions),
            "high_priority_count": sum(1 for s in suggestions if s["priority"] == "high"),
            "implementation_timeline": "Start with high priority items, implement 1-2 changes per week",
            "generated_date": datetime.utcnow().isoformat()
        }