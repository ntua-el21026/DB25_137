import React from "react";
import { Navigate } from "react-router-dom";

export default function ProtectedRoute({ children }) {
	const token = sessionStorage.getItem("token");
	const ts = parseInt(sessionStorage.getItem("token_ts"), 10);
	const maxAge = 15 * 60 * 1000; // 15 minutes in milliseconds
	const now = Date.now();
	const expired = !ts || now - ts > maxAge;

	if (!token || expired) {
		sessionStorage.clear(); // Expired or missing token
		return <Navigate to="/login" replace />;
	}

	return children;
}
