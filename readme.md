# PROJECT: SMART WASTE SEGREGATION AND RECYCLING RECOMMENDATION SYSTEM

Act as a senior AI/ML engineer, computer vision researcher, Python backend developer, and full-stack software architect.

Build a complete, functional, modern AI-powered Smart Waste Segregation and Recycling Recommendation System.

This must be a genuine AIML project. Do not use external vision APIs or pretrained general-purpose AI APIs to perform the main waste classification. The actual predictions must come from locally integrated and fine-tuned machine learning models.

The application should identify waste materials from uploaded images, detect multiple objects, classify their waste categories, and provide intelligent recycling and disposal recommendations.

==================================================
1. PROJECT OBJECTIVES
==================================================

The system must provide the following capabilities:

1. Identify waste materials from images.
2. Detect multiple waste objects in a single image.
3. Classify waste into appropriate categories.
4. Determine whether an item is recyclable, compostable, hazardous, or residual waste.
5. Recommend appropriate disposal methods.
6. Suggest recycling processes.
7. Estimate environmental benefits of recycling using transparent assumptions.
8. Maintain a history of waste analysis.
9. Display waste statistics and environmental impact dashboards.

==================================================
2. TECHNOLOGY STACK
==================================================

Frontend:
- React.js with Vite
- Tailwind CSS
- React Router
- Recharts for analytics
- Lucide React for icons

Backend:
- Python
- FastAPI
- Pydantic
- REST APIs

Machine Learning:
- PyTorch
- Torchvision
- Ultralytics YOLO
- OpenCV
- NumPy
- Pandas
- Scikit-learn
- Pillow

Database:
- MongoDB
- MongoDB Atlas or local MongoDB
- Use MongoDB for users, prediction history, and analytics.

Testing:
- Pytest
- FastAPI TestClient
- React testing tools

==================================================
3. DATASET MANAGEMENT
==================================================

Use the following datasets:

A. TrashNet:
https://github.com/garythung/trashnet

B. RealWaste:
https://doi.org/10.21227/65m5-rr72

C. TACO:
https://github.com/pedropro/TACO

The datasets will be manually downloaded and placed inside:

datasets/
    trashnet/
    realwaste/
    taco/

Build a proper dataset preparation pipeline.

Requirements:

1. Inspect dataset directory structures.
2. Identify available classes.
3. Read existing annotations.
4. Check corrupted and duplicate images.
5. Generate dataset statistics.
6. Handle class imbalance.
7. Normalize image dimensions.
8. Apply suitable image augmentation.
9. Create training, validation, and testing splits.
10. Prevent data leakage between splits.
11. Preserve original dataset labels.
12. Create a documented class-mapping system.

Do not assume all three datasets have identical classes.

Create scripts for preprocessing rather than manually modifying the original datasets.

==================================================
4. MACHINE LEARNING MODELS
==================================================

Implement two separate computer vision pipelines.

MODEL A: WASTE IMAGE CLASSIFICATION

Use transfer learning with EfficientNet or MobileNetV3.

Requirements:

- Load a pretrained architecture.
- Replace the classification head.
- Train using TrashNet and RealWaste.
- Support configurable training parameters.
- Save trained model weights.
- Implement validation.
- Calculate accuracy, precision, recall, F1-score.
- Generate confusion matrices.
- Display training and validation loss curves.
- Save training logs.
- Implement inference on new images.

Do not claim model accuracy without actually training and evaluating it.

MODEL B: MULTI-OBJECT WASTE DETECTION

Use Ultralytics YOLO.

Requirements:

- Use TACO annotations.
- Convert COCO annotations into the required YOLO format.
- Preserve bounding box coordinates correctly.
- Train or fine-tune an appropriate pretrained YOLO model.
- Detect multiple waste objects in one image.
- Return class names, bounding boxes, and confidence scores.
- Generate annotated images.
- Calculate mAP50 and mAP50-95.
- Save model weights.

Use a small model variant initially to reduce hardware requirements.

If a dataset or annotation is incompatible, report the problem and provide a conversion solution instead of silently ignoring it.

==================================================
5. RECYCLING RECOMMENDATION ENGINE
==================================================

Develop a separate recommendation engine.

Create:

backend/
    recommendations/
        recycling_data.csv
        recommendation_engine.py

The CSV should contain:

- Object name
- Material
- Waste category
- Recyclability
- Recommended bin
- Recycling method
- Preparation instructions
- Disposal instructions
- Environmental impact information

Waste categories:

1. Organic waste
2. Paper waste
3. Plastic waste
4. Metal waste
5. Glass waste
6. Electronic waste
7. Hazardous waste
8. Textile waste
9. Residual waste

Recommendation examples:

Banana peel:
- Category: Organic
- Recommendation: Composting
- Bin: Wet waste

Plastic bottle:
- Material: PET, when confidently identified
- Category: Plastic
- Recommendation: Empty, rinse, and send to an appropriate plastic recycling facility.

Aluminium can:
- Category: Metal
- Recommendation: Metal recycling.

Battery:
- Category: Hazardous/e-waste
- Recommendation: Authorized battery collection facility.

IMPORTANT:

Do not assume every plastic, paper, or glass object is recyclable.

Recommendations must account for contamination, material type, and local disposal rules.

Keep disposal rules configurable by location.

Do not invent environmental impact values. Any estimated carbon savings or energy savings must use documented conversion factors and clearly display that they are estimates.

==================================================
6. BACKEND DEVELOPMENT
==================================================

Develop a modular FastAPI backend.

Required endpoints:

POST /api/analyze

- Accept an image.
- Validate its format and size.
- Run object detection.
- Run classification where appropriate.
- Generate recycling recommendations.
- Return structured JSON.
- Return an annotated image or its accessible result path.

GET /api/history

- Fetch previous predictions.

GET /api/analytics

- Return waste category statistics.
- Return recyclable and non-recyclable counts.
- Return environmental impact estimates.

GET /api/health

- Check backend and ML model availability.

POST /api/auth/register

POST /api/auth/login

Implement authentication securely.

Additional requirements:

- Proper exception handling.
- Input validation.
- Image upload security.
- CORS configuration.
- Logging.
- Environment variables.
- API documentation.
- Modular architecture.

Never expose database credentials or secrets in frontend code.

==================================================
7. FRONTEND DEVELOPMENT
==================================================

Build a professional and modern dashboard.

Design inspiration:
Modern environmental technology SaaS dashboard.

Use a clean green, white, and neutral color palette.

Pages:

A. LANDING PAGE

- Project introduction.
- Explanation of smart waste segregation.
- How the system works.
- Key features.
- Get Started button.

B. DASHBOARD

- Total waste analyzed.
- Recyclable waste percentage.
- Organic waste percentage.
- Hazardous waste count.
- Recent analysis.
- Waste distribution charts.

C. WASTE ANALYSIS PAGE

- Drag-and-drop image upload.
- Image preview.
- Analyze button.
- Loading animation.
- Display annotated image.
- Display detected objects.
- Display confidence scores.
- Display material classification.
- Display recommended waste bin.
- Display recycling instructions.

D. ANALYSIS HISTORY

- Previous uploaded images.
- Predictions.
- Categories.
- Dates.
- Search and filtering.

E. ANALYTICS PAGE

- Waste distribution.
- Recycling trends.
- Category-wise statistics.
- Estimated environmental benefits.

F. ABOUT PAGE

- Project objectives.
- Technologies used.
- Dataset information.
- Model information.

Make the interface responsive for desktop, tablet, and mobile.

==================================================
8. SYSTEM INTEGRATION
==================================================

Connect the React frontend to the FastAPI backend.

The complete workflow should be:

1. User uploads an image.
2. Frontend sends the image to FastAPI.
3. Backend validates the image.
4. YOLO detects individual waste objects.
5. Classification model predicts the material category.
6. Recommendation engine retrieves disposal recommendations.
7. Backend returns structured results.
8. Frontend displays bounding boxes and recommendations.
9. Prediction is stored in MongoDB when database functionality is enabled.
10. Analytics are updated.

Handle cases where:

- No waste object is detected.
- Confidence is too low.
- An unsupported object is uploaded.
- The image is corrupted.
- Multiple objects are detected.
- A detected object has no matching recommendation.

Never force a prediction when model confidence is insufficient. Display an uncertain/unknown result instead.

==================================================
9. PROJECT STRUCTURE
==================================================

Use a modular structure similar to:

Smart-Waste-Management/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── context/
│   │   └── assets/
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   ├── recommendations/
│   │   ├── database/
│   │   └── utils/
│   │
│   ├── ml/
│   │   ├── preprocessing/
│   │   ├── classification/
│   │   ├── detection/
│   │   ├── training/
│   │   └── evaluation/
│   │
│   ├── tests/
│   └── requirements.txt
│
├── datasets/
│   ├── trashnet/
│   ├── realwaste/
│   └── taco/
│
├── trained_models/
│
├── notebooks/
│
├── scripts/
│
├── docs/
│
├── .gitignore
├── .env.example
└── README.md

You may improve the structure if technically necessary.

==================================================
10. DEVELOPMENT RULES
==================================================

Follow these rules strictly:

1. Do not generate the entire project in one unverified step.
2. First inspect the available system environment.
3. Create a detailed implementation plan.
4. Build the ML pipeline before integrating it into the backend.
5. Use actual datasets, not fabricated training data.
6. Do not generate fake model evaluation results.
7. Never hardcode model predictions.
8. Never use mock responses in the final integrated application.
9. Use reusable components.
10. Write clean, documented code.
11. Create requirements.txt.
12. Create README.md with complete setup instructions.
13. Create .env.example.
14. Include error handling and testing.
15. Keep model weights outside Git.
16. Use environment variables for secrets.
17. Ensure the project can run locally on Windows.

If GPU acceleration is unavailable, provide a CPU-compatible fallback.

==================================================
11. DEVELOPMENT PHASES
==================================================

Work through these phases sequentially.

PHASE 1:
Inspect environment, create architecture, inspect datasets, and prepare the development environment.

PHASE 2:
Implement dataset preprocessing and generate dataset reports.

PHASE 3:
Implement and train the image classification model.

PHASE 4:
Implement and train the YOLO object detection model.

PHASE 5:
Build the recycling recommendation engine.

PHASE 6:
Build and test the FastAPI backend.

PHASE 7:
Build the React frontend.

PHASE 8:
Integrate frontend, backend, and trained ML models.

PHASE 9:
Perform end-to-end testing and fix issues.

PHASE 10:
Prepare documentation, architecture diagrams, model evaluation reports, and final project instructions.

==================================================
12. FIRST TASK
==================================================

DO NOT START CODING THE ENTIRE APPLICATION IMMEDIATELY.

Start by:

1. Inspecting the current workspace.
2. Checking installed Python, Node.js, Git, and available GPU.
3. Inspecting the downloaded datasets.
4. Identifying missing dependencies.
5. Proposing the final architecture.
6. Creating a detailed development roadmap.
7. Identifying hardware limitations.

Then implement PHASE 1.

After each phase, run relevant tests, verify the output, and report:

- Files created.
- Files modified.
- Commands executed.
- Tests performed.
- Problems encountered.
- Remaining tasks.

Do not proceed with expensive model training until dataset preparation and model configuration have been verified.

The final goal is a fully functional, locally executable Smart Waste Segregation and Recycling Recommendation System with genuine machine learning inference.