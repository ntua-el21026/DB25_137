// src/components/UserBadge.jsx
import React, { useEffect, useState } from "react";

export default function UserBadge() {
	const [username, setUsername] = useState("");

	useEffect(() => {
		const stored = sessionStorage.getItem("username");
		if (stored) setUsername(stored);
	}, []);

	if (!username) return null;

	return (
		<div className="absolute top-4 left-6 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-md text-sm font-semibold">
			Welcome, <span className="font-bold">{username}</span>!
		</div>
	);
}
