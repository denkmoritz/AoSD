// components/HeatmapLayer.js
import { useEffect } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet.heat";

const HeatmapLayer = ({ data, maxIntensity }) => {
    const map = useMap();

    useEffect(() => {
        if (!map || !data.length) return;

        // Remove existing heatmap layers before adding a new one
        map.eachLayer((layer) => {
            if (layer instanceof L.HeatLayer) {
                map.removeLayer(layer);
            }
        });

        // Normalize intensity values for consistent coloring
        const heatData = data.map((d) => [d[0], d[1], d[2] / maxIntensity]);

        const heatLayer = L.heatLayer(heatData, {
            radius: 20,
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

export default HeatmapLayer;