# -*- coding: utf-8 -*-
"""NM Project.py

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1lA4xtKh8HCr5uXcGmrAu0HCmdodnnoMy
"""

!pip install ipywidgets

from google.colab import files
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import ipywidgets as widgets
from IPython.display import display, clear_output
import plotly.express as px

uploaded = files.upload()
df = pd.read_csv('only_road_accidents_data_month2.csv')
df.columns = df.columns.str.strip()

months = ['JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE',
          'JULY','AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER']
df_long = df.melt(id_vars=['STATE/UT', 'YEAR'],
                  value_vars=months,
                  var_name='Month', value_name='Accident_Count')
df_long['Month'] = pd.Categorical(df_long['Month'], categories=months, ordered=True)
df_long = df_long.sort_values(by=['YEAR', 'Month'])
df_long['Month_Num'] = df_long['Month'].cat.codes + 1
df_long['State_Code'] = df_long['STATE/UT'].astype('category').cat.codes

print("\nSummary Statistics:")
print(df_long.describe())

top_5_states = df_long.groupby('STATE/UT')['Accident_Count'].sum().nlargest(5).index
df_top_5_states = df_long[df_long['STATE/UT'].isin(top_5_states)]
plt.figure(figsize=(16, 8))
sns.lineplot(data=df_top_5_states, x='Month', y='Accident_Count', hue='STATE/UT')
plt.xticks(rotation=45)
plt.title("Monthly Accident Trends for Top 5 States")
plt.tight_layout()
plt.show()

selected_states = top_5_states
df_selected_states = df_long[df_long['STATE/UT'].isin(selected_states)]
yearly_state_trends = df_selected_states.groupby(['YEAR', 'STATE/UT'])['Accident_Count'].sum().reset_index()
plt.figure(figsize=(12, 6))
sns.lineplot(data=yearly_state_trends, x='YEAR', y='Accident_Count', hue='STATE/UT')
plt.title(f"Yearly Accident Trends for {', '.join(selected_states)}")
plt.xlabel("Year")
plt.ylabel("Total Accidents")
plt.legend(title="State/UT")
plt.grid(True)
plt.tight_layout()
plt.show()

plt.figure(figsize=(8, 6))
sns.histplot(df_long['Accident_Count'], kde=True)
plt.title("Distribution of Monthly Accident Counts")
plt.xlabel("Accident Count")
plt.ylabel("Frequency")
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 6))
sns.boxplot(y=df_long['Accident_Count'])
plt.title("Boxplot of Monthly Accident Counts (Outlier Detection)")
plt.ylabel("Accident Count")
plt.tight_layout()
plt.show()

pivot_table_interactive = df_long.pivot_table(index='STATE/UT', columns='Month', values='Accident_Count')
fig_heatmap = px.imshow(pivot_table_interactive,
                        labels=dict(x="Month", y="State/UT", color="Accident Count"),
                        color_continuous_scale="YlOrRd",
                        title="Interactive State-wise Monthly Road Accident Heatmap")
fig_heatmap.show()

X = df_long[['YEAR', 'Month_Num', 'State_Code']]
y = df_long['Accident_Count']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

gbr_model = GradientBoostingRegressor(random_state=42)
gbr_model.fit(X_train, y_train)
gbr_y_pred = gbr_model.predict(X_test)
gbr_mae = mean_absolute_error(y_test, gbr_y_pred)
gbr_r2 = r2_score(y_test, gbr_y_pred)
print(f"\nGradient Boosting Regressor Evaluation:")
print(f"Mean Absolute Error: {gbr_mae:.2f}")
print(f"R² Score: {gbr_r2:.2f}")

param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [None, 5, 10],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 3, 5]
}
grid_search = GridSearchCV(RandomForestRegressor(random_state=42), param_grid, cv=3, scoring='neg_mean_absolute_error')
grid_search.fit(X_train, y_train)
best_rf_model = grid_search.best_estimator_
best_rf_y_pred = best_rf_model.predict(X_test)
best_rf_mae = mean_absolute_error(y_test, best_rf_y_pred)
best_rf_r2 = r2_score(y_test, best_rf_y_pred)
print("\nRandom Forest Regressor with Hyperparameter Tuning:")
print(f"Best Parameters: {grid_search.best_params_}")
print(f"Mean Absolute Error: {best_rf_mae:.2f}")
print(f"R² Score: {best_rf_r2:.2f}")

importances = best_rf_model.feature_importances_
feature_names = X.columns
plt.figure(figsize=(6,4))
sns.barplot(x=importances, y=feature_names)
plt.title("Feature Importance (Tuned Random Forest)")
plt.tight_layout()
plt.show()

def predict_accidents(year, month, state_code, model):
    prediction = model.predict(np.array([[year, month, state_code]]))
    return max(0, int(prediction[0]))

state_options = list(df_long['STATE/UT'].unique())
state_options.sort()
year_widget = widgets.IntSlider(min=df_long['YEAR'].min(), max=df_long['YEAR'].max(), step=1, value=df_long['YEAR'].max(), description='Year:')
month_widget = widgets.IntSlider(min=1, max=12, step=1, value=1, description='Month:')
state_widget = widgets.Dropdown(options=state_options, value=state_options[0], description='State:')
prediction_output = widgets.Output()
predict_button = widgets.Button(description="Predict Accidents")

def on_predict_button_clicked(b):
    with prediction_output:
        clear_output(wait=True)
        selected_year = year_widget.value
        selected_month = month_widget.value
        selected_state = state_widget.value
        state_code = df_long[df_long['STATE/UT'] == selected_state]['State_Code'].iloc[0]
        predicted_count = predict_accidents(selected_year, selected_month, state_code, best_rf_model)
        print(f"Predicted number of accidents in {selected_state} in {months[selected_month-1]}, {selected_year}: {predicted_count}")

predict_button.on_click(on_predict_button_clicked)
display(widgets.VBox([year_widget, month_widget, state_widget, predict_button, prediction_output]))

print("\n--- Model Performance ---")
print(f"Random Forest (Initial) - MAE: {mae:.2f}, R²: {r2:.2f}")
print(f"Gradient Boosting Regressor - MAE: {gbr_mae:.2f}, R²: {gbr_r2:.2f}")
print(f"Random Forest (Tuned) - MAE: {best_rf_mae:.2f}, R²: {best_rf_r2:.2f}")

joblib.dump(best_rf_model, 'best_accident_predictor_rf_model.pkl')

print("\n--- Real-Time Accident Risk Predictor (Rule-Based) ---")
time_widget = widgets.Dropdown(
    options=[('Night (0)', 0), ('Morning (1)', 1), ('Afternoon (2)', 2), ('Evening (3)', 3)],
    value=1,
    description='Time:'
)

weather_widget = widgets.Dropdown(
    options=[('Clear (0)', 0), ('Rain (1)', 1), ('Fog (2)', 2), ('Snow (3)', 3)],
    value=0,
    description='Weather:'
)

road_widget = widgets.Dropdown(
    options=[('Dry (0)', 0), ('Wet (1)', 1), ('Icy (2)', 2)],
    value=0,
    description='Road:'
)

traffic_widget = widgets.IntSlider(
    value=150,
    min=0,
    max=500,
    step=10,
    description='Traffic Vol:'
)

output = widgets.Output()

def on_change(change):
    with output:
        clear_output(wait=True)
        risk = predict_risk_widget(
            time_widget.value,
            weather_widget.value,
            road_widget.value,
            traffic_widget.value
        )
        print(f"🚦 Predicted Accident Risk Level (Rule-Based): {risk}")

for widget in [time_widget, weather_widget, road_widget, traffic_widget]:
    widget.observe(on_change, names='value')

display(widgets.VBox([time_widget, weather_widget, road_widget, traffic_widget, output]))
on_change(None)

plt.figure(figsize=(10,12))
state_totals.plot(kind='barh', color='teal')
plt.xlabel("Total Accidents")
plt.title("Total Accidents by State/UT")
plt.tight_layout()
plt.show()

plt.figure(figsize=(10,5))
sns.lineplot(x=yearly_totals.index, y=yearly_totals.values, marker='o')
plt.title("Yearly Road Accidents in India")
plt.xlabel("Year")
plt.ylabel("Total Accidents")
plt.grid(True)
plt.tight_layout()
plt.show()

plt.figure(figsize=(10,5))
sns.boxplot(data=df_long, x='Month', y='Accident_Count')
plt.title("Month-wise Distribution of Accident Counts")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()