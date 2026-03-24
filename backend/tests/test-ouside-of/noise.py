# # ============================================================
# #         NOISE INJECTOR - PLUG & PLAY VERSION
# # ============================================================

# import numpy as np
# import pandas as pd


# # ── ✏️  EDIT ONLY THIS SECTION ───────────────────────────────

# FILE_NAME        = "Iris.csv"   # 👈 change this to your file name
# NOISE_PERCENTAGE = 10                # 👈 change % (0–100)
# NOISE_TYPE       = 'gaussian'        # 👈 'gaussian' | 'uniform' | 'salt_pepper' | 'missing'
# SAVE_OUTPUT      = True              # 👈 True to save noisy file, False to skip

# # ─────────────────────────────────────────────────────────────


# # ── CORE FUNCTIONS ───────────────────────────────────────────

# def inject_noise(data, noise_percentage, noise_type='gaussian', random_state=42):
#     np.random.seed(random_state)
#     if isinstance(data, pd.DataFrame):
#         return _inject_noise_df(data, noise_percentage, noise_type)
#     elif isinstance(data, np.ndarray):
#         return _inject_noise_array(data, noise_percentage, noise_type)
#     else:
#         raise TypeError("Data must be a pandas DataFrame or numpy ndarray.")


# def _inject_noise_array(arr, pct, noise_type):
#     noisy = arr.astype(float).copy()
#     n_elements = noisy.size
#     n_noisy = int(n_elements * pct / 100)
#     indices = np.unravel_index(
#         np.random.choice(n_elements, n_noisy, replace=False), arr.shape
#     )
#     if noise_type == 'gaussian':
#         noisy[indices] += np.random.normal(0, np.std(noisy), n_noisy)
#     elif noise_type == 'uniform':
#         range_ = np.ptp(noisy)
#         noisy[indices] += np.random.uniform(-range_ * 0.1, range_ * 0.1, n_noisy)
#     elif noise_type == 'salt_pepper':
#         min_val, max_val = np.min(noisy), np.max(noisy)
#         noisy[indices] = np.where(np.random.rand(n_noisy) > 0.5, max_val, min_val)
#     elif noise_type == 'missing':
#         noisy[indices] = np.nan
#     else:
#         raise ValueError(f"Unknown noise_type: '{noise_type}'")
#     return noisy


# def _inject_noise_df(df, pct, noise_type):
#     noisy_df = df.copy()
#     numeric_cols = df.select_dtypes(include=[np.number]).columns
#     for col in numeric_cols:
#         col_data = noisy_df[col].values.astype(float)
#         n_noisy = int(len(col_data) * pct / 100)
#         indices = np.random.choice(len(col_data), n_noisy, replace=False)
#         if noise_type == 'gaussian':
#             col_data[indices] += np.random.normal(0, np.std(col_data), n_noisy)
#         elif noise_type == 'uniform':
#             range_ = np.ptp(col_data)
#             col_data[indices] += np.random.uniform(-range_ * 0.1, range_ * 0.1, n_noisy)
#         elif noise_type == 'salt_pepper':
#             min_val, max_val = np.min(col_data), np.max(col_data)
#             col_data[indices] = np.where(np.random.rand(n_noisy) > 0.5, max_val, min_val)
#         elif noise_type == 'missing':
#             col_data[indices] = np.nan
#         else:
#             raise ValueError(f"Unknown noise_type: '{noise_type}'")
#         noisy_df[col] = col_data
#     return noisy_df


# def noise_report(original, noisy):
#     orig_num  = original.select_dtypes(include=[np.number])
#     noisy_num = noisy.select_dtypes(include=[np.number])
#     diff      = noisy_num - orig_num
#     changed   = (diff != 0) & (~diff.isna())
#     total     = orig_num.size
#     print("=" * 45)
#     print("           NOISE INJECTION REPORT")
#     print("=" * 45)
#     print(f"  Total values        : {total}")
#     print(f"  Values changed      : {changed.sum().sum()} ({changed.sum().sum()/total*100:.1f}%)")
#     print(f"  Missing (NaN) added : {noisy_num.isna().sum().sum()}")
#     print("-" * 45)
#     print(f"  {'Column':<22} {'Changed':>8} {'% Changed':>10}")
#     print(f"  {'-'*22} {'-'*8} {'-'*10}")
#     for col in orig_num.columns:
#         n = changed[col].sum()
#         print(f"  {col:<22} {n:>8} {n/len(orig_num)*100:>9.1f}%")
#     print("=" * 45)


# # ── AUTO FILE LOADER (supports CSV, Excel, JSON, TSV) ────────

# def load_file(file_name):
#     ext = file_name.strip().split('.')[-1].lower()
#     loaders = {
#         'csv'  : pd.read_csv,
#         'tsv'  : lambda f: pd.read_csv(f, sep='\t'),
#         'xlsx' : pd.read_excel,
#         'xls'  : pd.read_excel,
#         'json' : pd.read_json,
#     }
#     if ext not in loaders:
#         raise ValueError(f"Unsupported file type: '.{ext}'. Supported: csv, tsv, xlsx, xls, json")
#     print(f"Loading '{file_name}'...")
#     return loaders[ext](file_name)


# # ── MAIN ─────────────────────────────────────────────────────

# if __name__ == "__main__":

#     # 1. Load your dataset
#     df = load_file(FILE_NAME)
#     print(f"Dataset loaded! Shape: {df.shape}")
#     print("\nFirst 5 rows:")
#     print(df.head())

#     # 2. Inject noise
#     noisy_df = inject_noise(df, noise_percentage=NOISE_PERCENTAGE, noise_type=NOISE_TYPE)

#     # 3. Print report
#     noise_report(df, noisy_df)

#     # 4. Show noisy preview
#     print("\nNoisy Dataset (first 5 rows):")
#     print(noisy_df.head())

#     # 5. Save output
#     if SAVE_OUTPUT:
#         output_name = FILE_NAME.rsplit('.', 1)[0] + f"_noisy_{NOISE_PERCENTAGE}pct.csv"
#         noisy_df.to_csv(output_name, index=False)
#         print(f"\n✅ Saved to: {output_name}")







import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score


def compare_datasets(clean_path, noisy_path, corrected_path, label_col="label"):

    # Load datasets
    clean_df = pd.read_csv(clean_path)
    noisy_df = pd.read_csv(noisy_path)
    corrected_df = pd.read_csv(corrected_path)

    # ----- Compute label noise -----
    noisy_mismatch = (clean_df[label_col] != noisy_df[label_col]).sum()
    corrected_mismatch = (clean_df[label_col] != corrected_df[label_col]).sum()

    noise_rate = noisy_mismatch / len(clean_df)
    corrected_noise_rate = corrected_mismatch / len(clean_df)

    # ----- Model evaluation -----
    def evaluate(df):
        X = df.drop(columns=[label_col])
        y = df[label_col]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        model = RandomForestClassifier(n_estimators=200, random_state=42)
        model.fit(X_train, y_train)

        preds = model.predict(X_test)

        acc = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds, average="weighted")

        return acc, f1

    clean_acc, clean_f1 = evaluate(clean_df)
    noisy_acc, noisy_f1 = evaluate(noisy_df)
    corrected_acc, corrected_f1 = evaluate(corrected_df)

    # ----- Print results -----
    print("\nDataset Comparison")
    print("-" * 40)
    print(f"Noise rate in noisy dataset: {noise_rate:.3f}")
    print(f"Noise rate after correction: {corrected_noise_rate:.3f}\n")

    print("Model Performance")
    print("-" * 40)
    print(f"Clean dataset     -> Accuracy: {clean_acc:.3f}, F1: {clean_f1:.3f}")
    print(f"Noisy dataset     -> Accuracy: {noisy_acc:.3f}, F1: {noisy_f1:.3f}")
    print(f"Corrected dataset -> Accuracy: {corrected_acc:.3f}, F1: {corrected_f1:.3f}")


# Example usage
compare_datasets(
    "Iris.csv",
    "Iris_noisy_10pct.csv",
    "Iris_noisy_cleaned.csv"
)