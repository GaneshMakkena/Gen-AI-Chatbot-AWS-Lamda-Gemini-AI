import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuthenticator } from '@aws-amplify/ui-react';
import { MessageSquare, User, FileText, Upload, LogOut, PlusCircle } from 'lucide-react';
import './Layout.css';

export function Layout() {
    const { signOut, user, authStatus } = useAuthenticator((context) => [context.user, context.authStatus]);
    const navigate = useNavigate();
    const isAuthenticated = authStatus === 'authenticated';

    const handleNewChat = () => {
        navigate('/chat');
    };

    const handleLogin = () => {
        navigate('/login');
    };

    return (
        <div className="app-layout">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <div className="app-logo">🏥 MediBot</div>
                </div>

                <button className="new-chat-btn" onClick={handleNewChat}>
                    <PlusCircle size={20} />
                    New Chat
                </button>

                <nav className="sidebar-nav">
                    <NavLink to="/chat" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
                        <MessageSquare size={20} />
                        Chat
                    </NavLink>

                    {isAuthenticated && (
                        <>
                            <NavLink to="/history" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
                                <FileText size={20} />
                                History
                            </NavLink>
                            <NavLink to="/profile" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
                                <User size={20} />
                                Profile
                            </NavLink>
                            <NavLink to="/upload" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
                                <Upload size={20} />
                                Upload Report
                            </NavLink>
                        </>
                    )}
                </nav>

                <div className="sidebar-footer">
                    {isAuthenticated ? (
                        <>
                            <div className="user-info">
                                <div className="user-avatar">{user?.signInDetails?.loginId?.charAt(0).toUpperCase() || user?.username?.charAt(0).toUpperCase()}</div>
                                <div className="user-name">{user?.signInDetails?.loginId || user?.username}</div>
                            </div>
                            <button className="sign-out-btn" onClick={signOut} title="Sign Out">
                                <LogOut size={18} />
                            </button>
                        </>
                    ) : (
                        <button className="sign-out-btn login-btn" onClick={handleLogin} style={{ width: '100%', justifyContent: 'center' }}>
                            <User size={18} style={{ marginRight: '8px' }} />
                            Sign In / Sign Up
                        </button>
                    )}
                </div>
            </aside>

            <main className="main-content" id="main-content">
                <Outlet />
            </main>
        </div>
    );
}
