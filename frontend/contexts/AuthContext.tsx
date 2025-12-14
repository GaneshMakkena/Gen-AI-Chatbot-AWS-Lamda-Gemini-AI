"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import {
    CognitoUserPool,
    CognitoUser,
    AuthenticationDetails,
    CognitoUserAttribute,
} from "amazon-cognito-identity-js";

// Types
interface User {
    userId: string;
    email: string;
    name: string;
}

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    signup: (email: string, password: string, name: string) => Promise<void>;
    confirmSignup: (email: string, code: string) => Promise<void>;
    logout: () => void;
    getToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Cognito configuration - will be fetched from API
let userPool: CognitoUserPool | null = null;

async function initCognito() {
    if (userPool) return userPool;

    try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://khucwqfzv4.execute-api.us-east-1.amazonaws.com/production";
        const response = await fetch(`${API_URL}/auth/config`);
        const config = await response.json();

        userPool = new CognitoUserPool({
            UserPoolId: config.userPoolId,
            ClientId: config.clientId,
        });

        return userPool;
    } catch (error) {
        console.error("Failed to init Cognito:", error);
        return null;
    }
}

// Provider Component
export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Check for existing session on mount
    useEffect(() => {
        checkSession();
    }, []);

    async function checkSession() {
        try {
            const pool = await initCognito();
            if (!pool) {
                setIsLoading(false);
                return;
            }

            const cognitoUser = pool.getCurrentUser();
            if (cognitoUser) {
                cognitoUser.getSession((err: Error | null, session: any) => {
                    if (err || !session?.isValid()) {
                        setUser(null);
                    } else {
                        // Get user attributes
                        cognitoUser.getUserAttributes((attrErr, attributes) => {
                            if (attrErr) {
                                console.error("Failed to get user attributes:", attrErr);
                                setUser(null);
                            } else {
                                const email = attributes?.find(a => a.Name === "email")?.Value || "";
                                const name = attributes?.find(a => a.Name === "name")?.Value || email.split("@")[0];
                                setUser({
                                    userId: cognitoUser.getUsername(),
                                    email,
                                    name,
                                });
                            }
                            setIsLoading(false);
                        });
                    }
                });
            } else {
                setIsLoading(false);
            }
        } catch (error) {
            console.error("Session check failed:", error);
            setIsLoading(false);
        }
    }

    async function login(email: string, password: string): Promise<void> {
        const pool = await initCognito();
        if (!pool) throw new Error("Authentication not available");

        return new Promise((resolve, reject) => {
            const cognitoUser = new CognitoUser({
                Username: email,
                Pool: pool,
            });

            const authDetails = new AuthenticationDetails({
                Username: email,
                Password: password,
            });

            cognitoUser.authenticateUser(authDetails, {
                onSuccess: (result) => {
                    cognitoUser.getUserAttributes((err, attributes) => {
                        const userName = attributes?.find(a => a.Name === "name")?.Value || email.split("@")[0];
                        setUser({
                            userId: cognitoUser.getUsername(),
                            email,
                            name: userName,
                        });
                        resolve();
                    });
                },
                onFailure: (err) => {
                    reject(new Error(err.message || "Login failed"));
                },
                newPasswordRequired: () => {
                    reject(new Error("New password required"));
                },
            });
        });
    }

    async function signup(email: string, password: string, name: string): Promise<void> {
        const pool = await initCognito();
        if (!pool) throw new Error("Authentication not available");

        return new Promise((resolve, reject) => {
            const attributeList = [
                new CognitoUserAttribute({ Name: "email", Value: email }),
                new CognitoUserAttribute({ Name: "name", Value: name }),
            ];

            pool.signUp(email, password, attributeList, [], (err, result) => {
                if (err) {
                    reject(new Error(err.message || "Signup failed"));
                } else {
                    resolve();
                }
            });
        });
    }

    async function confirmSignup(email: string, code: string): Promise<void> {
        const pool = await initCognito();
        if (!pool) throw new Error("Authentication not available");

        return new Promise((resolve, reject) => {
            const cognitoUser = new CognitoUser({
                Username: email,
                Pool: pool,
            });

            cognitoUser.confirmRegistration(code, true, (err, result) => {
                if (err) {
                    reject(new Error(err.message || "Confirmation failed"));
                } else {
                    resolve();
                }
            });
        });
    }

    function logout() {
        if (userPool) {
            const cognitoUser = userPool.getCurrentUser();
            if (cognitoUser) {
                cognitoUser.signOut();
            }
        }
        setUser(null);
    }

    async function getToken(): Promise<string | null> {
        const pool = await initCognito();
        if (!pool) return null;

        return new Promise((resolve) => {
            const cognitoUser = pool.getCurrentUser();
            if (!cognitoUser) {
                resolve(null);
                return;
            }

            cognitoUser.getSession((err: Error | null, session: any) => {
                if (err || !session?.isValid()) {
                    resolve(null);
                } else {
                    resolve(session.getIdToken().getJwtToken());
                }
            });
        });
    }

    return (
        <AuthContext.Provider
            value={{
                user,
                isAuthenticated: !!user,
                isLoading,
                login,
                signup,
                confirmSignup,
                logout,
                getToken,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

// Hook to use auth context
export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
