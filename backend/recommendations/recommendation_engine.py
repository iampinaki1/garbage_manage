"""
Recycling Recommendation Engine.
Provides deterministic, localized, and contamination-aware recycling recommendations
and documented environmental impact metrics across 9 canonical waste categories.

Documented references:
- US EPA Waste Reduction Model (WARM) v15
- European Environment Agency (EEA) Packaging & Plastic Recycling Directives
- Wrap UK Textiles & Material Impact Benchmarks
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent

# Default CSV file paths
DEFAULT_CSV_PATHS = [
    Path(__file__).resolve().parent / "recycling_data.csv",
    ROOT / "backend" / "recommendations" / "recycling_data.csv",
    ROOT / "backend" / "app" / "recommendations" / "recycling_data.csv",
]

# Supported Location Guidelines
LOCATION_PROFILES = {
    "us_epa": {
        "name": "United States (EPA Guidelines)",
        "blue_bin": "Blue Bin (Curbside Commingled Recyclables: paper, rigid plastic #1 & #2, metal cans)",
        "green_bin": "Green Bin (Yard Trimmings & Organics / Composting)",
        "black_bin": "Black / Grey Bin (General Non-Recyclable Landfill)",
        "hazardous": "Household Hazardous Waste (HHW) Collection Facility / Retail Drop-off",
        "soft_plastics": "Designated Supermarket Soft Plastic Drop-off Kiosk (Never curbside)",
        "glass": "Blue Bin or Dedicated Curbside Glass Caddy",
        "e_waste": "Municipal E-waste Drop-off Depot or Certified Electronics Recycler"
    },
    "eu_standard": {
        "name": "European Union (Standard Dual-System / Grüne Punkt)",
        "blue_bin": "Blue Bin (Papiertonne: Clean Dry Paper & Cardboard)",
        "yellow_bin": "Yellow Bin / Gelber Sack (Lightweight Packaging: Plastics, Metals, Composites)",
        "green_bin": "Brown Bin (Biotonne: Organic Food Waste & Garden Composting)",
        "black_bin": "Grey / Black Bin (Restmüll: Non-Recyclable Residual Waste)",
        "hazardous": "Schadstoffmobil / Municipal Hazardous Depot (Batteries at supermarkets)",
        "soft_plastics": "Yellow Bin / Gelber Sack (Accepted in most EU packaging schemes)",
        "glass": "Altglas Container (Divided by White, Green, and Brown glass)",
        "e_waste": "Wertstoffhof (Municipal Recycling Center) or Electrical Retailer Take-Back"
    },
    "uk_wrap": {
        "name": "United Kingdom (WRAP Framework)",
        "blue_bin": "Blue / Mixed Dry Recycling Bin (Paper, Tins, Rigid Plastics)",
        "green_bin": "Brown / Green Caddy (Food Scraps & Garden Waste)",
        "black_bin": "Black Wheelie Bin (General Residual Landfill / EfW)",
        "hazardous": "Local Council Household Waste Recycling Centre (HWRC)",
        "soft_plastics": "Supermarket Front-of-Store Soft Plastic Collection Points",
        "glass": "Glass Bottle Bank or Mixed Dry Recycling (Council specific)",
        "e_waste": "HWRC Council Amenity Site or Retail Take-Back"
    },
    "india_cpcb": {
        "name": "India (CPCB Solid Waste Management Rules)",
        "blue_bin": "Blue Bin (Dry Waste: Paper, Clean Plastics, Metals, Glass for formal/informal sorting)",
        "green_bin": "Green Bin (Wet Waste: Kitchen Food Scraps & Biodegradable Organics for Composting)",
        "black_bin": "Black Bin (Domestic Hazardous / Sanitary Residual Waste)",
        "hazardous": "Authorized E-Waste & Hazardous Material Collection Center",
        "soft_plastics": "Dry Waste Segregation / Plastic Waste Processing Facility",
        "glass": "Blue Bin (Segregated unbroken glass) or Kabadiwala / Scrap Dealer",
        "e_waste": "Authorized EPR E-Waste Collection Point"
    }
}

# Average item weights in kg for realistic single-item impact calculations
AVERAGE_ITEM_WEIGHTS_KG = {
    "organic_waste": 0.150,     # ~150g (banana peel, food scraps)
    "paper_waste": 0.080,       # ~80g (folded paper, small cardboard)
    "plastic_waste": 0.035,     # ~35g (standard 500ml PET bottle or tub)
    "metal_waste": 0.015,       # ~15g (aluminium soda can)
    "glass_waste": 0.220,       # ~220g (glass bottle / condiment jar)
    "electronic_waste": 0.180,  # ~180g (smartphone / cable / mouse)
    "hazardous_waste": 0.050,   # ~50g (alkaline battery / aerosol can)
    "textile_waste": 0.200,     # ~200g (cotton t-shirt)
    "residual_waste": 0.050     # ~50g (diaper / composite wrapper)
}


class RecyclingRecommendationEngine:
    """Production recommendation engine for waste segregation and environmental impact."""

    def __init__(self, csv_path: Optional[Union[str, Path]] = None):
        self.csv_path = self._locate_csv(csv_path)
        self.database: List[Dict[str, Any]] = []
        self.category_index: Dict[str, List[Dict[str, Any]]] = {}
        self._load_database()

    def _locate_csv(self, preferred_path: Optional[Union[str, Path]]) -> Path:
        if preferred_path:
            p = Path(preferred_path)
            if p.exists():
                return p
        for p in DEFAULT_CSV_PATHS:
            if p.exists():
                return p
        raise FileNotFoundError(
            f"Recycling database CSV not found in search paths: {[str(p) for p in DEFAULT_CSV_PATHS]}"
        )

    def _load_database(self) -> None:
        self.database.clear()
        self.category_index.clear()
        
        with open(self.csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean and parse types
                item = {
                    "object_name": row["object_name"].strip(),
                    "material": row["material"].strip(),
                    "waste_category": row["waste_category"].strip().lower(),
                    "recyclable": row["recyclable"].strip().lower(),
                    "recommended_bin": row["recommended_bin"].strip(),
                    "recycling_method": row["recycling_method"].strip(),
                    "preparation_instructions": row["preparation_instructions"].strip(),
                    "disposal_instructions": row["disposal_instructions"].strip(),
                    "contamination_risk": row.get("contamination_risk", "medium").strip().lower(),
                    "contamination_notes": row.get("contamination_notes", "").strip(),
                    "co2_saved_kg_per_kg": float(row.get("co2_saved_kg_per_kg", 0.0) or 0.0),
                    "energy_saved_kwh_per_kg": float(row.get("energy_saved_kwh_per_kg", 0.0) or 0.0),
                    "reference_source": row.get("reference_source", "EPA WARM / EEA").strip()
                }
                self.database.append(item)
                cat = item["waste_category"]
                if cat not in self.category_index:
                    self.category_index[cat] = []
                self.category_index[cat].append(item)

        logger.info(f"Loaded {len(self.database)} recycling items across {len(self.category_index)} categories.")

    def get_supported_locations(self) -> List[str]:
        """Returns list of supported location profile identifiers."""
        return list(LOCATION_PROFILES.keys())

    def get_recommendation(
        self,
        category: str,
        query_item: Optional[str] = None,
        location: str = "us_epa",
        is_contaminated: bool = False,
        custom_weight_kg: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Produces comprehensive disposal guidance for a detected waste category.
        
        Args:
            category: Canonical category string (e.g. 'plastic_waste' or 'organic_waste')
            query_item: Optional specific object name (e.g. 'PET Water Bottle' or 'Banana Peel')
            location: Location profile key ('us_epa', 'eu_standard', 'uk_wrap', 'india_cpcb')
            is_contaminated: Flag indicating presence of food grease, chemical, or dirt contamination
            custom_weight_kg: Optional override for item mass in kg
        """
        normalized_cat = category.strip().lower()
        loc_profile = LOCATION_PROFILES.get(location, LOCATION_PROFILES["us_epa"])
        
        # 1. Match database item or select category baseline
        matched_item = self._find_best_match(normalized_cat, query_item)
        
        # 2. Determine base recyclability
        raw_recyclable = matched_item.get("recyclable", "false")
        is_recyclable = raw_recyclable == "true"
        is_conditional = raw_recyclable == "conditional"
        
        # 3. Apply Contamination Logic
        contamination_applied = False
        disposal_override_note = ""
        bin_override = None
        
        if is_contaminated and (is_recyclable or is_conditional):
            # Contamination ruins clean paper/plastic recyclability
            if normalized_cat in ["paper_waste", "cardboard"]:
                is_recyclable = False
                is_conditional = False
                contamination_applied = True
                bin_override = loc_profile["green_bin"] if "pizza" in matched_item["object_name"].lower() else loc_profile["black_bin"]
                disposal_override_note = "CONTAMINATION ALERT: Food grease/oil permanently soils paper fibers preventing pulping. Must NOT be placed in paper recycling bin."
            elif normalized_cat == "plastic_waste":
                contamination_applied = True
                disposal_override_note = "CONTAMINATION WARNING: Thorough rinsing required before placing in recycling. Severely soiled unrinsed plastics must be discarded into general waste."
            elif normalized_cat == "glass_waste":
                contamination_applied = True
                disposal_override_note = "CONTAMINATION NOTE: Food residue should be rinsed out with clean water to prevent odor and furnace contamination."

        # 4. Resolve Localized Recommended Bin
        recommended_bin = self._resolve_local_bin(matched_item, normalized_cat, loc_profile, bin_override, is_recyclable, is_conditional)
        
        # 5. Calculate Documented Environmental Impact
        weight_kg = custom_weight_kg if (custom_weight_kg and custom_weight_kg > 0) else AVERAGE_ITEM_WEIGHTS_KG.get(normalized_cat, 0.05)
        
        co2_factor = matched_item.get("co2_saved_kg_per_kg", 0.0)
        energy_factor = matched_item.get("energy_saved_kwh_per_kg", 0.0)
        
        if is_recyclable or is_conditional:
            est_co2_saved = round(co2_factor * weight_kg, 4)
            est_energy_saved = round(energy_factor * weight_kg, 4)
        else:
            est_co2_saved = 0.0
            est_energy_saved = 0.0

        # Recyclability status string
        if is_conditional:
            status_str = "Conditionally Recyclable (Specialized Stream)"
        elif is_recyclable:
            status_str = "Recyclable"
        else:
            status_str = "Non-Recyclable"

        # 6. Build Final Structured Output
        return {
            "category": normalized_cat,
            "category_display": normalized_cat.replace("_", " ").title(),
            "matched_item": matched_item["object_name"],
            "material": matched_item["material"],
            "is_recyclable": is_recyclable,
            "is_conditional": is_conditional,
            "recyclability_status": status_str,
            "recommended_bin": recommended_bin,
            "recycling_method": matched_item["recycling_method"],
            "preparation_instructions": matched_item["preparation_instructions"],
            "disposal_instructions": matched_item["disposal_instructions"] if not disposal_override_note else f"{disposal_override_note} {matched_item['disposal_instructions']}",
            "contamination_assessment": {
                "risk_level": matched_item.get("contamination_risk", "medium"),
                "is_contaminated": is_contaminated,
                "contamination_notes": matched_item.get("contamination_notes", ""),
                "action_taken": disposal_override_note if contamination_applied else "None required."
            },
            "environmental_impact": {
                "estimated_co2_saved_kg": est_co2_saved,
                "estimated_energy_saved_kwh": est_energy_saved,
                "assumed_weight_kg": round(weight_kg, 3),
                "factors_used": {
                    "co2_kg_per_kg": co2_factor,
                    "energy_kwh_per_kg": energy_factor
                },
                "disclaimer": "Estimates based on published EPA WARM v15 and EEA life-cycle conversion factors. Actual savings depend on local energy grid and recycling facility efficiency.",
                "reference_source": matched_item.get("reference_source", "EPA WARM v15")
            },
            "location_context": {
                "profile_id": location,
                "jurisdiction": loc_profile["name"],
                "local_guideline": self._get_local_rule_summary(normalized_cat, loc_profile)
            }
        }

    def _find_best_match(self, category: str, query_item: Optional[str]) -> Dict[str, Any]:
        """Matches a query string to a database record or returns category fallback."""
        items = self.category_index.get(category, [])
        if not items:
            # Fallback for unrecognized categories
            return {
                "object_name": category.replace("_", " ").title(),
                "material": "Mixed or Unspecified Material",
                "waste_category": category,
                "recyclable": "false",
                "recommended_bin": "Black Bin (General Waste)",
                "recycling_method": "Municipal solid waste handling",
                "preparation_instructions": "Inspect item for recycling identification symbols.",
                "disposal_instructions": "Check with local municipal recycling guidelines.",
                "contamination_risk": "medium",
                "contamination_notes": "Unclassified materials should not contaminate standard recycling streams.",
                "co2_saved_kg_per_kg": 0.0,
                "energy_saved_kwh_per_kg": 0.0,
                "reference_source": "General Municipal Solid Waste Guidelines"
            }

        if query_item:
            q = query_item.lower().strip()
            # 1. Exact match on object name
            for it in items:
                if q == it["object_name"].lower():
                    return it
            # 2. Substring match
            for it in items:
                if q in it["object_name"].lower() or any(w in it["object_name"].lower() for w in q.split()):
                    return it

        # Default to first primary representative item in category
        return items[0]

    def _resolve_local_bin(
        self,
        item: Dict[str, Any],
        category: str,
        profile: Dict[str, str],
        bin_override: Optional[str],
        is_recyclable: bool,
        is_conditional: bool
    ) -> str:
        """Adapts recommended bin dynamically based on location profile rules."""
        if bin_override:
            return bin_override

        # Soft plastics / Plastic film special handling
        if "soft" in item["object_name"].lower() or "film" in item["object_name"].lower() or "grocery bag" in item["object_name"].lower():
            return profile.get("soft_plastics", item["recommended_bin"])

        # Hazardous / Batteries
        if category == "hazardous_waste" or "battery" in item["object_name"].lower():
            return profile.get("hazardous", item["recommended_bin"])

        # E-Waste
        if category == "electronic_waste":
            return profile.get("e_waste", item["recommended_bin"])

        # Organics
        if category == "organic_waste":
            return profile.get("green_bin", item["recommended_bin"])

        # Non-recyclables
        if not is_recyclable and not is_conditional:
            return profile.get("black_bin", item["recommended_bin"])

        # Recyclable paper/cardboard
        if category == "paper_waste":
            return profile.get("blue_bin", item["recommended_bin"])

        # Recyclable glass
        if category == "glass_waste":
            return profile.get("glass", profile.get("blue_bin", item["recommended_bin"]))

        # Recyclable plastic or metal
        if category in ["plastic_waste", "metal_waste"]:
            if "yellow_bin" in profile:
                return profile["yellow_bin"]
            return profile.get("blue_bin", item["recommended_bin"])

        return item["recommended_bin"]

    def _get_local_rule_summary(self, category: str, profile: Dict[str, str]) -> str:
        """Provides brief local context for the waste category."""
        if category == "plastic_waste":
            return f"Under {profile['name']}, rigid plastics go to {profile.get('yellow_bin', profile.get('blue_bin'))}, while soft film bags require special grocery drop-off."
        elif category == "paper_waste":
            return f"Clean paper & cardboard belong in {profile.get('blue_bin')}. Food-soiled paper belongs in {profile.get('green_bin')} or {profile.get('black_bin')}."
        elif category == "electronic_waste":
            return f"Never dispose of electronics in curbside bins. Use {profile.get('e_waste')}."
        elif category == "hazardous_waste":
            return f"Toxic materials and batteries require specialized drop-off at {profile.get('hazardous')}."
        elif category == "organic_waste":
            return f"Organics must be kept separate in {profile.get('green_bin')} to prevent methane generation in landfills."
        return f"Follow local municipal sorting guidelines under {profile['name']}."


# Global Singleton Instance
_engine_instance: Optional[RecyclingRecommendationEngine] = None

def get_recommendation_engine() -> RecyclingRecommendationEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RecyclingRecommendationEngine()
    return _engine_instance


if __name__ == "__main__":
    engine = RecyclingRecommendationEngine()
    print("Testing Recommendation Engine across categories and locations:")
    samples = [
        ("plastic_waste", "PET Water Bottle", "us_epa", False),
        ("paper_waste", "Greasy Pizza Box", "us_epa", True),
        ("metal_waste", "Aluminium Beverage Can", "eu_standard", False),
        ("hazardous_waste", "Alkaline / Lithium Battery", "india_cpcb", False),
        ("organic_waste", "Banana Peel", "uk_wrap", False)
    ]
    for cat, item, loc, cont in samples:
        res = engine.get_recommendation(category=cat, query_item=item, location=loc, is_contaminated=cont)
        print(f"\n[{res['category_display']} - {res['matched_item']}] (Location: {loc}, Contaminated: {cont})")
        print(f"  Recyclability : {res['recyclability_status']}")
        print(f"  Bin           : {res['recommended_bin']}")
        print(f"  CO2 Saved     : {res['environmental_impact']['estimated_co2_saved_kg']} kg CO2e")
        print(f"  Energy Saved  : {res['environmental_impact']['estimated_energy_saved_kwh']} kWh")
        print(f"  Prep          : {res['preparation_instructions']}")

