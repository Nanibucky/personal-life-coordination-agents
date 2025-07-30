"""
Pantry Tracker Tool for Agent Bucky
Real-time household inventory management
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from shared.mcp_framework.base_server import BaseMCPTool, ExecutionContext, ExecutionResult

@dataclass
class InventoryItem:
    name: str
    quantity: float
    unit: str
    expiration_date: Optional[datetime]
    category: str
    brand: str
    location: str  # pantry, fridge, freezer
    cost_per_unit: float
    barcode: Optional[str] = None
    last_updated: datetime = datetime.utcnow()

class PantryTrackerTool(BaseMCPTool):
    """Real-time household inventory management"""
    
    def __init__(self):
        super().__init__("pantry_tracker", "Track pantry inventory and expiration dates")
        self.inventory = {}
        self.consumption_patterns = {}
        self.reorder_points = {}
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add_item", "remove_item", "update_quantity", "get_inventory", 
                            "check_expiry", "scan_receipt", "set_reorder_point", "predict_needs"]
                },
                "item_name": {"type": "string"},
                "quantity": {"type": "number"},
                "unit": {"type": "string"},
                "expiration_date": {"type": "string", "format": "date"},
                "location": {"type": "string", "enum": ["pantry", "fridge", "freezer"]},
                "category": {"type": "string"},
                "brand": {"type": "string"},
                "cost": {"type": "number"},
                "barcode": {"type": "string"},
                "receipt_data": {"type": "object"},
                "consumption_rate": {"type": "number"}
            },
            "required": ["action"]
        }
    
    def get_return_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "inventory": {"type": "object"},
                "expiring_items": {"type": "array"},
                "low_stock_items": {"type": "array"},
                "shopping_suggestions": {"type": "array"},
                "consumption_insights": {"type": "object"}
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        action = parameters["action"]
        
        try:
            if action == "add_item":
                result = await self._add_inventory_item(parameters, context)
            elif action == "remove_item":
                result = await self._remove_inventory_item(parameters, context)
            elif action == "update_quantity":
                result = await self._update_item_quantity(parameters, context)
            elif action == "get_inventory":
                result = await self._get_current_inventory(context)
            elif action == "check_expiry":
                result = await self._check_expiring_items(context)
            elif action == "scan_receipt":
                result = await self._process_receipt(parameters.get("receipt_data", {}), context)
            elif action == "set_reorder_point":
                result = await self._set_reorder_point(parameters, context)
            else:  # predict_needs
                result = await self._predict_shopping_needs(context)
            
            return ExecutionResult(
                success=True,
                result=result,
                execution_time=0.5,
                context_updates={"last_inventory_update": datetime.utcnow().isoformat()}
            )
        
        except Exception as e:
            self.logger.error(f"Pantry tracking failed: {e}")
            return ExecutionResult(success=False, error=str(e), execution_time=0.0)
    
    async def _add_inventory_item(self, params: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Add new item to inventory"""
        expiration_date = None
        if params.get("expiration_date"):
            try:
                expiration_date = datetime.fromisoformat(params["expiration_date"])
            except ValueError:
                # Handle different date formats
                expiration_date = datetime.now() + timedelta(days=30)  # Default 30 days
        
        item = InventoryItem(
            name=params["item_name"],
            quantity=params.get("quantity", 1),
            unit=params.get("unit", "piece"),
            expiration_date=expiration_date,
            category=params.get("category", "other"),
            brand=params.get("brand", "generic"),
            location=params.get("location", "pantry"),
            cost_per_unit=params.get("cost", 0.0),
            barcode=params.get("barcode")
        )
        
        self.inventory[item.name] = item
        
        # Set default reorder point if not exists
        if item.name not in self.reorder_points:
            self.reorder_points[item.name] = max(1, item.quantity * 0.2)  # 20% of current quantity
        
        return {
            "success": True,
            "item_added": item.name,
            "current_quantity": item.quantity,
            "location": item.location,
            "expiry_warning": self._check_item_expiry_warning(item)
        }
    
    async def _remove_inventory_item(self, params: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Remove item from inventory (consumption tracking)"""
        item_name = params["item_name"]
        consumed_quantity = params.get("quantity", 1)
        
        if item_name not in self.inventory:
            return {"success": False, "error": f"Item {item_name} not found in inventory"}
        
        item = self.inventory[item_name]
        
        # Track consumption pattern
        self._track_consumption(item_name, consumed_quantity)
        
        # Update quantity
        item.quantity = max(0, item.quantity - consumed_quantity)
        item.last_updated = datetime.utcnow()
        
        # Check if item is now low stock
        low_stock_warning = item.quantity <= self.reorder_points.get(item_name, 1)
        
        # Remove item if quantity is 0
        if item.quantity == 0:
            del self.inventory[item_name]
            return {
                "success": True,
                "item_consumed": item_name,
                "remaining_quantity": 0,
                "item_depleted": True,
                "reorder_suggested": True
            }
        
        return {
            "success": True,
            "item_consumed": item_name,
            "consumed_quantity": consumed_quantity,
            "remaining_quantity": item.quantity,
            "low_stock_warning": low_stock_warning,
            "reorder_suggested": low_stock_warning
        }
    
    async def _update_item_quantity(self, params: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Update item quantity (for corrections or restocking)"""
        item_name = params["item_name"]
        new_quantity = params["quantity"]
        
        if item_name not in self.inventory:
            return {"success": False, "error": f"Item {item_name} not found"}
        
        item = self.inventory[item_name]
        old_quantity = item.quantity
        item.quantity = new_quantity
        item.last_updated = datetime.utcnow()
        
        return {
            "success": True,
            "item_updated": item_name,
            "old_quantity": old_quantity,
            "new_quantity": new_quantity,
            "change": new_quantity - old_quantity
        }
    
    async def _get_current_inventory(self, context: ExecutionContext) -> Dict[str, Any]:
        """Get complete inventory status with analysis"""
        inventory_summary = {
            "total_items": len(self.inventory),
            "items": {},
            "expiring_soon": [],
            "low_stock": [],
            "by_location": {"pantry": [], "fridge": [], "freezer": []},
            "by_category": {},
            "total_value": 0
        }
        
        current_date = datetime.now()
        
        for name, item in self.inventory.items():
            days_until_expiry = None
            if item.expiration_date:
                days_until_expiry = (item.expiration_date - current_date).days
            
            item_data = {
                "quantity": item.quantity,
                "unit": item.unit,
                "location": item.location,
                "category": item.category,
                "brand": item.brand,
                "cost_per_unit": item.cost_per_unit,
                "total_value": item.quantity * item.cost_per_unit,
                "expiration_date": item.expiration_date.isoformat() if item.expiration_date else None,
                "days_until_expiry": days_until_expiry,
                "last_updated": item.last_updated.isoformat()
            }
            
            inventory_summary["items"][name] = item_data
            inventory_summary["total_value"] += item_data["total_value"]
            
            # Check for expiring items (within 7 days)
            if days_until_expiry is not None and days_until_expiry <= 7:
                urgency = "urgent" if days_until_expiry <= 1 else "high" if days_until_expiry <= 3 else "medium"
                inventory_summary["expiring_soon"].append({
                    "name": name,
                    "days_until_expiry": days_until_expiry,
                    "quantity": item.quantity,
                    "urgency": urgency
                })
            
            # Check for low stock
            reorder_point = self.reorder_points.get(name, 1)
            if item.quantity <= reorder_point:
                inventory_summary["low_stock"].append({
                    "name": name,
                    "current_quantity": item.quantity,
                    "reorder_point": reorder_point,
                    "suggested_order_quantity": self._calculate_suggested_order_quantity(name)
                })
            
            # Group by location
            inventory_summary["by_location"][item.location].append(name)
            
            # Group by category
            if item.category not in inventory_summary["by_category"]:
                inventory_summary["by_category"][item.category] = []
            inventory_summary["by_category"][item.category].append(name)
        
        return inventory_summary
    
    async def _check_expiring_items(self, context: ExecutionContext) -> Dict[str, Any]:
        """Check for items expiring soon with detailed analysis"""
        expiring_items = []
        current_date = datetime.now()
        
        for name, item in self.inventory.items():
            if item.expiration_date:
                days_until_expiry = (item.expiration_date - current_date).days
                
                if days_until_expiry <= 14:  # Check items expiring within 2 weeks
                    if days_until_expiry <= 0:
                        urgency = "expired"
                        action = "discard_immediately"
                    elif days_until_expiry <= 1:
                        urgency = "urgent"
                        action = "use_today"
                    elif days_until_expiry <= 3:
                        urgency = "high"
                        action = "use_this_week"
                    elif days_until_expiry <= 7:
                        urgency = "medium"
                        action = "plan_meals"
                    else:
                        urgency = "low"
                        action = "monitor"
                    
                    # Calculate potential waste cost
                    waste_cost = item.quantity * item.cost_per_unit if days_until_expiry <= 0 else 0
                    
                    expiring_items.append({
                        "name": name,
                        "expiration_date": item.expiration_date.isoformat(),
                        "days_until_expiry": days_until_expiry,
                        "quantity": item.quantity,
                        "unit": item.unit,
                        "location": item.location,
                        "urgency": urgency,
                        "recommended_action": action,
                        "potential_waste_cost": waste_cost,
                        "meal_suggestions": self._suggest_meals_for_item(name)
                    })
        
        # Sort by urgency (expired first, then by days remaining)
        expiring_items.sort(key=lambda x: (x["urgency"] != "expired", x["days_until_expiry"]))
        
        total_waste_risk = sum(item["potential_waste_cost"] for item in expiring_items)
        
        return {
            "expiring_items": expiring_items,
            "total_expiring": len(expiring_items),
            "urgent_count": len([i for i in expiring_items if i["urgency"] in ["expired", "urgent"]]),
            "total_waste_risk": round(total_waste_risk, 2),
            "recommendations": self._generate_expiry_recommendations(expiring_items)
        }
    
    async def _process_receipt(self, receipt_data: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Process shopping receipt to update inventory"""
        processed_items = []
        total_cost = 0
        
        # Mock receipt processing - would use OCR and parsing in real implementation
        items = receipt_data.get("items", [])
        
        for item_data in items:
            item_name = item_data.get("name", "Unknown Item")
            quantity = item_data.get("quantity", 1)
            cost = item_data.get("cost", 0)
            
            # Add to inventory
            if item_name in self.inventory:
                # Update existing item
                self.inventory[item_name].quantity += quantity
                self.inventory[item_name].last_updated = datetime.utcnow()
            else:
                # Add new item with estimated expiration
                estimated_expiry = self._estimate_expiration_date(item_name)
                new_item = InventoryItem(
                    name=item_name,
                    quantity=quantity,
                    unit=item_data.get("unit", "piece"),
                    expiration_date=estimated_expiry,
                    category=self._auto_categorize_item(item_name),
                    brand=item_data.get("brand", "unknown"),
                    location=self._suggest_storage_location(item_name),
                    cost_per_unit=cost / quantity if quantity > 0 else 0
                )
                self.inventory[item_name] = new_item
            
            processed_items.append({
                "name": item_name,
                "quantity": quantity,
                "cost": cost,
                "location": self.inventory[item_name].location,
                "estimated_expiry": self.inventory[item_name].expiration_date.isoformat() if self.inventory[item_name].expiration_date else None
            })
            total_cost += cost
        
        return {
            "receipt_processed": True,
            "items_added": len(processed_items),
            "processed_items": processed_items,
            "total_cost": round(total_cost, 2),
            "store": receipt_data.get("store", "Unknown"),
            "date": receipt_data.get("date", datetime.now().isoformat())
        }
    
    async def _set_reorder_point(self, params: Dict, context: ExecutionContext) -> Dict[str, Any]:
        """Set reorder point for automatic shopping suggestions"""
        item_name = params["item_name"]
        reorder_point = params.get("quantity", 1)
        
        self.reorder_points[item_name] = reorder_point
        
        return {
            "success": True,
            "item": item_name,
            "reorder_point": reorder_point,
            "current_quantity": self.inventory.get(item_name, {}).quantity if item_name in self.inventory else 0
        }
    
    async def _predict_shopping_needs(self, context: ExecutionContext) -> Dict[str, Any]:
        """Predict future shopping needs based on consumption patterns"""
        predictions = []
        
        for item_name, consumption_data in self.consumption_patterns.items():
            if item_name in self.inventory:
                current_quantity = self.inventory[item_name].quantity
                avg_consumption = consumption_data.get("avg_daily_consumption", 0.1)
                
                days_until_depletion = current_quantity / avg_consumption if avg_consumption > 0 else 999
                
                if days_until_depletion <= 14:  # Predict items needed within 2 weeks
                    suggested_quantity = self._calculate_suggested_order_quantity(item_name)
                    
                    predictions.append({
                        "item": item_name,
                        "current_quantity": current_quantity,
                        "days_until_depletion": round(days_until_depletion, 1),
                        "avg_daily_consumption": round(avg_consumption, 2),
                        "suggested_order_quantity": suggested_quantity,
                        "priority": "high" if days_until_depletion <= 7 else "medium"
                    })
        
        return {
            "shopping_predictions": predictions,
            "high_priority_items": [p for p in predictions if p["priority"] == "high"],
            "estimated_shopping_needed_by": (datetime.now() + timedelta(days=7)).isoformat(),
            "prediction_confidence": 0.75
        }
    
    def _check_item_expiry_warning(self, item: InventoryItem) -> Optional[str]:
        """Check if item needs expiry warning"""
        if not item.expiration_date:
            return None
        
        days_until_expiry = (item.expiration_date - datetime.now()).days
        
        if days_until_expiry <= 1:
            return "expires_very_soon"
        elif days_until_expiry <= 3:
            return "expires_soon"
        elif days_until_expiry <= 7:
            return "expires_this_week"
        
        return None
    
    def _track_consumption(self, item_name: str, quantity: float):
        """Track consumption patterns for predictive ordering"""
        if item_name not in self.consumption_patterns:
            self.consumption_patterns[item_name] = {
                "total_consumed": 0,
                "consumption_events": [],
                "avg_daily_consumption": 0
            }
        
        pattern = self.consumption_patterns[item_name]
        pattern["total_consumed"] += quantity
        pattern["consumption_events"].append({
            "quantity": quantity,
            "date": datetime.now().isoformat()
        })
        
        # Calculate rolling average (last 30 days)
        recent_events = [e for e in pattern["consumption_events"] 
                        if (datetime.now() - datetime.fromisoformat(e["date"])).days <= 30]
        
        if recent_events:
            total_recent = sum(e["quantity"] for e in recent_events)
            days_span = max(1, len(recent_events))  # Avoid division by zero
            pattern["avg_daily_consumption"] = total_recent / days_span
    
    def _calculate_suggested_order_quantity(self, item_name: str) -> float:
        """Calculate suggested order quantity based on consumption patterns"""
        if item_name in self.consumption_patterns:
            avg_daily = self.consumption_patterns[item_name].get("avg_daily_consumption", 0.1)
            # Order enough for 2 weeks plus buffer
            return max(1, avg_daily * 14 * 1.2)
        
        # Default suggestion
        return 2
    
    def _suggest_meals_for_item(self, item_name: str) -> List[str]:
        """Suggest meals that use expiring items"""
        # Mock meal suggestions - would integrate with recipe database
        meal_suggestions = {
            "milk": ["Pancakes", "Smoothies", "Cereal"],
            "eggs": ["Scrambled eggs", "Omelet", "French toast"],
            "bread": ["Toast", "Sandwiches", "French toast"],
            "bananas": ["Banana bread", "Smoothies", "Pancakes"],
            "yogurt": ["Parfait", "Smoothies", "Snack"],
            "cheese": ["Grilled cheese", "Pasta", "Salad"],
            "chicken": ["Stir fry", "Soup", "Salad"],
            "vegetables": ["Stir fry", "Soup", "Salad"]
        }
        
        for key, suggestions in meal_suggestions.items():
            if key in item_name.lower():
                return suggestions[:3]  # Return top 3 suggestions
        
        return ["Use in soup", "Add to salad", "Cook quickly"]
    
    def _generate_expiry_recommendations(self, expiring_items: List[Dict]) -> List[str]:
        """Generate recommendations based on expiring items"""
        recommendations = []
        
        urgent_items = [i for i in expiring_items if i["urgency"] in ["expired", "urgent"]]
        
        if urgent_items:
            recommendations.append(f"Use {len(urgent_items)} items immediately to avoid waste")
        
        high_priority = [i for i in expiring_items if i["urgency"] == "high"]
        if high_priority:
            recommendations.append(f"Plan meals for {len(high_priority)} items expiring this week")
        
        if len(expiring_items) > 5:
            recommendations.append("Consider meal prep to use multiple expiring items")
        
        total_value = sum(i["potential_waste_cost"] for i in expiring_items)
        if total_value > 20:
            recommendations.append(f"Potential waste value: ${total_value:.2f} - prioritize usage")
        
        return recommendations
    
    def _estimate_expiration_date(self, item_name: str) -> Optional[datetime]:
        """Estimate expiration date for new items"""
        # Default expiration estimates by category
        estimates = {
            "dairy": 7,    # days
            "meat": 3,
            "seafood": 2,
            "produce": 5,
            "bread": 5,
            "frozen": 90,
            "canned": 365,
            "dry_goods": 180
        }
        
        category = self._auto_categorize_item(item_name)
        days = estimates.get(category, 30)  # Default 30 days
        
        return datetime.now() + timedelta(days=days)
    
    def _auto_categorize_item(self, item_name: str) -> str:
        """Automatically categorize item based on name"""
        item_lower = item_name.lower()
        
        if any(dairy in item_lower for dairy in ["milk", "cheese", "yogurt", "butter", "cream"]):
            return "dairy"
        elif any(meat in item_lower for meat in ["chicken", "beef", "pork", "turkey", "bacon"]):
            return "meat"
        elif any(seafood in item_lower for seafood in ["fish", "salmon", "tuna", "shrimp", "crab"]):
            return "seafood"
        elif any(produce in item_lower for produce in ["apple", "banana", "carrot", "onion", "tomato", "lettuce", "potato"]):
            return "produce"
        elif any(bread in item_lower for bread in ["bread", "bagel", "muffin", "roll"]):
            return "bread"
        elif "frozen" in item_lower:
            return "frozen"
        elif any(canned in item_lower for canned in ["canned", "jar", "bottle"]):
            return "canned"
        else:
            return "dry_goods"
    
    def _suggest_storage_location(self, item_name: str) -> str:
        """Suggest optimal storage location for item"""
        category = self._auto_categorize_item(item_name)
        
        location_map = {
            "dairy": "fridge",
            "meat": "fridge",
            "seafood": "fridge",
            "produce": "fridge",
            "bread": "pantry",
            "frozen": "freezer",
            "canned": "pantry",
            "dry_goods": "pantry"
        }
        
        return location_map.get(category, "pantry")