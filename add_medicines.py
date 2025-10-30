"""
Script to populate medicines table with data from medicine.json
Including many-to-many relationship with diseases
"""
import json
import os
import sys
from pathlib import Path
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.db.session import SessionLocal, engine
from app.models.database import Base, Medicines, Disease, MedicineDiseaseLink

# Image directory
MEDICINE_IMAGES_DIR = "uploads/medicines"
BASE_URL = "http://localhost:8000"


def find_medicine_image(medicine_name: str) -> str:
    """
    Find image file for medicine by name
    Searches for files starting with the medicine name
    Returns relative path like: uploads/medicines/filename.jpg
    """
    if not os.path.exists(MEDICINE_IMAGES_DIR):
        return None
    
    # Normalize medicine name for comparison
    medicine_name_lower = medicine_name.lower().replace(" ", "").replace("-", "")
    
    for filename in os.listdir(MEDICINE_IMAGES_DIR):
        # Normalize filename for comparison
        file_lower = filename.lower().replace(" ", "").replace("-", "")
        
        # Check if filename starts with medicine name (without extension)
        file_base = os.path.splitext(file_lower)[0]
        if file_base.startswith(medicine_name_lower[:10]):  # Match first 10 chars
            return f"{MEDICINE_IMAGES_DIR}/{filename}"
    
    return None


def parse_disease_ids(disease_id_str) -> list:
    """
    Parse disease_id field which can be:
    - Single integer: 1
    - Comma-separated string: "10,15"
    Returns list of integers
    """
    if disease_id_str is None:
        return []
    
    # Convert to string if it's a number
    if isinstance(disease_id_str, (int, float)):
        return [int(disease_id_str)]
    
    # Parse comma-separated string
    try:
        disease_ids = [int(id.strip()) for id in str(disease_id_str).split(',')]
        return disease_ids
    except ValueError:
        print(f"Warning: Invalid disease_id format: {disease_id_str}")
        return []


def add_medicines(db: Session):
    """Add medicines from JSON file to database"""
    
    # Load JSON data
    json_file = "medicine.json"
    if not os.path.exists(json_file):
        print(f"Error: {json_file} not found!")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        medicines_data = json.load(f)
    
    print(f"Found {len(medicines_data)} medicines in JSON file\n")
    
    # Get all diseases for validation
    all_diseases = {d.id: d.disease_name for d in db.query(Disease).all()}
    print(f"Found {len(all_diseases)} diseases in database\n")
    
    added_count = 0
    skipped_count = 0
    error_count = 0
    
    for idx, medicine_data in enumerate(medicines_data, 1):
        try:
            medicine_name = medicine_data.get('name')
            
            # Check if medicine already exists
            existing = db.query(Medicines).filter(Medicines.name == medicine_name).first()
            if existing:
                print(f"[{idx}/{len(medicines_data)}] ⏭️  SKIPPED: '{medicine_name}' already exists")
                skipped_count += 1
                continue
            
            # Parse disease_ids
            disease_ids = parse_disease_ids(medicine_data.get('disease_id'))
            
            if not disease_ids:
                print(f"[{idx}/{len(medicines_data)}] ❌ ERROR: '{medicine_name}' - No valid disease_id")
                error_count += 1
                continue
            
            # Validate all disease_ids exist
            invalid_diseases = [did for did in disease_ids if did not in all_diseases]
            if invalid_diseases:
                print(f"[{idx}/{len(medicines_data)}] ❌ ERROR: '{medicine_name}' - Invalid disease_ids: {invalid_diseases}")
                error_count += 1
                continue
            
            # Find corresponding image
            image_url = find_medicine_image(medicine_name)
            
            # Prepare image URLs as JSON array (for multi-image support)
            image_urls_json = None
            if image_url:
                image_urls_json = json.dumps([image_url])
            
            # Create medicine
            new_medicine = Medicines(
                name=medicine_name,
                description=medicine_data.get('description', ''),
                generic_name=medicine_data.get('generic_name'),
                type=medicine_data.get('type'),
                dosage=medicine_data.get('dosage'),
                side_effects=medicine_data.get('side_effects'),
                suitable_for=medicine_data.get('suitable_for'),
                price=medicine_data.get('price'),
                image_url=image_urls_json
            )
            
            db.add(new_medicine)
            db.flush()  # Get the medicine ID
            
            # Create medicine-disease links
            for disease_id in disease_ids:
                link = MedicineDiseaseLink(
                    medicine_id=new_medicine.id,
                    disease_id=disease_id
                )
                db.add(link)
            
            db.commit()
            
            # Prepare display info
            disease_names = [all_diseases[did] for did in disease_ids]
            diseases_str = ", ".join(disease_names[:2]) + (f" (+{len(disease_names)-2})" if len(disease_names) > 2 else "")
            image_status = "🖼️" if image_url else "⚪"
            
            print(f"[{idx}/{len(medicines_data)}] ✅ ADDED: '{medicine_name}' {image_status}")
            print(f"    └─ Diseases: {diseases_str}")
            if image_url:
                print(f"    └─ Image: {os.path.basename(image_url)}")
            
            added_count += 1
            
        except Exception as e:
            db.rollback()
            print(f"[{idx}/{len(medicines_data)}] ❌ ERROR: '{medicine_name}' - {str(e)}")
            error_count += 1
            continue
    
    print("\n" + "="*70)
    print("SUMMARY:")
    print(f"  ✅ Added: {added_count}")
    print(f"  ⏭️  Skipped (already exists): {skipped_count}")
    print(f"  ❌ Errors: {error_count}")
    print(f"  📊 Total processed: {len(medicines_data)}")
    print("="*70)


def main():
    """Main function"""
    print("="*70)
    print("MEDICINE DATABASE POPULATOR")
    print("="*70)
    print()
    
    # Check if images directory exists
    if not os.path.exists(MEDICINE_IMAGES_DIR):
        print(f"Warning: Image directory '{MEDICINE_IMAGES_DIR}' not found!")
        print("Medicines will be added without images.\n")
    else:
        image_files = [f for f in os.listdir(MEDICINE_IMAGES_DIR) if os.path.isfile(os.path.join(MEDICINE_IMAGES_DIR, f))]
        print(f"Found {len(image_files)} image files in {MEDICINE_IMAGES_DIR}/")
        print()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Add medicines
        add_medicines(db)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        db.rollback()
        
    finally:
        db.close()
    
    print("\n✅ Script completed!")


if __name__ == "__main__":
    main()
