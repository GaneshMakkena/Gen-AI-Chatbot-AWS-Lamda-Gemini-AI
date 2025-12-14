"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
    User, Heart, Pill, AlertTriangle, FileText,
    ChevronLeft, Trash2, Plus, Loader2, Shield, Clock
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

interface HealthProfile {
    user_id: string;
    conditions: Array<{ name: string; added_at: string; source: string }>;
    medications: Array<{ name: string; dosage: string; added_at: string }>;
    allergies: Array<{ name: string; added_at: string }>;
    blood_type: string;
    age: number | null;
    gender: string;
    key_facts: Array<{ text: string; added_at: string }>;
    report_summaries: Array<{ summary: string; report_type: string; added_at: string }>;
    last_updated: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://khucwqfzv4.execute-api.us-east-1.amazonaws.com/production";

export default function ProfilePage() {
    const [profile, setProfile] = useState<HealthProfile | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");

    const { isAuthenticated, user, getToken } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!isAuthenticated) {
            router.push("/login");
            return;
        }
        fetchProfile();
    }, [isAuthenticated]);

    async function fetchProfile() {
        try {
            const token = await getToken();
            if (!token) return;

            const response = await fetch(`${API_URL}/profile`, {
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                setProfile(data);
            } else {
                setError("Failed to load profile");
            }
        } catch (err) {
            setError("Failed to load profile");
        } finally {
            setIsLoading(false);
        }
    }

    async function removeCondition(conditionName: string) {
        try {
            const token = await getToken();
            if (!token) return;

            await fetch(`${API_URL}/profile/condition/${encodeURIComponent(conditionName)}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${token}` }
            });

            fetchProfile();
        } catch (err) {
            console.error("Failed to remove condition:", err);
        }
    }

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-900 via-indigo-800 to-purple-900 flex items-center justify-center">
                <Loader2 className="w-12 h-12 text-cyan-400 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
            {/* Header */}
            <header className="bg-slate-800/50 backdrop-blur-lg border-b border-slate-700/50 sticky top-0 z-50">
                <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-2 text-white hover:text-cyan-400 transition-colors">
                        <ChevronLeft className="w-5 h-5" />
                        <span>Back to Chat</span>
                    </Link>
                    <h1 className="text-xl font-bold text-white">Health Profile</h1>
                    <div className="w-24" /> {/* Spacer */}
                </div>
            </header>

            {/* Content */}
            <main className="max-w-4xl mx-auto px-4 py-8">
                {/* User Info Card */}
                <div className="bg-slate-800/50 backdrop-blur-lg rounded-2xl p-6 mb-6 border border-slate-700/50">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white text-2xl font-bold">
                            {user?.name?.charAt(0).toUpperCase() || "U"}
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold text-white">{user?.name}</h2>
                            <p className="text-slate-400">{user?.email}</p>
                        </div>
                    </div>

                    {/* Basic Info */}
                    <div className="grid grid-cols-3 gap-4 mt-4">
                        <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                            <p className="text-slate-400 text-xs mb-1">Age</p>
                            <p className="text-white font-medium">{profile?.age || "—"}</p>
                        </div>
                        <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                            <p className="text-slate-400 text-xs mb-1">Gender</p>
                            <p className="text-white font-medium">{profile?.gender || "—"}</p>
                        </div>
                        <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                            <p className="text-slate-400 text-xs mb-1">Blood Type</p>
                            <p className="text-white font-medium">{profile?.blood_type || "—"}</p>
                        </div>
                    </div>
                </div>

                {/* Conditions */}
                <section className="bg-slate-800/50 backdrop-blur-lg rounded-2xl p-6 mb-6 border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-4">
                        <Heart className="w-5 h-5 text-red-400" />
                        <h3 className="text-lg font-semibold text-white">Medical Conditions</h3>
                    </div>

                    {profile?.conditions && profile.conditions.length > 0 ? (
                        <div className="space-y-2">
                            {profile.conditions.map((condition, idx) => (
                                <div key={idx} className="flex items-center justify-between bg-slate-700/50 rounded-lg px-4 py-3">
                                    <div>
                                        <p className="text-white font-medium">
                                            {typeof condition === "string" ? condition : condition.name}
                                        </p>
                                        {typeof condition !== "string" && (
                                            <p className="text-slate-400 text-xs">
                                                Added from {condition.source} • {new Date(condition.added_at).toLocaleDateString()}
                                            </p>
                                        )}
                                    </div>
                                    <button
                                        onClick={() => removeCondition(typeof condition === "string" ? condition : condition.name)}
                                        className="p-2 text-slate-400 hover:text-red-400 transition-colors"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-slate-400 italic">No conditions recorded</p>
                    )}
                </section>

                {/* Medications */}
                <section className="bg-slate-800/50 backdrop-blur-lg rounded-2xl p-6 mb-6 border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-4">
                        <Pill className="w-5 h-5 text-blue-400" />
                        <h3 className="text-lg font-semibold text-white">Medications</h3>
                    </div>

                    {profile?.medications && profile.medications.length > 0 ? (
                        <div className="space-y-2">
                            {profile.medications.map((med, idx) => (
                                <div key={idx} className="bg-slate-700/50 rounded-lg px-4 py-3">
                                    <p className="text-white font-medium">
                                        {typeof med === "string" ? med : med.name}
                                        {typeof med !== "string" && med.dosage && (
                                            <span className="text-cyan-400 ml-2">{med.dosage}</span>
                                        )}
                                    </p>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-slate-400 italic">No medications recorded</p>
                    )}
                </section>

                {/* Allergies */}
                <section className="bg-slate-800/50 backdrop-blur-lg rounded-2xl p-6 mb-6 border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-4">
                        <AlertTriangle className="w-5 h-5 text-yellow-400" />
                        <h3 className="text-lg font-semibold text-white">Allergies</h3>
                    </div>

                    {profile?.allergies && profile.allergies.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                            {profile.allergies.map((allergy, idx) => (
                                <span key={idx} className="px-3 py-1.5 bg-yellow-500/20 text-yellow-300 rounded-full text-sm">
                                    {typeof allergy === "string" ? allergy : allergy.name}
                                </span>
                            ))}
                        </div>
                    ) : (
                        <p className="text-slate-400 italic">No allergies recorded</p>
                    )}
                </section>

                {/* Key Facts */}
                {profile?.key_facts && profile.key_facts.length > 0 && (
                    <section className="bg-slate-800/50 backdrop-blur-lg rounded-2xl p-6 mb-6 border border-slate-700/50">
                        <div className="flex items-center gap-2 mb-4">
                            <FileText className="w-5 h-5 text-purple-400" />
                            <h3 className="text-lg font-semibold text-white">Health Notes</h3>
                        </div>

                        <div className="space-y-2">
                            {profile.key_facts.map((fact, idx) => (
                                <div key={idx} className="bg-slate-700/50 rounded-lg px-4 py-3">
                                    <p className="text-white">
                                        {typeof fact === "string" ? fact : fact.text}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </section>
                )}

                {/* Privacy Notice */}
                <div className="flex items-start gap-3 p-4 bg-slate-800/30 rounded-xl border border-slate-700/30">
                    <Shield className="w-5 h-5 text-green-400 mt-0.5" />
                    <div>
                        <p className="text-slate-300 text-sm">
                            Your health information is encrypted and private. Only you can see this data.
                            It's used to provide personalized medical advice.
                        </p>
                        <p className="text-slate-500 text-xs mt-1">
                            <Clock className="w-3 h-3 inline mr-1" />
                            Last updated: {profile?.last_updated ? new Date(profile.last_updated).toLocaleString() : "Never"}
                        </p>
                    </div>
                </div>
            </main>
        </div>
    );
}
