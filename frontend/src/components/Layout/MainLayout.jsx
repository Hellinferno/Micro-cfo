import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

const MainLayout = () => {
    return (
        <div className="flex h-screen bg-slate-50 overflow-hidden">
            {/* Sidebar - Fixed width handled internally */}
            <Sidebar />

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col h-full relative overflow-hidden w-full lg:w-auto">
                <div className="flex-1 overflow-y-auto overflow-x-hidden">
                    <Outlet />
                </div>
            </main>
        </div>
    );
};

export default MainLayout;
