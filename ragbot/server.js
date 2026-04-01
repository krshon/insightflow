import express from "express";
import cors from "cors";
import fs from "fs";
import csv from "csv-parser";
import dotenv from "dotenv";
import { GoogleGenerativeAI } from "@google/generative-ai";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

const model = genAI.getGenerativeModel({
  model: "gemini-2.5-flash"
});

function readCSV(filePath) {
  return new Promise((resolve) => {
    const rows = [];

    fs.createReadStream(filePath)
      .pipe(csv())
      .on("data", (data) => rows.push(data))
      .on("end", () => resolve(rows));
  });
}

function analyzeDataset(rows) {

  const regionSales = {};
  const categoryProfit = {};
  const segmentSales = {};

  rows.forEach(row => {

    const region = row.Region;
    const category = row.Category;
    const segment = row.Segment;

    const sales = parseFloat(row.Sales || 0);
    const profit = parseFloat(row.Profit || 0);

    regionSales[region] = (regionSales[region] || 0) + sales;
    categoryProfit[category] = (categoryProfit[category] || 0) + profit;
    segmentSales[segment] = (segmentSales[segment] || 0) + sales;
  });

  return {
    totalRows: rows.length,
    regionSales,
    categoryProfit,
    segmentSales
  };
}

const rows = await readCSV("sales.csv");
const analytics = analyzeDataset(rows);

app.post("/ask", async (req, res) => {

  const question = req.body.question;

  const prompt = `
You are a professional business data analyst.

DATASET ANALYTICS SUMMARY:

Total Records:
${analytics.totalRows}

Region-wise Sales:
${JSON.stringify(analytics.regionSales)}

Category-wise Profit:
${JSON.stringify(analytics.categoryProfit)}

Segment-wise Sales:
${JSON.stringify(analytics.segmentSales)}

QUESTION:
${question}

Answer clearly with insights.
`;

  const result = await model.generateContent(prompt);

  res.json({
    answer: result.response.text()
  });

});

app.listen(3000, () =>
  console.log("Server running at http://localhost:3000")
);