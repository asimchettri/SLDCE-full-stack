from sklearn.model_selection import train_test_split

def split_data(df, target, test_size=0.2, random_state=42):
    X = df.drop(columns=[target])
    y = df[target]

    return train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )
