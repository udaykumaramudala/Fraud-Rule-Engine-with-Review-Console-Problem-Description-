import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.engine.base import BaseRule, RuleResult
from app.engine.registry import register_rule

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth in kilometers.
    """
    R = 6371.0 # Radius of Earth in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

@register_rule
class ImpossibleTravelRule(BaseRule):
    rule_id = "impossible_geographical_location"
    rule_name = "Impossible Geographical Location"
    description = "Detects physically impossible travel velocity between consecutive transactions across different locations"
    enabled = True
    weight = 1.0
    parameters = {
        "max_commercial_speed_kmh": 850.0, # Approximate cruising speed of commercial airliners
        "high_risk_speed_kmh": 600.0,
        "min_distance_threshold_km": 50.0, # Ignore tiny GPS jitter within same metro area
        "instant_teleport_min_distance_km": 300.0,
        "instant_teleport_max_minutes": 15.0
    }

    def evaluate(
        self,
        transaction: Dict[str, Any],
        user_history: List[Dict[str, Any]],
        system_context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        lat1 = transaction.get("latitude")
        lon1 = transaction.get("longitude")

        if lat1 is None or lon1 is None:
            return RuleResult(
                is_flagged=False,
                risk_score=0.0,
                severity="LOW",
                reason="Transaction has no geographical coordinates provided.",
                metadata={}
            )

        current_time = transaction.get("timestamp")
        if isinstance(current_time, str):
            current_time = datetime.fromisoformat(current_time.replace("Z", "+00:00"))
        if not current_time:
            current_time = datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        # Find the most recent previous transaction with coordinates
        valid_history = []
        for tx in user_history:
            if tx.get("latitude") is not None and tx.get("longitude") is not None:
                tx_time = tx.get("timestamp")
                if isinstance(tx_time, str):
                    tx_time = datetime.fromisoformat(tx_time.replace("Z", "+00:00"))
                if tx_time:
                    if tx_time.tzinfo is None:
                        tx_time = tx_time.replace(tzinfo=timezone.utc)
                    valid_history.append((tx_time, tx))

        if not valid_history:
            return RuleResult(
                is_flagged=False,
                risk_score=0.0,
                severity="LOW",
                reason="First geolocated transaction for this user. Location recorded as baseline.",
                metadata={"location_name": transaction.get("location_name", "Unknown")}
            )

        # Sort by timestamp descending to find immediate predecessor
        valid_history.sort(key=lambda item: item[0], reverse=True)
        prev_time, prev_tx = valid_history[0]

        time_delta_seconds = abs((current_time - prev_time).total_seconds())
        # Prevent division by zero: if same second, assume at least 1 second
        elapsed_hours = max(1.0, time_delta_seconds) / 3600.0
        elapsed_minutes = time_delta_seconds / 60.0

        lat2 = float(prev_tx.get("latitude"))
        lon2 = float(prev_tx.get("longitude"))

        distance_km = haversine_distance_km(float(lat1), float(lon1), lat2, lon2)
        implied_speed_kmh = distance_km / elapsed_hours

        curr_loc_name = transaction.get("location_name") or f"({lat1:.3f}, {lon1:.3f})"
        prev_loc_name = prev_tx.get("location_name") or f"({lat2:.3f}, {lon2:.3f})"

        metadata = {
            "origin_location": prev_loc_name,
            "origin_coords": {"lat": lat2, "lon": lon2},
            "destination_location": curr_loc_name,
            "destination_coords": {"lat": float(lat1), "lon": float(lon1)},
            "distance_km": round(distance_km, 2),
            "elapsed_minutes": round(elapsed_minutes, 1),
            "implied_speed_kmh": round(implied_speed_kmh, 1),
            "max_allowed_speed_kmh": self.parameters["max_commercial_speed_kmh"]
        }

        # Check if distance is negligible (e.g. coffee shop next door or same city jitter)
        if distance_km < self.parameters["min_distance_threshold_km"]:
            return RuleResult(
                is_flagged=False,
                risk_score=0.0,
                severity="LOW",
                reason=f"Geographical distance is normal ({distance_km:.1f} km from {prev_loc_name}).",
                metadata=metadata
            )

        # Instant Teleportation check: e.g. London to Tokyo in 10 minutes
        is_teleport = (
            distance_km >= self.parameters["instant_teleport_min_distance_km"] and
            elapsed_minutes <= self.parameters["instant_teleport_max_minutes"]
        )

        if is_teleport or implied_speed_kmh > (self.parameters["max_commercial_speed_kmh"] * 1.5):
            return RuleResult(
                is_flagged=True,
                risk_score=95.0,
                severity="CRITICAL",
                reason=(
                    f"Impossible travel detected: {distance_km:,.1f} km traversed between '{prev_loc_name}' "
                    f"and '{curr_loc_name}' in only {elapsed_minutes:.1f} minutes. "
                    f"Required travel speed of {implied_speed_kmh:,.1f} km/h is physically impossible."
                ),
                metadata=metadata
            )

        if implied_speed_kmh > self.parameters["max_commercial_speed_kmh"]:
            return RuleResult(
                is_flagged=True,
                risk_score=85.0,
                severity="HIGH",
                reason=(
                    f"High-speed impossible transit: Distance {distance_km:,.1f} km in {elapsed_minutes:.1f} minutes "
                    f"requires {implied_speed_kmh:,.1f} km/h, exceeding commercial flight speeds ({self.parameters['max_commercial_speed_kmh']} km/h)."
                ),
                metadata=metadata
            )

        if implied_speed_kmh > self.parameters["high_risk_speed_kmh"]:
            return RuleResult(
                is_flagged=True,
                risk_score=50.0,
                severity="MEDIUM",
                reason=(
                    f"Unusually fast relocation: {distance_km:,.1f} km in {elapsed_minutes:.1f} minutes "
                    f"({implied_speed_kmh:,.1f} km/h) suggests proxy/VPN hopping or concurrent card usage."
                ),
                metadata=metadata
            )

        return RuleResult(
            is_flagged=False,
            risk_score=0.0,
            severity="LOW",
            reason=f"Plausible travel speed: {distance_km:.1f} km covered in {elapsed_minutes:.1f} min ({implied_speed_kmh:.1f} km/h).",
            metadata=metadata
        )
