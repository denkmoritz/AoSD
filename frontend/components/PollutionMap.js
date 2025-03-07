import React, { useState, useEffect, useRef } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet.heat";
import "leaflet/dist/leaflet.css";
import axios from "axios";

const HeatmapLayer = ({ data, maxIntensity }) => {
    const map = useMap();

    useEffect(() => {
        if (!map || !data.length) return;

        // ✅ Remove existing heatmap layers before adding a new one
        map.eachLayer((layer) => {
            if (layer instanceof L.HeatLayer) {
                map.removeLayer(layer);
            }
        });

        // ✅ Convert data to the format required by leaflet-heat
        const heatData = data.map((d) => [d[0], d[1], d[2] / maxIntensity]); // Normalize intensity

        // ✅ Create heatmap layer with fixed zoom behavior
        const heatLayer = L.heatLayer(heatData, {
            radius: 20,  // ✅ Fix radius to avoid extreme changes when zooming
            blur: 25,
            maxZoom: 14,
            minOpacity: 0.2,
            gradient: {
                0.1: "blue",
                0.3: "cyan",
                0.5: "lime",
                0.7: "yellow",
                1.0: "red",
            },
        });

        heatLayer.addTo(map);
    }, [map, data, maxIntensity]);

    return null;
};

// ✅ FIXED: Legend Always Visible & Rounded Values
const Legend = ({ min, max }) => {
    return (
        <div style={{
            position: "fixed",
            bottom: "20px",
            right: "20px",
            padding: "10px",
            backgroundColor: "rgba(255, 255, 255, 0.9)",
            borderRadius: "5px",
            fontSize: "12px",
            boxShadow: "0px 0px 5px rgba(0,0,0,0.5)",
            zIndex: 1000
        }}>
            <strong>NO₂ Concentration (µg/m³)</strong>
            <div style={{ display: "flex", alignItems: "center", marginTop: "5px" }}>
                <span style={{ marginRight: "5px" }}>{min.toFixed(3)}</span>
                <div style={{
                    width: "100px",
                    height: "10px",
                    background: "linear-gradient(to right, blue, cyan, lime, yellow, red)"
                }}></div>
                <span style={{ marginLeft: "5px" }}>{max.toFixed(3)}</span>
            </div>
        </div>
    );
};

const PollutionMap = () => {
    const [pollutionData, setPollutionData] = useState([]);
    const [timestamps, setTimestamps] = useState([]);
    const [formattedTimestamps, setFormattedTimestamps] = useState([]);
    const [currentTimestampIndex, setCurrentTimestampIndex] = useState(0);
    const [maxIntensity, setMaxIntensity] = useState(1);
    const [isAnimating, setIsAnimating] = useState(false);
    const animationRef = useRef(null);
    const dataRef = useRef({});
    const [currentTimestamp, setCurrentTimestamp] = useState(""); // ✅ Show correct timestamp

    const fetchLiveData = async () => {
        try {
            console.log("🔄 Fetching Live NO₂ Data...");
            const response = await axios.get("http://localhost:8000/pollution/live");

            if (response.data.status === "processing") {
                console.warn("⚠ Data is still processing. Try again later.");
                return;
            }

            // ✅ Store fetched data for animation
            dataRef.current = response.data;
            const newTimestamps = Object.keys(response.data);
            setTimestamps(newTimestamps);

            // ✅ Fetch formatted timestamps from backend
            const timestampsResponse = await axios.get("http://localhost:8000/pollution/timestamps");
            if (timestampsResponse.data.timestamps) {
                setFormattedTimestamps(timestampsResponse.data.timestamps);
            }

            // ✅ Find max pollution value for a consistent legend
            let maxPollution = 0;
            newTimestamps.forEach(ts => {
                const values = response.data[ts].map(d => d[2]);
                maxPollution = Math.max(maxPollution, ...values);
            });

            setMaxIntensity(maxPollution);

            // ✅ Set initial pollution data
            if (newTimestamps.length > 0) {
                setCurrentTimestamp(timestampsResponse.data.timestamps[0]);  // ✅ Show correct timestamp
                setPollutionData(response.data[newTimestamps[0]] || []);
            }

            console.log("✅ Live Data Updated:", response.data);
        } catch (error) {
            console.error("❌ Error fetching live pollution data:", error.message);
        }
    };

    useEffect(() => {
        fetchLiveData();
    }, []);

    const startAnimation = () => {
        if (!timestamps.length) return;

        setIsAnimating(true);
        animationRef.current = setInterval(() => {
            setCurrentTimestampIndex((prevIndex) => {
                const nextIndex = (prevIndex + 1) % timestamps.length;
                console.log(`🔄 Updating Heatmap to ${formattedTimestamps[nextIndex]}`);

                setCurrentTimestamp(formattedTimestamps[nextIndex]);  // ✅ Update the displayed timestamp
                setPollutionData(dataRef.current[timestamps[nextIndex]] || []);
                return nextIndex;
            });
        }, 2000);
    };

    const stopAnimation = () => {
        setIsAnimating(false);
        clearInterval(animationRef.current);
    };

    return (
        <div style={{ width: "100%", height: "90vh", position: "relative" }}>
            <h2>NO₂ Pollution Heatmap</h2>

            {/* ✅ Correct Timestamp Display */}
            <div style={{
                position: "fixed",
                top: "10px",
                right: "10px",
                padding: "8px",
                backgroundColor: "rgba(0, 0, 0, 0.7)",
                color: "white",
                borderRadius: "5px",
                fontSize: "16px",
                zIndex: 1000
            }}>
                <strong>Time:</strong> {currentTimestamp}
            </div>

            {/* ✅ Animation Controls */}
            <div>
                <button onClick={startAnimation} disabled={isAnimating}>▶ Start Animation</button>
                <button onClick={stopAnimation} disabled={!isAnimating}>⏹ Stop Animation</button>
            </div>

            {/* ✅ Map Container (Fixed Zoom Level) */}
            <MapContainer center={[35.6895, 139.6917]} zoom={11} style={{ height: "100%", width: "100%" }}>
                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                <HeatmapLayer data={pollutionData} maxIntensity={maxIntensity} />
            </MapContainer>

            {/* ✅ Legend is now fixed & always visible */}
            <Legend min={0} max={maxIntensity} />
        </div>
    );
};

export default PollutionMap;