import streamlit as st
import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import LabelEncoder

# === 🕐 Step 1: Time-based features
def prepare_datetime_features(df):
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['day_of_week'] = df['date'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['day_sin'] = np.sin(2 * np.pi * df['day'] / 31)
    df['day_cos'] = np.cos(2 * np.pi * df['day'] / 31)
    df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    df.drop(columns=['month', 'day', 'day_of_week'], inplace=True)
    return df

# === Step 2: Encode 'family'
def encode_family_column(df, encoder_path="family_label_encoder.pkl"):
    with open(encoder_path, "rb") as f:
        encoder = pickle.load(f)
    df['family_encoded'] = encoder.transform(df['family'])
    df.drop(columns=['family'], inplace=True)
    return df

# === Prediction pipeline
def predict_sales(test_df):
    test_original = test_df.copy()

    # Prepare features
    test_df = prepare_datetime_features(test_df)
    test_df = encode_family_column(test_df)

    # Load scaler
    with open("x_scaler.pkl", "rb") as f:
        x_scaler = pickle.load(f)

    numerical_cols = ['onpromotion', 'year', 'is_weekend',
                      'month_sin', 'month_cos', 'day_sin', 'day_cos',
                      'dow_sin', 'dow_cos']

    X_test = x_scaler.transform(test_df[numerical_cols])

    # Load model
    with open("best_model.pkl", "rb") as f:
        model = pickle.load(f)

    y_pred_scaled = model.predict(X_test).reshape(-1, 1)

    # Inverse transform
    with open("y_scaler.pkl", "rb") as f:
        y_scaler = pickle.load(f)

    y_pred = y_scaler.inverse_transform(y_pred_scaled)

    # Add predictions to original
    test_original["sales"] = y_pred.flatten()

    return test_original

# === 🖥️ Streamlit app
st.title("🛒 Store Sales Prediction App")

uploaded_file = st.file_uploader("⬆️ حمّل ملف test.csv", type="csv")

if uploaded_file is not None:
    test_df = pd.read_csv(uploaded_file)

    if st.button("🔮 تنبأ بالمبيعات"):
        try:
            result_df = predict_sales(test_df)
            st.success("تمت العملية بنجاح!")

            st.dataframe(result_df.head())

            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ تحميل ملف submission.csv",
                data=csv,
                file_name='submission.csv',
                mime='text/csv'
            )
        except Exception as e:
            st.error(f"حصل خطأ: {e}")
