import os
import vertexai
from vertexai.generative_models import GenerativeModel
import os
from google.cloud import aiplatform


def get_model():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")  # Get project ID from environment
    print(project_id)
    aiplatform.init(project=project_id, location="us-central1")
    # Check the docs for the actual API call.
    # This is how you might list models (if the API supports it).
    models = aiplatform.Model.list(location="us-central1")  # Or a similar function

    # Find the latest model (logic depends on what the API returns)
    latest_model = None
    for model in models:
        # Example:  Check if the model name starts with "gemini" and
        # has a higher version number (you'll need a way to parse versions)
        if model.display_name.startswith("gemini"):  # Or model.name, etc.
            # ... (version comparison logic) ...
            if latest_model is None or model.display_name > latest_model.display_name:  # Example comparison
                latest_model = model

    if latest_model:
        model = aiplatform.Model(
            model_name=latest_model.resource_name)  # Or however you instantiate based on the listing
        print(model)
        return model
    else:
        print("No Gemini models found.")
        return None


def get_predictions(input_str):
    command = "Explain this "

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")  # Get project ID from environment
    vertexai.init(project=project_id, location="us-central1")

    generative_multimodal_model = GenerativeModel("gemini-2.0-flash-exp")
    response = generative_multimodal_model.generate_content(command + input_str)
    print(response.text)
    return response.text


# Windows (PowerShell):
# $env:GOOGLE_CLOUD_PROJECT="my-project-xxxx-xxxx"


if __name__ == '__main__':
    # get_model()
    input_str = """CME ERROR: 30"""
    get_predictions(input_str)
