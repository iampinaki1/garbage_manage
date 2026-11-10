"""
Command-Line Waste Inspection & Recommendation Tool.

Usage:
  python scripts/predict.py --image datasets/trashnet/cardboard/cardboard1.jpg
  python scripts/predict.py --image path/to/waste.jpg --location eu_standard --contaminated
"""

import sys
import argparse
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.pipeline_service import pipeline_service
from backend.recommendations.recommendation_engine import LOCATION_PROFILES

def sync_run(coro):
    """Executes coroutine chain synchronously without socket-bound event loops."""
    sub_stack = [coro]
    while sub_stack:
        current = sub_stack[-1]
        try:
            res = current.send(None)
            if hasattr(res, "send"):
                sub_stack.append(res)
        except StopIteration as e:
            sub_stack.pop()
            if sub_stack:
                try:
                    sub_stack[-1].send(e.value)
                except StopIteration:
                    pass
            else:
                return e.value

def main():
    parser = argparse.ArgumentParser(
        description="Run end-to-end AI waste analysis on an image via CLI"
    )
    parser.add_argument(
        "--image",
        type=str,
        required=True,
        help="Path to the waste image file (JPEG, PNG, WebP)"
    )
    parser.add_argument(
        "--location",
        type=str,
        default="us_epa",
        choices=list(LOCATION_PROFILES.keys()),
        help="Disposal jurisdiction: 'us_epa', 'eu_standard', 'uk_wrap', 'india_cpcb'"
    )
    parser.add_argument(
        "--contaminated",
        action="store_true",
        help="Flag if the item is soiled with grease, food, or chemical residues"
    )
    
    args = parser.parse_args()
    img_path = Path(args.image)
    
    if not img_path.exists():
        print(f"\n[ERROR] Image not found at: {img_path}")
        sys.exit(1)
        
    print("\n=======================================================")
    print(" EcoSort AI - Autonomous Vision Waste Inspection       ")
    print("=======================================================")
    print(f"Target Image   : {img_path.resolve()}")
    print(f"Jurisdiction   : {LOCATION_PROFILES[args.location]['name']}")
    print(f"Contamination  : {'YES (Soiled/Greasy)' if args.contaminated else 'NO (Clean)'}")
    print("Executing YOLO detection & MobileNetV3 classification...\n")
    
    with open(img_path, "rb") as f:
        img_bytes = f.read()
        
    try:
        res = sync_run(pipeline_service.analyze_image(
            image_bytes=img_bytes,
            filename=img_path.name,
            location=args.location,
            is_contaminated=args.contaminated
        ))
    except Exception as e:
        print(f"[ERROR] Inference pipeline failed: {e}")
        sys.exit(1)
        
    summary = res.summary
    print("----------------- INFERENCE SUMMARY ------------------")
    print(f"Analysis ID       : {res.analysis_id}")
    print(f"Inference Latency : {summary.inference_latency_ms:.1f} ms")
    print(f"Objects Detected  : {summary.total_objects_detected}")
    print(f"Primary Category  : {summary.primary_category_display}")
    print(f"Overall Status    : {summary.overall_recyclability}")
    print(f"Est. CO2 Avoided  : {summary.total_co2_saved_kg:.4f} kg CO2e")
    print(f"Est. Energy Saved : {summary.total_energy_saved_kwh:.4f} kWh")
    print(f"Annotated Visual  : {ROOT / 'backend' / res.annotated_image_url.lstrip('/')}")
    print("------------------------------------------------------\n")
    
    for det in res.detections:
        print(f"Object #{det.object_id}: {det.category_display} ({det.matched_item})")
        print(f"  Confidence   : {det.confidence * 100:.1f}%")
        print(f"  Material     : {det.material}")
        print(f"  Status       : {det.recyclability_status}")
        print(f"  Target Bin   : {det.recommended_bin}")
        print(f"  Method       : {det.recycling_method}")
        print(f"  Preparation  : {det.preparation_instructions}")
        print(f"  Disposal     : {det.disposal_instructions}")
        if det.contamination_assessment.is_contaminated:
            print(f"  Contam Risk  : {det.contamination_assessment.risk_level.upper()} - {det.contamination_assessment.action_taken}")
        print(f"  Impact       : {det.environmental_impact.estimated_co2_saved_kg} kg CO2e | {det.environmental_impact.estimated_energy_saved_kwh} kWh")
        bx = det.box_pixels
        print(f"  Bounding Box : [x1={bx.x1}, y1={bx.y1}, x2={bx.x2}, y2={bx.y2}] ({bx.width}x{bx.height}px)")
        print()

    print("=======================================================")
    print(" Inspection complete. Ready for disposal.             ")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
