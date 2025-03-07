import React from "react";
import { useRouter } from "next/router";
import Image from "next/image";

const Home = () => {
  const router = useRouter();

  return (
    <div
      style={{
        width: "100%",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        padding: "20px",
        fontFamily: "Arial, sans-serif",
        backgroundColor: "#070b1d", // Dark mode background
        color: "#ffffff", // Dark mode text color
      }}
    >
      <h1 style={{ fontSize: "2.5rem", marginBottom: "20px", fontWeight: "bold" }}>
        NO₂ Pollution Forecasting & Visualization
      </h1>

      <p
        style={{
          maxWidth: "800px",
          fontSize: "1.2rem",
          lineHeight: "1.6",
          marginBottom: "30px",
          color: "#a4a5b8", // Dark mode secondary text color
        }}
      >
        This project provides a <strong>real-time visualization</strong> of NO₂ pollution levels across Tokyo’s special wards using data from{" "}
        <strong>OpenAQ</strong> and <strong>OpenWeather</strong>. The pollution radar{" "}
        <strong>interpolates sensor data</strong> using <strong>geostatistical Kriging</strong> to generate a smooth pollution heatmap. Additionally, the system predicts{" "}
        <strong>future NO₂ levels</strong> for the next <strong>four hours</strong> based on weather and time-related patterns.
      </p>

      <h3>🔍 Key Features</h3>
      <ul
        style={{
          textAlign: "left",
          maxWidth: "600px",
          margin: "20px auto",
          fontSize: "1.1rem",
          lineHeight: "1.8",
          color: "#a4a5b8", // Dark mode secondary text color
        }}
      >
        <li>
          <strong>📡 Live NO₂ Data:</strong> Real-time pollution data from Tokyo’s sensor network.
        </li>
        <li>
          <strong>📊 Kriging Interpolation:</strong> Generates smooth pollution heatmaps.
        </li>
        <li>
          <strong>🔮 Future Predictions:</strong> Forecasts NO₂ levels for the next <strong>four hours</strong>.
        </li>
        <li>
          <strong>🕹️ Interactive Visualization:</strong> Explore air pollution dynamics over time.
        </li>
      </ul>

      <h3>📡 NO₂ Monitoring Stations in Tokyo</h3>
      <div style={{ margin: "20px 0" }}>
        <Image
          src="/no2_station_map.png"
          alt="NO₂ Monitoring Stations Distribution in Tokyo"
          width={600}
          height={400}
          style={{ borderRadius: "10px", boxShadow: "0px 0px 10px rgba(0,0,0,0.2)" }}
        />
      </div>

      <h3>📚 Data Sources & Attribution</h3>
      <p
        style={{
          maxWidth: "800px",
          fontSize: "1rem",
          lineHeight: "1.5",
          color: "#a4a5b8", // Dark mode secondary text color
        }}
      >
        - <strong>OpenAQ API</strong>: Aggregates real-time air quality data from public and governmental sources. Users must comply with OpenAQ’s{" "}
        <a href="https://openaq.org/" target="_blank" rel="noopener noreferrer" style={{ color: "#0071ff" }}>
          terms of use
        </a>
        .<br />
        - <strong>OpenWeather API</strong>: Provides meteorological data essential for NO₂ forecasting. Data usage must be credited per OpenWeather’s{" "}
        <a href="https://openweathermap.org/" target="_blank" rel="noopener noreferrer" style={{ color: "#0071ff" }}>
          attribution policy
        </a>
        .
      </p>

      <h3>📖 Research Basis</h3>
      <p
        style={{
          maxWidth: "800px",
          fontSize: "1rem",
          lineHeight: "1.5",
          color: "#a4a5b8", // Dark mode secondary text color
        }}
      >
        The prediction model is inspired by <strong>"BACK TO THE FUTURE: GNN-BASED NO₂ FORECASTING VIA FUTURE COVARIATES"</strong> by{" "}
        <strong>Antonio Giganti et al.</strong>. The methodology incorporates <strong>past and future covariates</strong> (e.g., weather forecasts, time of day) using a{" "}
        <strong>Spatiotemporal Graph Neural Network (STGNN)</strong> to enhance forecasting accuracy.
      </p>

      <button
        onClick={() => router.push("/radar")}
        style={{
          marginTop: "30px",
          padding: "12px 24px",
          fontSize: "1.2rem",
          backgroundColor: "#0071ff", // Dark mode button color
          color: "white",
          border: "none",
          borderRadius: "5px",
          cursor: "pointer",
          transition: "background 0.3s",
        }}
      >
        🌍 Explore the NO₂ Pollution Radar
      </button>
    </div>
  );
};

export default Home;