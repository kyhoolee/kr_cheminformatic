- Tuyệt vời! Với nền tảng vững chắc về Học máy (ML) và tìm kiếm lân cận (Nearest Search), tôi sẽ bóc tách các khái niệm cốt lõi trong lĩnh vực 
    - **Hóa học Hợp chất (Chemoinformatics)** 
    - **So khớp Bằng sáng chế (Patent Matching)** 

## 🧪 Khái niệm Cơ bản trong Hóa học Hợp chất

Trong lĩnh vực này, 
    - đối tượng không phải là các vector số hay hình ảnh, 
    - mà là các **phân tử**.

### 1. Biểu diễn Hợp chất Hóa học (Chemical Representation)

- Đây là cách chúng ta chuyển một cấu trúc vật lý thành dữ liệu máy tính có thể xử lý.

| Khái niệm | Giải thích | Vai trò trong Dự án |
| :--- | :--- | :--- |

| **SMILES** 
    - | **S**implified **M**olecular-**I**nput **L**ine-**E**ntry **S**ystem. 
        - Một chuỗi ký tự ASCII đơn giản, ngắn gọn mô tả cấu trúc phân tử 
            - (vd: `CCO` là Ethanol). 

    - Cần chuẩn hóa thành **Canonical SMILES** 
        - để đảm bảo cùng một phân tử luôn có cùng một chuỗi ký tự. |

| **InChI/InChIKey** 
    - | **I**UPAC **I**nternational **C**hemical **I**dentifier. 
        - Một tiêu chuẩn xác định phân tử dựa trên cấu trúc (phiên bản chuẩn hóa hơn SMILES). 
        - **InChIKey** là phiên bản băm (hash) rút gọn (27 ký tự) của InChI. 

    - | **SMILES** là đầu vào chính, nhưng **InChIKey** được dùng để 
        - kiểm tra **khớp trùng tuyệt đối (Exact Match)** 
        - nhanh chóng ở Stage 1/2. |

| **Fingerprint (FP)** 
    - | Một vector bit (thường 1024–2048 bits) 
        - mã hóa sự hiện diện của 
            - các **cấu trúc con** (substructures) 
            - hoặc **mô típ hóa học** trong phân tử. 
        - Ví dụ: **ECFP** (Extended Connectivity Fingerprint). 
    
    - | **Biểu diễn số hóa** dùng cho **Truy hồi (Retrieval - Stage 1)**. 
        - FPs được lập chỉ mục trong FAISS 
            - để tìm kiếm các phân tử **tương đồng** (Near-duplicate/Analog)

| **Molecule Graph** 
    - | Phân tử được biểu diễn như một đồ thị (Graph), 
        - trong đó các **nguyên tử** (Atoms) là các **nút** (Nodes) 
        - và **liên kết** (Bonds) là các **cạnh** (Edges). 

    - | Cơ sở cho 
        - các kỹ thuật Học sâu dựa trên đồ thị (**GNN Embedding**) 
        - và dùng để kiểm tra so khớp cấu trúc con chính xác (**Graph Isomorphism**). 

### 2. Các Vấn đề Chuẩn hóa (Normalization)

- Trong thế giới thực, 
    - một chất có thể được viết theo nhiều cách 
        - (đồng phân, muối, v.v.). 
    - Chuẩn hóa là bắt buộc trước khi lập chỉ mục và so khớp.


| Vấn đề | Giải thích | Vai trò trong So khớp |
| :--- | :--- | :--- |

| **Tautomer** | 
    - Các đồng phân có thể chuyển đổi qua lại rất nhanh 
        - (vd: Keto-Enol). 
        - SMILES khác nhau nhưng là cùng một phân tử về mặt hóa học. 

    - Phải chuẩn hóa về dạng **canonical tautomer** 
        - để cùng một phân tử tautomerize vẫn khớp với claim gốc. 

| **Muối/Dung môi** | 
    - Hợp chất có thể đi kèm 
        - muối (vd: NaCl) 
        - hoặc dung môi (vd: nước, ethanol) 
        - trong bằng sáng chế. 

    - Cần **loại bỏ** (strip) 
        - các thành phần muối/dung môi 
        - không liên quan đến hoạt tính chính 
        - trước khi so khớp cấu trúc. 

| **Stereochemistry (Stereo)** | 
    - Cấu hình lập thể 3D (ví dụ: Chirality, cis/trans). 
        - Thường được ký hiệu bằng `@@` trong SMILES. 

    - Cần có chính sách: 
        - **Relaxed** (bỏ stereo) cho tìm kiếm tương đồng (Stage 1) 
        - và **Strict** (giữ stereo) cho so khớp chính xác (Stage 2)

---

## 🔬 Phân tích So khớp Bằng sáng chế (Patent Matching)

- Bài toán so khớp bằng sáng chế hóa học chủ yếu dựa trên 
    - logic so khớp cấu trúc, 
    - nhưng phức tạp hơn 
    - vì sự tồn tại của **Markush Claims**.

### 1. Phân loại So khớp (Matching Types)

| Loại So khớp | Mô tả | Công cụ (Chemoinformatics) |
| :--- | :--- | :--- |

| **Khớp trùng tuyệt đối (Exact Match)** | 
    - Cấu trúc đầu vào hoàn toàn giống với một cấu trúc đã được cấp bằng sáng chế. 
    - | So sánh **InChIKey** hoặc **Canonical SMILES**. |

| **Khớp cấu trúc con (Substructure Match)** | 
    - Cấu trúc đầu vào **chứa** (là siêu cấu trúc của) một cấu trúc con đã được cấp bằng sáng chế, 
    - hoặc ngược lại, cấu trúc đầu vào là cấu trúc con của một cấu trúc được bảo hộ rộng. 
    - Sử dụng **RDKit SubstructMatch** 
        - để kiểm tra ánh xạ (mapping) nguyên tử/liên kết. 

| **Khớp bao phủ Markush (Markush Match)** | 
    - Cấu trúc đầu vào là một trường hợp cụ thể (specific instance) được bao phủ bởi một **Claim Markush** tổng quát. 
    - Sử dụng **QueryMol/SMARTS** + Logic quy tắc (Rule-based logic) để ánh xạ các nhóm thế R (R-groups). 

### 2. Thách thức Markush Claims

[cite_start]**Markush Claim** là trái tim và là thách thức lớn nhất của dự án này[cite: 25].

* **Định nghĩa:**
    - Markush là một cách để mô tả **một lớp lớn các hợp chất** (class of compounds) trong một bằng sáng chế bằng cách xác định 
        - một **cấu trúc lõi (core scaffold)** và nhiều **vị trí thế (R-groups)**, 
        - kèm theo danh sách các nhóm chức năng hoặc phạm vi 
            - (vd: C1-C6 alkyl) có thể gắn vào các vị trí đó.

    * *Ví dụ:* 
        - Một claim có thể bảo vệ công thức: 
            - **Lõi-R1**, 
            - trong đó **R1** là *halogen* (F, Cl, Br, I) hoặc *alkyl C1-C3*.

* **Kỹ thuật So khớp Markush:**
    1.  **Biểu diễn Claim:** 
        - Chuyển claim Markush thành một **QueryMol** hoặc chuỗi **SMARTS** 
            - (Smiles ARbitrary Target Specification) đặc biệt, 
            - có khả năng mô tả các vị trí R-group và ràng buộc logic

    2.  **Ánh xạ (Mapping):** 
        - Kiểm tra xem hợp chất query có thể **phù hợp** 
        - với cấu trúc lõi của Markush hay không.

    3.  **Xác minh R-group:** 
        - Đối với mỗi vị trí R-group trên hợp chất query, 
        - kiểm tra xem nhóm thế đó có nằm trong **danh sách cho phép** hoặc **phạm vi** 
            - (vd: C1-C6 alkyl) được định nghĩa trong Claim hay không.


### 3. Tương đồng Hóa học (Chemical Similarity)

- Khái niệm này hỗ trợ tìm kiếm các 
    - **analog (tương tự)** 
    - **near-duplicate (gần giống)**, 
    - thường được dùng ở **Stage 1 (Retrieval)**.

* **Chỉ số Tanimoto:** 
    - Đây là thước đo phổ biến nhất để đo độ tương đồng giữa hai Fingerprint.
        $$
        Tanimoto(A, B) = \frac{|A \cap B|}{|A \cup B|}
        $$
    * Giá trị cao (gần 1.0) cho thấy hai hợp chất có cấu trúc và nhóm chức năng tương tự. Ngưỡng tương đồng này dùng để lọc sơ bộ ứng viên patent.

---

**Tóm lại:** 
    - Thành công của dự án sẽ nằm ở việc kết hợp sức mạnh của 
        - **Nearest Search/Embedding** (Stage 1) 
            - để tìm kiếm nhanh các **Fingerprint/Embedding** 
        - và sự chính xác của các thuật toán **Chemoinformatics** (Stage 2) 
            - để thực hiện so khớp **Graph Isomorphism** và phân tích **Markush** phức tạp.

Bạn muốn tôi làm rõ thêm về **công cụ RDKit** hoặc các **kỹ thuật GNN/Embedding** cụ thể trong bối cảnh này không?