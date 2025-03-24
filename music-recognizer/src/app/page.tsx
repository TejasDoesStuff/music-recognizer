"use client";

import { useState } from "react";
import Image from "next/image";

export default function Home() {
  const [link, setLink] = useState("");
  const [loading, setLoading] = useState(false);
  const [spectrogram, setSpectrogram] = useState(null);

  const handleUpload = async () => {
    if (!link) {
      alert("Please enter a link!");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/download_audio", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ link }),
      });

      const data = await response.json();
      console.log(data);

      setSpectrogram(data.spectrogram);

    } catch (error) {
      console.error("Error uploading link:", error);
      alert("An error occurred while processing the link.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen w-full p-6 bg-gradient-to-b from-gray-900 to-black">
      <div className="max-w-md w-full flex flex-col items-center gap-12">
        <h1 className="text-5xl font-bold text-white text-center drop-shadow-[0_0_10px_rgba(255,255,255,0.5)]">
          Music Recognizer
        </h1>

        <div
          className="bg-gradient-to-r from-blue-600 to-blue-500 rounded-full p-8 aspect-square flex justify-center items-center drop-shadow-[0_0_25px_rgba(59,130,246,0.6)] hover:scale-105 hover:drop-shadow-[0_0_30px_rgba(59,130,246,0.8)] transition-all duration-300 ease-in-out cursor-pointer"
          onClick={() => console.log("Recognize")}
        >
          <h2 className="text-xl font-bold text-white">Listen</h2>
        </div>

        <div className="w-full flex flex-col items-center gap-2">
          <label
            className="text-white font-medium drop-shadow-[0_0_5px_rgba(255,255,255,0.5)]"
            htmlFor="textbox"
          >
            Upload new song:
          </label>
          <input
            className="bg-gray-800/50 border border-gray-700 rounded-lg text-white w-full h-12 px-4 backdrop-blur-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
            type="text"
            id="textbox"
            name="textbox"
            placeholder="Input YouTube/Spotify link..."
            value={link}
            onChange={(e) => setLink(e.target.value)}
          />
          <button
            className="cursor-pointer w-1/3 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-all duration-300 ease-in-out drop-shadow-[0_0_25px_rgba(59,130,246,0.6)] hover:drop-shadow-[0_0_30px_rgba(59,130,246,0.8)]"
            onClick={handleUpload}
            disabled={loading}
          >
            {loading ? "Uploading..." : "Upload"}
          </button>
        </div>
        {spectrogram && (
        <div className="mt-6">
          <h2 className="text-xl font-bold text-white">Spectrogram</h2>
          <Image
            src={`data:image/png;base64,${spectrogram}`}
            alt="Spectrogram"
            className="mt-4"
            width={1024}
            height={512}
          />
        </div>
      )}
      </div>
    </div>
  );
}
