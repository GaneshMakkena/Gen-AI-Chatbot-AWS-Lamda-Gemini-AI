"use client";

import { useState } from "react";
import Link from "next/link";
import { Mail, Lock, KeyRound, Loader2, AlertCircle, CheckCircle, Stethoscope, ArrowLeft } from "lucide-react";
import {
    CognitoUserPool,
    CognitoUser,
} from "amazon-cognito-identity-js";

// Cognito config will be fetched from API
const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://khucwqfzv4.execute-api.us-east-1.amazonaws.com/production";

export default function ForgotPasswordPage() {
    const [step, setStep] = useState<"email" | "code" | "success">("email");
    const [email, setEmail] = useState("");
    const [code, setCode] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [cognitoUser, setCognitoUser] = useState<CognitoUser | null>(null);

    async function handleSendCode(e: React.FormEvent) {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        try {
            // Fetch Cognito config
            const configResponse = await fetch(`${API_URL}/auth/config`);
            if (!configResponse.ok) throw new Error("Failed to get auth config");
            const config = await configResponse.json();

            const userPool = new CognitoUserPool({
                UserPoolId: config.userPoolId,
                ClientId: config.clientId,
            });

            const user = new CognitoUser({
                Username: email,
                Pool: userPool,
            });

            setCognitoUser(user);

            user.forgotPassword({
                onSuccess: () => {
                    setStep("code");
                    setIsLoading(false);
                },
                onFailure: (err) => {
                    setError(err.message || "Failed to send reset code");
                    setIsLoading(false);
                },
                inputVerificationCode: () => {
                    setStep("code");
                    setIsLoading(false);
                },
            });
        } catch (err: any) {
            setError(err.message || "Failed to send reset code");
            setIsLoading(false);
        }
    }

    async function handleResetPassword(e: React.FormEvent) {
        e.preventDefault();
        setError("");

        if (newPassword !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        if (newPassword.length < 8) {
            setError("Password must be at least 8 characters");
            return;
        }

        if (!cognitoUser) {
            setError("Session expired. Please start over.");
            return;
        }

        setIsLoading(true);

        cognitoUser.confirmPassword(code, newPassword, {
            onSuccess: () => {
                setStep("success");
                setIsLoading(false);
            },
            onFailure: (err) => {
                setError(err.message || "Failed to reset password");
                setIsLoading(false);
            },
        });
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-900 via-indigo-800 to-purple-900 flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/10 backdrop-blur-lg mb-4">
                        <Stethoscope className="w-8 h-8 text-cyan-400" />
                    </div>
                    <h1 className="text-3xl font-bold text-white mb-2">
                        {step === "success" ? "Password Reset!" : "Reset Password"}
                    </h1>
                    <p className="text-white/70">
                        {step === "email" && "Enter your email to receive a reset code"}
                        {step === "code" && "Enter the code sent to your email"}
                        {step === "success" && "Your password has been updated"}
                    </p>
                </div>

                {/* Form */}
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 shadow-2xl border border-white/20">
                    {/* Error Message */}
                    {error && (
                        <div className="flex items-center gap-2 p-3 mb-6 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200">
                            <AlertCircle className="w-5 h-5 flex-shrink-0" />
                            <span className="text-sm">{error}</span>
                        </div>
                    )}

                    {/* Step 1: Email */}
                    {step === "email" && (
                        <form onSubmit={handleSendCode} className="space-y-6">
                            <div>
                                <label className="block text-white/80 text-sm font-medium mb-2">
                                    Email Address
                                </label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/50" />
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-full pl-11 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
                                        placeholder="you@example.com"
                                        required
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={isLoading}
                                className="w-full py-3 px-4 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-semibold rounded-lg shadow-lg transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Sending...
                                    </>
                                ) : (
                                    <>
                                        <Mail className="w-5 h-5" />
                                        Send Reset Code
                                    </>
                                )}
                            </button>
                        </form>
                    )}

                    {/* Step 2: Code + New Password */}
                    {step === "code" && (
                        <form onSubmit={handleResetPassword} className="space-y-6">
                            <div>
                                <label className="block text-white/80 text-sm font-medium mb-2">
                                    Verification Code
                                </label>
                                <div className="relative">
                                    <KeyRound className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/50" />
                                    <input
                                        type="text"
                                        value={code}
                                        onChange={(e) => setCode(e.target.value)}
                                        className="w-full pl-11 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
                                        placeholder="Enter 6-digit code"
                                        required
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-white/80 text-sm font-medium mb-2">
                                    New Password
                                </label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/50" />
                                    <input
                                        type="password"
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                        className="w-full pl-11 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
                                        placeholder="••••••••"
                                        required
                                        minLength={8}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-white/80 text-sm font-medium mb-2">
                                    Confirm Password
                                </label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/50" />
                                    <input
                                        type="password"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        className="w-full pl-11 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
                                        placeholder="••••••••"
                                        required
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={isLoading}
                                className="w-full py-3 px-4 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-semibold rounded-lg shadow-lg transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Resetting...
                                    </>
                                ) : (
                                    "Reset Password"
                                )}
                            </button>

                            <button
                                type="button"
                                onClick={() => setStep("email")}
                                className="w-full text-white/50 hover:text-white/70 text-sm"
                            >
                                ← Back to email
                            </button>
                        </form>
                    )}

                    {/* Step 3: Success */}
                    {step === "success" && (
                        <div className="text-center py-4">
                            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/20 mb-4">
                                <CheckCircle className="w-8 h-8 text-emerald-400" />
                            </div>
                            <p className="text-white/80 mb-6">
                                Your password has been successfully reset.
                            </p>
                            <Link
                                href="/login"
                                className="inline-flex items-center gap-2 py-3 px-6 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-semibold rounded-lg shadow-lg transition-all"
                            >
                                <ArrowLeft className="w-5 h-5" />
                                Back to Login
                            </Link>
                        </div>
                    )}

                    {/* Back to Login */}
                    {step !== "success" && (
                        <div className="mt-6 text-center">
                            <Link href="/login" className="text-white/50 hover:text-white/70 text-sm">
                                ← Back to Login
                            </Link>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
