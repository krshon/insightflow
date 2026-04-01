import fs from "fs";
import csv from "csv-parser";
import dotenv from "dotenv";
import { GoogleGenerativeAI } from "@google/generative-ai";

dotenv.config();

// Initialize Gemini
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

const model = genAI.getGenerativeModel({
  model: "gemini-2.5-flash"
});

// Load CSV
function readCSV(filePath) {
  return new Promise((resolve) => {
    const rows = [];

    fs.createReadStream(filePath)
      .pipe(csv())
      .on("data", (data) => rows.push(data))
      .on("end", () => {
        resolve(JSON.stringify(rows.slice(0, 200))); 
        // limit rows so Gemini works faster
      });
  });
}

// Ask Gemini
async function askQuestion(question) {

  const csvData = await readCSV("sales.csv");

  const prompt = `
You are a data analyst assistant.

Answer ONLY using this dataset.

DATA:
${csvData}

QUESTION:
${question}

Also give short insight if possible.
`;

  const result = await model.generateContent(prompt);

  console.log("\nAnswer:\n");
  console.log(result.response.text());
}

// Example question
askQuestion("Which region has highest sales?");