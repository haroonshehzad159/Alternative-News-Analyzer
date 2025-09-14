
import pandas as pd

from processor import analyze_sentiment_from_text, setup_nltk

def get_prediction_label(score_dict):
    """
    Converts a VADER compound score dictionary into a simple sentiment label.
    This is the rule we will use to judge the program's output.
    """
    # This uses the standard thresholds for VADER's compound score
    if score_dict['compound'] >= 0.05:
        return 'Positive'
    elif score_dict['compound'] <= -0.05:
        return 'Negative'
    else:
        return 'Neutral'

def evaluate_sentiment_accuracy():
    """
    Main function to run the evaluation. It loads the dataset, gets a prediction
    for each sentence, compares it to the true label, and calculates accuracy.
    """
    print("--- Starting Sentiment Model Evaluation ---")
    
    setup_nltk()
    
    # Load our manually labeled "answer key" dataset from the CSV file
    try:
        dataset_df = pd.read_csv('sentiment_test_data.csv')
        print(f"Successfully loaded {len(dataset_df)} sentences from the test file.")
    except FileNotFoundError:
        print("ERROR: 'sentiment_test_data.csv' not found in the project folder!")
        print("Please make sure you have created and saved the file correctly.")
        return

    correct_predictions = 0
    total_predictions = len(dataset_df)
    
    print("Running predictions and comparing with your labels...")
    # Loop through each row in our dataset
    for index, row in dataset_df.iterrows():
        sentence_text = row['Sentence']
        true_label = row['MyLabel']
        
        # Get the sentiment score from our processor.py function
        sentiment_score = analyze_sentiment_from_text(sentence_text)
        
        program_prediction = get_prediction_label(sentiment_score)
        
        # Check if the program's prediction matches your own label
        if program_prediction == true_label:
            correct_predictions += 1
    
    # Calculate the final accuracy score
    accuracy = (correct_predictions / total_predictions) * 100
    
    print("\n--- Evaluation Complete ---")
    print(f"Total Sentences Tested: {total_predictions}")
    print(f"Correct Predictions Made by the Program: {correct_predictions}")
    print(f"Final Accuracy: {accuracy:.2f}%")
    
    
    return accuracy

if __name__ == '__main__':
    evaluate_sentiment_accuracy()