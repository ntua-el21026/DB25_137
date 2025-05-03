import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {
	const [username, setUsername] = useState("");
	const [password, setPassword] = useState("");
	const [error, setError] = useState("");
	const [showPassword, setShowPassword] = useState(false);
	const navigate = useNavigate();

	const handleLogin = async (e) => {
		e.preventDefault();
		setError("");

		try {
			const res = await fetch("http://localhost:8000/api/login", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ username, password })
			});

			const data = await res.json();

			if (!res.ok || !data.token) {
				throw new Error(data.error || "Login failed");
			}

			sessionStorage.setItem("token", data.token);
			sessionStorage.setItem("username", username);
			sessionStorage.setItem("token_ts", Date.now().toString());
			navigate("/");
		} catch (err) {
			setError(err.message);
		}
	};

	const handleKeyPress = (e) => {
		if (e.key === "Enter") {
			handleLogin(e);
		}
	};

	return (
		<div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-sky-100 to-blue-200">
			<form onSubmit={handleLogin} className="bg-white shadow-lg rounded-xl px-8 py-6 w-96">
				<img src="/logo.jpg" alt="Pulse University Logo" className="h-20 w-20 mx-auto mb-4 rounded-full object-cover border border-blue-300 shadow-sm" />

				<h2 className="text-2xl font-bold text-center mb-2 text-blue-700">
					DB137
				</h2>
				<h2 className="text-2xl font-bold text-center mb-6 text-blue-700">
					Pulse University Database
				</h2>

				{error && <p className="text-red-600 text-sm mb-4 text-center">{error}</p>}

				<label className="block mb-2 text-sm font-semibold">Username</label>
				<input
					type="text"
					value={username}
					onChange={(e) => setUsername(e.target.value)}
					required
					className="w-full px-3 py-2 mb-4 border border-gray-300 rounded focus:outline-none focus:ring focus:ring-blue-300"
				/>

				<label className="block mb-2 text-sm font-semibold">Password</label>
				<div className="relative mb-6">
					<input
						type={showPassword ? "text" : "password"}
						value={password}
						onChange={(e) => setPassword(e.target.value)}
						onKeyDown={handleKeyPress}
						required
						className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring focus:ring-blue-300 pr-10"
					/>
					<button
						type="button"
						onClick={() => setShowPassword(!showPassword)}
						className="absolute top-1/2 right-2 -translate-y-1/2 text-sm text-gray-500 hover:text-gray-700"
						tabIndex={-1}
					>
						{showPassword ? "🙈" : "👁️"}
					</button>
				</div>

				<button
					type="submit"
					className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded transition"
				>
					Log In
				</button>
			</form>
		</div>
	);
}
