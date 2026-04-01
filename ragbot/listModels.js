import dotenv from "dotenv";

dotenv.config();

async function listModels() {
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1/models?key=${process.env.GEMINI_API_KEY}`
  );

  const data = await response.json();

  if (!data.models) {
    console.log("No models returned. Check API key.");
    return;
  }

  console.log("\nAvailable Gemini models:\n");

  data.models.forEach((model) => {
    console.log(model.name);
  });
}

listModels();