import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Logout from "./pages/Logout";
import Main from "./pages/Main";
import NotFound from "./pages/NotFound";
import ProtectedRoute from "./auth/ProtectedRoute";

const isAuthenticated = () => {
	return !!localStorage.getItem("token");
};

export default function App() {
	return (
		<BrowserRouter>
			<Routes>
				{/* Always allow access to login and logout */}
				<Route path="/login" element={<Login />} />
				<Route path="/logout" element={<Logout />} />

				{/* Protect main app route */}
				<Route
					path="/"
					element={
						<ProtectedRoute>
							<Main />
						</ProtectedRoute>
					}
				/>

				{/* Fallback */}
				<Route path="*" element={<NotFound />} />
			</Routes>
		</BrowserRouter>
	);
}
