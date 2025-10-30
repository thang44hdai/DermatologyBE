"""
Script to add disease data with images
"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.database import Disease


# Disease data with image mapping
DISEASES_DATA = [
    {
        "disease_name": "Mụn trứng cá",
        "description": "Bệnh lý da phổ biến do tắc nghẽn lỗ chân lông, viêm nang lông và tuyến bã nhờn, thường xuất hiện ở tuổi dậy thì.",
        "symptoms": "Mụn đầu trắng, mụn đầu đen, mụn mủ, mụn bọc, sẩn viêm, có thể để lại sẹo.",
        "treatment": "Rửa mặt nhẹ nhàng 2 lần/ngày, dùng benzoyl peroxide, retinoid bôi ngoài, kháng sinh (clindamycin, doxycycline), isotretinoin nặng, tránh nặn mụn.",
        "image": "uploads/diseases/acne.jpg"
    },
    {
        "disease_name": "Mụn trứng cá thông thường",
        "description": "Dạng mụn trứng cá phổ biến nhất (acne vulgaris), liên quan đến hormone, vi khuẩn P.acnes và sản xuất bã nhờn quá mức.",
        "symptoms": "Mụn comedone (đầu trắng/đen), sẩn viêm, mụn mủ, nang, chủ yếu ở mặt, ngực, lưng.",
        "treatment": "Thuốc bôi (adapalene, tretinoin, benzoyl peroxide), kháng sinh uống/bôi, tránh dầu nhờn, hormone therapy nếu cần.",
        "image": "uploads/diseases/acne-vulgaris.jpg"
    },
    {
        "disease_name": "Sừng hóa quang hóa",
        "description": "Tổn thương tiền ung thư do tiếp xúc lâu dài với tia UV, thường gặp ở người lớn tuổi da trắng.",
        "symptoms": "Mảng đỏ sần sùi, có vảy, đường kính <1cm, trên vùng da tiếp xúc nắng (mặt, tay, da đầu).",
        "treatment": "Kem 5-FU, imiquimod, cryotherapy, curettage, phẫu thuật cắt bỏ nếu nghi ngờ chuyển dạng.",
        "image": "uploads/diseases/actinic-keratosis.jpg"
    },
    {
        "disease_name": "Ung thư biểu mô tế bào đáy",
        "description": "Loại ung thư da phổ biến nhất, phát sinh từ tế bào đáy biểu bì, ít di căn nhưng xâm lấn tại chỗ.",
        "symptoms": "Nốt ngọc trai, nổi gờ, loét trung tâm, mạch máu nổi, chảy máu dễ dàng.",
        "treatment": "Phẫu thuật Mohs, cắt bỏ thông thường, xạ trị, vismodegib (nặng), theo dõi định kỳ.",
        "image": "uploads/diseases/basal-cell-carcinoma.jpg"
    },
    {
        "disease_name": "Ung thư biểu mô tế bào đáy dạng morpheiform",
        "description": "Thể ít gặp của BCC, xâm lấn sâu, ranh giới không rõ, giống sẹo.",
        "symptoms": "Mảng cứng, phẳng, màu da hoặc trắng, không loét rõ, lan rộng ngầm.",
        "treatment": "Phẫu thuật Mohs ưu tiên, xạ trị, kiểm tra biên an toàn rộng.",
        "image": "uploads/diseases/basal-cell-carcinoma-morpheiform.jpg"
    },
    {
        "disease_name": "U xơ da",
        "description": "Khối u lành tính từ nguyên bào sợi, thường ở chi dưới, màu nâu đỏ.",
        "symptoms": "Nốt chắc, đường kính 0.5-1cm, lõm khi ấn (dấu hiệu dimple), không đau.",
        "treatment": "Theo dõi hoặc cắt bỏ nếu gây khó chịu thẩm mỹ.",
        "image": "uploads/diseases/dermatofibroma.jpg"
    },
    {
        "disease_name": "Viêm da cơ",
        "description": "Bệnh tự miễn ảnh hưởng da và cơ, liên quan viêm cơ vân, có thể kèm ung thư.",
        "symptoms": "Phát ban heliotrope (mí mắt tím), papules Gottron (mu bàn tay), yếu cơ gần, khó nuốt.",
        "treatment": "Corticoid liều cao, methotrexate, IVIG, kiểm tra ung thư tiềm ẩn.",
        "image": "uploads/diseases/dermatomyositis.jpg"
    },
    {
        "disease_name": "Chàm tổ đỉa",
        "description": "Thể chàm mạn tính ở lòng bàn tay/chân, mụn nước ngứa sâu dưới da.",
        "symptoms": "Mụn nước nhỏ sâu, ngứa dữ dội, bong vảy, nứt nẻ khi khô.",
        "treatment": "Tránh kích ứng, kem steroid mạnh, PUVA, alitretinoin (nặng).",
        "image": "uploads/diseases/dyshidrotic-eczema.jpg"
    },
    {
        "disease_name": "Chàm",
        "description": "Nhóm bệnh viêm da mạn tính có yếu tố di truyền, rối loạn hàng rào da.",
        "symptoms": "Ngứa, đỏ, mụn nước, liken hóa, khô da, hay ở khuỷu, khoeo chân.",
        "treatment": "Dưỡng ẩm, corticosteroid bôi, tacrolimus, tránh dị ứng nguyên, dupilumab (nặng).",
        "image": "uploads/diseases/eczema.webp"
    },
    {
        "disease_name": "Nốt ruồi biểu bì",
        "description": "Tổn thương lành tính bẩm sinh hoặc mắc phải từ tế bào biểu bì, dạng tuyến tính.",
        "symptoms": "Dải hoặc mảng nâu/verrucous, theo đường Blaschko, có thể ở thân, chi.",
        "treatment": "Theo dõi, cắt bỏ nếu gây thẩm mỹ hoặc nghi ngờ ác tính hóa.",
        "image": "uploads/diseases/epidermal-nevus.webp"
    },
    {
        "disease_name": "Viêm nang lông",
        "description": "Viêm nhiễm nang lông do vi khuẩn (S.aureus), nấm hoặc kích ứng.",
        "symptoms": "Sẩn mủ quanh lông, ngứa, đỏ, có thể để lại sẹo nhỏ.",
        "treatment": "Kháng sinh bôi (mupirocin), vệ sinh, tránh cạo râu ướt.",
        "image": "uploads/diseases/folliculitis.jpg"
    },
    {
        "disease_name": "Sarcoma Kaposi",
        "description": "Ung thư mạch máu liên quan HHV-8, thường gặp ở người suy giảm miễn dịch (HIV).",
        "symptoms": "Mảng/mảng nâu đỏ/tím, phù, loét, hay ở chi dưới, niêm mạc.",
        "treatment": "HAART (HIV), hóa trị (liposomal doxorubicin), xạ trị cục bộ.",
        "image": "uploads/diseases/kaposi-sarcoma.jpg"
    },
    {
        "disease_name": "Sẹo lồi",
        "description": "Sẹo tăng sinh quá mức vượt ra ngoài vết thương ban đầu, do collagen dư thừa.",
        "symptoms": "Khối cứng, đỏ, ngứa, lan rộng theo thời gian, hay ở vai, ngực.",
        "treatment": "Tiêm corticosteroid nội tổn thương, silicone gel, laser, phẫu thuật + xạ trị.",
        "image": "uploads/diseases/keloid.jpg"
    },
    {
        "disease_name": "U hắc tố ác tính",
        "description": "Ung thư hắc tố da nguy hiểm, phát sinh từ tế bào melanocyte, di căn sớm.",
        "symptoms": "Nốt không đều (ABCDE), đổi màu, chảy máu, ngứa, >6mm.",
        "treatment": "Cắt rộng + sinh thiết hạch cửa, immunotherapy (pembrolizumab), targeted therapy (BRAF).",
        "image": "uploads/diseases/malignant-melanoma.jpg"
    },
    {
        "disease_name": "U hắc tố",
        "description": "Tên chung cho khối u từ tế bào melanocyte, bao gồm lành tính và ác tính (melanoma).",
        "symptoms": "Nốt nâu/đen, có thể phẳng hoặc nổi, thay đổi kích thước/màu.",
        "treatment": "Theo dõi hoặc cắt bỏ nếu nghi ngờ ác tính.",
        "image": "uploads/diseases/melanoma.jpg"
    },
    {
        "disease_name": "Nấm da dạng nấm",
        "description": "Lymphoma tế bào T da nguyên phát, giai đoạn sớm giống bệnh da thông thường.",
        "symptoms": "Mảng đỏ, vảy, ngứa, sau thành cục/u, giai đoạn muộn có hạch.",
        "treatment": "PUVA, retinoid, interferon, hóa trị, ghép tế bào gốc.",
        "image": "uploads/diseases/mycosis-fungoides.jpg"
    },
    {
        "disease_name": "Ngứa cục",
        "description": "Bệnh mạn tính do gãi kéo dài, tạo vòng luẩn quẩn ngứa-gãi.",
        "symptoms": "Cục cứng ngứa dữ dội, liken hóa, hay ở chi, lưng.",
        "treatment": "Ngừng gãi, corticosteroid bôi/tiêm, capsaicin, thalidomide, UVB.",
        "image": "uploads/diseases/prurigo-nodularis.png"
    },
    {
        "disease_name": "U hạt sinh mủ",
        "description": "Khối u mạch máu lành tính, dễ chảy máu, thường sau chấn thương.",
        "symptoms": "Nốt đỏ tươi, cuống, chảy máu khi va chạm, phát triển nhanh.",
        "treatment": "Cắt bỏ, đốt laser, silver nitrate, không tự hết.",
        "image": "uploads/diseases/pyogenic-granuloma.webp"
    },
    {
        "disease_name": "Sừng hóa tiết bã",
        "description": "Khối u lành tính ở người lớn tuổi, do tăng sinh tế bào sừng, dính chặt.",
        "symptoms": "Mảng nâu/đen sần sùi, dính như dán, hay ở lưng, mặt.",
        "treatment": "Cryotherapy, curettage, không cần nếu không phiền.",
        "image": "uploads/diseases/seborrheic-keratosis.jpg"
    },
    {
        "disease_name": "Ung thư biểu mô tế bào vảy",
        "description": "Ung thư da từ tế bào vảy, có thể di căn nếu không điều trị sớm.",
        "symptoms": "Mảng đỏ có vảy, loét, sừng hóa, trên vùng tiếp xúc nắng.",
        "treatment": "Phẫu thuật cắt bỏ, Mohs, xạ trị, 5-FU bôi (Bowen).",
        "image": "uploads/diseases/squamous-cell-carcinoma.webp"
    },
    {
        "disease_name": "U hắc tố lan rộng bề mặt",
        "description": "Thể melanoma phổ biến nhất, lan ngang trước khi xâm nhập sâu.",
        "symptoms": "Mảng nâu không đều, viền bất thường, màu đa dạng, trên thân.",
        "treatment": "Cắt rộng theo độ dày Breslow, sinh thiết hạch, immunotherapy.",
        "image": "uploads/diseases/superficial-spreading-melanoma-ssm.webp"
    },
    {
        "disease_name": "Zona thần kinh",
        "description": "Nhiễm Herpes Zoster (varicella-zoster virus tái hoạt), đau theo dây thần kinh.",
        "symptoms": "Đau rát, mụn nước theo dải một bên, hay ở ngực/lưng/mặt.",
        "treatment": "Acyclovir/valacyclovir sớm (trong 72h), giảm đau, vaccine phòng ngừa.",
        "image": "uploads/diseases/zona.webp"
    },
    {
        "disease_name": "Thủy đậu",
        "description": "Nhiễm virus varicella-zoster lần đầu, lây qua đường hô hấp, hay ở trẻ em.",
        "symptoms": "Sốt, mệt, mụn nước toàn thân trên nền đỏ, ngứa, đóng vảy.",
        "treatment": "Hạ sốt, calamine, acyclovir nếu nặng, vaccine phòng ngừa.",
        "image": "uploads/diseases/chickenpox.jpg"
    }
]


def add_diseases(db: Session):
    """
    Add disease data to database
    
    Args:
        db: Database session
    """
    added_count = 0
    skipped_count = 0
    error_count = 0
    
    print("=" * 70)
    print("🏥 Adding Disease Data to Database")
    print("=" * 70)
    print()
    
    for idx, disease_data in enumerate(DISEASES_DATA, 1):
        try:
            # Check if disease already exists
            existing = db.query(Disease).filter(
                Disease.disease_name == disease_data["disease_name"]
            ).first()
            
            if existing:
                print(f"⏭️  [{idx}/{len(DISEASES_DATA)}] Skipped: '{disease_data['disease_name']}' (already exists)")
                skipped_count += 1
                continue
            
            # Check if image file exists
            image_path = disease_data["image"]
            if not os.path.exists(image_path):
                print(f"⚠️  [{idx}/{len(DISEASES_DATA)}] Warning: Image not found for '{disease_data['disease_name']}'")
                print(f"    Expected: {image_path}")
                image_path = None
            
            # Create disease
            disease = Disease(
                disease_name=disease_data["disease_name"],
                description=disease_data["description"],
                symptoms=disease_data["symptoms"],
                treatment=disease_data["treatment"],
                image_url=image_path
            )
            
            db.add(disease)
            db.commit()
            db.refresh(disease)
            
            print(f"✅ [{idx}/{len(DISEASES_DATA)}] Added: '{disease_data['disease_name']}' (ID: {disease.id})")
            added_count += 1
            
        except Exception as e:
            db.rollback()
            print(f"❌ [{idx}/{len(DISEASES_DATA)}] Error adding '{disease_data['disease_name']}': {str(e)}")
            error_count += 1
    
    print()
    print("=" * 70)
    print("📊 Summary")
    print("=" * 70)
    print(f"✅ Successfully added: {added_count}")
    print(f"⏭️  Skipped (already exists): {skipped_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📝 Total processed: {len(DISEASES_DATA)}")
    print("=" * 70)


if __name__ == "__main__":
    print("\n")
    db: Session = SessionLocal()
    
    try:
        add_diseases(db)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        db.rollback()
    finally:
        db.close()
    
    print("\n✨ Done!\n")
