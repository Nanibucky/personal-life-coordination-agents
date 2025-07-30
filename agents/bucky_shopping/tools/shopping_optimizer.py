"""
Shopping Optimizer Tool for Agent Bucky
Route and timing optimization for shopping trips
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import random
import math

from shared.mcp_framework.base_server import BaseMCPTool, ExecutionContext, ExecutionResult

class ShoppingOptimizerTool(BaseMCPTool):
    """Route and timing optimization for shopping trips"""
    
    def __init__(self):
        super().__init__("shopping_optimizer", "Optimize shopping routes, timing, and efficiency")
        self.store_database = self._load_store_database()
        self.traffic_patterns = self._load_traffic_patterns()
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["optimize_route", "find_best_time", "calculate_trip_cost", "group_by_store", "analyze_efficiency"]
                },
                "shopping_list": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of items to shop for"
                },
                "home_address": {
                    "type": "string",
                    "description": "Starting point for route optimization"
                },
                "preferred_stores": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Preferred stores to include in route"
                },
                "transportation": {
                    "type": "string",
                    "enum": ["car", "public_transport", "walking", "bike"],
                    "default": "car"
                },
                "time_constraints": {
                    "type": "object",
                    "properties": {
                        "max_trip_duration": {"type": "integer"},
                        "preferred_times": {"type": "array"},
                        "avoid_times": {"type": "array"}
                    }
                },
                "priorities": {
                    "type": "object",
                    "properties": {
                        "minimize_time": {"type": "boolean"},
                        "minimize_cost": {"type": "boolean"},
                        "minimize_distance": {"type": "boolean"},
                        "maximize_deals": {"type": "boolean"}
                    }
                }
            },
            "required": ["action", "shopping_list"]
        }
    
    def get_return_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "optimized_route": {"type": "array"},
                "estimated_time": {"type": "number"},
                "estimated_cost": {"type": "number"},
                "store_groupings": {"type": "object"},
                "efficiency_score": {"type": "number"},
                "alternative_routes": {"type": "array"}
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        action = parameters["action"]
        shopping_list = parameters["shopping_list"]
        
        try:
            if action == "optimize_route":
                result = await self._optimize_shopping_route(
                    shopping_list,
                    parameters.get("home_address", "Default Address"),
                    parameters.get("preferred_stores", []),
                    parameters.get("transportation", "car"),
                    parameters.get("priorities", {}),
                    context
                )
            elif action == "find_best_time":
                result = await self._find_optimal_shopping_time(
                    parameters.get("preferred_stores", []),
                    parameters.get("time_constraints", {}),
                    context
                )
            elif action == "calculate_trip_cost":
                result = await self._calculate_trip_costs(
                    shopping_list,
                    parameters.get("transportation", "car"),
                    parameters.get("preferred_stores", []),
                    context
                )
            elif action == "group_by_store":
                result = await self._group_items_by_store(
                    shopping_list,
                    parameters.get("preferred_stores", []),
                    context
                )
            else:
                result = await self._analyze_shopping_efficiency(
                    shopping_list,
                    parameters.get("preferred_stores", []),
                    context
                )
            
            return ExecutionResult(
                success=True,
                result=result,
                execution_time=0.9,
                context_updates={"last_route_optimization": datetime.utcnow().isoformat()}
            )
            
        except Exception as e:
            self.logger.error(f"Shopping optimization failed: {e}")
            return ExecutionResult(success=False, error=str(e), execution_time=0.0)
    
    def _load_store_database(self) -> Dict[str, Any]:
        """Load store information database"""
        return {
            "kroger": {
                "address": "123 Main St",
                "coordinates": (42.3601, -71.0589),
                "hours": {"weekday": "6:00-24:00", "weekend": "6:00-24:00"},
                "peak_times": ["17:00-19:00", "12:00-14:00"],
                "parking": "free",
                "categories": ["grocery", "pharmacy", "deli"]
            },
            "walmart": {
                "address": "456 Oak Ave",
                "coordinates": (42.3651, -71.0656),
                "hours": {"weekday": "6:00-23:00", "weekend": "6:00-23:00"},
                "peak_times": ["18:00-20:00", "13:00-15:00"],
                "parking": "free",
                "categories": ["grocery", "general", "pharmacy"]
            },
            "target": {
                "address": "789 Pine Rd",
                "coordinates": (42.3501, -71.0489),
                "hours": {"weekday": "8:00-22:00", "weekend": "8:00-22:00"},
                "peak_times": ["16:00-18:00", "11:00-13:00"],
                "parking": "free",
                "categories": ["general", "grocery", "clothing"]
            },
            "costco": {
                "address": "321 Cedar Blvd",
                "coordinates": (42.3751, -71.0756),
                "hours": {"weekday": "10:00-20:30", "weekend": "9:30-18:00"},
                "peak_times": ["14:00-16:00", "11:00-12:00"],
                "parking": "free",
                "categories": ["wholesale", "grocery", "gas"]
            },
            "whole_foods": {
                "address": "654 Elm St",
                "coordinates": (42.3451, -71.0423),
                "hours": {"weekday": "7:00-22:00", "weekend": "7:00-22:00"},
                "peak_times": ["17:30-19:30", "12:30-14:30"],
                "parking": "paid",
                "categories": ["organic", "grocery", "prepared_foods"]
            }
        }
    
    def _load_traffic_patterns(self) -> Dict[str, Any]:
        """Load traffic pattern data"""
        return {
            "peak_hours": ["7:00-9:00", "17:00-19:00"],
            "low_traffic": ["10:00-11:00", "14:00-16:00", "20:00-22:00"],
            "weekend_patterns": {"saturday": "busy_morning", "sunday": "steady_afternoon"},
            "weather_impact": {"rain": 1.3, "snow": 1.8, "clear": 1.0}
        }
    
    async def _optimize_shopping_route(self, shopping_list: List[str], home_address: str, 
                                     preferred_stores: List[str], transportation: str,
                                     priorities: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Optimize the shopping route using TSP-like algorithm"""
        
        # Group items by best store
        store_assignments = self._assign_items_to_stores(shopping_list, preferred_stores)
        
        # Calculate optimal route between stores
        optimal_route = self._calculate_optimal_route(store_assignments, home_address, transportation)
        
        # Apply priority optimization
        if priorities.get("minimize_time"):
            optimal_route = self._optimize_for_time(optimal_route)
        elif priorities.get("minimize_cost"):
            optimal_route = self._optimize_for_cost(optimal_route)
        
        total_time = sum(stop["estimated_time"] + stop["travel_time"] for stop in optimal_route)
        total_distance = sum(stop["distance_km"] for stop in optimal_route)
        
        return {
            "optimized_route": optimal_route,
            "total_estimated_time": total_time,
            "total_distance_km": round(total_distance, 2),
            "fuel_cost_estimate": round(total_distance * 0.15, 2),  # $0.15 per km
            "efficiency_score": self._calculate_efficiency_score(optimal_route),
            "route_type": "optimal",
            "transportation_method": transportation,
            "optimization_criteria": list(priorities.keys()) if priorities else ["balanced"]
        }
    
    def _assign_items_to_stores(self, shopping_list: List[str], preferred_stores: List[str]) -> Dict[str, List[str]]:
        """Assign items to the best stores based on availability and prices"""
        store_assignments = {}
        available_stores = preferred_stores if preferred_stores else ["kroger", "walmart", "target"]
        
        # Mock item-to-store assignment logic
        for item in shopping_list:
            # Categorize items and assign to appropriate stores
            if any(keyword in item.lower() for keyword in ["organic", "natural", "fresh"]):
                best_store = "whole_foods" if "whole_foods" in available_stores else available_stores[0]
            elif any(keyword in item.lower() for keyword in ["bulk", "family", "large"]):
                best_store = "costco" if "costco" in available_stores else available_stores[0]
            else:
                # Default assignment - rotate through stores for variety
                best_store = available_stores[len(store_assignments) % len(available_stores)]
            
            if best_store not in store_assignments:
                store_assignments[best_store] = []
            store_assignments[best_store].append(item)
        
        return store_assignments
    
    def _calculate_optimal_route(self, store_assignments: Dict[str, List[str]], 
                               home_address: str, transportation: str) -> List[Dict[str, Any]]:
        """Calculate optimal route between stores"""
        route = []
        stores_to_visit = list(store_assignments.keys())
        
        # Simple nearest-neighbor algorithm for TSP
        current_location = "home"
        unvisited_stores = stores_to_visit.copy()
        
        while unvisited_stores:
            # Find nearest unvisited store
            nearest_store = self._find_nearest_store(current_location, unvisited_stores)
            store_info = self.store_database[nearest_store]
            
            # Calculate travel time and distance
            travel_time, distance = self._calculate_travel_metrics(current_location, nearest_store, transportation)
            
            # Estimate shopping time based on items
            items_count = len(store_assignments[nearest_store])
            shopping_time = self._estimate_shopping_time(nearest_store, items_count)
            
            stop_info = {
                "store": nearest_store.replace("_", " ").title(),
                "address": store_info["address"],
                "items": store_assignments[nearest_store],
                "item_count": items_count,
                "estimated_shopping_time": shopping_time,
                "travel_time": travel_time,
                "distance_km": distance,
                "optimal_visit_time": self._suggest_visit_time(nearest_store),
                "crowd_level": self._predict_crowd_level(nearest_store),
                "parking_info": store_info["parking"]
            }
            
            route.append(stop_info)
            unvisited_stores.remove(nearest_store)
            current_location = nearest_store
        
        return route
    
    def _find_nearest_store(self, current_location: str, available_stores: List[str]) -> str:
        """Find the nearest store from current location"""
        if current_location == "home":
            # Start with the store that has the most items
            return max(available_stores, key=lambda s: len(self.store_database.get(s, {}).get("categories", [])))
        
        # Simple distance calculation (mock)
        distances = {}
        for store in available_stores:
            # Mock distance calculation
            distances[store] = random.uniform(2.0, 8.0)
        
        return min(distances, key=distances.get)
    
    def _calculate_travel_metrics(self, from_location: str, to_store: str, transportation: str) -> Tuple[int, float]:
        """Calculate travel time and distance"""
        # Mock travel calculation
        base_distance = random.uniform(2.0, 8.0)
        
        if transportation == "car":
            travel_time = int(base_distance * 4)  # 4 minutes per km
        elif transportation == "public_transport":
            travel_time = int(base_distance * 8)  # 8 minutes per km
        elif transportation == "bike":
            travel_time = int(base_distance * 6)  # 6 minutes per km
        else:  # walking
            travel_time = int(base_distance * 12)  # 12 minutes per km
        
        return travel_time, base_distance
    
    def _estimate_shopping_time(self, store: str, item_count: int) -> int:
        """Estimate shopping time based on store and item count"""
        base_time_per_item = {
            "kroger": 3,
            "walmart": 4,
            "target": 5,
            "costco": 6,
            "whole_foods": 4
        }
        
        base_time = base_time_per_item.get(store, 4)
        shopping_time = base_time * item_count + 10  # 10 min base time for checkout
        
        return min(shopping_time, 60)  # Cap at 60 minutes
    
    def _suggest_visit_time(self, store: str) -> str:
        """Suggest optimal visit time for store"""
        store_info = self.store_database.get(store, {})
        peak_times = store_info.get("peak_times", [])
        
        # Suggest non-peak times
        optimal_times = ["09:00", "14:00", "20:00"]
        for time in optimal_times:
            if not any(self._time_in_range(time, peak) for peak in peak_times):
                return time
        
        return "10:00"  # Default
    
    def _time_in_range(self, time: str, time_range: str) -> bool:
        """Check if time falls within a time range"""
        # Simple time range check (mock implementation)
        return False  # Simplified for demo
    
    def _predict_crowd_level(self, store: str) -> str:
        """Predict crowd level at store"""
        current_hour = datetime.now().hour
        
        if 7 <= current_hour <= 9 or 17 <= current_hour <= 19:
            return "high"
        elif 10 <= current_hour <= 11 or 14 <= current_hour <= 16:
            return "low"
        else:
            return "medium"
    
    def _optimize_for_time(self, route: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize route for minimum time"""
        # Sort by lowest crowd level and shortest shopping time
        return sorted(route, key=lambda x: (
            {"low": 1, "medium": 2, "high": 3}[x["crowd_level"]],
            x["estimated_shopping_time"]
        ))
    
    def _optimize_for_cost(self, route: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize route for minimum cost"""
        # Prioritize stores with better deals and lower travel costs
        return sorted(route, key=lambda x: (
            x["distance_km"],  # Lower distance = lower fuel cost
            {"free": 0, "paid": 1}.get(x["parking_info"], 0)  # Free parking first
        ))
    
    def _calculate_efficiency_score(self, route: List[Dict[str, Any]]) -> float:
        """Calculate overall route efficiency score"""
        total_items = sum(stop["item_count"] for stop in route)
        total_time = sum(stop["estimated_shopping_time"] + stop["travel_time"] for stop in route)
        total_distance = sum(stop["distance_km"] for stop in route)
        
        # Efficiency = items per minute per km
        if total_time > 0 and total_distance > 0:
            efficiency = (total_items / total_time) * (10 / total_distance)  # Normalized
            return round(min(efficiency * 10, 10), 2)  # Scale to 0-10
        return 5.0
    
    async def _find_optimal_shopping_time(self, preferred_stores: List[str], 
                                        time_constraints: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Find the best time to go shopping"""
        
        max_duration = time_constraints.get("max_trip_duration", 120)  # minutes
        preferred_times = time_constraints.get("preferred_times", [])
        avoid_times = time_constraints.get("avoid_times", [])
        
        # Analyze different time slots
        time_slots = []
        current_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        for hour in range(8, 22):  # 8 AM to 10 PM
            slot_time = current_time.replace(hour=hour)
            
            # Skip if in avoid times
            time_str = slot_time.strftime("%H:00")
            if any(avoid in time_str for avoid in avoid_times):
                continue
            
            # Calculate score for this time slot
            crowd_score = self._calculate_crowd_score(hour)
            traffic_score = self._calculate_traffic_score(hour)
            availability_score = self._calculate_store_availability_score(hour, preferred_stores)
            
            overall_score = (crowd_score + traffic_score + availability_score) / 3
            
            time_slot = {
                "time": time_str,
                "overall_score": round(overall_score, 2),
                "crowd_level": self._get_crowd_level_description(crowd_score),
                "traffic_level": self._get_traffic_level_description(traffic_score),
                "store_availability": "excellent" if availability_score > 8 else "good" if availability_score > 6 else "fair",
                "estimated_total_time": max_duration - int((10 - overall_score) * 5),  # Better scores = faster trips
                "pros": self._get_time_slot_pros(hour),
                "cons": self._get_time_slot_cons(hour)
            }
            time_slots.append(time_slot)
        
        # Sort by overall score
        time_slots.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return {
            "optimal_time": time_slots[0]["time"],
            "best_score": time_slots[0]["overall_score"],
            "all_time_options": time_slots[:5],  # Top 5 options
            "recommendation": f"Best time is {time_slots[0]['time']} with {time_slots[0]['crowd_level']} crowds",
            "factors_considered": ["crowd_levels", "traffic_patterns", "store_hours", "checkout_wait_times"]
        }
    
    def _calculate_crowd_score(self, hour: int) -> float:
        """Calculate crowd score (higher = less crowded)"""
        if hour in [8, 9, 21]:  # Early morning, late evening
            return 9.0
        elif hour in [10, 11, 14, 15, 20]:  # Off-peak
            return 7.5
        elif hour in [12, 13, 16]:  # Moderate
            return 5.0
        else:  # Peak hours 17-19
            return 2.0
    
    def _calculate_traffic_score(self, hour: int) -> float:
        """Calculate traffic score (higher = less traffic)"""
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hour
            return 2.0
        elif 10 <= hour <= 16 or 20 <= hour <= 22:  # Good traffic
            return 8.0
        else:
            return 6.0
    
    def _calculate_store_availability_score(self, hour: int, stores: List[str]) -> float:
        """Calculate store availability score"""
        if 8 <= hour <= 21:  # Most stores open
            return 9.0
        elif hour == 7 or hour == 22:  # Some stores open
            return 6.0
        else:  # Limited availability
            return 3.0
    
    def _get_crowd_level_description(self, score: float) -> str:
        if score >= 8: return "very_low"
        elif score >= 6: return "low"
        elif score >= 4: return "moderate"
        else: return "high"
    
    def _get_traffic_level_description(self, score: float) -> str:
        if score >= 7: return "light"
        elif score >= 5: return "moderate"
        else: return "heavy"
    
    def _get_time_slot_pros(self, hour: int) -> List[str]:
        pros = []
        if hour <= 9:
            pros.extend(["Fresh inventory", "Less crowded", "Shorter checkout lines"])
        elif 10 <= hour <= 15:
            pros.extend(["Good store staffing", "All departments open", "Parking available"])
        elif hour >= 20:
            pros.extend(["Very low crowds", "Quick shopping", "Easy parking"])
        return pros
    
    def _get_time_slot_cons(self, hour: int) -> List[str]:
        cons = []
        if hour <= 8:
            cons.extend(["Some departments may not be open", "Limited prepared foods"])
        elif 17 <= hour <= 19:
            cons.extend(["Peak crowds", "Long checkout lines", "Limited parking"])
        elif hour >= 21:
            cons.extend(["Limited fresh items", "Some departments closing"])
        return cons
    
    async def _calculate_trip_costs(self, shopping_list: List[str], transportation: str, 
                                  stores: List[str], context: ExecutionContext) -> Dict[str, Any]:
        """Calculate comprehensive trip costs"""
        
        cost_breakdown = {
            "transportation": self._calculate_transportation_cost(transportation, stores),
            "parking": self._calculate_parking_costs(stores),
            "time_value": self._calculate_time_value_cost(shopping_list, stores),
            "opportunity_cost": self._calculate_opportunity_cost(shopping_list, stores)
        }
        
        total_cost = sum(cost_breakdown.values())
        
        return {
            "cost_breakdown": cost_breakdown,
            "total_trip_cost": round(total_cost, 2),
            "cost_per_item": round(total_cost / len(shopping_list), 2),
            "comparison": {
                "vs_delivery": round(total_cost - 15.99, 2),  # Typical delivery fee
                "vs_single_store": round(total_cost - (total_cost * 0.3), 2)  # 30% savings estimate
            },
            "cost_optimization_tips": [
                "Combine trips to reduce transportation costs",
                "Shop during off-peak hours to save time",
                "Use store apps for parking discounts"
            ]
        }
    
    def _calculate_transportation_cost(self, transportation: str, stores: List[str]) -> float:
        """Calculate transportation costs"""
        total_distance = len(stores) * 5.0  # Estimated 5km per store
        
        costs = {
            "car": total_distance * 0.15,  # $0.15 per km (gas + wear)
            "public_transport": len(stores) * 3.50,  # $3.50 per trip
            "bike": 0.0,  # Free
            "walking": 0.0  # Free
        }
        
        return costs.get(transportation, 0.0)
    
    def _calculate_parking_costs(self, stores: List[str]) -> float:
        """Calculate parking costs"""
        parking_fees = {"whole_foods": 2.00, "downtown_target": 3.00}
        return sum(parking_fees.get(store, 0.0) for store in stores)
    
    def _calculate_time_value_cost(self, shopping_list: List[str], stores: List[str]) -> float:
        """Calculate time value cost (time is money)"""
        estimated_hours = len(stores) * 0.75 + len(shopping_list) * 0.05  # 45 min per store + 3 min per item
        hourly_rate = 25.0  # Assumed hourly value
        return estimated_hours * hourly_rate
    
    def _calculate_opportunity_cost(self, shopping_list: List[str], stores: List[str]) -> float:
        """Calculate opportunity cost of not choosing alternatives"""
        # Cost of not using delivery or meal kits
        if len(shopping_list) > 20:
            return 10.0  # High opportunity cost for large shops
        return 0.0
    
    async def _group_items_by_store(self, shopping_list: List[str], preferred_stores: List[str], 
                                  context: ExecutionContext) -> Dict[str, Any]:
        """Group shopping items by optimal store"""
        
        store_groupings = self._assign_items_to_stores(shopping_list, preferred_stores)
        
        # Add store-specific information
        detailed_groupings = {}
        for store, items in store_groupings.items():
            store_info = self.store_database.get(store, {})
            detailed_groupings[store] = {
                "items": items,
                "item_count": len(items),
                "store_info": {
                    "address": store_info.get("address", ""),
                    "hours": store_info.get("hours", {}),
                    "specialties": store_info.get("categories", [])
                },
                "estimated_cost": round(random.uniform(15.99, 89.99), 2),  # Mock cost
                "estimated_time": self._estimate_shopping_time(store, len(items)),
                "availability_score": round(random.uniform(0.8, 0.98), 2),
                "price_competitiveness": round(random.uniform(0.7, 0.95), 2)
            }
        
        return {
            "store_groupings": detailed_groupings,
            "total_stores": len(detailed_groupings),
            "items_distribution": {store: len(items) for store, items in store_groupings.items()},
            "optimization_summary": "Items grouped by store specialty and price competitiveness"
        }
    
    async def _analyze_shopping_efficiency(self, shopping_list: List[str], preferred_stores: List[str], 
                                         context: ExecutionContext) -> Dict[str, Any]:
        """Analyze overall shopping efficiency and suggest improvements"""
        
        current_efficiency = {
            "route_efficiency": round(random.uniform(0.6, 0.9), 2),
            "time_efficiency": round(random.uniform(0.7, 0.95), 2),
            "cost_efficiency": round(random.uniform(0.65, 0.88), 2),
            "convenience_score": round(random.uniform(0.8, 0.95), 2)
        }
        
        improvements = []
        if current_efficiency["route_efficiency"] < 0.8:
            improvements.append({
                "area": "route_optimization",
                "suggestion": "Reorganize store order to minimize backtracking",
                "potential_savings": "15-20 minutes"
            })
        
        if current_efficiency["cost_efficiency"] < 0.8:
            improvements.append({
                "area": "cost_optimization",
                "suggestion": "Shop at discount stores for non-perishables",
                "potential_savings": "$10-15 per trip"
            })
        
        efficiency_trends = {
            "weekly_pattern": "Efficiency peaks on Tuesday/Wednesday",
            "seasonal_variation": "Winter trips 20% less efficient due to weather",
            "improvement_rate": "Efficiency improved 12% over last 3 months"
        }
        
        return {
            "current_efficiency": current_efficiency,
            "overall_score": round(sum(current_efficiency.values()) / len(current_efficiency), 2),
            "improvement_opportunities": improvements,
            "efficiency_trends": efficiency_trends,
            "benchmarks": {
                "average_shopper": 0.72,
                "efficient_shopper": 0.85,
                "your_ranking": "Above average"
            }
        }