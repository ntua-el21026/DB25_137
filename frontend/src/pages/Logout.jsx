import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Logout() {
	const navigate = useNavigate();
	const [username, setUsername] = useState("");

	useEffect(() => {
		const name = sessionStorage.getItem("username");
		setUsername(name || "");
	}, []);

	useEffect(() => {
		if (username) {
			sessionStorage.clear();
		}
	}, [username]);

	const goToLogin = () => {
		navigate("/login", { replace: true });
	};

	return (
		<div className="flex flex-col items-center justify-center h-screen bg-gradient-to-br from-blue-50 to-blue-100 text-gray-700">
			<div className="text-center p-6 bg-white rounded-xl shadow-md w-80">
				<img
					src="/logo.jpg"
					alt="Pulse University Logo"
					className="h-20 w-20 mx-auto mb-4 rounded-full object-cover border border-blue-300 shadow-sm"
				/>
				<h2 className="text-xl font-semibold text-blue-700 mb-2">
					You have been logged out
				</h2>
				{username && (
					<p className="text-sm text-blue-700 mb-3">
						Goodbye from the DB137, <span className="font-medium">{username}</span>
					</p>
				)}
				<button
					onClick={goToLogin}
					className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
				>
					Go to Login
				</button>
			</div>
		</div>
	);
}
