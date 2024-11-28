from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import pandas as pd
import joblib

# Read the dataset
train_df = pd.read_csv("Datasets/train.csv")

# Extracting target variable and features
target = train_df['stream']
data = train_df[['grades_math', 'grades_sci', 'grades_eng', 'grades_ss', 'grades_comp',
                 'Computer', 'CivilServices', 'MarketingSales', 'Science', 'Mathematics',
                 'SocialSciencesHumanities', 'PerformingFineArts', 'Business', 'FinanceAccounting',
                 'Healthcare', 'Aptitude', 'science', 'commerce', 'arts', 'general1', 'general2']]

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(data, target, test_size=0.3, random_state=42)

# Initialize and train the model
rf_model = RandomForestRegressor()
rf_model.fit(X_train, y_train)

# Make predictions on the testing set
y_pred = rf_model.predict(X_test)

# Evaluate the model
mse = mean_squared_error(y_test, y_pred)
print("Mean Squared Error:", mse)

r2 = r2_score(y_test, y_pred)
print("R-squared score:", r2)

# Print the results
results = pd.DataFrame({'Actual_stream': y_test.values, 'Predicted_stream': y_pred})
print(results)

# Save the trained model using joblib
joblib.dump(rf_model, 'random_forest_model.pkl')
