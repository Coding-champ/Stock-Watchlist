import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import './VolumeProfile.css';
import '../styles/skeletons.css';

import { useApi } from '../hooks/useApi';
import { formatPrice } from '../utils/currencyUtils';

/**
 * Volume Profile Component
 * 
 * Displays volume distribution across price levels:
 * - Horizontal bars showing volume at each price level
 * - POC (Point of Control) - highlighted bar
 * - Value Area (70% of volume) - shaded region
 * - HVN/LVN markers
 */
function VolumeProfile({ stockId, period = 30, numBins = 50, height = 400, onLoad = null }) {
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { fetchApi } = useApi();

  useEffect(() => {
    if (!stockId) return;

    const fetchVolumeProfile = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchApi(`/stock-data/${stockId}/volume-profile?period_days=${period}&num_bins=${numBins}`);

        if (data.error) throw new Error(data.error);

        const chartData = data.price_levels.map((price, index) => ({
          price: price,
          volume: data.volumes[index],
          isPOC: Math.abs(price - data.poc) < 0.01,
          isInValueArea: price >= data.value_area.low && price <= data.value_area.high,
          isHVN: data.hvn_levels.some(hvn => Math.abs(price - hvn) < 0.01),
          isLVN: data.lvn_levels.some(lvn => Math.abs(price - lvn) < 0.01)
        }));

        setProfileData({ ...data, chartData });
        if (onLoad) onLoad(data);
      } catch (err) {
        console.error('Error fetching volume profile:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchVolumeProfile();
  }, [stockId, period, numBins, onLoad, fetchApi]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const stockLike = profileData && profileData.ticker ? { ticker_symbol: profileData.ticker, country: profileData.country } : null;
      return (
        <div className="volume-profile-tooltip">
          <p className="price">{formatPrice(Number(data.price), stockLike, 2)}</p>
          <p className="volume">Volume: {data.volume.toLocaleString()}</p>
          {data.isPOC && <p className="marker poc">POC - Point of Control</p>}
          {data.isInValueArea && <p className="marker va">In Value Area</p>}
          {data.isHVN && <p className="marker hvn">High Volume Node</p>}
          {data.isLVN && <p className="marker lvn">Low Volume Node</p>}
        </div>
      );
    }
    return null;
  };

  // Bar color based on classification
  const getBarColor = (data) => {
    if (data.isPOC) return '#22c55e'; // Green - POC
    if (data.isHVN) return '#3b82f6'; // Blue - HVN
    if (data.isInValueArea) return '#60a5fa'; // Light Blue - Value Area
    if (data.isLVN) return '#ef4444'; // Red - LVN
    return '#94a3b8'; // Gray - Normal
  };

  if (loading) {
    return (
      <div className="volume-profile-container loading">
        <div className="loading-spinner"></div>
        <p>Loading Volume Profile...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="volume-profile-container error">
        <p className="error-message">⚠️ {error}</p>
      </div>
    );
  }

  if (!profileData) {
    return null;
  }

  return (
    <div className="volume-profile-container">
      {/* Header with Key Levels */}
      <div className="volume-profile-header">
        <h4>Volume Profile ({period} days)</h4>
        <div className="key-levels">
          <div className="level-item poc">
            <span className="label">POC:</span>
            <span className="value">{formatPrice(Number(profileData.poc), profileData && profileData.ticker ? { ticker_symbol: profileData.ticker } : null, 2)}</span>
          </div>
          <div className="level-item vah">
            <span className="label">VAH:</span>
            <span className="value">{formatPrice(Number(profileData.value_area.high), profileData && profileData.ticker ? { ticker_symbol: profileData.ticker } : null, 2)}</span>
          </div>
          <div className="level-item val">
            <span className="label">VAL:</span>
            <span className="value">{formatPrice(Number(profileData.value_area.low), profileData && profileData.ticker ? { ticker_symbol: profileData.ticker } : null, 2)}</span>
          </div>
        </div>
      </div>

      {/* Volume Profile Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={profileData.chartData}
          layout="vertical"
          margin={{ top: 5, right: 20, bottom: 5, left: 5 }}
        >
          <XAxis type="number" hide />
          <YAxis 
            type="category" 
            dataKey="price"
            tickFormatter={(value) => formatPrice(Number(value), profileData && profileData.ticker ? { ticker_symbol: profileData.ticker } : null, 2)}
            width={60}
            tick={{ fontSize: 11 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="volume" radius={[0, 4, 4, 0]}>
            {profileData.chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="volume-profile-legend">
        <div className="legend-item">
          <span className="color-box poc"></span>
          <span>POC - Point of Control</span>
        </div>
        <div className="legend-item">
          <span className="color-box hvn"></span>
          <span>HVN - High Volume Node</span>
        </div>
        <div className="legend-item">
          <span className="color-box va"></span>
          <span>Value Area (70%)</span>
        </div>
        <div className="legend-item">
          <span className="color-box lvn"></span>
          <span>LVN - Low Volume Node</span>
        </div>
      </div>

      {/* Stats */}
      <div className="volume-profile-stats">
        <div className="stat">
          <span className="label">Total Volume:</span>
          <span className="value">{profileData.total_volume.toLocaleString()}</span>
        </div>
        <div className="stat">
          <span className="label">Price Range:</span>
          <span className="value">
            {formatPrice(Number(profileData.price_range.min), profileData && profileData.ticker ? { ticker_symbol: profileData.ticker } : null, 2)} - {formatPrice(Number(profileData.price_range.max), profileData && profileData.ticker ? { ticker_symbol: profileData.ticker } : null, 2)}
          </span>
        </div>
        <div className="stat">
          <span className="label">HVN Levels:</span>
          <span className="value">{profileData.hvn_levels.length}</span>
        </div>
        <div className="stat">
          <span className="label">LVN Levels:</span>
          <span className="value">{profileData.lvn_levels.length}</span>
        </div>
      </div>
    </div>
  );
}

export default VolumeProfile;
