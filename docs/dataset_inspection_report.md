# Dataset Inspection, Integrity & Statistical Analysis Report

## 1. Overview & Integrity Verification
- **Total Images Scanned**: 7329
- **Valid & Structurally Intact Images**: 7329
- **Unique Clean Images**: 7326
- **Corrupted / Truncated Images Detected**: 0
- **Duplicate Images Detected (SHA-256)**: 3
- **Class Imbalance Ratio (Max / Min non-zero)**: 6.17x

---

## 2. Dataset Distribution by Source
| Dataset Source | Image Count | Status |
| :--- | :--- | :--- |
| **Realwaste** | 4752 | Verified |
| **Trashnet** | 2527 | Verified |
| **Taco** | 50 | Verified |

---

## 3. Canonical Waste Category Distribution
| Category ID | Canonical Category | Sample Count | Percentage |
| :--- | :--- | :--- | :--- |
| 0 | `organic_waste` | 847 | 11.56% |
| 1 | `paper_waste` | 1962 | 26.78% |
| 2 | `plastic_waste` | 1416 | 19.33% |
| 3 | `metal_waste` | 1223 | 16.69% |
| 4 | `glass_waste` | 928 | 12.67% |
| 5 | `electronic_waste` | 0 | 0.0% |
| 6 | `hazardous_waste` | 0 | 0.0% |
| 7 | `textile_waste` | 318 | 4.34% |
| 8 | `residual_waste` | 632 | 8.63% |

---

## 4. Image Dimensional Statistics
- **Resolution Range**: 512x384 to 3264x3264 px
- **Average Resolution**: 528.2 x 485.6 px
- **Mean Aspect Ratio (W/H)**: 1.11

---

## 5. Preprocessing & Mitigation Strategy
1. **Duplicate Exclusion**: All detected duplicate content hashes are quarantined to avoid identical images appearing in both train and test splits (preventing data leakage).
2. **Class Imbalance Handling**: Class weights are computed via `compute_class_weight('balanced')` to apply loss weighting during model training, supplemented by targeted data augmentation for under-represented categories.
3. **Dimension Normalization**: All classification images are resized and standardized to `224x224` with ImageNet normalization tensors, while YOLO detection images are scaled to `640x640`.
