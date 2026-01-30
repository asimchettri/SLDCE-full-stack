
# SLDCE Phase 1 Workflow


1. Upload Clean Dataset

Upload CSV file with correct labels
System stores 178 samples in database
Column names preserved (alcohol, malic_acid, ash, etc.)


2. Train Baseline Model ⭐

Choose model type (Random Forest / Logistic Regression / SVM)
System trains on clean data
Result: 95% accuracy (this is our target to beat)


3. Inject Noise

Manually corrupt 20% of labels (36 samples out of 178)
Save as new CSV file


4. Upload Noisy Dataset

Upload the corrupted CSV
Now we have dataset with wrong labels


5. Run Detection

System trains model on noisy data
Accuracy drops to 78% (proof noise hurts performance)
Detects ~35 suspicious samples using:

Confidence analysis (model disagrees with label)
Anomaly detection (unusual feature patterns)




6. Generate Suggestions

System ranks suspicious samples by priority
Creates correction suggestions with reasons
Example: "Sample #45: Change from 1 → 2 (92% confidence)"


7. Review Suggestions

Human reviews each suggestion
3 options per sample:

✅ Accept (use suggested label)
❌ Reject (keep current label)
✏️ Modify (enter custom label)


In our test: Accepted 25, Rejected 8, Modified 2


8. Apply Corrections

System updates database with accepted changes
27 labels corrected (out of 36 corrupted)
Noise reduced from 20% → 5%


9. Retrain Model

Train new model on corrected dataset
Accuracy improves to 85% (+7% from noisy)


10. Compare Results

Baseline (clean): 95%
Noisy model: 78% (-17%)
After corrections: 85% (+7%)
Proves the system works!


11. Download Cleaned Dataset

Export corrected data as CSV
Original column names preserved
Ready to use for production

