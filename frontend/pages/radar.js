import dynamic from 'next/dynamic';
import React, { useState, useEffect, useRef } from "react";
import { useRouter } from 'next/router';
import "leaflet/dist/leaflet.css";
import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

// Dynamically import MapContainer and TileLayer with SSR disabled
const MapContainer = dynamic(
    () => import("react-leaflet").then((mod) => mod.MapContainer),
    { ssr: false }
);
const TileLayer = dynamic(
    () => import("react-leaflet").then((mod) => mod.TileLayer),
    { ssr: false }
);
const useMap = dynamic(
    () => import("react-leaflet").then((mod) => mod.useMap),
    { ssr: false }
);

// Dynamically import Leaflet and HeatmapLayer with SSR disabled
const L = dynamic(() => import("leaflet"), { ssr: false });
const HeatmapLayer = dynamic(() => import("../components/HeatmapLayer"), { ssr: false });

// ✅ Fixed & Always Visible Legend
const Legend = ({ min, max }) => {
    return (
        <div style={{
            position: "fixed",
            bottom: "20px",
            right: "20px",
            padding: "10px",
            backgroundColor: "rgba(0, 0, 0, 0.8)", // Dark mode background
            borderRadius: "5px",
            fontSize: "12px",
            boxShadow: "0px 0px 5px rgba(0,0,0,0.5)",
            zIndex: 1000,
            color: "#ffffff", // Dark mode text color
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

// ✅ Main Component
const PollutionRadar = () => {
    const router = useRouter();
    const [pollutionData, setPollutionData] = useState([]);
    const [timestamps, setTimestamps] = useState([]);
    const [formattedTimestamps, setFormattedTimestamps] = useState([]);
    const [currentTimestampIndex, setCurrentTimestampIndex] = useState(0);
    const [maxIntensity, setMaxIntensity] = useState(1);
    const [isAnimating, setIsAnimating] = useState(false);
    const animationRef = useRef(null);
    const dataRef = useRef({});
    const [currentTimestamp, setCurrentTimestamp] = useState("");

    // ✅ Disable scrolling while on radar page
    useEffect(() => {
        document.body.style.overflow = "hidden"; // Disable scrolling
        document.documentElement.style.overflow = "hidden"; // Disable scrolling on the html element
        return () => {
            document.body.style.overflow = "auto"; // Restore scrolling when leaving
            document.documentElement.style.overflow = "auto"; // Restore scrolling on the html element
        };
    }, []);

    const fetchLiveData = async () => {
        try {
            console.log("🔄 API BASE URL:", JSON.stringify(API_BASE_URL));
    
            // ✅ Ensure response is assigned before using it
            const response = await axios.get(`${API_BASE_URL}/pollution/live`);
    
            if (!response || !response.data) {
                throw new Error("Invalid response from the API.");
            }
    
            if (response.data.status === "processing") {
                console.warn("⚠ Data is still processing. Try again later.");
                return;
            }
    
            dataRef.current = response.data;
            const newTimestamps = Object.keys(response.data);
            setTimestamps(newTimestamps);
    
            // ✅ Ensure timestamps are fetched correctly
            const timestampsResponse = await axios.get(`${API_BASE_URL}/pollution/timestamps`);
            if (timestampsResponse.data && timestampsResponse.data.timestamps) {
                setFormattedTimestamps(timestampsResponse.data.timestamps);
            }
    
            let maxPollution = 0;
            newTimestamps.forEach(ts => {
                const values = response.data[ts].map(d => d[2]);
                maxPollution = Math.max(maxPollution, ...values);
            });
    
            setMaxIntensity(maxPollution);
    
            if (newTimestamps.length > 0) {
                setCurrentTimestamp(timestampsResponse.data.timestamps[0]);
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

    // ✅ Animation Logic
    const toggleAnimation = () => {
        if (isAnimating) {
            stopAnimation();
        } else {
            startAnimation();
        }
    };

    const startAnimation = () => {
        if (!timestamps.length) return;
        setIsAnimating(true);
        animationRef.current = setInterval(() => {
            setCurrentTimestampIndex((prevIndex) => {
                const nextIndex = (prevIndex + 1) % timestamps.length;
                console.log(`🔄 Updating Heatmap to ${formattedTimestamps[nextIndex]}`);

                setCurrentTimestamp(formattedTimestamps[nextIndex]);
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
        <div style={{ width: "100%", height: "100vh", position: "relative", backgroundColor: "#070b1d", color: "#ffffff" }}>
            {/* ✅ Display Correct Time */}
            <div style={{
                position: "absolute",
                top: "15px",
                right: "15px",
                background: "rgba(0,0,0,0.8)",
                color: "#fff",
                padding: "5px 15px",
                borderRadius: "5px",
                zIndex: 1000
            }}>
                <strong>Time:</strong> {currentTimestamp}
            </div>

            {/* ✅ Animation Control */}
            <div style={{
                position: "absolute",
                top: "15px",
                left: "50%",
                transform: "translateX(-50%)",
                zIndex: 1000,
            }}>
                <button
                    onClick={toggleAnimation}
                    style={{
                        backgroundColor: isAnimating ? "#dc3545" : "#0071ff",
                        color: "#fff",
                        border: "none",
                        padding: "10px 20px",
                        borderRadius: "5px",
                        cursor: "pointer"
                    }}
                >
                    {isAnimating ? "⏹ Stop Animation" : "▶ Start Animation"}
                </button>
            </div>

            {/* ✅ Map with Fixed Zoom */}
            {typeof window !== "undefined" && (
                <MapContainer
                    center={[35.6895, 139.6917]}
                    zoom={11}
                    style={{ height: "100vh", width: "100%", position: "absolute", top: 0, left: 0 }}
                >
                    {/* Dark-themed basemap */}
                    <TileLayer
                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    />
                    <HeatmapLayer data={pollutionData} maxIntensity={maxIntensity} />
                </MapContainer>
            )}

            {/* ✅ Always Visible Legend */}
            <Legend min={0} max={maxIntensity} />
        </div>
    );
};

export default PollutionRadar;