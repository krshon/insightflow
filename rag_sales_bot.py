import pandas as pd
from transformers import pipeline

# Load dataset
df = pd.read_csv("retail_sales_dataset.csv")

# Load small free LLM (~250MB)
qa_pipeline = pipeline("text2text-generation", model="google/flan-t5-small")

print("🤖 Smart CSV Chatbot Ready! Type 'exit' to stop.\n")


def ask_model(question):

    # provide dataset preview as context
    context = df.head(200).to_string()

    prompt = f"""
    You are a data analyst.

    Dataset sample:
    {context}

    Answer this question using the dataset:

    {question}
    """

    result = qa_pipeline(prompt, max_length=200)[0]["generated_text"]
    return result


while True:
    query = input("Ask: ")

    if query.lower() == "exit":
        print("Goodbye 👋")
        break

    answer = ask_model(query)
    print("\nAnswer:", answer)
