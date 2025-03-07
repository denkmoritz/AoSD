import axios from "axios";

export default async function handler(req, res) {
    const { timestamp } = req.query;

    if (!timestamp) {
        return res.status(400).json({ error: "Missing timestamp parameter" });
    }

    try {
        console.log(`🔄 Fetching Kriging data from FastAPI: http://127.0.0.1:8000/pollution/${timestamp}`);
        const response = await axios.get(`http://127.0.0.1:8000/pollution/${timestamp}`);

        console.log("✅ FastAPI Kriging Response:", response.data);
        res.status(200).json(response.data);
    } catch (error) {
        console.error("❌ Next.js API Proxy Error:", error.message);
        res.status(500).json({ error: "Failed to fetch pollution data" });
    }
}
