import json
from groq import Groq
import os

def main():
    # ---------------------------------
    # Groq Client Configuration
    # ---------------------------------
    # Get API key from environment variable
    # Set with: export GROQ_API_KEY="your-api-key-here"
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    client = Groq(api_key=api_key)

    # ---------------------------------
    # File paths
    # ---------------------------------
    INPUT_FILE = "input_symptoms.json"
    OUTPUT_FILE = "assessment_result.json"

    # ---------------------------------
    # Load symptoms from JSON
    # ---------------------------------
    with open(INPUT_FILE, "r") as f:
        input_data = json.load(f)

    symptoms = input_data["symptoms"]

    # ---------------------------------
    # Create completion
    # ---------------------------------
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You are a professional veterinary triage assistant."
            },
            {
                "role": "user",
                "content": f"""
    Classify the following pet symptoms into ONLY ONE category:

    1. Emergency – life-threatening, needs immediate vet care
    2. Urgent – needs vet care soon
    3. Routine – can be monitored or handled with basic care

    Give a short reason.

    Respond strictly in this format:
    Category: <Emergency/Urgent/Routine>
    Reason: <one-line explanation>

    Symptoms:
    {symptoms}
    """
            }
        ],
        temperature=0.2,
        max_completion_tokens=300,
        top_p=1,
        reasoning_effort="medium",
        stream=True
    )

    # ---------------------------------
    # Collect streamed response
    # ---------------------------------
    final_response = ""

    print("\n--- Assessment ---\n")

    for chunk in completion:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="")
            final_response += content

    # ---------------------------------
    # Save output to JSON
    # ---------------------------------
    output_data = {
        "pet_id": input_data.get("pet_id", None),
        "symptoms": symptoms,
        "assessment": final_response.strip()
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output_data, f, indent=4)

    print("\n\nAssessment saved to:", OUTPUT_FILE)


if __name__=="__main__":
    main()