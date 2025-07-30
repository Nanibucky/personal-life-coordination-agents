"""
Recovery Monitor Tool for Agent Luna
Monitor and optimize recovery metrics
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

from shared.mcp_framework.base_server import BaseMCPTool, ExecutionContext, ExecutionResult

class RecoveryMonitorTool(BaseMCPTool):
    """Monitor and optimize recovery metrics"""
    
    def __init__(self):
        super().__init__("recovery_monitor", "Monitor recovery and prevent overtraining")
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["assess_recovery", "predict_readiness", "recommend_rest", "analyze_sleep"]
                },
                "recovery_data": {
                    "type": "object",
                    "properties": {
                        "hrv": {"type": "number"},
                        "resting_hr": {"type": "number"},
                        "sleep_hours": {"type": "number"},
                        "sleep_quality": {"type": "number"},
                        "stress_level": {"type": "number"},
                        "soreness_rating": {"type": "number"}
                    }
                },
                "recent_workouts": {"type": "array"}
            },
            "required": ["action"]
        }
    
    def get_return_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "recovery_score": {"type": "number"},
                "readiness_level": {"type": "string"},
                "recommendations": {"type": "array"},
                "sleep_analysis": {"type": "object"},
                "training_adjustments": {"type": "object"}
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        action = parameters["action"]
        recovery_data = parameters.get("recovery_data", {})
        
        try:
            if action == "assess_recovery":
                result = await self._assess_recovery_status(recovery_data, context)
            elif action == "predict_readiness":
                result = await self._predict_training_readiness(
                    recovery_data,
                    parameters.get("recent_workouts", []),
                    context
                )
            elif action == "analyze_sleep":
                result = await self._analyze_sleep_patterns(recovery_data, context)
            else:
                result = await self._recommend_recovery_actions(recovery_data, context)
            
            return ExecutionResult(success=True, result=result, execution_time=0.7)
            
        except Exception as e:
            self.logger.error(f"Recovery monitoring failed: {e}")
            return ExecutionResult(success=False, error=str(e), execution_time=0.0)
    
    async def _assess_recovery_status(self, recovery_data: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Assess current recovery status"""
        
        # Calculate recovery score based on multiple factors
        hrv_score = min(100, (recovery_data.get("hrv", 40) / 50) * 100)
        hr_score = max(0, 100 - (recovery_data.get("resting_hr", 65) - 50) * 2)
        sleep_score = min(100, (recovery_data.get("sleep_hours", 7) / 8) * 100)
        stress_score = max(0, 100 - recovery_data.get("stress_level", 5) * 10)
        soreness_score = max(0, 100 - recovery_data.get("soreness_rating", 3) * 15)
        
        # Weight the scores (HRV and sleep are most important)
        recovery_score = (
            hrv_score * 0.3 + 
            sleep_score * 0.25 + 
            hr_score * 0.2 + 
            stress_score * 0.15 + 
            soreness_score * 0.1
        )
        
        # Determine readiness level and recommendations
        if recovery_score >= 85:
            readiness = "excellent"
            recommendations = [
                "Ready for high-intensity training",
                "Consider challenging workout or new personal records",
                "Perfect time for skill development"
            ]
        elif recovery_score >= 70:
            readiness = "good"
            recommendations = [
                "Moderate to high intensity training recommended",
                "Focus on technique and form",
                "Monitor energy levels during workout"
            ]
        elif recovery_score >= 55:
            readiness = "fair"
            recommendations = [
                "Light to moderate training only",
                "Prioritize recovery activities",
                "Consider active recovery or mobility work"
            ]
        else:
            readiness = "poor"
            recommendations = [
                "Rest day strongly recommended",
                "Focus on sleep and stress management",
                "Consider gentle walking or stretching only"
            ]
        
        return {
            "recovery_score": round(recovery_score, 1),
            "readiness_level": readiness,
            "recommendations": recommendations,
            "component_scores": {
                "hrv": round(hrv_score, 1),
                "heart_rate": round(hr_score, 1),
                "sleep": round(sleep_score, 1),
                "stress": round(stress_score, 1),
                "soreness": round(soreness_score, 1)
            },
            "assessment_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _predict_training_readiness(self, recovery_data: Dict, recent_workouts: List, context: ExecutionContext) -> Dict[str, Any]:
        """Predict training readiness for upcoming sessions"""
        
        current_recovery = await self._assess_recovery_status(recovery_data, context)
        
        # Analyze recent training load
        total_load = sum(workout.get("intensity_score", 5) for workout in recent_workouts[-7:])  # Last 7 days
        avg_daily_load = total_load / 7 if recent_workouts else 0
        
        # Calculate training stress balance
        recent_high_intensity = sum(1 for workout in recent_workouts[-3:] if workout.get("intensity_score", 0) >= 8)
        
        # Predict readiness for next 3 days
        predictions = []
        base_score = current_recovery["recovery_score"]
        
        for day in range(1, 4):
            # Prediction model factors
            natural_recovery = day * 8  # Natural recovery over time
            training_fatigue = avg_daily_load * 3  # Cumulative fatigue effect
            high_intensity_penalty = recent_high_intensity * 5  # Extra penalty for recent high intensity
            
            predicted_score = base_score + natural_recovery - training_fatigue - high_intensity_penalty
            predicted_score = max(0, min(100, predicted_score))
            
            # Determine training recommendation
            if predicted_score >= 85:
                training_recommendation = "High intensity training"
                workout_types = ["Strength training", "HIIT", "Sports performance"]
            elif predicted_score >= 70:
                training_recommendation = "Moderate intensity training"
                workout_types = ["Moderate cardio", "Light strength", "Skill work"]
            elif predicted_score >= 55:
                training_recommendation = "Light training or technique work"
                workout_types = ["Yoga", "Walking", "Mobility work"]
            else:
                training_recommendation = "Rest or active recovery"
                workout_types = ["Complete rest", "Gentle stretching", "Meditation"]
            
            predictions.append({
                "day": f"Day +{day}",
                "predicted_score": round(predicted_score, 1),
                "recommendation": training_recommendation,
                "suggested_activities": workout_types,
                "confidence": max(0.5, 0.85 - (day * 0.1)),  # Confidence decreases with time
                "factors": {
                    "base_recovery": round(base_score, 1),
                    "natural_recovery": round(natural_recovery, 1),
                    "training_fatigue": round(training_fatigue, 1)
                }
            })
        
        return {
            "current_readiness": current_recovery,
            "predictions": predictions,
            "training_load_analysis": {
                "recent_avg_load": round(avg_daily_load, 1),
                "high_intensity_sessions": recent_high_intensity,
                "load_trend": "increasing" if avg_daily_load > 6 else "stable" if avg_daily_load > 3 else "light",
                "recommended_adjustment": self._get_load_adjustment_recommendation(avg_daily_load, recent_high_intensity)
            },
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    def _get_load_adjustment_recommendation(self, avg_load: float, high_intensity_count: int) -> str:
        """Get training load adjustment recommendation"""
        if avg_load > 8 or high_intensity_count > 2:
            return "reduce_intensity"
        elif avg_load < 3 and high_intensity_count == 0:
            return "increase_activity"
        else:
            return "maintain_current_level"
    
    async def _analyze_sleep_patterns(self, recovery_data: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Analyze sleep patterns for recovery optimization"""
        sleep_hours = recovery_data.get("sleep_hours", 7)
        sleep_quality = recovery_data.get("sleep_quality", 75)
        
        # Mock sleep analysis - would integrate with sleep tracking devices
        sleep_analysis = {
            "total_sleep": sleep_hours,
            "sleep_efficiency": sleep_quality,
            "estimated_deep_sleep": sleep_hours * 0.25,  # ~25% of sleep
            "estimated_rem_sleep": sleep_hours * 0.20,   # ~20% of sleep
            "estimated_light_sleep": sleep_hours * 0.55,  # ~55% of sleep
            "sleep_debt": max(0, 8 - sleep_hours),
            "sleep_consistency": 85,  # Mock consistency score
            "recovery_quality": "good" if sleep_quality > 80 else "fair" if sleep_quality > 60 else "poor"
        }
        
        # Sleep recommendations
        recommendations = []
        
        if sleep_hours < 7:
            recommendations.append("Increase total sleep time to 7-9 hours")
        
        if sleep_quality < 75:
            recommendations.extend([
                "Improve sleep environment (dark, cool, quiet)",
                "Establish consistent bedtime routine",
                "Avoid screens 1 hour before bed"
            ])
        
        if sleep_analysis["sleep_debt"] > 1:
            recommendations.append("Consider earlier bedtime to reduce sleep debt")
        
        sleep_analysis["recommendations"] = recommendations
        sleep_analysis["analysis_date"] = datetime.utcnow().isoformat()
        
        return {"sleep_analysis": sleep_analysis}
    
    async def _recommend_recovery_actions(self, recovery_data: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Recommend specific recovery actions"""
        recovery_score = recovery_data.get("recovery_score", 70)
        stress_level = recovery_data.get("stress_level", 5)
        soreness_rating = recovery_data.get("soreness_rating", 3)
        
        recommendations = []
        
        # Recovery actions based on overall score
        if recovery_score < 60:
            recommendations.extend([
                {
                    "action": "prioritize_sleep",
                    "description": "Get 8-9 hours of quality sleep tonight",
                    "priority": "high",
                    "time_required": "8-9 hours"
                },
                {
                    "action": "stress_management",
                    "description": "Practice meditation or deep breathing",
                    "priority": "high",
                    "time_required": "10-20 minutes"
                }
            ])
        
        # Stress-specific recommendations
        if stress_level > 6:
            recommendations.extend([
                {
                    "action": "relaxation_techniques",
                    "description": "Try progressive muscle relaxation or yoga",
                    "priority": "medium",
                    "time_required": "15-30 minutes"
                },
                {
                    "action": "nature_exposure",
                    "description": "Spend time outdoors or in natural light",
                    "priority": "medium",
                    "time_required": "20-30 minutes"
                }
            ])
        
        # Soreness-specific recommendations
        if soreness_rating > 5:
            recommendations.extend([
                {
                    "action": "active_recovery",
                    "description": "Light walking or gentle movement",
                    "priority": "medium",
                    "time_required": "20-30 minutes"
                },
                {
                    "action": "soft_tissue_work",
                    "description": "Foam rolling or gentle massage",
                    "priority": "medium",
                    "time_required": "10-15 minutes"
                }
            ])
        
        # General recovery recommendations
        recommendations.extend([
            {
                "action": "hydration",
                "description": "Drink 2-3 liters of water throughout the day",
                "priority": "low",
                "time_required": "ongoing"
            },
            {
                "action": "nutrition_timing",
                "description": "Eat balanced meals with adequate protein",
                "priority": "medium",
                "time_required": "ongoing"
            }
        ])
        
        return {
            "recovery_recommendations": recommendations,
            "priority_actions": [r for r in recommendations if r["priority"] == "high"],
            "total_recommendations": len(recommendations),
            "estimated_recovery_time": "12-24 hours with proper actions",
            "generated_at": datetime.utcnow().isoformat()
        }