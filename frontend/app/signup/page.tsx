"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { Mail, Lock, User, UserPlus, Loader2, AlertCircle, Stethoscope, CheckCircle, Eye, EyeOff } from "lucide-react";

export default function SignupPage() {
    const [step, setStep] = useState<"signup" | "confirm">("signup");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [name, setName] = useState("");
    const [code, setCode] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const { signup, confirmSignup, login } = useAuth();
    const router = useRouter();

    async function handleSignup(e: React.FormEvent) {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        try {
            await signup(email, password, name);
            setStep("confirm");
        } catch (err: any) {
            setError(err.message || "Signup failed. Please try again.");
        } finally {
            setIsLoading(false);
        }
    }

    async function handleConfirm(e: React.FormEvent) {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        try {
            await confirmSignup(email, code);
            // Auto-login after confirmation
            await login(email, password);
            router.push("/");
        } catch (err: any) {
            setError(err.message || "Confirmation failed. Please try again.");
        } finally {
            setIsLoading(false);
        }
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
                        {step === "signup" ? "Create Account" : "Verify Email"}
                    </h1>
                    <p className="text-white/70">
                        {step === "signup"
                            ? "Join MediBot for personalized health assistance"
                            : "Enter the verification code sent to your email"}
                    </p>
                </div>

                {/* Form Card */}
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 shadow-2xl border border-white/20">
                    {step === "signup" ? (
                        <form onSubmit={handleSignup} className="space-y-6">
                            {/* Error Message */}
                            {error && (
                                <div className="flex items-center gap-2 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200">
                                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                                    <span className="text-sm">{error}</span>
                                </div>
                            )}

                            {/* Name Input */}
                            <div>
                                <label className="block text-white/80 text-sm font-medium mb-2">
                                    Full Name
                                </label>
                                <div className="relative">
                                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/50" />
                                    <input
                                        type="text"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        className="w-full pl-11 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
                                        placeholder="John Doe"
                                        required
                                    />
                                </div>
                            </div>

                            {/* Email Input */}
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

                            <div>
                                <label className="block text-white/80 text-sm font-medium mb-2">
                                    Password
                                </label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/50" />
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="w-full pl-11 pr-12 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
                                        placeholder="••••••••"
                                        required
                                        minLength={8}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/50 hover:text-white/80"
                                    >
                                        {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                    </button>
                                </div>
                                <p className="mt-1 text-white/50 text-xs">
                                    At least 8 characters with uppercase, lowercase, and number
                                </p>
                            </div>

                            {/* Submit Button */}
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="w-full py-3 px-4 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-semibold rounded-lg shadow-lg transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Creating account...
                                    </>
                                ) : (
                                    <>
                                        <UserPlus className="w-5 h-5" />
                                        Create Account
                                    </>
                                )}
                            </button>
                        </form>
                    ) : (
                        <form onSubmit={handleConfirm} className="space-y-6">
                            {/* Success Message */}
                            <div className="flex items-center gap-2 p-3 bg-green-500/20 border border-green-500/50 rounded-lg text-green-200">
                                <CheckCircle className="w-5 h-5 flex-shrink-0" />
                                <span className="text-sm">Verification code sent to {email}</span>
                            </div>

                            {/* Error Message */}
                            {error && (
                                <div className="flex items-center gap-2 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200">
                                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                                    <span className="text-sm">{error}</span>
                                </div>
                            )}

                            {/* Verification Code Input */}
                            <div>
                                <label className="block text-white/80 text-sm font-medium mb-2">
                                    Verification Code
                                </label>
                                <input
                                    type="text"
                                    value={code}
                                    onChange={(e) => setCode(e.target.value)}
                                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white text-center text-2xl tracking-widest placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
                                    placeholder="000000"
                                    required
                                    maxLength={6}
                                />
                            </div>

                            {/* Submit Button */}
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="w-full py-3 px-4 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-semibold rounded-lg shadow-lg transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Verifying...
                                    </>
                                ) : (
                                    <>
                                        <CheckCircle className="w-5 h-5" />
                                        Verify & Sign In
                                    </>
                                )}
                            </button>
                        </form>
                    )}

                    {/* Login Link */}
                    <div className="mt-6 text-center">
                        <p className="text-white/70">
                            Already have an account?{" "}
                            <Link href="/login" className="text-cyan-400 hover:text-cyan-300 font-medium">
                                Sign in
                            </Link>
                        </p>
                    </div>

                    {/* Back to Home */}
                    <div className="mt-4 text-center">
                        <Link href="/" className="text-white/50 hover:text-white/70 text-sm">
                            ← Back to MediBot
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
