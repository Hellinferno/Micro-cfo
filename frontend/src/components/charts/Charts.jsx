import React from 'react';
import { clsx } from 'clsx';
import {
    LineChart,
    Line,
    AreaChart,
    Area,
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';

// Health Score Gauge Component
export const HealthScoreGauge = ({ score = 0, size = 200 }) => {
    const getColor = (score) => {
        if (score < 40) return '#DC2626'; // Red
        if (score < 70) return '#F59E0B'; // Amber
        return '#16A34A'; // Green
    };

    const getLabel = (score) => {
        if (score < 40) return 'Critical';
        if (score < 70) return 'Needs Attention';
        return 'Healthy';
    };

    const color = getColor(score);
    const circumference = 2 * Math.PI * 70;
    const strokeDashoffset = circumference - (score / 100) * circumference * 0.75;

    return (
        <div className="relative" style={{ width: size, height: size }}>
            <svg viewBox="0 0 160 160" className="w-full h-full transform -rotate-135">
                {/* Background arc */}
                <circle
                    cx="80"
                    cy="80"
                    r="70"
                    fill="none"
                    stroke="#E2E8F0"
                    strokeWidth="12"
                    strokeDasharray={circumference * 0.75}
                    strokeLinecap="round"
                />
                {/* Value arc */}
                <circle
                    cx="80"
                    cy="80"
                    r="70"
                    fill="none"
                    stroke={color}
                    strokeWidth="12"
                    strokeDasharray={circumference * 0.75}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    className="transition-all duration-1000 ease-out"
                />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-4xl font-bold" style={{ color }}>{score}</span>
                <span className="text-sm text-slate-500 mt-1">{getLabel(score)}</span>
            </div>
        </div>
    );
};

// Cash Flow Line Chart
export const CashFlowChart = ({ data }) => {
    return (
        <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                    <linearGradient id="colorInflow" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorOutflow" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
                    </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#94A3B8" />
                <YAxis tick={{ fontSize: 12 }} stroke="#94A3B8" tickFormatter={(value) => `₹${value / 1000}K`} />
                <Tooltip
                    contentStyle={{ borderRadius: '8px', border: '1px solid #E2E8F0' }}
                    formatter={(value) => [`₹${value.toLocaleString()}`, '']}
                />
                <Legend />
                <Area
                    type="monotone"
                    dataKey="inflow"
                    stroke="#10B981"
                    fillOpacity={1}
                    fill="url(#colorInflow)"
                    name="Inflow"
                />
                <Area
                    type="monotone"
                    dataKey="outflow"
                    stroke="#EF4444"
                    fillOpacity={1}
                    fill="url(#colorOutflow)"
                    name="Outflow"
                />
            </AreaChart>
        </ResponsiveContainer>
    );
};

// Compliance Pie Chart
export const CompliancePieChart = ({ data }) => {
    const COLORS = ['#16A34A', '#F59E0B', '#DC2626'];

    return (
        <ResponsiveContainer width="100%" height={200}>
            <PieChart>
                <Pie
                    data={data}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    fill="#8884d8"
                    paddingAngle={5}
                    dataKey="value"
                >
                    {data.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                </Pie>
                <Tooltip />
                <Legend />
            </PieChart>
        </ResponsiveContainer>
    );
};

// Bar Chart for Subsidies/Penalties
export const SubsidyBarChart = ({ data }) => {
    return (
        <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="#94A3B8" />
                <YAxis tick={{ fontSize: 12 }} stroke="#94A3B8" tickFormatter={(value) => `₹${value / 1000}K`} />
                <Tooltip
                    contentStyle={{ borderRadius: '8px', border: '1px solid #E2E8F0' }}
                    formatter={(value) => [`₹${value.toLocaleString()}`, '']}
                />
                <Bar dataKey="amount" fill="#10B981" radius={[4, 4, 0, 0]} />
            </BarChart>
        </ResponsiveContainer>
    );
};

export default { HealthScoreGauge, CashFlowChart, CompliancePieChart, SubsidyBarChart };
