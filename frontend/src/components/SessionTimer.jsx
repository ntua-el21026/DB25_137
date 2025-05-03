import React, { useEffect, useState } from "react";

const SESSION_TIMEOUT_MS = 15 * 60 * 1000; // 15 minutes

export default function SessionTimer() {
	const [timeLeft, setTimeLeft] = useState(SESSION_TIMEOUT_MS / 1000);

	useEffect(() => {
		// Decrease timer every second
		const interval = setInterval(() => {
			setTimeLeft((prev) => {
				if (prev <= 1) {
					sessionStorage.clear();
					window.location.href = "/login";
					return 0;
				}
				return prev - 1;
			});
		}, 1000);

		return () => clearInterval(interval);
	}, []);

	const refreshSession = () => {
		setTimeLeft(SESSION_TIMEOUT_MS / 1000);
	};

	const formatTime = (seconds) => {
		const m = Math.floor(seconds / 60);
		const s = seconds % 60;
		return `${m}:${s.toString().padStart(2, "0")}`;
	};

	return (
		<div className="fixed bottom-4 right-4 bg-white shadow-lg border border-blue-200 p-3 rounded-lg text-sm text-gray-700 flex items-center gap-3 z-20">
			<span>Session expires in: <strong>{formatTime(timeLeft)}</strong></span>
			<button
				onClick={refreshSession}
				className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600 transition"
			>
				Refresh
			</button>
		</div>
	);
}
