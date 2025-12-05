# Đặc tả & Phân tích: Mô hình phát hiện xâm phạm bằng sáng chế cho hợp chất hóa học

- Tài liệu này tổng hợp yêu cầu từ `_1_patent_detect/prb.1.chemi_patent.pdf`, 
  - phân tích bài toán, 
  - đề xuất kiến trúc 
  - kế hoạch triển khai

## 1) Mục tiêu & Phạm vi
- Xây dựng mô hình/phần mềm 
  - kiểm tra khả năng 
    - xâm phạm bằng sáng chế (patent infringement) 
    - cho hợp chất hóa học

- Đầu vào: 
  - Ver1: SMILES (tùy chọn InChI). 
  - Ver2: hình ảnh cấu trúc/Markush từ patent.

- Đầu ra:
  - Nhãn: `Patented`/`Not patented` 
    - ở mức độ “khả năng xâm phạm” cho hỗ trợ R&D, 
    - không thay thế tư vấn pháp lý

  - Nếu `Patented`, 
    - chỉ ra phần cấu trúc vi phạm/được bao phủ (highlight) 
    - giải thích ngắn gọn 
      - claim/Markush nào bao phủ
      - phần lõi/nhánh nào match

- Tích hợp dự kiến: như một chức năng bổ sung cho Pharmaco‑Net.

- Không nằm trong phạm vi mốc đầu (có thể PoC): 
  - phán định pháp lý đầy đủ, 
  - trích xuất ảnh Markush độ chính xác cao, 
  - phân tích quyền theo quốc gia/thời hạn/ước lệ pháp lý chi tiết.


## 2) Yêu cầu kỹ thuật
- Ngôn ngữ: Python 3.9+
- Thư viện: 
  - RDKit; 
  - PyTorch/TensorFlow (nếu dùng embedding học sâu); 
  - FAISS/Annoy (chỉ mục ANN)

- Hỗ trợ 
  - chuẩn hoá SMILES/InChI; 
  - xử lý tautomer/stereo/salt/solvate.

## 3) Bài toán cốt lõi
1) Khớp trùng (exact/duplicate): 
  - đồng nhất với cấu trúc đã được bảo hộ.

2) Khớp bao phủ Markush: 
  - cấu trúc con của claim Markush hoặc là trường hợp cụ thể của mẫu chung 
  - R‑group, phạm vi thay thế, lớp chức chức năng, v.v.

3) Khớp gần (near‑duplicate/analog): 
  - đồng phân
  - tautomer
  - biến thể nhẹ của scaffold cốt lõi.

- Thách thức chính: 
  - biểu diễn và so khớp Markush, 
  - liên kết ảnh↔cấu trúc (OSR), 
  - chuẩn hoá hoá học nhất quán, 
  - cân bằng Recall/Precision.

## 4) Kiến trúc đề xuất (2 tầng)
- Tổng quan: 
  - Stage 1: Retrieval nhanh (Stage 1) 
  - Stage 2: Verification chính xác (Stage 2)
  - Stage 3: Giải thích (Explain/Highlight)

### 4.1 Dữ liệu/Knowledge Base
- Nguồn: 
  - USPTO/Google Patents/nguồn sở hữu.
  - Ưu tiên nguồn đã có cấu trúc số hoá (SMILES/SDF) để giảm phụ thuộc OSR.

- Chuẩn hoá trước khi lập chỉ mục:
  - Loại muối/solvent (RDKit SaltRemover);
  - Chuẩn tautomer (RDKit rdMolStandardize);
  - Chuẩn stereo (policy: giữ/chuẩn hoá có kiểm soát tuỳ use‑case);
  - Chuẩn canonical SMILES + InChIKey.

- Biểu diễn:
  - Fingerprint: 
    - ECFP4/ECFP6 (radius 2/3), 
    - 2048 bits;

  - Tuỳ chọn embedding GNN (D‑MPNN/Graphormer) 
    - để tăng Recall cho analog gần;

  - Với Markush: 
    - lưu QueryMol/SMARTS 
    - mô tả R‑group, atom lists, recursive SMARTS.

### 4.2 Query candidate (Stage 1)
- Chỉ mục ANN (FAISS) trên fingerprint/embedding 
  - để lấy top‑K patent/claim ứng viên nhanh 
  - (K≈50–200 tuỳ quy mô).

- Lọc sơ bộ 
  - theo InChIKey (exact) 
  - ngưỡng tương đồng (Tanimoto ≥ t1) 
  - để tăng Recall.

### 4.3 Exact verify (Stage 2)
- Exact/duplicate: 
  - so InChIKey/full graph‑isomorphism.

- Substructure: 
  - `RDKit.Chem.HasSubstructMatch` với `SubstructMatch` để lấy mapping.

- Markush: 
  - Biểu diễn claim bằng QueryMol/SMARTS 
    - atom lists, 
    - valence, 
    - vị trí thế, 
    - recursive SMARTS

  - Ánh xạ query→claim 
    - bằng substructure matching trên QueryMol;

  - Nếu claim nêu phạm vi (vd. “C1–C6 alkyl”), 
    - ánh xạ qua danh sách thay thế đã chuẩn hoá 
    - hoặc enumerate có kiểm soát (giới hạn để tránh nổ tổ hợp).

- Chấm điểm xác minh: 
  - kết hợp bằng rules/learning‑to‑rank 
    - điểm match lõi, 
    - số vị trí R được thoả, 
    - ràng buộc stereo/tautomer

### 4.4 Giải thích/Highlight
- Trả về:
  - Danh sách patent/claim ứng viên 
    - id, 
    - tiêu đề, 
    - link nếu có, 
    - điểm tin cậy

  - Atom/bond mapping 
    - cho phần trùng/bao phủ để highlight;

  - Lý do khớp: 
    - ví dụ: 
      - core scaffold trùng; 
      - R1∈C1–C3‑alkyl khớp với ‑CH3

### 4.5 Ảnh → Cấu trúc (OSR) [tùy mốc]
- Công cụ: 
  - DECIMER, 
  - MolScribe, 
  - OSRA. 

- Đề xuất:
  - triển khai sau khi pipeline SMILES ổn định (M4+)

## 5) Chuẩn hoá hoá học (đề xuất policy)
- Loại muối/solvent; 
  - neutralize charges nếu phù hợp.

- Tautomer canonicalization: 
  - dùng `rdMolStandardize.TautomerEnumerator` (policy cố định).

- Stereo: hai chế độ cấu hình
  - Strict: giữ stereo khi match exact/substructure; 
  - Relaxed: bỏ stereo cho truy hồi/đánh giá tương đồng ở Stage 1.

- Normalization: 
  - `rdMolStandardize.Cleanup` + canonical SMILES.

## 6) Lưu trữ & Chỉ mục
- Bảng cấu trúc: 
  - molecule_id, 
  - patent_id, 
  - claim_id, 
  - smiles_canonical, 
  - inchikey, 
  - fp_ecfp4, 
  - meta…

- Bảng markush: 
  - claim_id, 
  - smarts/querymol, 
  - constraints, 
  - examples…

- Chỉ mục ANN: 
  - FAISS IVF/PQ hoặc HNSW (tuỳ quy mô và RAM). 
  - Nén PQ để tiết kiệm bộ nhớ.

## 7) Pipeline E2E (sơ đồ luồng)
1) Ingest → 
2) Normalize (salt/tautomer/stereo) → 
3) Fingerprint/Embedding → 
4) Build Index → 
5) Query (SMILES) → 
6) Retrieval Top‑K → 
7) Verification (exact/substructure/Markush) → 
8) Explain/Highlight → 
9) Output API.

## 8) API dự kiến
```http
POST /v1/patent/check
{
  "smiles": "CCOc1ccc2nc(S(N)(=O)=O)sc2c1"
}

200 OK
{
  "label": "Patented",               // hoặc "Not patented"
  "candidates": [
    {
      "patent_id": "US1234567A",
      "claim_id": "Claim 12",
      "score": 0.92,
      "reason": "Substructure match on core scaffold; R1=C1‑alkyl",
      "mapping": {"atoms": [0,1,2,...], "bonds": [0,3,5,...]}
    },
    ...
  ],
  "normalization": {"policy": "tautomer_canonical, stereo_relaxed_stage1"}
}
```

Pseudo‑code core:
```python
def standardize(smiles):
    mol = Chem.MolFromSmiles(smiles)
    mol = rdMolStandardize.Cleanup(mol)
    mol = rdMolStandardize.Uncharger().uncharge(mol)
    mol = rdMolStandardize.TautomerEnumerator().Canonicalize(mol)
    return Chem.MolToSmiles(mol, canonical=True)

def is_patented(smiles):
    q = standardize(smiles)
    fp = morgan_fp(q)
    topk = faiss_search(fp, K)
    hits = []
    for cand in topk:
        if exact_or_substruct_match(q, cand):
            hits.append(score_and_explain(q, cand))
        elif cand.has_markush:
            if markush_match(q, cand.querymol, cand.constraints):
                hits.append(score_and_explain_markush(q, cand))
    return aggregate_label(hits), hits
```

## 9) Đánh giá & Chỉ số
- Truy hồi (Stage 1): 
  - Recall@K (K=50/100) ≥ 0.95 cho exact/near‑duplicate; 
  - AUC‑PR.

- Xác minh (Stage 2): 
  - Precision ≥ 0.90 cho substructure/Markush; 
  - FNR tối thiểu.

- Latency: 
  - < 200–300 ms/truy vấn (chỉ Stage 1+2, không tính I/O) 
  - với chỉ mục ~1–10M cấu trúc.

- Báo cáo lỗi: 
  - phân rã theo loại 
    - (exact, substructure, Markush)
  - tension Precision–Recall, 
  - phân tích các case false-positive, false-negative

- Ground truth (đề xuất):
  - Tập pilot 50k–200k cấu trúc có ánh xạ đến patent/claim; 
  - thêm tập Markush thủ công (~200–500 claim) để kiểm định.

## 10) Mốc & Deliverables (gợi ý chi tiết hoá)
- M1: Dữ liệu & Chuẩn hoá
  - Pipeline 
    + ingest 
    + standardize 
    + fingerprint 
    + FAISS index (pilot dataset)

  - Demo API `is_patented(smiles)` trả top‑K ứng viên.

- M2: Kiến trúc & Tích hợp cơ bản
  - 2‑stage 
    - retrieval+verification; 
    - exact/substructure ready; 
    - config policy chuẩn hoá;

  - Báo cáo Recall@K trên pilot.

- M3: Huấn luyện/Validation
  - Thêm GNN embedding (tuỳ); 
  - tối ưu tham số ANN; 
  - tuning ngưỡng; 
  - đánh giá đầy đủ.

- M4: Tối ưu & Markush v1
  - Parser Markush rule‑based + QueryMol; 
    - enumerate kiểm soát; 
    - tối ưu latency và bộ nhớ.

  - PoC OSR (DECIMER/MolScribe) nếu kịp.

- M5: Bàn giao
  - Mã nguồn + model + README tái lập; 
  - báo cáo đánh giá; 
  - 100 mẫu demo theo yêu cầu.

## 11) Rủi ro & Giảm thiểu
- Markush phức tạp 
  - → Ưu tiên QueryMol/SMARTS + enumerate hạn chế; 
  - mở rộng dần ràng buộc.

- OSR sai số 
  - → Trì hoãn, ưu tiên dữ liệu có SMILES/số hoá; 
  - thêm kiểm định thủ công.

- Thiếu dữ liệu patent chuẩn 
  - → Kết hợp nhiều nguồn; 
  - log case mơ hồ; 
  - vòng phản hồi dán nhãn bổ sung.

- Chuẩn hoá ảnh hưởng kết quả 
  - → Cố định policy; 
  - hỗ trợ chế độ strict/relaxed; 
  - log trace transform.

## 12) Mở & Cần xác nhận
- Phạm vi pháp lý: trả “khả năng xâm phạm” hỗ trợ nghiên cứu hay yêu cầu kết luận pháp lý chặt?
- Ưu tiên giai đoạn 1: chỉ SMILES→patent hay cần OSR ngay?
- Mục tiêu định lượng cuối cùng (Precision/Recall/Latency)?
- Quy mô dữ liệu mục tiêu (số cấu trúc/claim/Markush)? Hạ tầng triển khai?
- Tích hợp Pharmaco‑Net: giao thức API, auth, SLO?

## 13) Tham khảo
- CAS SciFinder (Markush): https://cas-product-help.zendesk.com/hc/en-us/articles/9838526793613-Find-Patent-Markush-Structures
- PatentFinder (arXiv): https://arxiv.org/html/2412.07819v1
- RDKit docs (standardize, substructure, query/SMARTS)
- FAISS docs (ANN indexing)

---

Gợi ý bước tiếp theo:
- Chốt policy chuẩn hoá (tautomer/stereo) và chỉ số mục tiêu.
- Mình có thể scaffold nhanh repo con: `ingest → normalize → index → match → explain` + API demo trên dữ liệu toy để review.
