"""
Price Comparator Tool for Agent Bucky
Multi-store price comparison and optimization
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import random
import statistics

from shared.mcp_framework.base_server import BaseMCPTool, ExecutionContext, ExecutionResult

class PriceComparatorTool(BaseMCPTool):
    """Multi-store price comparison and optimization"""
    
    def __init__(self):
        super().__init__("price_comparator", "Compare prices across multiple stores and find best deals")
        self.store_apis = {
            "kroger": {"api_key": "", "base_url": "https://api.kroger.com"},
            "walmart": {"api_key": "", "base_url": "https://api.walmart.com"},
            "target": {"api_key": "", "base_url": "https://api.target.com"},
            "costco": {"api_key": "", "base_url": "https://api.costco.com"},
            "whole_foods": {"api_key": "", "base_url": "https://api.wholefoods.com"}
        }
        self.price_history = {}
        self.price_alerts = {}
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["compare_prices", "find_deals", "track_price", "get_price_history", 
                            "set_price_alert", "analyze_trends"]
                },
                "items": {"type": "array", "items": {"type": "string"}},
                "stores": {"type": "array", "items": {"type": "string"}},
                "budget_limit": {"type": "number"},
                "location": {"type": "string"},
                "price_threshold": {"type": "number"},
                "time_period": {"type": "string", "enum": ["week", "month", "quarter", "year"]}
            },
            "required": ["action", "items"]
        }
    
    def get_return_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "price_comparisons": {"type": "array"},
                "best_deals": {"type": "array"},
                "total_savings": {"type": "number"},
                "recommended_stores": {"type": "array"},
                "price_trends": {"type": "object"},
                "alert_status": {"type": "object"}
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        action = parameters["action"]
        items = parameters["items"]
        
        try:
            if action == "compare_prices":
                result = await self._compare_item_prices(
                    items, 
                    parameters.get("stores", []), 
                    parameters.get("location", ""),
                    context
                )
            elif action == "find_deals":
                result = await self._find_current_deals(items, context)
            elif action == "track_price":
                result = await self._setup_price_tracking(items, context)
            elif action == "get_price_history":
                result = await self._get_price_history(
                    items, 
                    parameters.get("time_period", "month"), 
                    context
                )
            elif action == "set_price_alert":
                result = await self._set_price_alert(
                    items, 
                    parameters.get("price_threshold", 0), 
                    context
                )
            else:  # analyze_trends
                result = await self._analyze_price_trends(items, context)
            
            return ExecutionResult(success=True, result=result, execution_time=1.0)
            
        except Exception as e:
            self.logger.error(f"Price comparison failed: {e}")
            return ExecutionResult(success=False, error=str(e), execution_time=0.0)
    
    async def _compare_item_prices(self, items: List[str], stores: List[str], location: str, context: ExecutionContext) -> Dict[str, Any]:
        """Compare prices across multiple stores"""
        price_comparisons = []
        total_savings = 0
        
        for item in items:
            item_comparison = {
                "item": item,
                "prices": {},
                "best_deal": None,
                "price_range": {},
                "availability": {},
                "store_ratings": {}
            }
            
            # Generate mock prices for different stores
            base_price = self._generate_base_price(item)
            store_prices = {}
            
            available_stores = stores if stores else list(self.store_apis.keys())
            
            for store in available_stores:
                # Add realistic price variation
                variation = self._get_store_price_variation(store, item)
                price = base_price * variation
                sale_price = price * 0.85 if self._is_on_sale(store, item) else None
                
                store_prices[store] = {
                    "regular_price": round(price, 2),
                    "sale_price": round(sale_price, 2) if sale_price else None,
                    "final_price": round(sale_price or price, 2),
                    "on_sale": sale_price is not None,
                    "in_stock": self._check_stock_status(store, item),
                    "store_brand_available": self._has_store_brand(store, item),
                    "unit_price": round((sale_price or price) / self._get_package_size(item), 3)
                }
            
            item_comparison["prices"] = store_prices
            
            # Find best deal
            in_stock_stores = {k: v for k, v in store_prices.items() if v["in_stock"]}
            if in_stock_stores:
                best_store = min(in_stock_stores.keys(), 
                               key=lambda s: in_stock_stores[s]["final_price"])
                
                max_price = max(in_stock_stores.values(), key=lambda x: x["final_price"])["final_price"]
                savings = max_price - in_stock_stores[best_store]["final_price"]
                
                item_comparison["best_deal"] = {
                    "store": best_store,
                    "price": in_stock_stores[best_store]["final_price"],
                    "savings": round(savings, 2),
                    "store_brand_option": in_stock_stores[best_store]["store_brand_available"]
                }
                total_savings += savings
            
            # Price range analysis
            in_stock_prices = [p["final_price"] for p in store_prices.values() if p["in_stock"]]
            if in_stock_prices:
                item_comparison["price_range"] = {
                    "min": min(in_stock_prices),
                    "max": max(in_stock_prices),
                    "avg": round(sum(in_stock_prices) / len(in_stock_prices), 2),
                    "price_spread": round(max(in_stock_prices) - min(in_stock_prices), 2)
                }
            
            price_comparisons.append(item_comparison)
        
        # Recommend best stores overall
        store_scores = self._calculate_store_scores(price_comparisons)
        recommended_stores = sorted(store_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "price_comparisons": price_comparisons,
            "total_potential_savings": round(total_savings, 2),
            "recommended_stores": [{"store": store, "score": score} for store, score in recommended_stores],
            "comparison_date": datetime.utcnow().isoformat(),
            "location": location,
            "money_saving_tips": self._generate_money_saving_tips(price_comparisons)
        }
    
    async def _find_current_deals(self, items: List[str], context: ExecutionContext) -> Dict[str, Any]:
        """Find current deals and promotions"""
        current_deals = []
        
        for item in items:
            deals = self._generate_mock_deals(item)
            current_deals.extend(deals)
        
        # Sort deals by savings percentage
        current_deals.sort(key=lambda x: x["discount_percent"], reverse=True)
        
        total_potential_savings = sum(deal["savings_amount"] for deal in current_deals)
        
        return {
            "current_deals": current_deals,
            "total_deals_found": len(current_deals),
            "total_potential_savings": round(total_potential_savings, 2),
            "deal_categories": self._categorize_deals(current_deals),
            "expiring_soon": [deal for deal in current_deals if self._deal_expires_soon(deal)],
            "best_deals": current_deals[:5]
        }
    
    async def _setup_price_tracking(self, items: List[str], context: ExecutionContext) -> Dict[str, Any]:
        """Setup price tracking for specified items"""
        tracking_setup = []
        
        for item in items:
            if item not in self.price_history:
                self.price_history[item] = []
            
            current_price = self._get_current_average_price(item)
            price_point = {
                "price": current_price,
                "date": datetime.utcnow().isoformat(),
                "stores_checked": list(self.store_apis.keys())
            }
            
            self.price_history[item].append(price_point)
            
            tracking_setup.append({
                "item": item,
                "current_price": current_price,
                "tracking_started": datetime.utcnow().isoformat(),
                "price_check_frequency": "daily",
                "alert_threshold": current_price * 0.9
            })
        
        return {
            "tracking_setup": tracking_setup,
            "items_tracked": len(items),
            "next_price_check": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "tracking_features": [
                "Daily price monitoring",
                "Trend analysis", 
                "Sale alerts",
                "Historical comparison"
            ]
        }
    
    async def _get_price_history(self, items: List[str], time_period: str, context: ExecutionContext) -> Dict[str, Any]:
        """Get price history for items"""
        price_histories = {}
        
        days_back = {"week": 7, "month": 30, "quarter": 90, "year": 365}
        cutoff_date = datetime.utcnow() - timedelta(days=days_back.get(time_period, 30))
        
        for item in items:
            if item in self.price_history:
                relevant_history = [
                    point for point in self.price_history[item]
                    if datetime.fromisoformat(point["date"]) >= cutoff_date
                ]
                
                if relevant_history:
                    prices = [point["price"] for point in relevant_history]
                    price_histories[item] = {
                        "price_points": relevant_history,
                        "min_price": min(prices),
                        "max_price": max(prices),
                        "avg_price": round(sum(prices) / len(prices), 2),
                        "current_price": prices[-1],
                        "price_trend": self._calculate_price_trend(prices),
                        "volatility": self._calculate_price_volatility(prices)
                    }
                else:
                    price_histories[item] = {"message": "No price history in selected period"}
            else:
                price_histories[item] = {"message": "No price tracking data available"}
        
        return {
            "price_histories": price_histories,
            "time_period": time_period,
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    async def _set_price_alert(self, items: List[str], price_threshold: float, context: ExecutionContext) -> Dict[str, Any]:
        """Set price alerts for items"""
        alert_setup = []
        
        for item in items:
            current_price = self._get_current_average_price(item)
            threshold = price_threshold if price_threshold > 0 else current_price * 0.9
            
            self.price_alerts[item] = {
                "threshold": threshold,
                "current_price": current_price,
                "created_date": datetime.utcnow().isoformat(),
                "alert_type": "below_threshold",
                "active": True
            }
            
            alert_setup.append({
                "item": item,
                "alert_threshold": threshold,
                "current_price": current_price,
                "potential_savings": round(current_price - threshold, 2),
                "alert_active": True
            })
        
        return {
            "price_alerts": alert_setup,
            "alerts_created": len(items),
            "monitoring_frequency": "daily",
            "notification_methods": ["in_app", "email"]
        }
    
    async def _analyze_price_trends(self, items: List[str], context: ExecutionContext) -> Dict[str, Any]:
        """Analyze price trends and predictions"""
        trend_analysis = {}
        
        for item in items:
            if item in self.price_history and len(self.price_history[item]) >= 5:
                prices = [point["price"] for point in self.price_history[item]]
                
                trend_analysis[item] = {
                    "trend_direction": self._calculate_price_trend(prices),
                    "price_stability": self._calculate_price_stability(prices),
                    "seasonal_pattern": self._detect_seasonal_pattern(item),
                    "prediction_next_month": self._predict_future_price(prices),
                    "best_time_to_buy": self._recommend_purchase_timing(item),
                    "confidence_score": 0.75
                }
            else:
                trend_analysis[item] = {"message": "Insufficient data for trend analysis"}
        
        return {
            "trend_analysis": trend_analysis,
            "market_insights": self._generate_market_insights(),
            "buying_recommendations": self._generate_buying_recommendations(trend_analysis)
        }
    
    # Helper methods
    def _generate_base_price(self, item: str) -> float:
        """Generate realistic base price for item"""
        price_map = {
            "milk": 3.49, "bread": 2.99, "eggs": 2.99, "cheese": 4.99,
            "chicken": 6.99, "beef": 8.99, "salmon": 12.99,
            "bananas": 1.99, "apples": 3.99, "tomatoes": 2.99,
            "rice": 2.49, "pasta": 1.99, "cereal": 4.49,
            "yogurt": 4.49, "butter": 3.99, "olive_oil": 7.99
        }
        
        for key, price in price_map.items():
            if key in item.lower():
                return price
        return 4.99
    
    def _get_store_price_variation(self, store: str, item: str) -> float:
        """Get price variation factor for different stores"""
        variations = {
            "walmart": 0.85, "kroger": 0.95, "target": 1.05,
            "whole_foods": 1.25, "costco": 0.80
        }
        return variations.get(store, 1.0)
    
    def _is_on_sale(self, store: str, item: str) -> bool:
        """Check if item is currently on sale"""
        return random.random() < 0.3
    
    def _check_stock_status(self, store: str, item: str) -> bool:
        """Check if item is in stock"""
        return random.random() < 0.9
    
    def _has_store_brand(self, store: str, item: str) -> bool:
        """Check if store has store-brand version"""
        store_brand_probability = {
            "walmart": 0.8, "kroger": 0.7, "target": 0.6,
            "whole_foods": 0.4, "costco": 0.9
        }
        return random.random() < store_brand_probability.get(store, 0.5)
    
    def _get_package_size(self, item: str) -> float:
        """Get typical package size for unit price calculation"""
        sizes = {"milk": 1.0, "bread": 1.0, "eggs": 12.0, "cheese": 0.5}
        for key, size in sizes.items():
            if key in item.lower():
                return size
        return 1.0
    
    def _calculate_store_scores(self, comparisons: List[Dict]) -> Dict[str, float]:
        """Calculate overall scores for stores"""
        store_scores = {}
        
        for comparison in comparisons:
            for store, price_data in comparison["prices"].items():
                if store not in store_scores:
                    store_scores[store] = 0
                
                if price_data["in_stock"]:
                    base_score = 50
                    if price_data["on_sale"]:
                        base_score += 20
                    if price_data["store_brand_available"]:
                        base_score += 10
                    store_scores[store] += base_score
        
        return store_scores
    
    def _generate_money_saving_tips(self, comparisons: List[Dict]) -> List[str]:
        """Generate money-saving tips"""
        tips = [
            "Compare unit prices, not just package prices",
            "Check for store brand alternatives", 
            "Look for items currently on sale",
            "Consider buying in bulk for non-perishables"
        ]
        
        sale_items = sum(1 for comp in comparisons 
                        for store_data in comp["prices"].values() 
                        if store_data.get("on_sale", False))
        
        if sale_items > len(comparisons) * 0.3:
            tips.append("Many items are on sale - good time to stock up!")
        
        return tips
    
    def _generate_mock_deals(self, item: str) -> List[Dict]:
        """Generate mock current deals"""
        deals = []
        stores = ["walmart", "kroger", "target"]
        
        for store in stores:
            if random.random() < 0.4:
                base_price = self._generate_base_price(item)
                discount = random.uniform(0.15, 0.40)
                
                deals.append({
                    "item": item,
                    "store": store,
                    "original_price": round(base_price, 2),
                    "sale_price": round(base_price * (1 - discount), 2),
                    "discount_percent": round(discount * 100, 1),
                    "savings_amount": round(base_price * discount, 2),
                    "deal_type": random.choice(["weekly_special", "clearance", "buy_one_get_one", "member_special"]),
                    "valid_until": (datetime.utcnow() + timedelta(days=random.randint(1, 14))).isoformat()
                })
        
        return deals
    
    def _categorize_deals(self, deals: List[Dict]) -> Dict[str, int]:
        """Categorize deals by type"""
        categories = {}
        for deal in deals:
            deal_type = deal["deal_type"]
            categories[deal_type] = categories.get(deal_type, 0) + 1
        return categories
    
    def _deal_expires_soon(self, deal: Dict) -> bool:
        """Check if deal expires within 3 days"""
        expiry_date = datetime.fromisoformat(deal["valid_until"])
        return (expiry_date - datetime.utcnow()).days <= 3
    
    def _get_current_average_price(self, item: str) -> float:
        """Get current average price across stores"""
        return self._generate_base_price(item) * random.uniform(0.9, 1.1)
    
    def _calculate_price_trend(self, prices: List[float]) -> str:
        """Calculate price trend direction"""
        if len(prices) < 2:
            return "stable"
        
        recent_avg = sum(prices[-3:]) / len(prices[-3:])
        older_avg = sum(prices[:-3]) / len(prices[:-3]) if len(prices) > 3 else prices[0]
        
        if recent_avg > older_avg * 1.05:
            return "increasing"
        elif recent_avg < older_avg * 0.95:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_price_volatility(self, prices: List[float]) -> str:
        """Calculate price volatility"""
        if len(prices) < 2:
            return "unknown"
        
        std_dev = statistics.stdev(prices)
        avg_price = statistics.mean(prices)
        volatility = std_dev / avg_price
        
        if volatility > 0.15:
            return "high"
        elif volatility > 0.05:
            return "medium"
        else:
            return "low"
    
    def _calculate_price_stability(self, prices: List[float]) -> float:
        """Calculate price stability score"""
        if len(prices) < 2:
            return 1.0
        
        volatility = statistics.stdev(prices) / statistics.mean(prices)
        return max(0, 1 - volatility)
    
    def _detect_seasonal_pattern(self, item: str) -> str:
        """Detect seasonal pricing patterns"""
        seasonal_items = {
            "ice_cream": "summer_peak",
            "soup": "winter_peak", 
            "barbecue": "summer_peak",
            "turkey": "thanksgiving_peak"
        }
        
        for key, pattern in seasonal_items.items():
            if key in item.lower():
                return pattern
        return "no_pattern"
    
    def _predict_future_price(self, prices: List[float]) -> float:
        """Predict future price"""
        if len(prices) < 3:
            return prices[-1] if prices else 0
        
        # Simple trend prediction
        recent_trend = (prices[-1] - prices[-3]) / 2
        return round(prices[-1] + recent_trend, 2)
    
    def _recommend_purchase_timing(self, item: str) -> str:
        """Recommend best time to purchase"""
        current_month = datetime.utcnow().month
        
        # Seasonal recommendations
        if "ice_cream" in item.lower():
            return "winter_months" if current_month in [12, 1, 2] else "wait_for_winter"
        elif "soup" in item.lower():
            return "summer_months" if current_month in [6, 7, 8] else "wait_for_summer"
        else:
            return "monitor_for_sales"
    
    def _generate_market_insights(self) -> List[str]:
        """Generate general market insights"""
        return [
            "Grocery prices tend to be lowest on Wednesdays",
            "End-of-month sales are common for clearing inventory",
            "Store brands typically offer 20-25% savings",
            "Bulk buying saves money for non-perishables"
        ]
    
    def _generate_buying_recommendations(self, trend_analysis: Dict) -> List[str]:
        """Generate buying recommendations based on trends"""
        recommendations = []
        
        for item, analysis in trend_analysis.items():
            if isinstance(analysis, dict) and "trend_direction" in analysis:
                if analysis["trend_direction"] == "increasing":
                    recommendations.append(f"Consider buying {item} now before prices rise further")
                elif analysis["trend_direction"] == "decreasing":
                    recommendations.append(f"Wait to buy {item} - prices are trending down")
                else:
                    recommendations.append(f"{item} prices are stable - good time to buy")
        
        return recommendations