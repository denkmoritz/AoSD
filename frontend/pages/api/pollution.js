import axios from "axios";

export default async function handler(req, res) {
    const { timestamp } = req.query;
    
    try {
        const response = await axios.get(`http://127.0.0.1:8000/pollution/${timestamp}`);
        res.status(200).json(response.data);
    } catch (error) {
        console.error("API Proxy Error:", error);
        res.status(500).json({ error: "Failed to fetch pollution data" });
    }
}
