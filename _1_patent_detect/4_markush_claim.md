Tuyệt vời. Với những kiến thức nền tảng đã có về RDKit, GNN và vai trò của chúng, việc đi sâu vào **Logic Markush Claim** sẽ là bước tiếp theo quan trọng nhất, vì đây là thách thức kỹ thuật cốt lõi trong dự án.

## 🧱 Đi sâu vào Logic Markush Claim

**Markush Claims** 
    - là công cụ mà các nhà phát minh sử dụng để xác định một **lớp các hợp chất** 
        - mà họ tuyên bố quyền sở hữu trí tuệ, 
    - cho phép bảo vệ hàng triệu hợp chất tiềm năng chỉ trong một công thức duy nhất. 
    - Việc so khớp 
        - một hợp chất truy vấn (query compound) 
        - với một Markush Claim 
        - đòi hỏi một quá trình 
            - phân tích và so khớp 
            - dựa trên quy tắc phức tạp. 

---

### 1. Cấu trúc của Markush Claim

Markush Claim về cơ bản được chia thành hai phần:

| Thành phần | Mô tả | Vai trò trong So khớp (Stage 2) |
| :--- | :--- | :--- |
| **Cấu trúc Lõi (Core Scaffold)** | 
    - Là bộ khung nguyên tử chung, bất biến 
        - có mặt trong tất cả các hợp chất thuộc Claim. | 
    - Dùng RDKit 
        - để thực hiện **Substructure Match** của query compound trên Core Scaffold. 
        - Nếu không khớp, compound không bị Claim bao phủ. |

| **Vị trí/Nhóm thế R (R-groups)** | 
    - Là các vị trí trên Lõi nơi có thể gắn các nhóm chức năng khác nhau. | 
    - Xác định vị trí R-group trên query compound, 
        - sau đó kiểm tra xem nhóm thế tại vị trí đó có **hợp lệ** 
        - theo định nghĩa của Claim hay không. |

| **Định nghĩa Nhóm thế (R-group Definitions)** | 
    - Danh sách các nhóm thế cho phép, 
        - thường được mô tả bằng ngôn ngữ tự nhiên (hoặc chuẩn hóa): 
        - *ví dụ: Halogen, C1-C6 alkyl, Aryl*, v.v. | 
    - Cần phải 
        - **phân tích cú pháp (parsing)** và 
        - **chuẩn hóa** các định nghĩa này 
        - thành các quy tắc hóa học có thể kiểm tra. |

---

### 2. Kỹ thuật Phân tích và So khớp Markush

Để so khớp một hợp chất query với Claim, mô hình cần thực hiện các bước sau:

#### A. Phân tách và Biểu diễn Claim
1.  **Parsing Claim Text/Image:** 
    Chuyển đổi công thức Markush (thường là hình ảnh hoặc văn bản có cấu trúc) thành một biểu diễn số hóa.

2.  **Biểu diễn Core:** 
    Lưu Core Scaffold dưới dạng **QueryMol** hoặc **SMARTS** để giữ lại các điểm kết nối R-group.

3.  **Biểu diễn R-Definitions:** Chuyển định nghĩa R-group thành các quy tắc kiểm tra:
    * **Nhóm kín (Closed List):** 
        - Nếu R1 = {Methyl, Ethyl, Propyl}, mỗi nhóm thế sẽ được kiểm tra exact match.
    * **Phạm vi (Generic Groups):** 
        - Nếu R1 = {C1-C6 alkyl}, 
            - hệ thống cần kiểm tra xem nhóm thế có phải là 
            - một chuỗi Carbon no, 
            - không phân nhánh hoặc phân nhánh, 
            - với số Carbon từ 1 đến 6 hay không. 
        - Điều này đòi hỏi logic **RDKit** để đếm nguyên tử và xác định loại nhóm.

#### B. Ánh xạ Hợp chất Query (Mapping)
1.  **Khớp Scaffold:** 
    - Dùng **RDKit SubstructMatch** để ánh xạ Core Scaffold của Claim lên hợp chất Query.

2.  **Trích xuất R-groups:** 
    - Sau khi Core khớp, hệ thống sẽ xác định phần cấu trúc nào của Query compound gắn vào các điểm kết nối R-group. 
    - Phần còn lại này là nhóm thế R thực tế.

#### C. Xác minh Quy tắc (Rule Verification)
1.  **Kiểm tra Ràng buộc:** 
    - Đối với mỗi nhóm thế R được trích xuất, 
    - kiểm tra xem nó có **thỏa mãn** định nghĩa trong Claim hay không.

2.  **Logic Boolean:** 
    - Kiểm tra các ràng buộc logic phức tạp 
    - (ví dụ: "ít nhất một trong R1, R2, R3 phải là Halogen").

3.  **Kết quả:** 
    - Nếu **Scaffold khớp** VÀ **TẤT CẢ** các nhóm thế R được trích xuất đều nằm trong định nghĩa của Claim, 
    - thì hợp chất query được **bao phủ (infringing)**.

---

## 📊 Chỉ số Đánh giá trong Ngữ cảnh Hóa học: $Recall@K$

Vì đây là bài toán 2 tầng, chúng ta cần hai bộ chỉ số:

### 1. Đánh giá Stage 1 (Retrieval - Truy hồi)

| Chỉ số | Ý nghĩa | Mục tiêu |
| :--- | :--- | :--- |
| **Recall@K** | 
    - Tỷ lệ các Claim vi phạm **thực sự** (Ground Truth) nằm trong $K$ ứng viên hàng đầu được FAISS/Embedding truy hồi. | 
    - Đặt mục tiêu cao (ví dụ: **$\geq 0.95$ Recall@50**) để đảm bảo mô hình không bỏ sót ứng viên patent quan trọng ngay từ đầu. |

| **AUC-PR** | **Area Under the Precision-Recall Curve.** 
    - Tốt hơn AUC-ROC cho các tập dữ liệu bị mất cân bằng (imbalanced) như bằng sáng chế (rất nhiều Not Patented). | 
    - Đánh giá khả năng phân biệt ứng viên tốt/xấu của mô hình Embedding/FP. |

### 2. Đánh giá Stage 2 (Verification - Xác minh)

| Chỉ số | Ý nghĩa | Tầm quan trọng |
| :--- | :--- | :--- |
| **Precision** | 
    - Tỷ lệ các Claim mô hình xác minh là vi phạm **thực sự** là vi phạm. | 
    - Cực kỳ quan trọng, vì $False\ Positive$ (FP) 
        - có thể dẫn đến **lãng phí thời gian và nguồn lực R&D** 
        - (tin rằng đã vi phạm nhưng thực ra là không). |

| **Recall (Sensitivity)** | 
    - Tỷ lệ các Claim vi phạm **thực sự** được mô hình xác định đúng là vi phạm. | 
    - Cực kỳ quan trọng, vì $False\ Negative$ (FN) 
        - có thể dẫn đến **vi phạm bằng sáng chế thực tế** (tin rằng an toàn nhưng thực ra là vi phạm). |

| **F1-Score** | 
    - Trung bình điều hòa của Precision và Recall. | 
    - Chỉ số cân bằng tổng thể, cần được tối ưu hóa. |

Trong lĩnh vực này, $False\ Negative$ (bỏ sót vi phạm) thường được coi là rủi ro lớn hơn $False\ Positive$. Do đó, việc tìm ra sự cân bằng giữa **Recall@K cao** ở Stage 1 và **Precision/Recall tối ưu** ở Stage 2 là chìa khóa.

Bạn muốn đi sâu hơn vào việc **Phân tích Cú pháp (Parsing) các định nghĩa R-group** thành các quy tắc RDKit/SMARTS, hay muốn thảo luận về việc **Tuning các tham số FAISS** để đạt được mục tiêu $Recall@K$ không?